from typing import List, Dict, Optional
import asyncio
from datetime import datetime
import json
import os
from cyclonedx.model import Bom, Component, ExternalReference
from cyclonedx.output import get_instance
from sigstore.sign import SignerError, Signer

from ..config import get_settings, VULNERABILITY_THRESHOLDS, Environment
from ..models.vulnerability import VulnerabilityReport, SeverityLevel
from .trivy_scanner import TrivyScanner
from .snyk_scanner import SnykScanner
from .zap_scanner import ZAPScanner

class SecurityCoordinator:
    def __init__(self):
        self.settings = get_settings()
        self.trivy = TrivyScanner()
        self.snyk = SnykScanner()
        self.zap = ZAPScanner()

    async def run_security_scan(
        self,
        repository_url: str,
        commit_sha: str,
        artifact_url: Optional[str] = None,
        scan_types: List[str] = None,
        blocking_severity: SeverityLevel = SeverityLevel.HIGH
    ) -> Dict:
        """
        Coordinate security scans across multiple tools
        """
        scan_types = scan_types or ["trivy", "snyk", "zap"]
        scan_tasks = []
        
        if "trivy" in scan_types and artifact_url:
            scan_tasks.append(self.trivy.scan_container(artifact_url))
        
        if "snyk" in scan_types:
            scan_tasks.append(self.snyk.scan_project(repository_url))
            if artifact_url:
                scan_tasks.append(self.snyk.scan_container(artifact_url))
        
        if "zap" in scan_types and artifact_url and artifact_url.startswith(("http://", "https://")):
            await self.zap.connect()
            scan_tasks.append(self.zap.scan_webapp(artifact_url))

        try:
            # Run scans concurrently
            scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            # Process results
            all_vulnerabilities = []
            for result in scan_results:
                if isinstance(result, Exception):
                    continue
                if isinstance(result, VulnerabilityReport):
                    all_vulnerabilities.extend(result.vulnerabilities)

            # Generate consolidated report
            consolidated_report = self._create_consolidated_report(
                all_vulnerabilities,
                repository_url,
                commit_sha
            )

            # Check if scan passes security threshold
            passed = self._check_security_threshold(
                consolidated_report,
                blocking_severity
            )

            # Generate and sign SBOM if scans pass
            sbom_url = None
            signature_url = None
            if passed:
                sbom_url, signature_url = await self.generate_and_sign_sbom(
                    repository_url,
                    commit_sha,
                    consolidated_report
                )

            return {
                "status": "success",
                "passed": passed,
                "report": consolidated_report.dict(),
                "sbom_url": sbom_url,
                "signature_url": signature_url
            }

        except Exception as e:
            raise Exception(f"Security scan coordination failed: {str(e)}")

    def _create_consolidated_report(
        self,
        vulnerabilities: List[Dict],
        repository_url: str,
        commit_sha: str
    ) -> VulnerabilityReport:
        """
        Create a consolidated report from all scan results
        """
        report = VulnerabilityReport(
            scanner_name="security-coordinator",
            scan_timestamp=datetime.utcnow().isoformat() + "Z",
            target=f"{repository_url}@{commit_sha}",
            vulnerabilities=vulnerabilities,
            metadata={
                "repository_url": repository_url,
                "commit_sha": commit_sha,
                "environment": self.settings.environment
            }
        )
        report.update_summary()
        return report

    def _check_security_threshold(
        self,
        report: VulnerabilityReport,
        blocking_severity: SeverityLevel
    ) -> bool:
        """
        Check if vulnerabilities exceed defined thresholds
        """
        env = Environment(self.settings.environment)
        thresholds = VULNERABILITY_THRESHOLDS[env]
        
        for severity in SeverityLevel:
            if severity.value in report.summary:
                found = report.summary[severity.value]
                allowed = thresholds.get(severity.value, 0)
                
                if found > allowed and severity.value <= blocking_severity:
                    return False
        
        return True

    async def generate_and_sign_sbom(
        self,
        repository_url: str,
        commit_sha: str,
        vulnerability_report: VulnerabilityReport
    ) -> tuple[str, str]:
        """
        Generate and sign SBOM using CycloneDX and Sigstore
        """
        try:
            # Create CycloneDX BOM
            bom = Bom()
            
            # Add components from vulnerability report
            for vuln in vulnerability_report.vulnerabilities:
                component = Component(
                    name=vuln.affected_component.split("@")[0],
                    version=vuln.affected_component.split("@")[1]
                )
                
                # Add vulnerability information
                ref = ExternalReference(
                    reference_type="issue-tracker",
                    url=vuln.references[0] if vuln.references else "",
                    comment=f"{vuln.severity}: {vuln.title}"
                )
                component.external_references.add(ref)
                
                bom.components.add(component)

            # Generate SBOM file
            output = get_instance(bom)
            sbom_path = os.path.join(
                self.settings.artifact_storage_path,
                f"sbom-{commit_sha}.json"
            )
            
            os.makedirs(os.path.dirname(sbom_path), exist_ok=True)
            with open(sbom_path, "w") as f:
                output.output_json(f)

            # Sign SBOM using Sigstore
            signer = Signer()
            signature_path = f"{sbom_path}.sig"
            
            with open(sbom_path, "rb") as f:
                signature = await signer.sign(f.read())
                
            with open(signature_path, "wb") as f:
                f.write(signature)

            # Return URLs (in practice, these would be uploaded to artifact storage)
            return sbom_path, signature_path

        except Exception as e:
            raise Exception(f"SBOM generation failed: {str(e)}")

    async def cleanup(self):
        """
        Cleanup resources
        """
        try:
            if self.zap and self.zap.zap:
                self.zap.zap.core.shutdown()
        except:
            pass
