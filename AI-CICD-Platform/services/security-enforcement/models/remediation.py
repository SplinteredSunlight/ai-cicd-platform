from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set

class RemediationStrategy(str, Enum):
    """
    Strategies for remediation
    """
    AUTOMATED = "AUTOMATED"  # Fully automated remediation
    ASSISTED = "ASSISTED"  # Assisted remediation (requires human input)
    MANUAL = "MANUAL"  # Manual remediation (human performs the remediation)

class RemediationStatus(str, Enum):
    """
    Status of a remediation action or plan
    """
    PENDING = "PENDING"  # Remediation is pending
    IN_PROGRESS = "IN_PROGRESS"  # Remediation is in progress
    COMPLETED = "COMPLETED"  # Remediation is completed
    FAILED = "FAILED"  # Remediation failed
    ROLLED_BACK = "ROLLED_BACK"  # Remediation was rolled back
    CANCELLED = "CANCELLED"  # Remediation was cancelled

class RemediationSource(str, Enum):
    """
    Source of a remediation action
    """
    TEMPLATE = "TEMPLATE"  # Action from a template
    CUSTOM = "CUSTOM"  # Custom action
    POLICY = "POLICY"  # Action from a policy
    EXTERNAL = "EXTERNAL"  # Action from an external source

class RemediationAction:
    """
    A remediation action
    """
    def __init__(
        self,
        id: str,
        vulnerability_id: str,
        name: str,
        description: str,
        strategy: RemediationStrategy,
        source: RemediationSource,
        steps: List[Dict[str, Any]],
        status: str = "PENDING",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.vulnerability_id = vulnerability_id
        self.name = name
        self.description = description
        self.strategy = strategy
        self.source = source
        self.steps = steps
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "vulnerability_id": self.vulnerability_id,
            "name": self.name,
            "description": self.description,
            "strategy": self.strategy,
            "source": self.source,
            "steps": self.steps,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemediationAction':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            vulnerability_id=data["vulnerability_id"],
            name=data["name"],
            description=data["description"],
            strategy=RemediationStrategy(data["strategy"]),
            source=RemediationSource(data["source"]),
            steps=data["steps"],
            status=data["status"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )

class RemediationPlan:
    """
    A plan for remediation
    """
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        target: str,
        actions: List[RemediationAction],
        status: RemediationStatus = RemediationStatus.PENDING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.target = target
        self.actions = actions
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.completed_at = completed_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target": self.target,
            "actions": [action.to_dict() for action in self.actions],
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemediationPlan':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            target=data["target"],
            actions=[RemediationAction.from_dict(action) for action in data["actions"]],
            status=RemediationStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            metadata=data.get("metadata", {})
        )

class RemediationRequest:
    """
    A request for remediation
    """
    def __init__(
        self,
        repository_url: str,
        commit_sha: str,
        vulnerabilities: List[str],
        auto_apply: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.repository_url = repository_url
        self.commit_sha = commit_sha
        self.vulnerabilities = vulnerabilities
        self.auto_apply = auto_apply
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "repository_url": self.repository_url,
            "commit_sha": self.commit_sha,
            "vulnerabilities": self.vulnerabilities,
            "auto_apply": self.auto_apply,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemediationRequest':
        """
        Create from dictionary
        """
        return cls(
            repository_url=data["repository_url"],
            commit_sha=data["commit_sha"],
            vulnerabilities=data["vulnerabilities"],
            auto_apply=data.get("auto_apply", False),
            metadata=data.get("metadata", {})
        )

class RemediationResult:
    """
    Result of a remediation action
    """
    def __init__(
        self,
        action_id: str,
        vulnerability_id: str,
        success: bool,
        status: RemediationStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        self.action_id = action_id
        self.vulnerability_id = vulnerability_id
        self.success = success
        self.status = status
        self.message = message
        self.details = details or {}
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "action_id": self.action_id,
            "vulnerability_id": self.vulnerability_id,
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemediationResult':
        """
        Create from dictionary
        """
        return cls(
            action_id=data["action_id"],
            vulnerability_id=data["vulnerability_id"],
            success=data["success"],
            status=RemediationStatus(data["status"]),
            message=data["message"],
            details=data.get("details", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )
