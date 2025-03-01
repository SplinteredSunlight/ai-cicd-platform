from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from .vulnerability import Vulnerability, SeverityLevel
from .vulnerability_database import VulnerabilityStatus

class RemediationStrategy(str, Enum):
    """
    Strategies for remediating vulnerabilities
    """
    UPGRADE = "UPGRADE"  # Upgrade the affected component to a fixed version
    PATCH = "PATCH"  # Apply a patch to the affected component
    REPLACE = "REPLACE"  # Replace the affected component with an alternative
    MITIGATE = "MITIGATE"  # Apply mitigation measures without fixing the vulnerability
    WORKAROUND = "WORKAROUND"  # Apply a workaround to avoid the vulnerability
    IGNORE = "IGNORE"  # Ignore the vulnerability (with justification)

class RemediationStatus(str, Enum):
    """
    Status of a remediation action
    """
    PENDING = "PENDING"  # Remediation is pending
    IN_PROGRESS = "IN_PROGRESS"  # Remediation is in progress
    COMPLETED = "COMPLETED"  # Remediation has been completed
    FAILED = "FAILED"  # Remediation has failed
    VERIFIED = "VERIFIED"  # Remediation has been verified

class RemediationSource(str, Enum):
    """
    Sources of remediation information
    """
    NCP = "NCP"  # NIST National Checklist Program
    CERT = "CERT"  # CERT Coordination Center
    OVAL = "OVAL"  # Open Vulnerability and Assessment Language
    SCAP = "SCAP"  # Security Content Automation Protocol
    EPSS = "EPSS"  # Exploit Prediction Scoring System
    VENDOR = "VENDOR"  # Vendor advisory
    COMMUNITY = "COMMUNITY"  # Community-provided remediation
    INTERNAL = "INTERNAL"  # Internally developed remediation
    OTHER = "OTHER"  # Other sources

class RemediationAction(BaseModel):
    """
    Action to remediate a vulnerability
    """
    id: str = Field(..., description="Unique identifier for the remediation action")
    vulnerability_id: str = Field(..., description="ID of the vulnerability being remediated")
    strategy: RemediationStrategy = Field(..., description="Remediation strategy")
    description: str = Field(..., description="Description of the remediation action")
    steps: List[str] = Field(..., description="Steps to perform the remediation")
    source: RemediationSource = Field(..., description="Source of the remediation information")
    status: RemediationStatus = Field(default=RemediationStatus.PENDING, description="Status of the remediation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this remediation was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When this remediation was last updated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "REM-20250225-001",
                "vulnerability_id": "CVE-2021-44228",
                "strategy": "UPGRADE",
                "description": "Upgrade Log4j to version 2.15.0 or later",
                "steps": [
                    "Update dependency in pom.xml or build.gradle",
                    "Change org.apache.logging.log4j:log4j-core from 2.14.1 to 2.15.0",
                    "Rebuild and deploy the application"
                ],
                "source": "CERT",
                "status": "PENDING",
                "created_at": "2025-02-25T00:00:00Z",
                "updated_at": "2025-02-25T00:00:00Z",
                "metadata": {
                    "confidence": "HIGH",
                    "effort": "LOW",
                    "downtime_required": False
                }
            }
        }

class RemediationPlan(BaseModel):
    """
    Plan for remediating multiple vulnerabilities
    """
    id: str = Field(..., description="Unique identifier for the remediation plan")
    name: str = Field(..., description="Name of the remediation plan")
    description: str = Field(..., description="Description of the remediation plan")
    target: str = Field(..., description="Target being remediated (e.g., repository, container)")
    actions: List[RemediationAction] = Field(default_factory=list, description="Remediation actions in this plan")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this plan was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When this plan was last updated")
    status: RemediationStatus = Field(default=RemediationStatus.PENDING, description="Overall status of the plan")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "PLAN-20250225-001",
                "name": "Log4j Remediation Plan",
                "description": "Plan to remediate Log4j vulnerabilities",
                "target": "https://github.com/example/repo@main",
                "actions": [
                    {
                        "id": "REM-20250225-001",
                        "vulnerability_id": "CVE-2021-44228",
                        "strategy": "UPGRADE",
                        "description": "Upgrade Log4j to version 2.15.0 or later",
                        "steps": [
                            "Update dependency in pom.xml or build.gradle",
                            "Change org.apache.logging.log4j:log4j-core from 2.14.1 to 2.15.0",
                            "Rebuild and deploy the application"
                        ],
                        "source": "CERT",
                        "status": "PENDING"
                    }
                ],
                "created_at": "2025-02-25T00:00:00Z",
                "updated_at": "2025-02-25T00:00:00Z",
                "status": "PENDING",
                "metadata": {
                    "priority": "HIGH",
                    "estimated_effort": "2 hours"
                }
            }
        }

class RemediationRequest(BaseModel):
    """
    Request to generate a remediation plan
    """
    repository_url: str = Field(..., description="URL of the repository to remediate")
    commit_sha: str = Field(..., description="Commit SHA to remediate")
    artifact_url: Optional[str] = Field(None, description="URL of the artifact to remediate (if applicable)")
    vulnerability_ids: Optional[List[str]] = Field(None, description="Specific vulnerability IDs to remediate")
    max_severity: Optional[SeverityLevel] = Field(None, description="Maximum severity to include in remediation")
    auto_apply: bool = Field(False, description="Whether to automatically apply the remediation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/example/repo",
                "commit_sha": "abcdef123456",
                "vulnerability_ids": ["CVE-2021-44228"],
                "max_severity": "HIGH",
                "auto_apply": False,
                "metadata": {
                    "priority": "HIGH"
                }
            }
        }

class RemediationResult(BaseModel):
    """
    Result of a remediation action
    """
    action_id: str = Field(..., description="ID of the remediation action")
    vulnerability_id: str = Field(..., description="ID of the vulnerability being remediated")
    success: bool = Field(..., description="Whether the remediation was successful")
    status: RemediationStatus = Field(..., description="Status of the remediation")
    message: str = Field(..., description="Message describing the result")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this result was recorded")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")

    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "REM-20250225-001",
                "vulnerability_id": "CVE-2021-44228",
                "success": True,
                "status": "COMPLETED",
                "message": "Successfully upgraded Log4j to version 2.15.0",
                "timestamp": "2025-02-25T01:00:00Z",
                "details": {
                    "previous_version": "2.14.1",
                    "new_version": "2.15.0",
                    "files_changed": 2
                }
            }
        }
