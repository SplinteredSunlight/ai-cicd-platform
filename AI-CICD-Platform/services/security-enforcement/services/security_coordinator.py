from typing import List, Dict, Optional, Any
import asyncio
from datetime import datetime
import json
import os
import uuid
from cyclonedx.model import Bom, Component, ExternalReference
from cyclonedx.output import get_instance
from sigstore.sign import SignerError, Signer

from ..config import get_settings, VULNERABILITY_THRESHOLDS, Environment
from ..models.vulnerability import VulnerabilityReport, SeverityLevel, Vulnerability
from ..models.vulnerability_database import (
    VulnerabilityDatabaseQuery,
    VulnerabilityDatabaseEntry,
    VulnerabilityStatus,
    VulnerabilitySource
)
from ..models.compliance_report import (
    ComplianceReport,
    ComplianceStandard,
    ComplianceRequirement,
    ComplianceViolation,
    ComplianceStatus,
    ComplianceReportSummary,
    ComplianceReportRequest
)
from ..models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from .trivy_scanner import TrivyScanner
from .snyk_scanner import SnykScanner
from .zap_scanner import ZAPScanner
from .vulnerability_database import VulnerabilityDatabase
from .compliance_reporting import ComplianceReportingService
from .remediation_service import RemediationService

class SecurityCoordinator:
    def __init__(self):
        self.settings = get_settings()
        self.trivy = TrivyScanner()
        self.snyk = SnykScanner()
        self.zap = ZAPScanner()
        self.vuln_db = VulnerabilityDatabase()
        self.compliance_service = ComplianceReportingService(self.vuln_db)
        self.remediation_service = RemediationService(self.vuln_db)
        
        # Initialize vulnerability database if auto-update is enabled
        if self.settings.vuln_db_auto_update:
            asyncio.create_task(self._initialize_vuln_db())
    
    async def _initialize_vuln_db(self):
        """Initialize vulnerability database with auto-update"""
        try:
            sources = [VulnerabilitySource(s) for s in self.settings.vuln_db_sources]
            await self.vuln_db.update_database(sources=sources)
        except Exception as e:
            # Log error but don't fail initialization
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to initialize vulnerability database", error=str(e))

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
            
            # Enrich vulnerabilities with database information
            enriched_vulnerabilities = await self.enrich_vulnerabilities_with_database(all_vulnerabilities)
            
            # Store newly discovered vulnerabilities in the database
            await self._store_vulnerabilities_in_database(enriched_vulnerabilities)

            # Generate consolidated report
            consolidated_report = self._create_consolidated_report(
                enriched_vulnerabilities,
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
    
    async def enrich_vulnerabilities_with_database(self, vulnerabilities: List[Vulnerability]) -> List[Vulnerability]:
        """
        Enrich vulnerability information with data from the vulnerability database
        """
        enriched_vulnerabilities = []
        
        for vuln in vulnerabilities:
            # Try to find the vulnerability in the database
            db_entry = await self.vuln_db.get_vulnerability(vuln.id)
            
            if db_entry:
                # Enrich with database information
                db_vuln = db_entry.vulnerability
                
                # Update fields if they're empty in the original vulnerability
                if not vuln.title and db_vuln.title:
                    vuln.title = db_vuln.title
                
                if not vuln.description and db_vuln.description:
                    vuln.description = db_vuln.description
                
                if not vuln.fix_version and db_vuln.fix_version:
                    vuln.fix_version = db_vuln.fix_version
                
                # Merge references
                db_refs = set(db_vuln.references)
                vuln_refs = set(vuln.references)
                vuln.references = list(vuln_refs.union(db_refs))
                
                # Add metadata about the database entry
                if not hasattr(vuln, "metadata"):
                    vuln.metadata = {}
                
                vuln.metadata.update({
                    "vuln_db_status": db_entry.status,
                    "vuln_db_sources": [s.value for s in db_entry.sources],
                    "vuln_db_last_updated": db_entry.last_updated.isoformat(),
                    "cwe_ids": db_entry.cwe_ids,
                    "affected_versions": db_entry.affected_versions,
                    "fixed_versions": db_entry.fixed_versions
                })
                
                # If the database has a higher CVSS score, use it
                if db_vuln.cvss_score > vuln.cvss_score:
                    vuln.cvss_score = db_vuln.cvss_score
                    vuln.severity = db_vuln.severity
            
            enriched_vulnerabilities.append(vuln)
        
        return enriched_vulnerabilities
    
    async def update_vulnerability_database(self, sources: List[str] = None, force: bool = False) -> Dict:
        """
        Update the vulnerability database
        """
        if sources:
            source_enums = [VulnerabilitySource(s) for s in sources]
        else:
            source_enums = None
        
        return await self.vuln_db.update_database(sources=source_enums, force=force)
    
    async def search_vulnerability_database(self, query: VulnerabilityDatabaseQuery) -> List[VulnerabilityDatabaseEntry]:
        """
        Search the vulnerability database
        """
        return await self.vuln_db.search_vulnerabilities(query)
    
    async def get_vulnerability_from_database(self, vuln_id: str) -> Optional[VulnerabilityDatabaseEntry]:
        """
        Get a specific vulnerability from the database
        """
        return await self.vuln_db.get_vulnerability(vuln_id)
    
    async def get_vulnerability_database_stats(self):
        """
        Get statistics about the vulnerability database
        """
        return await self.vuln_db.get_database_stats()
    
    async def update_vulnerability_status(self, vuln_id: str, status: VulnerabilityStatus, notes: Optional[str] = None) -> bool:
        """
        Update the status of a vulnerability in the database
        """
        return await self.vuln_db.update_vulnerability_status(vuln_id, status, notes)
    
    async def add_custom_vulnerability(self, entry: VulnerabilityDatabaseEntry) -> bool:
        """
        Add a custom vulnerability to the database
        """
        return await self.vuln_db.add_custom_vulnerability(entry)
    
    async def generate_compliance_report(
        self,
        request: ComplianceReportRequest
    ) -> Dict[str, Any]:
        """
        Generate a compliance report for a repository
        
        Args:
            request: ComplianceReportRequest object
            
        Returns:
            Dictionary with the compliance report
        """
        try:
            # Run a security scan to get vulnerabilities
            scan_result = await self.run_security_scan(
                repository_url=request.repository_url,
                commit_sha=request.commit_sha,
                artifact_url=request.artifact_url,
                scan_types=["trivy", "snyk", "zap"]  # Use all scanners
            )
            
            # Extract vulnerabilities from the scan result
            vulnerabilities = []
            if scan_result.get("status") == "success" and scan_result.get("report"):
                report = scan_result.get("report", {})
                vulnerabilities = report.get("vulnerabilities", [])
            
            # Generate the compliance report
            compliance_report = await self.compliance_service.generate_compliance_report(
                repository_url=request.repository_url,
                commit_sha=request.commit_sha,
                standards=request.standards,
                vulnerabilities=vulnerabilities,
                include_vulnerability_details=request.include_vulnerabilities
            )
            
            # Generate a summary
            summary = self.compliance_service.get_compliance_report_summary(compliance_report)
            
            # Store the report (in a real implementation, this would be stored in a database)
            report_path = os.path.join(
                self.settings.artifact_storage_path,
                f"compliance-report-{compliance_report.id}.json"
            )
            
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w") as f:
                f.write(compliance_report.json(indent=2))
            
            return {
                "status": "success",
                "report_id": compliance_report.id,
                "summary": summary.dict(),
                "report_path": report_path,
                "report": compliance_report.dict() if request.include_vulnerabilities else None
            }
            
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("Compliance report generation failed", error=str(e))
            
            return {
                "status": "error",
                "message": f"Compliance report generation failed: {str(e)}"
            }
    
    async def get_compliance_report(self, report_id: str) -> Optional[ComplianceReport]:
        """
        Get a compliance report by ID
        
        Args:
            report_id: ID of the compliance report
            
        Returns:
            ComplianceReport object or None if not found
        """
        # In a real implementation, this would retrieve the report from a database
        report_path = os.path.join(
            self.settings.artifact_storage_path,
            f"compliance-report-{report_id}.json"
        )
        
        if not os.path.exists(report_path):
            return None
        
        try:
            with open(report_path, "r") as f:
                report_data = json.load(f)
                return ComplianceReport(**report_data)
        except Exception:
            return None
    
    async def update_from_additional_sources(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Update vulnerability database from additional sources
        
        Args:
            days_back: Number of days to look back for recent vulnerabilities
            
        Returns:
            Dictionary with update results
        """
        return await self.compliance_service.update_from_additional_sources(days_back)
    
    async def generate_remediation_plan(self, request: RemediationRequest) -> RemediationPlan:
        """
        Generate a remediation plan for vulnerabilities
        
        Args:
            request: Remediation request
            
        Returns:
            Remediation plan
        """
        return await self.remediation_service.generate_remediation_plan(request)
    
    async def apply_remediation_plan(self, plan_id: str) -> List[RemediationResult]:
        """
        Apply a remediation plan
        
        Args:
            plan_id: ID of the remediation plan
            
        Returns:
            List of remediation results
        """
        return await self.remediation_service.apply_remediation_plan(plan_id)
    
    async def get_remediation_plan(self, plan_id: str) -> Optional[RemediationPlan]:
        """
        Get a remediation plan by ID
        
        Args:
            plan_id: ID of the remediation plan
            
        Returns:
            Remediation plan, or None if not found
        """
        return await self.remediation_service.get_remediation_plan(plan_id)
    
    async def get_all_remediation_plans(self) -> List[RemediationPlan]:
        """
        Get all remediation plans
        
        Returns:
            List of remediation plans
        """
        return await self.remediation_service.get_all_remediation_plans()
    
    async def get_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Get remediation actions for a vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability
            
        Returns:
            List of remediation actions
        """
        return await self.remediation_service.get_remediation_actions(vulnerability_id)
    
    async def _store_vulnerabilities_in_database(self, vulnerabilities: List[Vulnerability]):
        """
        Store newly discovered vulnerabilities in the database
        """
        for vuln in vulnerabilities:
            # Skip if the vulnerability is already in the database
            existing = await self.vuln_db.get_vulnerability(vuln.id)
            if existing:
                continue
            
            # Create a new database entry
            entry = VulnerabilityDatabaseEntry(
                vulnerability=vuln,
                sources=[VulnerabilitySource.INTERNAL],  # Mark as internally discovered
                status=VulnerabilityStatus.ACTIVE,
                affected_versions=[],
                fixed_versions=[vuln.fix_version] if vuln.fix_version else [],
                published_date=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                notes=f"Discovered during security scan of {vuln.affected_component}"
            )
            
            # Add metadata if available
            if hasattr(vuln, "metadata") and vuln.metadata:
                if "cwe_ids" in vuln.metadata:
                    entry.cwe_ids = vuln.metadata["cwe_ids"]
                
                if "affected_versions" in vuln.metadata:
                    entry.affected_versions = vuln.metadata["affected_versions"]
                
                if "fixed_versions" in vuln.metadata:
                    entry.fixed_versions = vuln.metadata["fixed_versions"]
            
            # Store in database
            await self.vuln_db.add_custom_vulnerability(entry)
