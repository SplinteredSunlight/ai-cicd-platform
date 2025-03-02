"""
Pipeline Models

This module defines the data models for deployment pipelines, including pipeline templates,
stages, steps, and execution details.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PipelineStep:
    """
    Represents a step in a deployment pipeline.
    """
    name: str
    type: str
    status: str = "pending"
    parameters: Dict[str, Any] = field(default_factory=dict)
    output: Optional[Any] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class PipelineStage:
    """
    Represents a stage in a deployment pipeline, containing multiple steps.
    """
    name: str
    status: str = "pending"
    steps: List[PipelineStep] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class PipelineTemplate:
    """
    Represents a deployment pipeline template that can be used to create pipelines.
    """
    id: str
    name: str
    description: str
    stages: List[Dict[str, Any]]
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment_type: str = "any"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DeploymentPipeline:
    """
    Represents a deployment pipeline instance created from a template.
    """
    id: str
    name: str
    description: str
    template_id: str
    parameters: Dict[str, Any]
    stages: List[PipelineStage]
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class PipelineExecution:
    """
    Represents the execution of a deployment pipeline.
    """
    id: str
    pipeline_id: str
    status: str = "pending"
    variables: Dict[str, Any] = field(default_factory=dict)
    stages_results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class PipelineSchedule:
    """
    Represents a schedule for running a deployment pipeline.
    """
    id: str
    pipeline_id: str
    name: str
    description: str
    cron_expression: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    last_execution_id: Optional[str] = None
    next_execution_time: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class PipelineVariable:
    """
    Represents a variable that can be used in a deployment pipeline.
    """
    id: str
    name: str
    description: str
    value: Any
    type: str = "string"
    is_secret: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class PipelineEnvironment:
    """
    Represents an environment for deployment pipelines.
    """
    id: str
    name: str
    description: str
    type: str
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class PipelineValidation:
    """
    Represents a validation check for a deployment pipeline.
    """
    id: str
    pipeline_id: str
    name: str
    description: str
    validation_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_at: Optional[str] = None
