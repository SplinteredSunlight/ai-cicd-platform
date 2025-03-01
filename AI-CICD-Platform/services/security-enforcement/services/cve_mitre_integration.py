import aiohttp
import asyncio
import structlog
from datetime import datetime, timedelta
import re
import json
from typing import Dict, List, Optional

from ..models.vulnerability import Vulnerability, SeverityLevel
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilitySource,
    VulnerabilityStatus
)

logger = structlog.get_logger()

class CVEMitreIntegration:
    """
    Integration with CVE MITRE database
    
    This class provides methods to fetch and process vulnerability data from the 
    MITRE CVE database, which is one of the most authoritative sources for CVE information.
    """
    
    def __init__(self):
        self.base_url = "https://cveawg.mitre.org/api"
        self.cve_url_template = "https://cve.mitre.org/cgi-bin/cvename.cgi?name={}"
    
    async def fetch_recent_cves(self, days_back: int = 30) -> List[VulnerabilityDatabaseEntry]:
        """
        Fetch recent CVEs from MITRE
        
        Args:
            days_back: Number of days to look back for recent CVEs
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        try:
            # Calculate the date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Construct the API URL
            url = f"{self.base_url}/cve/search"
            
            # Prepare the request payload
            payload = {
                "time": {
                    "modified": {
                        "$gte": start_date_str,
                        "$lte": end_date_str
                    }
                },
                "resultsPerPage": 2000  # Maximum allowed by the API
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"MITRE CVE API returned status {response.status}")
                        return []
                    
                    data = await response.json()
                    cves = data.get("cveRecords", [])
                    
                    # Process the CVEs
                    return await self._process_cves(cves)
        
        except Exception as e:
            logger.error(f"Error fetching CVEs from MITRE: {str(e)}")
            return []
    
    async def _process_cves(self, cves: List[Dict]) -> List[VulnerabilityDatabaseEntry]:
        """
        Process CVE records from MITRE
        
        Args:
            cves: List of CVE records from the MITRE API
            
        Returns:
            List of VulnerabilityDatabaseEntry objects
        """
        entries = []
        
        for cve_record in cves:
            try:
                # Extract the CVE metadata
                cve = cve_record.get("cve", {})
                
                # Get the CVE ID
                cve_id = cve.get("id")
                if not cve_id:
                    continue
                
                # Get the CVE metadata
                metadata = cve.get("metadata", {})
                
                # Get the CVE description
                descriptions = cve.get("descriptions", [])
                description = ""
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        description = desc.get("value", "")
                        break
                
                # Get the CVE title (use the first line of the description)
                title = description.split("\n")[0][:100] if description else cve_id
                
                # Get the CVE references
                references = []
                for ref in cve.get("references", []):
                    url = ref.get("url")
                    if url:
                        references.append(url)
                
                # Add the MITRE CVE URL
                references.append(self.cve_url_template.format(cve_id))
                
                # Get the CVE metrics
                metrics = cve.get("metrics", {})
                
                # Try to get CVSS v3.1 score first, then v3.0, then v2.0
                cvss_data = None
                cvss_score = 0.0
                
                if "cvssMetricV31" in metrics:
                    cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {}) if metrics["cvssMetricV31"] else {}
                elif "cvssMetricV30" in metrics:
                    cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {}) if metrics["cvssMetricV30"] else {}
                elif "cvssMetricV2" in metrics:
                    cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {}) if metrics["cvssMetricV2"] else {}
                
                if cvss_data:
                    cvss_score = float(cvss_data.get("baseScore", 0.0))
                
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
                
                # Get the affected components
                # This is a bit tricky as MITRE doesn't have a standardized format for this
                # We'll try to extract it from the configurations
                affected_component = ""
                affected_versions = []
                
                configurations = cve.get("configurations", [])
                for config in configurations:
                    for node in config.get("nodes", []):
                        for cpe_match in node.get("cpeMatch", []):
                            cpe = cpe_match.get("criteria", "")
                            if cpe.startswith("cpe:2.3:"):
                                # Parse the CPE string
                                parts = cpe.split(":")
                                if len(parts) > 5:
                                    vendor = parts[3]
                                    product = parts[4]
                                    version = parts[5]
                                    
                                    if not affected_component:
                                        affected_component = f"{vendor}:{product}"
                                    
                                    if version != "*" and version not in affected_versions:
                                        affected_versions.append(version)
                
                # Get the CWE IDs
                cwe_ids = []
                for weakness in cve.get("weaknesses", []):
                    for description in weakness.get("description", []):
                        if description.get("lang") == "en":
                            value = description.get("value", "")
                            if value.startswith("CWE-"):
                                cwe_ids.append(value)
                
                # Create the vulnerability object
                vulnerability = Vulnerability(
                    id=cve_id,
                    title=title,
                    description=description,
                    severity=severity,
                    cvss_score=cvss_score,
                    affected_component=affected_component,
                    references=references
                )
                
                # Create the database entry
                published_date = None
                if "datePublished" in metadata:
                    try:
                        published_date = datetime.fromisoformat(metadata["datePublished"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                last_updated = datetime.utcnow()
                if "dateUpdated" in metadata:
                    try:
                        last_updated = datetime.fromisoformat(metadata["dateUpdated"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                entry = VulnerabilityDatabaseEntry(
                    vulnerability=vulnerability,
                    sources=[VulnerabilitySource.OSINT],
                    status=VulnerabilityStatus.ACTIVE,
                    affected_versions=affected_versions,
                    published_date=published_date,
                    last_updated=last_updated,
                    cwe_ids=cwe_ids,
                    tags={"mitre", "cve"},
                    notes=f"Imported from MITRE CVE database on {datetime.utcnow().isoformat()}"
                )
                
                entries.append(entry)
            
            except Exception as e:
                logger.error(f"Error processing CVE {cve_record.get('cve', {}).get('id', 'unknown')}: {str(e)}")
                continue
        
        return entries
