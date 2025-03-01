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
import zipfile
import io

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

class SCAPIntegration:
    """
    Integration with SCAP (Security Content Automation Protocol)
    
    SCAP is a suite of specifications that standardize the format and nomenclature by which
    software flaw and security configuration information is communicated, both to machines
    and humans.
    
    SCAP includes several standards:
    - XCCDF (Extensible Configuration Checklist Description Format)
    - OVAL (Open Vulnerability and Assessment Language)
    - CCE (Common Configuration Enumeration)
    - CPE (Common Platform Enumeration)
    - CVE (Common Vulnerabilities and Exposures)
    - CVSS (Common Vulnerability Scoring System)
    
    API Documentation: https://csrc.nist.gov/projects/security-content-automation-protocol
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://nvd.nist.gov/download/scap/content"
        self.api_key = self.settings.scap_api_key
        self.temp_dir = Path(tempfile.gettempdir()) / "scap_content"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def fetch_scap_content_index(self) -> List[Dict[str, Any]]:
        """
        Fetch the index of available SCAP content
        
        Returns:
            List of SCAP content items
        """
        try:
            # Build the API URL
            url = f"{self.base_url}/index.json"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch data from the SCAP content index
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch SCAP content index", status=response.status)
                        return []
                    
                    data = await response.json()
                    return data.get("content", [])
        
        except Exception as e:
            logger.error("Error fetching SCAP content index", error=str(e))
            return []
    
    async def fetch_scap_content(self, content_id: str) -> Optional[Path]:
        """
        Fetch and extract SCAP content
        
        Args:
            content_id: ID of the SCAP content
            
        Returns:
            Path to the extracted SCAP content, or None if not available
        """
        try:
            # Build the API URL
            url = f"{self.base_url}/{content_id}.zip"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch data from the SCAP content
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch SCAP content", status=response.status)
                        return None
                    
                    # Read the ZIP content
                    content = await response.read()
                    
                    # Extract the ZIP content
                    content_dir = self.temp_dir / content_id
                    os.makedirs(content_dir, exist_ok=True)
                    
                    with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                        zip_file.extractall(content_dir)
                    
                    return content_dir
        
        except Exception as e:
            logger.error("Error fetching SCAP content", error=str(e))
            return None
    
    async def find_xccdf_file(self, content_dir: Path) -> Optional[Path]:
        """
        Find the XCCDF file in the SCAP content
        
        Args:
            content_dir: Path to the SCAP content directory
            
        Returns:
            Path to the XCCDF file, or None if not found
        """
        try:
            # Look for XCCDF files
            xccdf_files = list(content_dir.glob("**/*xccdf*.xml"))
            
            if not xccdf_files:
                return None
            
            # Return the first XCCDF file
            return xccdf_files[0]
        
        except Exception as e:
            logger.error("Error finding XCCDF file", error=str(e))
            return None
    
    async def parse_xccdf_file(self, xccdf_file: Path) -> Dict[str, Any]:
        """
        Parse an XCCDF file
        
        Args:
            xccdf_file: Path to the XCCDF file
            
        Returns:
            Parsed XCCDF content as a dictionary
        """
        try:
            # Parse the XML file
            tree = ET.parse(xccdf_file)
            root = tree.getroot()
            
            # Define namespaces
            ns = {
                "xccdf": "http://checklists.nist.gov/xccdf/1.2",
                "cpe": "http://cpe.mitre.org/language/2.0",
                "xhtml": "http://www.w3.org/1999/xhtml"
            }
            
            # Extract benchmark metadata
            benchmark = root
            benchmark_id = benchmark.get("id", "")
            benchmark_title = benchmark.find("./xccdf:title", ns)
            benchmark_title_text = benchmark_title.text if benchmark_title is not None else ""
            
            benchmark_description = benchmark.find("./xccdf:description", ns)
            benchmark_description_text = benchmark_description.text if benchmark_description is not None else ""
            
            # Extract profiles
            profiles = []
            for profile in benchmark.findall("./xccdf:Profile", ns):
                profile_id = profile.get("id", "")
                profile_title = profile.find("./xccdf:title", ns)
                profile_title_text = profile_title.text if profile_title is not None else ""
                
                profile_description = profile.find("./xccdf:description", ns)
                profile_description_text = profile_description.text if profile_description is not None else ""
                
                profiles.append({
                    "id": profile_id,
                    "title": profile_title_text,
                    "description": profile_description_text
                })
            
            # Extract rules
            rules = []
            for rule in benchmark.findall(".//xccdf:Rule", ns):
                rule_id = rule.get("id", "")
                rule_severity = rule.get("severity", "")
                
                rule_title = rule.find("./xccdf:title", ns)
                rule_title_text = rule_title.text if rule_title is not None else ""
                
                rule_description = rule.find("./xccdf:description", ns)
                rule_description_text = rule_description.text if rule_description is not None else ""
                
                # Extract fix elements
                fixes = []
                for fix in rule.findall("./xccdf:fix", ns):
                    fix_id = fix.get("id", "")
                    fix_platform = fix.get("platform", "")
                    fix_text = fix.text if fix is not None else ""
                    
                    fixes.append({
                        "id": fix_id,
                        "platform": fix_platform,
                        "text": fix_text
                    })
                
                # Extract check elements
                checks = []
                for check in rule.findall("./xccdf:check", ns):
                    check_system = check.get("system", "")
                    
                    check_content_refs = []
                    for content_ref in check.findall("./xccdf:check-content-ref", ns):
                        content_ref_href = content_ref.get("href", "")
                        content_ref_name = content_ref.get("name", "")
                        
                        check_content_refs.append({
                            "href": content_ref_href,
                            "name": content_ref_name
                        })
                    
                    checks.append({
                        "system": check_system,
                        "content_refs": check_content_refs
                    })
                
                # Extract CVE references
                cve_refs = []
                for reference in rule.findall("./xccdf:reference", ns):
                    ref_href = reference.get("href", "")
                    if "cve" in ref_href.lower():
                        cve_id = ref_href.split("/")[-1]
                        cve_refs.append(cve_id)
                
                rules.append({
                    "id": rule_id,
                    "severity": rule_severity,
                    "title": rule_title_text,
                    "description": rule_description_text,
                    "fixes": fixes,
                    "checks": checks,
                    "cve_refs": cve_refs
                })
            
            # Construct the result
            result = {
                "id": benchmark_id,
                "title": benchmark_title_text,
                "description": benchmark_description_text,
                "profiles": profiles,
                "rules": rules
            }
            
            return result
        
        except Exception as e:
            logger.error("Error parsing XCCDF file", error=str(e))
            return {}
    
    async def find_rules_for_cve(self, xccdf_content: Dict[str, Any], cve_id: str) -> List[Dict[str, Any]]:
        """
        Find rules in XCCDF content that address a specific CVE
        
        Args:
            xccdf_content: Parsed XCCDF content
            cve_id: ID of the vulnerability (e.g., CVE-2021-44228)
            
        Returns:
            List of rules that address the CVE
        """
        try:
            # Find rules that reference the CVE
            matching_rules = []
            for rule in xccdf_content.get("rules", []):
                if cve_id in rule.get("cve_refs", []):
                    matching_rules.append(rule)
            
            return matching_rules
        
        except Exception as e:
            logger.error("Error finding rules for CVE", error=str(e))
            return []
    
    async def fetch_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Fetch remediation actions for a specific vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability (e.g., CVE-2021-44228)
            
        Returns:
            List of remediation actions
        """
        try:
            # Fetch SCAP content index
            content_index = await self.fetch_scap_content_index()
            
            # Process each content item
            remediation_actions = []
            for content_item in content_index:
                content_id = content_item.get("id")
                if not content_id:
                    continue
                
                # Fetch and extract SCAP content
                content_dir = await self.fetch_scap_content(content_id)
                if not content_dir:
                    continue
                
                # Find XCCDF file
                xccdf_file = await self.find_xccdf_file(content_dir)
                if not xccdf_file:
                    continue
                
                # Parse XCCDF file
                xccdf_content = await self.parse_xccdf_file(xccdf_file)
                if not xccdf_content:
                    continue
                
                # Find rules for the CVE
                rules = await self.find_rules_for_cve(xccdf_content, vulnerability_id)
                if not rules:
                    continue
                
                # Create remediation actions for each rule
                for rule in rules:
                    # Extract fixes
                    steps = []
                    for fix in rule.get("fixes", []):
                        fix_text = fix.get("text", "")
                        if fix_text:
                            steps.append(fix_text)
                    
                    # If no fixes, use rule description
                    if not steps:
                        steps.append(rule.get("description", ""))
                    
                    # Determine remediation strategy
                    strategy = self._determine_remediation_strategy(rule, steps)
                    
                    # Create a remediation action
                    action = RemediationAction(
                        id=f"REM-SCAP-{uuid.uuid4().hex[:8]}",
                        vulnerability_id=vulnerability_id,
                        strategy=strategy,
                        description=f"Apply SCAP rule: {rule.get('title', 'Unknown')}",
                        steps=steps,
                        source=RemediationSource.SCAP,
                        status=RemediationStatus.PENDING,
                        metadata={
                            "scap_content_id": content_id,
                            "rule_id": rule.get("id"),
                            "severity": rule.get("severity"),
                            "checks": rule.get("checks")
                        }
                    )
                    
                    remediation_actions.append(action)
            
            return remediation_actions
        
        except Exception as e:
            logger.error("Error fetching remediation actions from SCAP", error=str(e))
            return []
    
    def _determine_remediation_strategy(self, rule: Dict[str, Any], steps: List[str]) -> RemediationStrategy:
        """
        Determine the remediation strategy based on the rule and steps
        
        Args:
            rule: Rule from XCCDF content
            steps: Extracted remediation steps
            
        Returns:
            Remediation strategy
        """
        # Default strategy
        strategy = RemediationStrategy.MITIGATE
        
        # Check rule title and description for strategy hints
        title = rule.get("title", "").lower()
        description = rule.get("description", "").lower()
        
        if any(keyword in title for keyword in ["update", "upgrade"]) or any(keyword in description for keyword in ["update", "upgrade"]):
            return RemediationStrategy.UPGRADE
        elif any(keyword in title for keyword in ["patch"]) or any(keyword in description for keyword in ["patch"]):
            return RemediationStrategy.PATCH
        elif any(keyword in title for keyword in ["replace", "alternative"]) or any(keyword in description for keyword in ["replace", "alternative"]):
            return RemediationStrategy.REPLACE
        elif any(keyword in title for keyword in ["workaround"]) or any(keyword in description for keyword in ["workaround"]):
            return RemediationStrategy.WORKAROUND
        
        # Check steps for strategy hints
        for step in steps:
            step_lower = step.lower()
            if any(keyword in step_lower for keyword in ["update", "upgrade"]):
                return RemediationStrategy.UPGRADE
            elif any(keyword in step_lower for keyword in ["patch"]):
                return RemediationStrategy.PATCH
            elif any(keyword in step_lower for keyword in ["replace", "alternative"]):
                return RemediationStrategy.REPLACE
            elif any(keyword in step_lower for keyword in ["workaround"]):
                return RemediationStrategy.WORKAROUND
        
        return strategy
