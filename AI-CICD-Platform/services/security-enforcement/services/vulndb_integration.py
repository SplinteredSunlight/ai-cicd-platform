import aiohttp
import asyncio
import structlog
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any

from ..models.vulnerability import Vulnerability, SeverityLevel
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilitySource,
    VulnerabilityStatus
)
from ..config import get_settings

logger = structlog.get_logger()

class VulnDBIntegration:
    """
    Integration with VulnDB (Risk Based Security's VulnDB)
    
    This class provides methods to fetch and process vulnerability data from VulnDB,
    which is a comprehensive commercial vulnerability database.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://vulndb.cyberriskanalytics.com/api/v1"
        self.headers = {
            "Accept": "application/json",
            "Authentication-Token": self.settings.vulndb_api_key
        }
    
    async def fetch_recent_vulnerabilities(self, days_back: int = 30) -> List[VulnerabilityDatabaseEntry]:
        """
        Fetch recent vulnerabilities from VulnDB
        
        Args:
            days_back: Number of days to look back for recent vulnerabilities
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        try:
            # Check if API key is configured
            if not self.settings.vulndb_api_key:
                logger.warning("VulnDB API key not configured")
                return []
            
            # Calculate the date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%d")
            
            # Construct the API URL
            url = f"{self.base_url}/vulnerabilities"
            params = {
                "modified_since": start_date_str,
                "size": 100,  # Maximum page size
                "page": 1
            }
            
            all_vulns = []
            
            # Paginate through all results
            while True:
                # Make the API request
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=self.headers) as response:
                        if response.status != 200:
                            logger.error(f"VulnDB API returned status {response.status}")
                            break
                        
                        data = await response.json()
                        vulns = data.get("results", [])
                        total_pages = data.get("total_pages", 1)
                        
                        all_vulns.extend(vulns)
                        
                        # Check if there are more pages
                        if params["page"] >= total_pages:
                            break
                        
                        params["page"] += 1
            
            # Process the vulnerabilities
            return await self._process_vulnerabilities(all_vulns)
        
        except Exception as e:
            logger.error(f"Error fetching vulnerabilities from VulnDB: {str(e)}")
            return []
    
    async def fetch_vulnerability_by_id(self, vuln_id: str) -> Optional[VulnerabilityDatabaseEntry]:
        """
        Fetch a specific vulnerability by ID
        
        Args:
            vuln_id: The vulnerability ID (e.g., CVE-...)
            
        Returns:
            VulnerabilityDatabaseEntry object or None if not found
        """
        try:
            # Check if API key is configured
            if not self.settings.vulndb_api_key:
                logger.warning("VulnDB API key not configured")
                return None
            
            # Construct the API URL
            url = f"{self.base_url}/vulnerabilities/find_by_cve_id"
            params = {"cve_id": vuln_id} if vuln_id.startswith("CVE-") else None
            
            if not params:
                logger.error(f"VulnDB only supports lookup by CVE ID, got {vuln_id}")
                return None
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"VulnDB API returned status {response.status}")
                        return None
                    
                    data = await response.json()
                    if not data.get("results"):
                        return None
                    
                    # Get the VulnDB ID
                    vulndb_id = data["results"][0].get("vulndb_id")
                    if not vulndb_id:
                        return None
                    
                    # Fetch the full vulnerability details
                    url = f"{self.base_url}/vulnerabilities/{vulndb_id}"
                    
                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 200:
                            logger.error(f"VulnDB API returned status {response.status}")
                            return None
                        
                        data = await response.json()
                        
                        # Process the vulnerability
                        entries = await self._process_vulnerabilities([data.get("vulnerability", {})])
                        return entries[0] if entries else None
        
        except Exception as e:
            logger.error(f"Error fetching vulnerability {vuln_id} from VulnDB: {str(e)}")
            return None
    
    async def _process_vulnerabilities(self, vulns: List[Dict[str, Any]]) -> List[VulnerabilityDatabaseEntry]:
        """
        Process vulnerability records from VulnDB
        
        Args:
            vulns: List of vulnerability records from the VulnDB API
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        entries = []
        
        for vuln in vulns:
            try:
                # Get the CVE ID if available
                cve_id = None
                ext_references = vuln.get("ext_references", [])
                for ref in ext_references:
                    if ref.get("type") == "CVE":
                        cve_id = ref.get("value")
                        break
                
                # Skip if no CVE ID
                if not cve_id:
                    continue
                
                # Get the vulnerability details
                title = vuln.get("title", "")
                description = vuln.get("description", "")
                
                # Get the references
                references = []
                for ref in ext_references:
                    url = ref.get("url")
                    if url:
                        references.append(url)
                
                # Get the CVSS data
                cvss_data = vuln.get("cvss_metrics", {})
                cvss_v3 = cvss_data.get("cvss_v3", {})
                cvss_v2 = cvss_data.get("cvss_v2", {})
                
                # Use CVSS v3 if available, otherwise v2
                cvss_score = 0.0
                if cvss_v3:
                    cvss_score = float(cvss_v3.get("score", 0.0))
                elif cvss_v2:
                    cvss_score = float(cvss_v2.get("score", 0.0))
                
                # Map the CVSS score to a severity level
                severity = SeverityLevel.UNKNOWN
                if cvss_score >= 9.0:
                    severity = SeverityLevel.CRITICAL
                elif cvss_score >= 7.0:
                    severity = SeverityLevel.HIGH
                elif cvss_score >= 4.0:
                    severity = SeverityLevel.MEDIUM
                elif cvss_score > 0:
                    severity = SeverityLevel.LOW
                
                # Get the affected products
                affected_component = ""
                affected_versions = []
                
                for product in vuln.get("products", []):
                    vendor = product.get("vendor", {}).get("name", "")
                    name = product.get("name", "")
                    
                    if vendor and name:
                        if not affected_component:
                            affected_component = f"{vendor}:{name}"
                        
                        # Get affected versions
                        for version in product.get("versions", []):
                            version_value = version.get("name", "")
                            if version_value and version_value not in affected_versions:
                                affected_versions.append(version_value)
                
                # Get the CWE IDs
                cwe_ids = []
                for classification in vuln.get("classifications", []):
                    if classification.get("type") == "CWE":
                        cwe_id = f"CWE-{classification.get('id')}"
                        if cwe_id not in cwe_ids:
                            cwe_ids.append(cwe_id)
                
                # Get the solution
                solution = vuln.get("solution", "")
                fix_version = None
                
                # Try to extract fix version from solution
                if solution:
                    # Look for common patterns like "upgrade to version X.Y.Z"
                    import re
                    fix_match = re.search(r"upgrade to (?:version )?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", solution, re.IGNORECASE)
                    if fix_match:
                        fix_version = fix_match.group(1)
                
                # Create the vulnerability object
                vulnerability = Vulnerability(
                    id=cve_id,
                    title=title,
                    description=description,
                    severity=severity,
                    cvss_score=cvss_score,
                    affected_component=affected_component,
                    fix_version=fix_version,
                    references=references
                )
                
                # Create the database entry
                published_date = None
                if "disclosure_date" in vuln:
                    try:
                        published_date = datetime.fromisoformat(vuln["disclosure_date"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                last_updated = datetime.utcnow()
                if "updated_at" in vuln:
                    try:
                        last_updated = datetime.fromisoformat(vuln["updated_at"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                # Get tags
                tags = {"vulndb"}
                for tag in vuln.get("keywords", []):
                    tags.add(tag.lower())
                
                entry = VulnerabilityDatabaseEntry(
                    vulnerability=vulnerability,
                    sources=[VulnerabilitySource.OSINT],
                    status=VulnerabilityStatus.ACTIVE,
                    affected_versions=affected_versions,
                    fixed_versions=[fix_version] if fix_version else [],
                    published_date=published_date,
                    last_updated=last_updated,
                    cwe_ids=cwe_ids,
                    tags=tags,
                    notes=f"Imported from VulnDB on {datetime.utcnow().isoformat()}"
                )
                
                entries.append(entry)
            
            except Exception as e:
                logger.error(f"Error processing vulnerability: {str(e)}")
                continue
        
        return entries
