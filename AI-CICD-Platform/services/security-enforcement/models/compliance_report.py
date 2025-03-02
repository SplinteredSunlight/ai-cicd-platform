from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .vulnerability import SeverityLevel

class ComplianceStandard(str, Enum):
    """
    Compliance standards
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

class ComplianceStatus(str, Enum):
    """
    Compliance status
    """
    COMPLIANT = "COMPLIANT"  # Fully compliant
    NON_COMPLIANT = "NON_COMPLIANT"  # Not compliant
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"  # Partially compliant
    UNKNOWN = "UNKNOWN"  # Compliance status unknown
    EXEMPT = "EXEMPT"  # Exempt from compliance
    NOT_APPLICABLE = "NOT_APPLICABLE"  # Compliance not applicable

class ComplianceControl:
    """
    A compliance control
    """
    def __init__(
        self,
        id: str,
        standard: ComplianceStandard,
        name: str,
        description: str,
        status: ComplianceStatus,
        evidence: Optional[List[str]] = None,
        findings: Optional[List[Dict[str, Any]]] = None,
        remediation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.standard = standard
        self.name = name
        self.description = description
        self.status = status
        self.evidence = evidence or []
        self.findings = findings or []
        self.remediation = remediation
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "standard": self.standard.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "evidence": self.evidence,
            "findings": self.findings,
            "remediation": self.remediation,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceControl':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            standard=ComplianceStandard(data["standard"]),
            name=data["name"],
            description=data["description"],
            status=ComplianceStatus(data["status"]),
            evidence=data.get("evidence", []),
            findings=data.get("findings", []),
            remediation=data.get("remediation"),
            metadata=data.get("metadata", {})
        )

class ComplianceReportSummary:
    """
    Summary of a compliance report
    """
    def __init__(
        self,
        id: str,
        repository_url: str,
        commit_sha: str,
        standards: List[ComplianceStandard],
        status: Dict[ComplianceStandard, ComplianceStatus],
        control_counts: Dict[ComplianceStandard, Dict[ComplianceStatus, int]],
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.repository_url = repository_url
        self.commit_sha = commit_sha
        self.standards = standards
        self.status = status
        self.control_counts = control_counts
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "repository_url": self.repository_url,
            "commit_sha": self.commit_sha,
            "standards": [s.value for s in self.standards],
            "status": {s.value: st.value for s, st in self.status.items()},
            "control_counts": {
                s.value: {st.value: count for st, count in counts.items()}
                for s, counts in self.control_counts.items()
            },
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceReportSummary':
        """
        Create from dictionary
        """
        standards = [ComplianceStandard(s) for s in data["standards"]]
        status = {
            ComplianceStandard(s): ComplianceStatus(st)
            for s, st in data["status"].items()
        }
        control_counts = {
            ComplianceStandard(s): {
                ComplianceStatus(st): count
                for st, count in counts.items()
            }
            for s, counts in data["control_counts"].items()
        }
        
        return cls(
            id=data["id"],
            repository_url=data["repository_url"],
            commit_sha=data["commit_sha"],
            standards=standards,
            status=status,
            control_counts=control_counts,
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )

class ComplianceReport:
    """
    A compliance report
    """
    def __init__(
        self,
        id: str,
        repository_url: str,
        commit_sha: str,
        standards: List[ComplianceStandard],
        controls: List[ComplianceControl],
        status: Dict[ComplianceStandard, ComplianceStatus],
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.repository_url = repository_url
        self.commit_sha = commit_sha
        self.standards = standards
        self.controls = controls
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "repository_url": self.repository_url,
            "commit_sha": self.commit_sha,
            "standards": [s.value for s in self.standards],
            "controls": [c.to_dict() for c in self.controls],
            "status": {s.value: st.value for s, st in self.status.items()},
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceReport':
        """
        Create from dictionary
        """
        standards = [ComplianceStandard(s) for s in data["standards"]]
        controls = [ComplianceControl.from_dict(c) for c in data["controls"]]
        status = {
            ComplianceStandard(s): ComplianceStatus(st)
            for s, st in data["status"].items()
        }
        
        return cls(
            id=data["id"],
            repository_url=data["repository_url"],
            commit_sha=data["commit_sha"],
            standards=standards,
            controls=controls,
            status=status,
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )
    
    def get_summary(self) -> ComplianceReportSummary:
        """
        Get a summary of the report
        """
        # Calculate control counts
        control_counts = {}
        for standard in self.standards:
            counts = {}
            for control in self.controls:
                if control.standard == standard:
                    counts[control.status] = counts.get(control.status, 0) + 1
            control_counts[standard] = counts
        
        return ComplianceReportSummary(
            id=self.id,
            repository_url=self.repository_url,
            commit_sha=self.commit_sha,
            standards=self.standards,
            status=self.status,
            control_counts=control_counts,
            created_at=self.created_at,
            metadata=self.metadata
        )

class ComplianceReportRequest:
    """
    Request for a compliance report
    """
    def __init__(
        self,
        repository_url: str,
        commit_sha: str,
        standards: List[ComplianceStandard],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.repository_url = repository_url
        self.commit_sha = commit_sha
        self.standards = standards
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "repository_url": self.repository_url,
            "commit_sha": self.commit_sha,
            "standards": [s.value for s in self.standards],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceReportRequest':
        """
        Create from dictionary
        """
        standards = [ComplianceStandard(s) for s in data["standards"]]
        
        return cls(
            repository_url=data["repository_url"],
            commit_sha=data["commit_sha"],
            standards=standards,
            metadata=data.get("metadata", {})
        )
