"""
Target Models

This module defines the data models for deployment targets, environments, credentials,
and operations.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DeploymentTarget:
    """
    Represents a deployment target such as Kubernetes, cloud provider, or on-premises.
    """
    id: str
    name: str
    type: str  # kubernetes, serverless, vm, etc.
    provider: str  # aws, azure, gcp, on-premises, etc.
    region: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetCredential:
    """
    Represents a credential for a deployment target.
    """
    id: str
    target_id: str
    type: str  # api_key, certificate, ssh_key, etc.
    value: Dict[str, Any]
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetEnvironment:
    """
    Represents an environment for a deployment target.
    """
    id: str
    name: str
    type: str  # development, staging, production, etc.
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DeploymentOperation:
    """
    Represents an operation on a deployment target.
    """
    id: str
    target_id: str
    environment_id: str
    type: str  # kubernetes_deploy, aws_lambda_deploy, vm_deploy, etc.
    status: str = "pending"  # pending, running, completed, failed, cancelled
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class TargetTemplate:
    """
    Represents a template for creating deployment targets.
    """
    id: str
    name: str
    description: str
    type: str  # kubernetes, serverless, vm, etc.
    provider: str  # aws, azure, gcp, on-premises, etc.
    properties_template: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetGroup:
    """
    Represents a group of deployment targets.
    """
    id: str
    name: str
    description: str
    target_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetHealthStatus:
    """
    Represents the health status of a deployment target.
    """
    id: str
    target_id: str
    status: str  # healthy, degraded, unhealthy
    checks: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetMetadata:
    """
    Represents metadata for a deployment target.
    """
    id: str
    target_id: str
    key: str
    value: Any
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetCapability:
    """
    Represents a capability of a deployment target.
    """
    id: str
    target_id: str
    name: str
    description: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TargetConstraint:
    """
    Represents a constraint for a deployment target.
    """
    id: str
    target_id: str
    name: str
    description: str
    constraint_type: str  # resource, security, compliance, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
