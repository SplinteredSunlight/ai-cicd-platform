"""
Approval Models

This module defines the data models for approval workflows, including approval policies,
requests, and decisions.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ApprovalPolicy:
    """
    Represents a policy for approval workflows.
    """
    id: str
    name: str
    description: str
    environment: str
    approvers: List[str]
    min_approvals: int = 1
    auto_approval_criteria: Dict[str, Any] = field(default_factory=dict)
    timeout_hours: int = 24
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ApprovalRequest:
    """
    Represents a request for approval.
    """
    id: str
    pipeline_id: str
    stage_id: str
    policy_id: str
    requester: str
    details: Dict[str, Any]
    status: str = "pending"  # pending, approved, rejected, expired, cancelled
    approvers: List[str] = field(default_factory=list)
    min_approvals: int = 1
    approvals: List[Dict[str, Any]] = field(default_factory=list)
    rejections: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None

@dataclass
class ApprovalDecision:
    """
    Represents a decision on an approval request.
    """
    id: str
    request_id: str
    approver: str
    decision: str  # approve, reject
    comment: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ApprovalNotification:
    """
    Represents a notification for an approval request.
    """
    id: str
    request_id: str
    recipient: str
    channel: str  # email, slack, etc.
    status: str = "pending"  # pending, sent, failed
    content: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sent_at: Optional[str] = None

@dataclass
class ApprovalRole:
    """
    Represents a role that can approve requests.
    """
    id: str
    name: str
    description: str
    members: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ApprovalAuditLog:
    """
    Represents an audit log entry for approval actions.
    """
    id: str
    request_id: str
    user: str
    action: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ApprovalTemplate:
    """
    Represents a template for approval requests.
    """
    id: str
    name: str
    description: str
    policy_id: str
    template_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ApprovalSchedule:
    """
    Represents a schedule for automatic approvals.
    """
    id: str
    name: str
    description: str
    policy_id: str
    cron_expression: str
    enabled: bool = True
    criteria: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run_at: Optional[str] = None
