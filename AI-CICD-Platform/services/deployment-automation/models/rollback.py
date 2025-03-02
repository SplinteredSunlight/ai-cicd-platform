"""
Rollback Models

This module defines the data models for rollback and recovery mechanisms, including
rollback plans, snapshots, and execution details.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class RollbackStrategy:
    """
    Represents a strategy for rolling back deployments.
    """
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    target_types: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class RollbackPlan:
    """
    Represents a plan for rolling back a deployment.
    """
    id: str
    deployment_id: str
    strategy_id: str
    target_info: Dict[str, Any]
    parameters: Dict[str, Any]
    steps: List[Dict[str, Any]]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class RollbackSnapshot:
    """
    Represents a snapshot of a deployment for rollback purposes.
    """
    id: str
    deployment_id: str
    target_info: Dict[str, Any]
    data: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class RollbackExecution:
    """
    Represents the execution of a rollback plan.
    """
    id: str
    plan_id: str
    snapshot_id: Optional[str]
    status: str = "pending"  # pending, running, completed, failed, cancelled
    reason: str = ""
    triggered_by: str = "system"
    steps: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class RollbackTrigger:
    """
    Represents a trigger for automatic rollbacks.
    """
    id: str
    name: str
    description: str
    deployment_id: str
    conditions: Dict[str, Any]
    enabled: bool = True
    action: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_triggered_at: Optional[str] = None

@dataclass
class RollbackVerification:
    """
    Represents a verification check for a rollback.
    """
    id: str
    execution_id: str
    name: str
    verification_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, passed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_at: Optional[str] = None

@dataclass
class RollbackAuditLog:
    """
    Represents an audit log entry for rollback actions.
    """
    id: str
    execution_id: str
    user: str
    action: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class RecoveryTest:
    """
    Represents a test for recovery mechanisms.
    """
    id: str
    name: str
    description: str
    deployment_id: str
    test_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, passed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_at: Optional[str] = None

@dataclass
class RollbackPolicy:
    """
    Represents a policy for rollback decisions.
    """
    id: str
    name: str
    description: str
    environment: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
