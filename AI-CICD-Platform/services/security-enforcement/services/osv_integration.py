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

logger = structlog.get_logger()

class OSVIntegration:
    """
    Integration with OSV (Open Source Vulnerabilities) database
    
    This class provides methods to fetch and process vulnerability data from the 
    OSV database, which focuses on open source package vulnerabilities across ecosystems.
    """
    
    def __init__(self):
        self.base_url = "https://api.osv.dev/v1"
    
    async def fetch_vulnerabilities_by_package(
        self, 
        ecosystem: str, 
        package: str
    ) -> List[VulnerabilityDatabaseEntry]:
        """
        Fetch vulnerabilities for a specific package
        
        Args:
            ecosystem: The package ecosystem (e.g., npm, pypi, maven)
            package: The package name
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        try:
            # Construct the API URL
            url = f"{self.base_url}/query"
            
            # Prepare the request payload
            payload = {
                "package": {
                    "name": package,
                    "ecosystem": ecosystem
                }
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"OSV API returned status {response.status}")
                        return []
                    
                    data = await response.json()
                    vulns = data.get("vulns", [])
                    
                    # Process the vulnerabilities
                    return await self._process_vulnerabilities(vulns)
        
        except Exception as e:
            logger.error(f"Error fetching vulnerabilities from OSV: {str(e)}")
            return []
    
    async def fetch_recent_vulnerabilities(self, days_back: int = 30) -> List[VulnerabilityDatabaseEntry]:
        """
        Fetch recent vulnerabilities from OSV
        
        Args:
            days_back: Number of days to look back for recent vulnerabilities
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        try:
            # Calculate the date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Construct the API URL for the vulnerabilities list
            url = f"{self.base_url}/vulns"
            params = {"page_token": ""}
            
            all_vulns = []
            
            # Paginate through all results
            while True:
                # Make the API request
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"OSV API returned status {response.status}")
                            break
                        
                        data = await response.json()
                        vulns = data.get("vulns", [])
                        next_page_token = data.get("next_page_token", "")
                        
                        # Filter vulnerabilities by date
                        filtered_vulns = []
                        for vuln in vulns:
                            modified = vuln.get("modified", "")
                            if modified and modified >= start_date_str:
                                filtered_vulns.append(vuln)
                        
                        all_vulns.extend(filtered_vulns)
                        
                        # Check if there are more pages
                        if not next_page_token:
                            break
                        
                        params["page_token"] = next_page_token
            
            # Process the vulnerabilities
            return await self._process_vulnerabilities(all_vulns)
        
        except Exception as e:
            logger.error(f"Error fetching recent vulnerabilities from OSV: {str(e)}")
            return []
    
    async def fetch_vulnerability_by_id(self, vuln_id: str) -> Optional[VulnerabilityDatabaseEntry]:
        """
        Fetch a specific vulnerability by ID
        
        Args:
            vuln_id: The vulnerability ID (e.g., GHSA-..., CVE-...)
            
        Returns:
            VulnerabilityDatabaseEntry object or None if not found
        """
        try:
            # Construct the API URL
            url = f"{self.base_url}/vulns/{vuln_id}"
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"OSV API returned status {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    # Process the vulnerability
                    entries = await self._process_vulnerabilities([data])
                    return entries[0] if entries else None
        
        except Exception as e:
            logger.error(f"Error fetching vulnerability {vuln_id} from OSV: {str(e)}")
            return None
    
    async def _process_vulnerabilities(self, vulns: List[Dict[str, Any]]) -> List[VulnerabilityDatabaseEntry]:
        """
        Process vulnerability records from OSV
        
        Args:
            vulns: List of vulnerability records from the OSV API
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        entries = []
        
        for vuln in vulns:
            try:
                # Get the vulnerability ID
                vuln_id = vuln.get("id", "")
                if not vuln_id:
                    continue
                
                # Map to CVE ID if available
                cve_id = None
                for alias in vuln.get("aliases", []):
                    if alias.startswith("CVE-"):
                        cve_id = alias
                        break
                
                # Use CVE ID if available, otherwise use OSV ID
                vuln_id = cve_id or vuln_id
                
                # Get the vulnerability details
                summary = vuln.get("summary", "")
                details = vuln.get("details", "")
                
                # Get the references
                references = []
                for ref in vuln.get("references", []):
                    url = ref.get("url")
                    if url:
                        references.append(url)
                
                # Get the severity
                # OSV doesn't provide CVSS scores directly, so we'll estimate based on severity
                severity = SeverityLevel.UNKNOWN
                cvss_score = 0.0
                
                # Check for CVSS data in the database_specific field
                database_specific = vuln.get("database_specific", {})
                if database_specific:
                    # Try to extract severity from GitHub Security Advisory
                    ghsa_severity = database_specific.get("severity")
                    if ghsa_severity:
                        if ghsa_severity.lower() == "critical":
                            severity = SeverityLevel.CRITICAL
                            cvss_score = 9.5
                        elif ghsa_severity.lower() == "high":
                            severity = SeverityLevel.HIGH
                            cvss_score = 8.0
                        elif ghsa_severity.lower() == "moderate":
                            severity = SeverityLevel.MEDIUM
                            cvss_score = 5.5
                        elif ghsa_severity.lower() == "low":
                            severity = SeverityLevel.LOW
                            cvss_score = 3.0
                
                # Get the affected packages
                affected_component = ""
                affected_versions = []
                fixed_versions = []
                
                for affected in vuln.get("affected", []):
                    package = affected.get("package", {})
                    ecosystem = package.get("ecosystem", "")
                    name = package.get("name", "")
                    
                    if ecosystem and name:
                        if not affected_component:
                            affected_component = f"{ecosystem}:{name}"
                        
                        # Get affected versions
                        for version_range in affected.get("ranges", []):
                            for event in version_range.get("events", []):
                                introduced = event.get("introduced", "")
                                fixed = event.get("fixed", "")
                                
                                if introduced and introduced != "0":
                                    affected_versions.append(f">={introduced}")
                                
                                if fixed and fixed not in fixed_versions:
                                    fixed_versions.append(fixed)
                                    if affected_versions and affected_versions[-1].startswith(">="):
                                        affected_versions[-1] += f",<{fixed}"
                        
                        # Get specific affected versions
                        for version in affected.get("versions", []):
                            if version not in affected_versions:
                                affected_versions.append(version)
                
                # Create the vulnerability object
                vulnerability = Vulnerability(
                    id=vuln_id,
                    title=summary,
                    description=details,
                    severity=severity,
                    cvss_score=cvss_score,
                    affected_component=affected_component,
                    fix_version=fixed_versions[0] if fixed_versions else None,
                    references=references
                )
                
                # Create the database entry
                published_date = None
                if "published" in vuln:
                    try:
                        published_date = datetime.fromisoformat(vuln["published"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                last_updated = datetime.utcnow()
                if "modified" in vuln:
                    try:
                        last_updated = datetime.fromisoformat(vuln["modified"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                entry = VulnerabilityDatabaseEntry(
                    vulnerability=vulnerability,
                    sources=[VulnerabilitySource.OSINT],
                    status=VulnerabilityStatus.ACTIVE,
                    affected_versions=affected_versions,
                    fixed_versions=fixed_versions,
                    published_date=published_date,
                    last_updated=last_updated,
                    tags={"osv", ecosystem} if ecosystem else {"osv"},
                    notes=f"Imported from OSV database on {datetime.utcnow().isoformat()}"
                )
                
                entries.append(entry)
            
            except Exception as e:
                logger.error(f"Error processing vulnerability {vuln.get('id', 'unknown')}: {str(e)}")
                continue
        
        return entries
