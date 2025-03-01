from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum

from .vulnerability import SeverityLevel
from .vulnerability_database import VulnerabilityStatus

class ComplianceStandard(str, Enum):
    """
    Supported compliance standards
    """
    PCI_DSS = "PCI_DSS"  # Payment Card Industry Data Security Standard
    HIPAA = "HIPAA"  # Health Insurance Portability and Accountability Act
    GDPR = "GDPR"  # General Data Protection Regulation
    SOC2 = "SOC2"  # Service Organization Control 2
    ISO27001 = "ISO27001"  # ISO/IEC 27001
    NIST_800_53 = "NIST_800_53"  # NIST Special Publication 800-53
    NIST_CSF = "NIST_CSF"  # NIST Cybersecurity Framework
    CIS = "CIS"  # Center for Internet Security
    OWASP_TOP_10 = "OWASP_TOP_10"  # OWASP Top 10
    CUSTOM = "CUSTOM"  # Custom compliance standard

class ComplianceRequirement(BaseModel):
    """
    Compliance requirement model
    """
    id: str = Field(..., description="Unique identifier for the requirement")
    standard: ComplianceStandard = Field(..., description="Compliance standard")
    title: str = Field(..., description="Short title of the requirement")
    description: str = Field(..., description="Detailed description of the requirement")
    section: Optional[str] = Field(None, description="Section or control ID within the standard")
    severity: SeverityLevel = Field(SeverityLevel.MEDIUM, description="Severity level of non-compliance")
    related_cwe_ids: List[str] = Field(default_factory=list, description="Related CWE IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "PCI-DSS-6.5.1",
                "standard": "PCI_DSS",
                "title": "Injection Flaws",
                "description": "Address common coding vulnerabilities in software development processes to prevent injection flaws, particularly SQL injection.",
                "section": "6.5.1",
                "severity": "HIGH",
                "related_cwe_ids": ["CWE-89", "CWE-564"]
            }
        }

class ComplianceStatus(str, Enum):
    """
    Status of compliance with a requirement
    """
    COMPLIANT = "COMPLIANT"  # Fully compliant
    NON_COMPLIANT = "NON_COMPLIANT"  # Not compliant
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"  # Partially compliant
    NOT_APPLICABLE = "NOT_APPLICABLE"  # Not applicable
    UNDER_REVIEW = "UNDER_REVIEW"  # Under review

class ComplianceViolation(BaseModel):
    """
    Compliance violation model
    """
    requirement_id: str = Field(..., description="ID of the violated requirement")
    vulnerability_ids: List[str] = Field(default_factory=list, description="IDs of related vulnerabilities")
    description: str = Field(..., description="Description of the violation")
    severity: SeverityLevel = Field(..., description="Severity level of the violation")
    remediation: Optional[str] = Field(None, description="Remediation steps")
    status: ComplianceStatus = Field(ComplianceStatus.NON_COMPLIANT, description="Status of the violation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requirement_id": "PCI-DSS-6.5.1",
                "vulnerability_ids": ["CVE-2021-12345"],
                "description": "SQL injection vulnerability detected in login form",
                "severity": "HIGH",
                "remediation": "Use parameterized queries or prepared statements",
                "status": "NON_COMPLIANT"
            }
        }

