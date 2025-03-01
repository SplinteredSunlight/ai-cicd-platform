import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import structlog
import re
import uuid
import json
from bs4 import BeautifulSoup

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

class CERTIntegration:
    """
    Integration with CERT Coordination Center Vulnerability Notes Database
    
    The CERT Coordination Center (CERT/CC) is part of the Software Engineering Institute (SEI),
    a federally funded research and development center at Carnegie Mellon University.
    CERT/CC studies internet security vulnerabilities, publishes security alerts,
    researches long-term changes in networked systems, and develops information and
    training to help improve security.
    
    API Documentation: https://kb.cert.org/vuls/api/
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://kb.cert.org/vuls/api"
        self.web_url = "https://kb.cert.org/vuls/id"
        self.api_key = self.settings.cert_api_key
    
    async def fetch_vulnerability_notes(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch vulnerability notes from CERT/CC
        
        Args:
            days_back: Number of days to look back for recent vulnerabilities
            
        Returns:
            List of vulnerability notes
        """
        try:
            # Calculate the date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for the API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Build the API URL
            url = f"{self.base_url}/search"
            
            # Add API key if available
            headers = {
                "Content-Type": "application/json"
            }
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Build the request payload
            payload = {
                "dateUpdatedStart": start_date_str,
                "dateUpdatedEnd": end_date_str,
                "limit": 100
            }
            
            # Fetch data from the CERT/CC API
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch CERT/CC vulnerability notes", status=response.status)
                        return []
                    
                    data = await response.json()
                    return data.get("results", [])
        
        except Exception as e:
            logger.error("Error fetching CERT/CC vulnerability notes", error=str(e))
            return []
    
    async def fetch_vulnerability_note(self, vuln_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific vulnerability note from CERT/CC
        
        Args:
            vuln_id: ID of the vulnerability note (e.g., VU#123456)
            
        Returns:
            Vulnerability note as a dictionary, or None if not found
        """
        try:
            # Extract the numeric ID from the VU# format
            numeric_id = vuln_id.replace("VU#", "").strip()
            
            # Build the API URL
            url = f"{self.base_url}/id/{numeric_id}"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch data from the CERT/CC API
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch CERT/CC vulnerability note", status=response.status)
                        return None
                    
                    return await response.json()
        
        except Exception as e:
            logger.error("Error fetching CERT/CC vulnerability note", error=str(e))
            return None
    
    async def fetch_vulnerability_note_html(self, vuln_id: str) -> Optional[str]:
        """
        Fetch the HTML content of a vulnerability note from CERT/CC website
        
        Args:
            vuln_id: ID of the vulnerability note (e.g., VU#123456)
            
        Returns:
            HTML content of the vulnerability note, or None if not found
        """
        try:
            # Extract the numeric ID from the VU# format
            numeric_id = vuln_id.replace("VU#", "").strip()
            
            # Build the URL
            url = f"{self.web_url}/{numeric_id}"
            
            # Fetch data from the CERT/CC website
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch CERT/CC vulnerability note HTML", status=response.status)
                        return None
                    
                    return await response.text()
        
        except Exception as e:
            logger.error("Error fetching CERT/CC vulnerability note HTML", error=str(e))
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
            # Fetch vulnerability notes that reference this CVE
            notes = await self.fetch_vulnerability_notes(days_back=365)  # Look back a year for relevant notes
            
            # Filter notes that reference this vulnerability
            relevant_notes = []
            for note in notes:
                cve_ids = note.get("cve", [])
                if vulnerability_id in cve_ids:
                    relevant_notes.append(note)
            
            # If no relevant notes found, return empty list
            if not relevant_notes:
                return []
            
            # Fetch details for each relevant note
            remediation_actions = []
            for note in relevant_notes:
                note_id = note.get("id")
                if not note_id:
                    continue
                
                # Format the VU# ID
                vu_id = f"VU#{note_id}"
                
                # Fetch the note details
                note_details = await self.fetch_vulnerability_note(vu_id)
                if not note_details:
                    continue
                
                # Fetch the HTML content for better remediation extraction
                html_content = await self.fetch_vulnerability_note_html(vu_id)
                
                # Extract remediation steps
                steps = self._extract_remediation_steps(note_details, html_content)
                
                # Determine the remediation strategy
                strategy = self._determine_remediation_strategy(note_details, steps)
                
                # Create a remediation action
                action = RemediationAction(
                    id=f"REM-CERT-{uuid.uuid4().hex[:8]}",
                    vulnerability_id=vulnerability_id,
                    strategy=strategy,
                    description=f"Apply CERT/CC recommendation: {note_details.get('title', 'Unknown')}",
                    steps=steps,
                    source=RemediationSource.CERT,
                    status=RemediationStatus.PENDING,
                    metadata={
                        "cert_id": vu_id,
                        "publication_date": note_details.get("datePublic"),
                        "update_date": note_details.get("dateUpdated"),
                        "severity": note_details.get("severity"),
                        "url": f"{self.web_url}/{note_id}"
                    }
                )
                
                remediation_actions.append(action)
            
            return remediation_actions
        
        except Exception as e:
            logger.error("Error fetching remediation actions from CERT/CC", error=str(e))
            return []
    
    def _extract_remediation_steps(self, note_details: Dict[str, Any], html_content: Optional[str]) -> List[str]:
        """
        Extract remediation steps from a vulnerability note
        
        Args:
            note_details: Vulnerability note details from the API
            html_content: HTML content of the vulnerability note
            
        Returns:
            List of remediation steps
        """
        steps = []
        
        # First, try to extract from the API response
        if "solution" in note_details and note_details["solution"]:
            solution = note_details["solution"]
            
            # Split the solution into steps
            solution_steps = solution.split("\n")
            for step in solution_steps:
                step = step.strip()
                if step:
                    steps.append(step)
        
        # If no steps were found and HTML content is available, try to extract from HTML
        if not steps and html_content:
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Look for the solution section
                solution_heading = soup.find(lambda tag: tag.name in ["h2", "h3", "h4"] and "solution" in tag.text.lower())
                if solution_heading:
                    # Get all paragraphs and list items after the solution heading
                    solution_elements = []
                    current = solution_heading.next_sibling
                    while current and not (current.name in ["h2", "h3", "h4"]):
                        if current.name in ["p", "li", "div"]:
                            solution_elements.append(current)
                        current = current.next_sibling
                    
                    # Extract text from the solution elements
                    for element in solution_elements:
                        text = element.get_text().strip()
                        if text:
                            steps.append(text)
            except Exception as e:
                logger.error("Error parsing HTML content", error=str(e))
        
        # If still no steps, extract from other fields
        if not steps:
            # Try to extract from overview
            if "overview" in note_details and note_details["overview"]:
                overview = note_details["overview"]
                steps.append(f"Overview: {overview}")
            
            # Try to extract from impact
            if "impact" in note_details and note_details["impact"]:
                impact = note_details["impact"]
                steps.append(f"Impact: {impact}")
            
            # Try to extract from recommendations
            if "recommendations" in note_details and note_details["recommendations"]:
                recommendations = note_details["recommendations"]
                steps.append(f"Recommendations: {recommendations}")
        
        return steps
    
    def _determine_remediation_strategy(self, note_details: Dict[str, Any], steps: List[str]) -> RemediationStrategy:
        """
        Determine the remediation strategy based on the note details and steps
        
        Args:
            note_details: Vulnerability note details from the API
            steps: Extracted remediation steps
            
        Returns:
            Remediation strategy
        """
        # Default strategy
        strategy = RemediationStrategy.MITIGATE
        
        # Check if any steps mention upgrading
        for step in steps:
            step_lower = step.lower()
            if "upgrade" in step_lower or "update to" in step_lower or "update the" in step_lower:
                return RemediationStrategy.UPGRADE
            elif "patch" in step_lower:
                return RemediationStrategy.PATCH
            elif "replace" in step_lower or "alternative" in step_lower:
                return RemediationStrategy.REPLACE
            elif "workaround" in step_lower:
                return RemediationStrategy.WORKAROUND
        
        # Check solution field for strategy hints
        if "solution" in note_details and note_details["solution"]:
            solution_lower = note_details["solution"].lower()
            if "upgrade" in solution_lower or "update to" in solution_lower or "update the" in solution_lower:
                return RemediationStrategy.UPGRADE
            elif "patch" in solution_lower:
                return RemediationStrategy.PATCH
            elif "replace" in solution_lower or "alternative" in solution_lower:
                return RemediationStrategy.REPLACE
            elif "workaround" in solution_lower:
                return RemediationStrategy.WORKAROUND
        
        return strategy
