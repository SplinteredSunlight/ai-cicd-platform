"""
Monitoring Models

This module defines the data models for deployment monitoring and verification, including
health checks, metrics, alerts, and monitoring rules.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class HealthCheck:
    """
    Represents a health check for a deployment.
    """
    id: str
    deployment_id: str
    environment_id: str
    status: str  # healthy, degraded, unhealthy
    checks: List[Dict[str, Any]]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Metric:
    """
    Represents a metric for a deployment.
    """
    id: str
    deployment_id: str
    environment_id: str
    name: str
    type: str
    unit: str
    description: str
    values: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, Any] = field(default_factory=dict)
    baseline: Optional[Dict[str, Any]] = None

@dataclass
class MetricBaseline:
    """
    Represents a baseline for a metric.
    """
    id: str
    metric_id: str
    deployment_id: str
    environment_id: str
    metric_name: str
    min: float
    max: float
    avg: float
    p95: float
    p99: float
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Alert:
    """
    Represents an alert for a deployment.
    """
    id: str
    deployment_id: str
    environment_id: str
    rule_id: str
    metric_id: Optional[str]
    severity: str  # critical, high, medium, low
    message: str
    details: Dict[str, Any]
    status: str = "active"  # active, resolved
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None

@dataclass
class MonitoringRule:
    """
    Represents a rule for monitoring deployments.
    """
    id: str
    name: str
    description: str
    metric_type: str
    conditions: Dict[str, Any]
    severity: str = "medium"  # critical, high, medium, low
    actions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MonitoringDashboard:
    """
    Represents a dashboard for monitoring deployments.
    """
    id: str
    name: str
    description: str
    panels: List[Dict[str, Any]]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MonitoringPanel:
    """
    Represents a panel in a monitoring dashboard.
    """
    id: str
    dashboard_id: str
    name: str
    type: str  # chart, table, gauge, etc.
    metrics: List[str]
    options: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class PerformanceTest:
    """
    Represents a performance test for a deployment.
    """
    id: str
    deployment_id: str
    environment_id: str
    name: str
    test_type: str  # load, stress, endurance, etc.
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    results: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class MonitoringIntegration:
    """
    Represents an integration with an external monitoring system.
    """
    id: str
    name: str
    type: str  # prometheus, datadog, cloudwatch, etc.
    configuration: Dict[str, Any]
    status: str = "enabled"  # enabled, disabled
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_sync_at: Optional[str] = None

@dataclass
class UserImpactAnalysis:
    """
    Represents an analysis of the impact of a deployment on users.
    """
    id: str
    deployment_id: str
    environment_id: str
    metrics: Dict[str, Any]
    segments: List[Dict[str, Any]]
    status: str = "pending"  # pending, running, completed
    results: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

@dataclass
class DeploymentVerification:
    """
    Represents a verification of a deployment.
    """
    id: str
    deployment_id: str
    environment_id: str
    verification_type: str  # health, metrics, performance, etc.
    status: str = "pending"  # pending, running, passed, failed
    results: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