class ComplianceReport(BaseModel):
    """
    Comprehensive compliance report
    """
    id: str = Field(..., description="Unique identifier for the report")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the report")
    target: str = Field(..., description="Target of the compliance assessment")
    standards: List[ComplianceStandard] = Field(..., description="Compliance standards assessed")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="List of compliance violations")
    summary: Dict[ComplianceStandard, Dict[ComplianceStatus, int]] = Field(
        default_factory=dict,
        description="Summary of compliance status by standard"
    )
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    def update_summary(self):
        """
        Update the summary counts based on violations
        """
        # Initialize summary
        self.summary = {standard: {status: 0 for status in ComplianceStatus} for standard in self.standards}
        
        # Count violations by standard and status
        for violation in self.violations:
            # Find the standard for this requirement
            for standard in self.standards:
                if violation.requirement_id.startswith(standard.value):
                    self.summary[standard][violation.status] += 1
                    break
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "CR-2025-02-25-001",
                "timestamp": "2025-02-25T12:00:00Z",
                "target": "example-app@1.0.0",
                "standards": ["PCI_DSS", "OWASP_TOP_10"],
                "violations": [
                    {
                        "requirement_id": "PCI-DSS-6.5.1",
                        "vulnerability_ids": ["CVE-2021-12345"],
                        "description": "SQL injection vulnerability detected in login form",
                        "severity": "HIGH",
                        "remediation": "Use parameterized queries or prepared statements",
                        "status": "NON_COMPLIANT"
                    }
                ],
                "summary": {
                    "PCI_DSS": {
                        "COMPLIANT": 10,
                        "NON_COMPLIANT": 1,
                        "PARTIALLY_COMPLIANT": 2,
                        "NOT_APPLICABLE": 0,
                        "UNDER_REVIEW": 0
                    },
                    "OWASP_TOP_10": {
                        "COMPLIANT": 8,
                        "NON_COMPLIANT": 1,
                        "PARTIALLY_COMPLIANT": 1,
                        "NOT_APPLICABLE": 0,
                        "UNDER_REVIEW": 0
                    }
                },
                "metadata": {
                    "scan_duration": 120,
                    "total_requirements": 22
                }
            }
        }

class ComplianceReportRequest(BaseModel):
    """
    Request to generate a compliance report
    """
    repository_url: str = Field(..., description="URL of the repository to assess")
    commit_sha: str = Field(..., description="Commit SHA to assess")
    artifact_url: Optional[str] = Field(None, description="URL of the artifact to assess")
    standards: List[ComplianceStandard] = Field(..., description="Compliance standards to assess")
    include_vulnerabilities: bool = Field(True, description="Include vulnerability details in the report")
    
    class Config:
        json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/example/repo",
                "commit_sha": "1234567890abcdef",
                "artifact_url": "https://example.com/artifacts/app-1.0.0.jar",
                "standards": ["PCI_DSS", "OWASP_TOP_10"],
                "include_vulnerabilities": True
            }
        }

class ComplianceReportSummary(BaseModel):
    """
    Summary of a compliance report
    """
    id: str = Field(..., description="Unique identifier for the report")
    timestamp: datetime = Field(..., description="Timestamp of the report")
    target: str = Field(..., description="Target of the compliance assessment")
    standards: List[ComplianceStandard] = Field(..., description="Compliance standards assessed")
    overall_status: ComplianceStatus = Field(..., description="Overall compliance status")
    summary: Dict[ComplianceStandard, Dict[ComplianceStatus, int]] = Field(
        ...,
        description="Summary of compliance status by standard"
    )
    critical_violations: int = Field(..., description="Number of critical violations")
    high_violations: int = Field(..., description="Number of high violations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "CR-2025-02-25-001",
                "timestamp": "2025-02-25T12:00:00Z",
                "target": "example-app@1.0.0",
                "standards": ["PCI_DSS", "OWASP_TOP_10"],
                "overall_status": "PARTIALLY_COMPLIANT",
                "summary": {
                    "PCI_DSS": {
                        "COMPLIANT": 10,
                        "NON_COMPLIANT": 1,
                        "PARTIALLY_COMPLIANT": 2,
                        "NOT_APPLICABLE": 0,
                        "UNDER_REVIEW": 0
                    },
                    "OWASP_TOP_10": {
                        "COMPLIANT": 8,
                        "NON_COMPLIANT": 1,
                        "PARTIALLY_COMPLIANT": 1,
                        "NOT_APPLICABLE": 0,
                        "UNDER_REVIEW": 0
                    }
                },
                "critical_violations": 0,
                "high_violations": 1
            }
        }

class ComplianceRequirementMapping(BaseModel):
    """
    Mapping between compliance requirements and vulnerability types
    """
    requirement_id: str = Field(..., description="ID of the requirement")
    cwe_ids: List[str] = Field(default_factory=list, description="CWE IDs related to this requirement")
    vulnerability_patterns: List[str] = Field(default_factory=list, description="Patterns to match in vulnerability titles/descriptions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requirement_id": "PCI-DSS-6.5.1",
                "cwe_ids": ["CWE-89", "CWE-564"],
                "vulnerability_patterns": ["sql injection", "command injection"]
            }
        }
