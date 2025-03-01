import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import structlog
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import os

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

class OVALIntegration:
    """
    Integration with OVAL (Open Vulnerability and Assessment Language)
    
    OVAL is an international standard to promote open and publicly available security content,
    and to standardize the transfer of this information across the entire spectrum of security tools and services.
    
    OVAL includes a language for encoding system details, and an assortment of content repositories
    held throughout the community.
    
    API Documentation: https://oval.cisecurity.org/repository
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://oval.cisecurity.org/repository/download"
        self.api_key = self.settings.oval_api_key
        self.temp_dir = Path(tempfile.gettempdir()) / "oval_definitions"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def fetch_oval_definitions(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch OVAL definitions from the repository
        
        Args:
            days_back: Number of days to look back for recent definitions
            
        Returns:
            List of OVAL definitions
        """
        try:
            # Calculate the date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Build the API URL for the index
            url = f"{self.base_url}/index.json"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch the index from the OVAL repository
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch OVAL index", status=response.status)
                        return []
                    
                    index_data = await response.json()
                    
                    # Extract definitions
                    definitions = []
                    for definition in index_data.get("definitions", []):
                        # Extract publication date
                        pub_date_str = definition.get("submitted", "")
                        try:
                            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                        except (ValueError, TypeError):
                            # Skip if date is invalid or missing
                            continue
                        
                        # Skip if published before the start date
                        if pub_date < start_date:
                            continue
                        
                        # Add to results
                        definitions.append(definition)
                    
                    return definitions
        
        except Exception as e:
            logger.error("Error fetching OVAL definitions", error=str(e))
            return []
    
    async def fetch_oval_definition(self, definition_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific OVAL definition
        
        Args:
            definition_id: ID of the OVAL definition
            
        Returns:
            OVAL definition as a dictionary, or None if not found
        """
        try:
            # Build the API URL
            url = f"{self.base_url}/definition/{definition_id}"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch the definition from the OVAL repository
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch OVAL definition", status=response.status)
                        return None
                    
                    # Save the XML content to a temporary file
                    xml_content = await response.text()
                    temp_file = self.temp_dir / f"{definition_id}.xml"
                    with open(temp_file, "w") as f:
                        f.write(xml_content)
                    
                    # Parse the XML content
                    return self._parse_oval_definition(temp_file)
        
        except Exception as e:
            logger.error("Error fetching OVAL definition", error=str(e))
            return None
    
    def _parse_oval_definition(self, xml_file: Path) -> Dict[str, Any]:
        """
        Parse an OVAL definition XML file
        
        Args:
            xml_file: Path to the XML file
            
        Returns:
            Parsed OVAL definition as a dictionary
        """
        try:
            # Parse the XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Define namespaces
            ns = {
                "oval": "http://oval.mitre.org/XMLSchema/oval-common-5",
                "oval-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance"
            }
            
            # Extract definition metadata
            definition = root.find(".//oval-def:definition", ns)
            if definition is None:
                return {}
            
            definition_id = definition.get("id", "")
            definition_class = definition.get("class", "")
            
            # Extract metadata
            metadata = definition.find("./oval-def:metadata", ns)
            if metadata is None:
                return {}
            
            title = metadata.find("./oval-def:title", ns)
            title_text = title.text if title is not None else ""
            
            description = metadata.find("./oval-def:description", ns)
            description_text = description.text if description is not None else ""
            
            # Extract affected platforms
            affected = metadata.findall("./oval-def:affected", ns)
            platforms = []
            for platform in affected:
                family = platform.get("family", "")
                platforms.append(family)
            
            # Extract references
            references = metadata.findall("./oval-def:reference", ns)
            refs = []
            for ref in references:
                ref_id = ref.get("ref_id", "")
                ref_url = ref.get("ref_url", "")
                ref_source = ref.get("source", "")
                refs.append({
                    "id": ref_id,
                    "url": ref_url,
                    "source": ref_source
                })
            
            # Extract CVEs
            cves = []
            for ref in refs:
                if ref["source"] == "CVE":
                    cves.append(ref["id"])
            
            # Extract criteria
            criteria = definition.find("./oval-def:criteria", ns)
            criteria_operator = criteria.get("operator", "") if criteria is not None else ""
            
            # Extract criteria items
            criteria_items = []
            if criteria is not None:
                for criterion in criteria.findall(".//oval-def:criterion", ns):
                    test_ref = criterion.get("test_ref", "")
                    comment = criterion.get("comment", "")
                    criteria_items.append({
                        "test_ref": test_ref,
                        "comment": comment
                    })
            
            # Extract tests
            tests = root.findall(".//oval-def:test", ns)
            test_details = []
            for test in tests:
                test_id = test.get("id", "")
                test_comment = test.get("comment", "")
                test_details.append({
                    "id": test_id,
                    "comment": test_comment
                })
            
            # Extract objects and states
            objects = root.findall(".//oval-def:object", ns)
            object_details = []
            for obj in objects:
                obj_id = obj.get("id", "")
                obj_details = []
                for child in obj:
                    if child.text:
                        obj_details.append({
                            "name": child.tag.split("}")[-1],
                            "value": child.text
                        })
                object_details.append({
                    "id": obj_id,
                    "details": obj_details
                })
            
            states = root.findall(".//oval-def:state", ns)
            state_details = []
            for state in states:
                state_id = state.get("id", "")
                state_details_list = []
                for child in state:
                    if child.text:
                        state_details_list.append({
                            "name": child.tag.split("}")[-1],
                            "value": child.text
                        })
                state_details.append({
                    "id": state_id,
                    "details": state_details_list
                })
            
            # Construct the result
            result = {
                "id": definition_id,
                "class": definition_class,
                "title": title_text,
                "description": description_text,
                "platforms": platforms,
                "references": refs,
                "cves": cves,
                "criteria": {
                    "operator": criteria_operator,
                    "items": criteria_items
                },
                "tests": test_details,
                "objects": object_details,
                "states": state_details
            }
            
            return result
        
        except Exception as e:
            logger.error("Error parsing OVAL definition", error=str(e))
            return {}
    
    async def fetch_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Fetch remediation actions for a specific vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability (e.g., CVE-2021-44228)
            
        Returns:
            List of remediation actions
        """
        try:
            # Fetch OVAL definitions that reference this CVE
            definitions = await self.fetch_oval_definitions(days_back=365)  # Look back a year for relevant definitions
            
            # Filter definitions that reference this vulnerability
            relevant_definitions = []
            for definition in definitions:
                refs = definition.get("references", [])
                for ref in refs:
                    if ref.get("source") == "CVE" and ref.get("ref_id") == vulnerability_id:
                        relevant_definitions.append(definition)
            
            # If no relevant definitions found, return empty list
            if not relevant_definitions:
                return []
            
            # Fetch details for each relevant definition
            remediation_actions = []
            for definition in relevant_definitions:
                definition_id = definition.get("id")
                if not definition_id:
                    continue
                
                # Fetch the definition details
                definition_details = await self.fetch_oval_definition(definition_id)
                if not definition_details:
                    continue
                
                # Extract remediation steps
                steps = self._extract_remediation_steps(definition_details)
                
                # Determine the remediation strategy
                strategy = self._determine_remediation_strategy(definition_details, steps)
                
                # Create a remediation action
                action = RemediationAction(
                    id=f"REM-OVAL-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vulnerability_id,
                    strategy=strategy,
                    description=f"Apply OVAL definition: {definition_details.get('title', 'Unknown')}",
                    steps=steps,
                    source=RemediationSource.OVAL,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "oval_id": definition_id,
                        "class": definition_details.get("class"),
                        "platforms": definition_details.get("platforms"),
                        "references": definition_details.get("references")
                    }
                )
                
                remediation_actions.append(action)
            
            return remediation_actions
        
        except Exception as e:
            logger.error("Error fetching remediation actions from OVAL", error=str(e))
            return []
    
    def _extract_remediation_steps(self, definition_details: Dict[str, Any]) -> List[str]:
        """
        Extract remediation steps from an OVAL definition
        
        Args:
            definition_details: OVAL definition details
            
        Returns:
            List of remediation steps
        """
        steps = []
        
        # Add title and description
        title = definition_details.get("title")
        if title:
            steps.append(f"Title: {title}")
        
        description = definition_details.get("description")
        if description:
            steps.append(f"Description: {description}")
        
        # Extract affected platforms
        platforms = definition_details.get("platforms", [])
        if platforms:
            steps.append(f"Affected platforms: {', '.join(platforms)}")
        
        # Extract criteria
        criteria = definition_details.get("criteria", {})
        criteria_items = criteria.get("items", [])
        if criteria_items:
            steps.append("Criteria:")
            for item in criteria_items:
                comment = item.get("comment")
                if comment:
                    steps.append(f"- {comment}")
        
        # Extract tests
        tests = definition_details.get("tests", [])
        if tests:
            steps.append("Tests:")
            for test in tests:
                comment = test.get("comment")
                if comment:
                    steps.append(f"- {comment}")
        
        # Extract objects and states
        objects = definition_details.get("objects", [])
        if objects:
            steps.append("Objects:")
            for obj in objects:
                obj_id = obj.get("id")
                obj_details = obj.get("details", [])
                if obj_details:
                    steps.append(f"- Object {obj_id}:")
                    for detail in obj_details:
                        name = detail.get("name")
                        value = detail.get("value")
                        if name and value:
                            steps.append(f"  - {name}: {value}")
        
        states = definition_details.get("states", [])
        if states:
            steps.append("States:")
            for state in states:
                state_id = state.get("id")
                state_details = state.get("details", [])
                if state_details:
                    steps.append(f"- State {state_id}:")
                    for detail in state_details:
                        name = detail.get("name")
                        value = detail.get("value")
                        if name and value:
                            steps.append(f"  - {name}: {value}")
        
        # Extract remediation hints from criteria and tests
        remediation_hints = []
        for item in criteria_items:
            comment = item.get("comment", "").lower()
            if any(keyword in comment for keyword in ["update", "upgrade", "patch", "install", "remove", "configure", "disable", "enable"]):
                remediation_hints.append(item.get("comment"))
        
        for test in tests:
            comment = test.get("comment", "").lower()
            if any(keyword in comment for keyword in ["update", "upgrade", "patch", "install", "remove", "configure", "disable", "enable"]):
                remediation_hints.append(test.get("comment"))
        
        if remediation_hints:
            steps.append("Remediation hints:")
            for hint in remediation_hints:
                steps.append(f"- {hint}")
        
        return steps
    
    def _determine_remediation_strategy(self, definition_details: Dict[str, Any], steps: List[str]) -> RemediationStrategy:
        """
        Determine the remediation strategy based on the definition details and steps
        
        Args:
            definition_details: OVAL definition details
            steps: Extracted remediation steps
            
        Returns:
            Remediation strategy
        """
        # Default strategy
        strategy = RemediationStrategy.MITIGATE
        
        # Check title and description for strategy hints
        title = definition_details.get("title", "").lower()
        description = definition_details.get("description", "").lower()
        
        if any(keyword in title for keyword in ["update", "upgrade"]) or any(keyword in description for keyword in ["update", "upgrade"]):
            return RemediationStrategy.UPGRADE
        elif any(keyword in title for keyword in ["patch"]) or any(keyword in description for keyword in ["patch"]):
            return RemediationStrategy.PATCH
        elif any(keyword in title for keyword in ["replace", "alternative"]) or any(keyword in description for keyword in ["replace", "alternative"]):
            return RemediationStrategy.REPLACE
        elif any(keyword in title for keyword in ["workaround"]) or any(keyword in description for keyword in ["workaround"]):
            return RemediationStrategy.WORKAROUND
        
        # Check criteria and tests for strategy hints
        criteria = definition_details.get("criteria", {})
        criteria_items = criteria.get("items", [])
        
        for item in criteria_items:
            comment = item.get("comment", "").lower()
            if any(keyword in comment for keyword in ["update", "upgrade"]):
                return RemediationStrategy.UPGRADE
            elif any(keyword in comment for keyword in ["patch"]):
                return RemediationStrategy.PATCH
            elif any(keyword in comment for keyword in ["replace", "alternative"]):
                return RemediationStrategy.REPLACE
            elif any(keyword in comment for keyword in ["workaround"]):
                return RemediationStrategy.WORKAROUND
        
        tests = definition_details.get("tests", [])
        for test in tests:
            comment = test.get("comment", "").lower()
            if any(keyword in comment for keyword in ["update", "upgrade"]):
                return RemediationStrategy.UPGRADE
            elif any(keyword in comment for keyword in ["patch"]):
                return RemediationStrategy.PATCH
            elif any(keyword in comment for keyword in ["replace", "alternative"]):
                return RemediationStrategy.REPLACE
            elif any(keyword in comment for keyword in ["workaround"]):
                return RemediationStrategy.WORKAROUND
        
        return strategy
