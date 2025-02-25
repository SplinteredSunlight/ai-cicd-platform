from typing import List, Dict, Optional
import httpx
import json
import subprocess
from ..config import get_settings, TRIVY_CONFIG, SeverityLevel
from ..models.vulnerability import Vulnerability

class TrivyScanner:
    def __init__(self):
        self.settings = get_settings()
        self.config = TRIVY_CONFIG

    async def scan_container(self, image_url: str) -> List[Vulnerability]:
        """
        Scan a container image using Trivy
        """
        try:
            cmd = [
                "trivy",
                "image",
                "--format", "json",
                "--severity", ",".join(self.config["severity"]),
                image_url
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=self.config["timeout"])

            if process.returncode != 0:
                raise Exception(f"Trivy scan failed: {stderr.decode()}")

            results = json.loads(stdout.decode())
            return self._parse_vulnerabilities(results)
        except subprocess.TimeoutExpired:
            raise Exception("Trivy scan timed out")
        except Exception as e:
            raise Exception(f"Trivy scan error: {str(e)}")

    async def scan_filesystem(self, path: str) -> List[Vulnerability]:
        """
        Scan a filesystem path using Trivy
        """
        try:
            cmd = [
                "trivy",
                "fs",
                "--format", "json",
                "--severity", ",".join(self.config["severity"]),
                path
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=self.config["timeout"])

            if process.returncode != 0:
                raise Exception(f"Trivy filesystem scan failed: {stderr.decode()}")

            results = json.loads(stdout.decode())
            return self._parse_vulnerabilities(results)
        except subprocess.TimeoutExpired:
            raise Exception("Trivy filesystem scan timed out")
        except Exception as e:
            raise Exception(f"Trivy filesystem scan error: {str(e)}")

    def _parse_vulnerabilities(self, scan_results: Dict) -> List[Vulnerability]:
        """
        Parse Trivy scan results into standardized Vulnerability objects
        """
        vulnerabilities = []
        
        for result in scan_results.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                vulnerability = Vulnerability(
                    id=vuln.get("VulnerabilityID"),
                    title=vuln.get("Title", "No title"),
                    description=vuln.get("Description", "No description"),
                    severity=SeverityLevel[vuln.get("Severity", "UNKNOWN").upper()],
                    cvss_score=float(vuln.get("CVSS", {}).get("nvd", {}).get("V3Score", 0.0)),
                    affected_component=f"{result.get('Target', 'Unknown')}:{vuln.get('PkgName')}@{vuln.get('InstalledVersion')}",
                    fix_version=vuln.get("FixedVersion"),
                    references=vuln.get("References", [])
                )
                vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def update_vulnerability_database(self):
        """
        Update Trivy's vulnerability database
        """
        try:
            cmd = ["trivy", "image", "--download-db-only"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=300)

            if process.returncode != 0:
                raise Exception(f"Database update failed: {stderr.decode()}")

            return True
        except Exception as e:
            raise Exception(f"Database update error: {str(e)}")
