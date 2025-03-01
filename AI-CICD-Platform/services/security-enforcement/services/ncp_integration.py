import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import structlog
import re
import uuid

from ..models.vulnerability import Vulnerability, SeverityLevel
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilitySource,
    VulnerabilityStatus
)
from ..models.remediation import (
    RemediationAction,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from ..config import get_settings

logger = structlog.get_logger()

class NCPIntegration:
    """
    Integration with NIST National Checklist Program (NCP)
    
    The NCP is the U.S. government repository of publicly available security checklists
    that provide detailed guidance on setting the security configuration of operating
    systems and applications.
    
    API Documentation: https://csrc.nist.gov/projects/national-checklist-program/services
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://csrc.nist.gov/CSRC/media/Projects/National-Checklist-Program/services/xml"
        self.api_key = self.settings.ncp_api_key
    
    async def fetch_checklists(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch security checklists from the NCP
        
        Args:
            days_back: Number of days to look back for recent checklists
            
        Returns:
            List of checklists
        """
        try:
            # Calculate the date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Build the API URL
            url = f"{self.base_url}/checklists.xml"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch data from the NCP API
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch NCP checklists", status=response.status)
                        return []
                    
                    # Parse XML response
                    import xml.etree.ElementTree as ET
                    xml_text = await response.text()
                    root = ET.fromstring(xml_text)
                    
                    # Extract checklists
                    checklists = []
                    for checklist in root.findall(".//Checklist"):
                        # Extract basic information
                        checklist_id = checklist.find("ChecklistID").text
                        name = checklist.find("Name").text
                        description = checklist.find("Description").text
                        
                        # Extract publication date
                        pub_date_elem = checklist.find("PublicationDate")
                        pub_date = pub_date_elem.text if pub_date_elem is not None else None
                        
                        # Skip if published before the start date
                        if pub_date:
                            pub_date_obj = datetime.strptime(pub_date, "%Y-%m-%d")
                            if pub_date_obj < start_date:
                                continue
                        
                        # Extract target products
                        target_products = []
                        for product in checklist.findall(".//TargetProduct"):
                            target_products.append(product.text)
                        
                        # Extract CVEs addressed by this checklist
                        cves = []
                        for cve in checklist.findall(".//CVE"):
                            cves.append(cve.text)
                        
                        # Extract checklist content
                        content_url = None
                        for resource in checklist.findall(".//Resource"):
                            if resource.find("Type").text == "Checklist":
                                content_url = resource.find("Location").text
                        
                        # Add to results
                        checklists.append({
                            "id": checklist_id,
                            "name": name,
                            "description": description,
                            "publication_date": pub_date,
                            "target_products": target_products,
                            "cves": cves,
                            "content_url": content_url
                        })
                    
                    return checklists
        
        except Exception as e:
            logger.error("Error fetching NCP checklists", error=str(e))
            return []
    
    async def fetch_checklist_content(self, content_url: str) -> Optional[str]:
        """
        Fetch the content of a specific checklist
        
        Args:
            content_url: URL of the checklist content
            
        Returns:
            Checklist content as text, or None if not available
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch checklist content", status=response.status)
                        return None
                    
                    return await response.text()
        
        except Exception as e:
            logger.error("Error fetching checklist content", error=str(e))
            return None
    
    async def fetch_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Fetch remediation actions for a specific vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability (e.g., CVE-2021-44228)
            
        Returns:
            List of remediation actions
        """
        try:
            # Fetch checklists that address this vulnerability
            checklists = await self.fetch_checklists(days_back=365)  # Look back a year for relevant checklists
            
            # Filter checklists that address this vulnerability
            relevant_checklists = []
            for checklist in checklists:
                if vulnerability_id in checklist.get("cves", []):
                    relevant_checklists.append(checklist)
            
            # If no relevant checklists found, return empty list
            if not relevant_checklists:
                return []
            
            # Fetch content for each relevant checklist
            remediation_actions = []
            for checklist in relevant_checklists:
                content_url = checklist.get("content_url")
                if not content_url:
                    continue
                
                content = await self.fetch_checklist_content(content_url)
                if not content:
                    continue
                
                # Extract remediation steps from the content
                # This is a simplified implementation - in a real system, this would involve
                # parsing the specific format of the checklist (e.g., XCCDF, OVAL)
                steps = self._extract_remediation_steps(content)
                
                # Create a remediation action
                action = RemediationAction(
                    id=f"REM-NCP-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vulnerability_id,
                    strategy=RemediationStrategy.MITIGATE,
                    description=f"Apply NIST checklist: {checklist.get('name')}",
                    steps=steps,
                    source=RemediationSource.NCP,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "checklist_id": checklist.get("id"),
                        "publication_date": checklist.get("publication_date"),
                        "target_products": checklist.get("target_products"),
                        "content_url": content_url
                    }
                )
                
                remediation_actions.append(action)
            
            return remediation_actions
        
        except Exception as e:
            logger.error("Error fetching remediation actions from NCP", error=str(e))
            return []
    
    def _extract_remediation_steps(self, content: str) -> List[str]:
        """
        Extract remediation steps from checklist content
        
        Args:
            content: Checklist content as text
            
        Returns:
            List of remediation steps
        """
        # This is a simplified implementation - in a real system, this would involve
        # parsing the specific format of the checklist (e.g., XCCDF, OVAL)
        
        # For XML content, try to extract steps from Rule elements
        if content.strip().startswith("<?xml") or content.strip().startswith("<"):
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(content)
                
                steps = []
                for rule in root.findall(".//Rule") + root.findall(".//rule"):
                    title = rule.find("title")
                    description = rule.find("description")
                    fix = rule.find("fix")
                    
                    if title is not None and title.text:
                        steps.append(title.text.strip())
                    
                    if description is not None and description.text:
                        steps.append(f"Description: {description.text.strip()}")
                    
                    if fix is not None and fix.text:
                        steps.append(f"Fix: {fix.text.strip()}")
                
                return steps
            except Exception:
                # If XML parsing fails, fall back to text extraction
                pass
        
        # For text content, extract lines that look like steps
        steps = []
        for line in content.split("\n"):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Look for lines that start with numbers, bullets, or keywords
            if (re.match(r"^\d+\.", line) or
                re.match(r"^-\s", line) or
                re.match(r"^•\s", line) or
                re.match(r"^Step\s+\d+:", line) or
                "configure" in line.lower() or
                "set " in line.lower() or
                "change " in line.lower() or
                "update " in line.lower() or
                "modify " in line.lower() or
                "install " in line.lower() or
                "remove " in line.lower()):
                steps.append(line)
        
        # If no steps were found, include the first few non-empty lines
        if not steps:
            count = 0
            for line in content.split("\n"):
                line = line.strip()
                if line:
                    steps.append(line)
                    count += 1
                    if count >= 5:
                        break
        
        return steps
