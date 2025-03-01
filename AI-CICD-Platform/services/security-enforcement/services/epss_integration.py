import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import structlog
import re
import uuid
import csv
from io import StringIO

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

class EPSSIntegration:
    """
    Integration with EPSS (Exploit Prediction Scoring System)
    
    EPSS is a data-driven effort for estimating the likelihood (probability) that a software
    vulnerability will be exploited in the wild. The goal of EPSS is to assist network defenders
    in prioritizing vulnerability remediation.
    
    API Documentation: https://www.first.org/epss/api
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.first.org/data/v1/epss"
        self.api_key = self.settings.epss_api_key
        self.csv_url = "https://epss.cyentia.com/epss_scores-current.csv.gz"
    
    async def fetch_epss_score(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch EPSS score for a specific CVE
        
        Args:
            cve_id: ID of the vulnerability (e.g., CVE-2021-44228)
            
        Returns:
            Dictionary with EPSS score and percentile, or None if not found
        """
        try:
            # Build the API URL
            url = f"{self.base_url}?cve={cve_id}"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch data from the EPSS API
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch EPSS score", status=response.status)
                        return None
                    
                    data = await response.json()
                    
                    # Extract EPSS score
                    if data.get("status") == "OK" and data.get("data"):
                        for item in data.get("data", []):
                            if item.get("cve") == cve_id:
                                return {
                                    "cve_id": cve_id,
                                    "epss_score": item.get("epss"),
                                    "percentile": item.get("percentile"),
                                    "date": item.get("date")
                                }
                    
                    return None
        
        except Exception as e:
            logger.error("Error fetching EPSS score", error=str(e))
            return None
    
    async def fetch_epss_scores_batch(self, cve_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch EPSS scores for multiple CVEs
        
        Args:
            cve_ids: List of CVE IDs
            
        Returns:
            Dictionary mapping CVE IDs to EPSS scores
        """
        try:
            # Build the API URL
            cve_param = ",".join(cve_ids)
            url = f"{self.base_url}?cve={cve_param}"
            
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["X-API-KEY"] = self.api_key
            
            # Fetch data from the EPSS API
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch EPSS scores", status=response.status)
                        return {}
                    
                    data = await response.json()
                    
                    # Extract EPSS scores
                    results = {}
                    if data.get("status") == "OK" and data.get("data"):
                        for item in data.get("data", []):
                            cve_id = item.get("cve")
                            if cve_id in cve_ids:
                                results[cve_id] = {
                                    "cve_id": cve_id,
                                    "epss_score": item.get("epss"),
                                    "percentile": item.get("percentile"),
                                    "date": item.get("date")
                                }
                    
                    return results
        
        except Exception as e:
            logger.error("Error fetching EPSS scores", error=str(e))
            return {}
    
    async def fetch_epss_csv(self) -> Optional[str]:
        """
        Fetch the latest EPSS CSV file
        
        Returns:
            CSV content as a string, or None if not available
        """
        try:
            # Fetch the CSV file
            async with aiohttp.ClientSession() as session:
                async with session.get(self.csv_url) as response:
                    if response.status != 200:
                        logger.error("Failed to fetch EPSS CSV", status=response.status)
                        return None
                    
                    # Decompress gzip content
                    import gzip
                    content = await response.read()
                    decompressed = gzip.decompress(content).decode("utf-8")
                    
                    return decompressed
        
        except Exception as e:
            logger.error("Error fetching EPSS CSV", error=str(e))
            return None
    
    async def parse_epss_csv(self, csv_content: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse EPSS CSV content
        
        Args:
            csv_content: CSV content as a string
            
        Returns:
            Dictionary mapping CVE IDs to EPSS scores
        """
        try:
            results = {}
            
            # Parse CSV content
            reader = csv.DictReader(StringIO(csv_content))
            for row in reader:
                cve_id = row.get("cve")
                epss_score = float(row.get("epss", 0))
                percentile = float(row.get("percentile", 0))
                model_version = row.get("model_version")
                score_date = row.get("score_date")
                
                results[cve_id] = {
                    "cve_id": cve_id,
                    "epss_score": epss_score,
                    "percentile": percentile,
                    "model_version": model_version,
                    "date": score_date
                }
            
            return results
        
        except Exception as e:
            logger.error("Error parsing EPSS CSV", error=str(e))
            return {}
    
    async def fetch_all_epss_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch all EPSS scores from the CSV file
        
        Returns:
            Dictionary mapping CVE IDs to EPSS scores
        """
        try:
            # Fetch the CSV file
            csv_content = await self.fetch_epss_csv()
            if not csv_content:
                return {}
            
            # Parse the CSV content
            return await self.parse_epss_csv(csv_content)
        
        except Exception as e:
            logger.error("Error fetching all EPSS scores", error=str(e))
            return {}
    
    def _determine_remediation_priority(self, epss_score: float, percentile: float) -> str:
        """
        Determine the remediation priority based on EPSS score and percentile
        
        Args:
            epss_score: EPSS score (0.0-1.0)
            percentile: Percentile (0.0-100.0)
            
        Returns:
            Priority level (CRITICAL, HIGH, MEDIUM, LOW)
        """
        if epss_score >= 0.5 or percentile >= 95:
            return "CRITICAL"
        elif epss_score >= 0.3 or percentile >= 85:
            return "HIGH"
        elif epss_score >= 0.1 or percentile >= 50:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def fetch_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Fetch remediation actions for a specific vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability (e.g., CVE-2021-44228)
            
        Returns:
            List of remediation actions
        """
        try:
            # Fetch EPSS score for the vulnerability
            epss_data = await self.fetch_epss_score(vulnerability_id)
            if not epss_data:
                return []
            
            # Extract EPSS score and percentile
            epss_score = epss_data.get("epss_score", 0.0)
            percentile = epss_data.get("percentile", 0.0)
            
            # Determine remediation priority
            priority = self._determine_remediation_priority(epss_score, percentile)
            
            # Create a remediation action
            action = RemediationAction(
                id=f"REM-EPSS-{uuid.uuid4().hex[:8]}",
                vulnerability_id=vulnerability_id,
                strategy=RemediationStrategy.MITIGATE,
                description=f"Prioritize remediation based on EPSS score: {epss_score:.4f} (percentile: {percentile:.1f})",
                steps=[
                    f"EPSS Score: {epss_score:.4f} (likelihood of exploitation)",
                    f"Percentile: {percentile:.1f} (relative to other vulnerabilities)",
                    f"Priority: {priority}",
                    f"Date: {epss_data.get('date', 'Unknown')}",
                    "Recommendation: Prioritize remediation based on EPSS score and other vulnerability characteristics."
                ],
                source=RemediationSource.EPSS,
                status=RemediationStatus.PENDING,
                metadata={
                    "epss_score": epss_score,
                    "percentile": percentile,
                    "priority": priority,
                    "date": epss_data.get("date")
                }
            )
            
            return [action]
        
        except Exception as e:
            logger.error("Error fetching remediation actions from EPSS", error=str(e))
            return []
    
    async def enrich_vulnerability_with_epss(self, vulnerability: VulnerabilityDatabaseEntry) -> VulnerabilityDatabaseEntry:
        """
        Enrich a vulnerability with EPSS data
        
        Args:
            vulnerability: Vulnerability database entry
            
        Returns:
            Enriched vulnerability database entry
        """
        try:
            # Fetch EPSS score for the vulnerability
            epss_data = await self.fetch_epss_score(vulnerability.vulnerability.id)
            if not epss_data:
                return vulnerability
            
            # Extract EPSS score and percentile
            epss_score = epss_data.get("epss_score", 0.0)
            percentile = epss_data.get("percentile", 0.0)
            
            # Determine remediation priority
            priority = self._determine_remediation_priority(epss_score, percentile)
            
            # Add EPSS data to metadata
            if "epss" not in vulnerability.metadata:
                vulnerability.metadata["epss"] = {}
            
            vulnerability.metadata["epss"] = {
                "score": epss_score,
                "percentile": percentile,
                "priority": priority,
                "date": epss_data.get("date")
            }
            
            # Add EPSS tag
            vulnerability.tags.add("epss")
            
            return vulnerability
        
        except Exception as e:
            logger.error("Error enriching vulnerability with EPSS", error=str(e))
            return vulnerability
    
    async def enrich_vulnerabilities_with_epss(self, vulnerabilities: List[VulnerabilityDatabaseEntry]) -> List[VulnerabilityDatabaseEntry]:
        """
        Enrich multiple vulnerabilities with EPSS data
        
        Args:
            vulnerabilities: List of vulnerability database entries
            
        Returns:
            List of enriched vulnerability database entries
        """
        try:
            # Extract CVE IDs
            cve_ids = [v.vulnerability.id for v in vulnerabilities]
            
            # Fetch EPSS scores for all CVEs
            epss_data = await self.fetch_epss_scores_batch(cve_ids)
            
            # Enrich vulnerabilities
            enriched_vulnerabilities = []
            for vulnerability in vulnerabilities:
                cve_id = vulnerability.vulnerability.id
                if cve_id in epss_data:
                    # Extract EPSS score and percentile
                    epss_score = epss_data[cve_id].get("epss_score", 0.0)
                    percentile = epss_data[cve_id].get("percentile", 0.0)
                    
                    # Determine remediation priority
                    priority = self._determine_remediation_priority(epss_score, percentile)
                    
                    # Add EPSS data to metadata
                    if "epss" not in vulnerability.metadata:
                        vulnerability.metadata["epss"] = {}
                    
                    vulnerability.metadata["epss"] = {
                        "score": epss_score,
                        "percentile": percentile,
                        "priority": priority,
                        "date": epss_data[cve_id].get("date")
                    }
                    
                    # Add EPSS tag
                    vulnerability.tags.add("epss")
                
                enriched_vulnerabilities.append(vulnerability)
            
            return enriched_vulnerabilities
        
        except Exception as e:
            logger.error("Error enriching vulnerabilities with EPSS", error=str(e))
            return vulnerabilities
