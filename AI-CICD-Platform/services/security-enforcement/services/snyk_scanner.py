from typing import List, Dict, Optional
import httpx
import json
import os
from datetime import datetime
from ..config import get_settings, SNYK_CONFIG, SeverityLevel
from ..models.vulnerability import Vulnerability, VulnerabilityReport

class SnykScanner:
    def __init__(self):
        self.settings = get_settings()
        self.config = SNYK_CONFIG
        self.api_key = self.settings.snyk_api_key
        self.base_url = "https://snyk.io/api/v1"
        
        if not self.api_key:
            raise ValueError("Snyk API key not configured")

    async def scan_project(self, project_path: str, package_manager: Optional[str] = None) -> VulnerabilityReport:
        """
        Scan a project directory using Snyk CLI
        """
        try:
            # Determine package manager from project files if not specified
            if not package_manager:
                package_manager = await self._detect_package_manager(project_path)

            # Run Snyk test command
            cmd = [
                "snyk",
                "test",
                "--json",
                "--severity-threshold=" + self.config["severity_threshold"],
                "--org=" + self.config["org_id"],
                project_path
            ]

            result = await self._run_snyk_command(cmd)
            return self._parse_scan_results(result, project_path)

        except Exception as e:
            raise Exception(f"Snyk project scan error: {str(e)}")

    async def scan_container(self, image_url: str) -> VulnerabilityReport:
        """
        Scan a container image using Snyk Container
        """
        try:
            cmd = [
                "snyk",
                "container",
                "test",
                "--json",
                "--severity-threshold=" + self.config["severity_threshold"],
                "--org=" + self.config["org_id"],
                image_url
            ]

            result = await self._run_snyk_command(cmd)
            return self._parse_scan_results(result, image_url)

        except Exception as e:
            raise Exception(f"Snyk container scan error: {str(e)}")

    async def scan_dependencies(self, manifest_file: str) -> VulnerabilityReport:
        """
        Scan dependencies from a manifest file (e.g., package.json, requirements.txt)
        """
        try:
            cmd = [
                "snyk",
                "test",
                "--json",
                "--severity-threshold=" + self.config["severity_threshold"],
                "--org=" + self.config["org_id"],
                "--file=" + os.path.basename(manifest_file),
                os.path.dirname(manifest_file)
            ]

            result = await self._run_snyk_command(cmd)
            return self._parse_scan_results(result, manifest_file)

        except Exception as e:
            raise Exception(f"Snyk dependency scan error: {str(e)}")

    async def _run_snyk_command(self, cmd: List[str]) -> Dict:
        """
        Execute a Snyk CLI command and return the results
        """
        import subprocess

        try:
            # Set SNYK_TOKEN environment variable for authentication
            env = os.environ.copy()
            env["SNYK_TOKEN"] = self.api_key

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            stdout, stderr = process.communicate(timeout=300)

            if process.returncode not in [0, 1]:  # Snyk returns 1 when vulnerabilities are found
                raise Exception(f"Snyk command failed: {stderr.decode()}")

            return json.loads(stdout.decode())

        except subprocess.TimeoutExpired:
            raise Exception("Snyk command timed out")
        except Exception as e:
            raise Exception(f"Snyk command error: {str(e)}")

    def _parse_scan_results(self, scan_results: Dict, target: str) -> VulnerabilityReport:
        """
        Parse Snyk scan results into a standardized VulnerabilityReport
        """
        vulnerabilities = []

        for vuln in scan_results.get("vulnerabilities", []):
            severity = vuln.get("severity", "unknown").upper()
            if severity not in SeverityLevel.__members__:
                severity = "UNKNOWN"

            vulnerability = Vulnerability(
                id=vuln.get("id", "SNYK-UNKNOWN"),
                title=vuln.get("title", "Unknown"),
                description=vuln.get("description", "No description available"),
                severity=SeverityLevel[severity],
                cvss_score=float(vuln.get("cvssScore", 0.0)),
                affected_component=f"{vuln.get('package', 'unknown')}@{vuln.get('version', 'unknown')}",
                fix_version=vuln.get("fixedIn", [None])[0],
                references=vuln.get("references", [])
            )
            vulnerabilities.append(vulnerability)

        report = VulnerabilityReport(
            scanner_name="snyk",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target=target,
            vulnerabilities=vulnerabilities,
            metadata={
                "unique_count": scan_results.get("uniqueCount", 0),
                "path": scan_results.get("path", ""),
                "docker_image_id": scan_results.get("docker", {}).get("imageId", ""),
                "project_name": scan_results.get("projectName", ""),
                "org_id": self.config["org_id"]
            }
        )
        report.update_summary()
        return report

    async def _detect_package_manager(self, project_path: str) -> str:
        """
        Detect the package manager used in the project
        """
        package_files = {
            "package.json": "npm",
            "requirements.txt": "pip",
            "Gemfile": "rubygems",
            "pom.xml": "maven",
            "build.gradle": "gradle",
            "go.mod": "gomodules"
        }

        for file_name, manager in package_files.items():
            if os.path.exists(os.path.join(project_path, file_name)):
                return manager

        return "unknown"
