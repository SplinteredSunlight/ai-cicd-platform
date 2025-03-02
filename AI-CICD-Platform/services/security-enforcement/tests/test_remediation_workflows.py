import pytest
import os
import json
from datetime import datetime
import asyncio

from ..services.remediation_workflows import (
    WorkflowStepType,
    WorkflowStepStatus,
    WorkflowStep,
    RemediationWorkflow,
    RemediationWorkflowService
)
from ..services.remediation_service import RemediationService
from ..services.approval_service import ApprovalService, ApprovalRole
from ..services.rollback_service import RollbackService, RollbackType
from ..models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)

@pytest.fixture
def workflow_service():
    """
    Create a workflow service for testing
    """
    return RemediationWorkflowService()

@pytest.fixture
def remediation_service():
    """
    Create a remediation service for testing
    """
    return RemediationService()

@pytest.fixture
def approval_service():
    """
    Create an approval service for testing
    """
    return ApprovalService()

@pytest.fixture
def rollback_service():
    """
    Create a rollback service for testing
    """
    return RollbackService()

@pytest.fixture
def sample_action():
    """
    Create a sample remediation action for testing
    """
    return RemediationAction(
        id="ACTION-20250301-12345678",
        vulnerability_id="CVE-2023-1234",
        name="Fix CVE-2023-1234",
        description="Fix for CVE-2023-1234 in example-dependency",
        strategy=RemediationStrategy.AUTOMATED,
        source=RemediationSource.TEMPLATE,
        steps=[
            {
                "name": "Update dependency",
                "description": "Update example-dependency to version 1.1.0",
                "action": "UPDATE",
                "parameters": {
                    "file_path": "package.json",
                    "dependency_name": "example-dependency",
                    "current_version": "1.0.0",
                    "fixed_version": "1.1.0"
                }
            }
        ],
        status="PENDING",
        created_at=datetime.utcnow(),
        metadata={
            "template_id": "TEMPLATE-DEPENDENCY-UPDATE",
            "template_name": "Dependency Update",
            "template_type": "DEPENDENCY_UPDATE",
            "variables": {
                "file_path": "package.json",
                "dependency_name": "example-dependency",
                "current_version": "1.0.0",
                "fixed_version": "1.1.0"
            }
        }
    )

@pytest.fixture
def sample_plan(sample_action):
    """
    Create a sample remediation plan for testing
    """
    return RemediationPlan(
        id="PLAN-20250301-12345678",
        name="Remediation Plan for example/repo@abcdef12",
        description="Remediation plan for 1 vulnerabilities",
        target="https://github.com/example/repo@abcdef1234567890",
        actions=[sample_action],
        status=RemediationStatus.PENDING,
        created_at=datetime.utcnow(),
        metadata={
            "repository_url": "https://github.com/example/repo",
            "commit_sha": "abcdef1234567890",
            "auto_apply": False
        }
    )

def test_workflow_step_creation():
    """
    Test creating a workflow step
    """
    step = WorkflowStep(
        id="STEP-12345678",
        name="Test Step",
        description="A test step",
        step_type=WorkflowStepType.REMEDIATION,
        action_id="ACTION-20250301-12345678",
        status=WorkflowStepStatus.PENDING,
        requires_approval=True,
        approval_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    )
    
    assert step.id == "STEP-12345678"
    assert step.name == "Test Step"
    assert step.description == "A test step"
    assert step.step_type == WorkflowStepType.REMEDIATION
    assert step.action_id == "ACTION-20250301-12345678"
    assert step.status == WorkflowStepStatus.PENDING
    assert step.requires_approval == True
    assert ApprovalRole.SECURITY_ADMIN in step.approval_roles
    assert ApprovalRole.DEVELOPER in step.approval_roles
    assert step.auto_approve_policy is None
    assert step.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert step.metadata["strategy"] == RemediationStrategy.AUTOMATED

def test_workflow_step_to_dict():
    """
    Test converting a workflow step to a dictionary
    """
    step = WorkflowStep(
        id="STEP-12345678",
        name="Test Step",
        description="A test step",
        step_type=WorkflowStepType.REMEDIATION,
        action_id="ACTION-20250301-12345678",
        status=WorkflowStepStatus.PENDING,
        requires_approval=True,
        approval_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    )
    
    step_dict = step.to_dict()
    
    assert step_dict["id"] == "STEP-12345678"
    assert step_dict["name"] == "Test Step"
    assert step_dict["description"] == "A test step"
    assert step_dict["step_type"] == WorkflowStepType.REMEDIATION
    assert step_dict["action_id"] == "ACTION-20250301-12345678"
    assert step_dict["status"] == WorkflowStepStatus.PENDING
    assert step_dict["requires_approval"] == True
    assert ApprovalRole.SECURITY_ADMIN.value in step_dict["approval_roles"]
    assert ApprovalRole.DEVELOPER.value in step_dict["approval_roles"]
    assert step_dict["auto_approve_policy"] is None
    assert step_dict["metadata"]["vulnerability_id"] == "CVE-2023-1234"
    assert step_dict["metadata"]["strategy"] == RemediationStrategy.AUTOMATED

def test_workflow_step_from_dict():
    """
    Test creating a workflow step from a dictionary
    """
    step_dict = {
        "id": "STEP-12345678",
        "name": "Test Step",
        "description": "A test step",
        "step_type": WorkflowStepType.REMEDIATION,
        "action_id": "ACTION-20250301-12345678",
        "status": WorkflowStepStatus.PENDING,
        "requires_approval": True,
        "approval_roles": [ApprovalRole.SECURITY_ADMIN.value, ApprovalRole.DEVELOPER.value],
        "auto_approve_policy": None,
        "result": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    }
    
    step = WorkflowStep.from_dict(step_dict)
    
    assert step.id == "STEP-12345678"
    assert step.name == "Test Step"
    assert step.description == "A test step"
    assert step.step_type == WorkflowStepType.REMEDIATION
    assert step.action_id == "ACTION-20250301-12345678"
    assert step.status == WorkflowStepStatus.PENDING
    assert step.requires_approval == True
    assert ApprovalRole.SECURITY_ADMIN in step.approval_roles
    assert ApprovalRole.DEVELOPER in step.approval_roles
    assert step.auto_approve_policy is None
    assert step.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert step.metadata["strategy"] == RemediationStrategy.AUTOMATED

def test_remediation_workflow_creation():
    """
    Test creating a remediation workflow
    """
    step1 = WorkflowStep(
        id="STEP-12345678",
        name="Remediate CVE-2023-1234",
        description="Apply remediation for CVE-2023-1234",
        step_type=WorkflowStepType.REMEDIATION,
        action_id="ACTION-20250301-12345678",
        status=WorkflowStepStatus.PENDING,
        requires_approval=True,
        approval_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    )
    
    step2 = WorkflowStep(
        id="STEP-87654321",
        name="Verify CVE-2023-1234",
        description="Verify remediation for CVE-2023-1234",
        step_type=WorkflowStepType.VERIFICATION,
        action_id="ACTION-20250301-12345678",
        status=WorkflowStepStatus.PENDING,
        requires_approval=False,
        approval_roles=[],
        auto_approve_policy=None,
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    )
    
    workflow = RemediationWorkflow(
        id="WORKFLOW-20250301-12345678",
        name="Workflow for Remediation Plan for example/repo@abcdef12",
        description="Remediation workflow for Remediation plan for 1 vulnerabilities",
        plan_id="PLAN-20250301-12345678",
        steps=[step1, step2],
        status=WorkflowStepStatus.PENDING,
        current_step_index=0,
        created_at=datetime.utcnow(),
        metadata={
            "repository_url": "https://github.com/example/repo",
            "commit_sha": "abcdef1234567890",
            "auto_apply": False
        }
    )
    
    assert workflow.id == "WORKFLOW-20250301-12345678"
    assert workflow.name == "Workflow for Remediation Plan for example/repo@abcdef12"
    assert workflow.description == "Remediation workflow for Remediation plan for 1 vulnerabilities"
    assert workflow.plan_id == "PLAN-20250301-12345678"
    assert len(workflow.steps) == 2
    assert workflow.steps[0].id == "STEP-12345678"
    assert workflow.steps[1].id == "STEP-87654321"
    assert workflow.status == WorkflowStepStatus.PENDING
    assert workflow.current_step_index == 0
    assert workflow.metadata["repository_url"] == "https://github.com/example/repo"
    assert workflow.metadata["commit_sha"] == "abcdef1234567890"
    assert workflow.metadata["auto_apply"] == False

def test_remediation_workflow_to_dict():
    """
    Test converting a remediation workflow to a dictionary
    """
    step1 = WorkflowStep(
        id="STEP-12345678",
        name="Remediate CVE-2023-1234",
        description="Apply remediation for CVE-2023-1234",
        step_type=WorkflowStepType.REMEDIATION,
        action_id="ACTION-20250301-12345678",
        status=WorkflowStepStatus.PENDING,
        requires_approval=True,
        approval_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    )
    
    step2 = WorkflowStep(
        id="STEP-87654321",
        name="Verify CVE-2023-1234",
        description="Verify remediation for CVE-2023-1234",
        step_type=WorkflowStepType.VERIFICATION,
        action_id="ACTION-20250301-12345678",
        status=WorkflowStepStatus.PENDING,
        requires_approval=False,
        approval_roles=[],
        auto_approve_policy=None,
        created_at=datetime.utcnow(),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    )
    
    workflow = RemediationWorkflow(
        id="WORKFLOW-20250301-12345678",
        name="Workflow for Remediation Plan for example/repo@abcdef12",
        description="Remediation workflow for Remediation plan for 1 vulnerabilities",
        plan_id="PLAN-20250301-12345678",
        steps=[step1, step2],
        status=WorkflowStepStatus.PENDING,
        current_step_index=0,
        created_at=datetime.utcnow(),
        metadata={
            "repository_url": "https://github.com/example/repo",
            "commit_sha": "abcdef1234567890",
            "auto_apply": False
        }
    )
    
    workflow_dict = workflow.to_dict()
    
    assert workflow_dict["id"] == "WORKFLOW-20250301-12345678"
    assert workflow_dict["name"] == "Workflow for Remediation Plan for example/repo@abcdef12"
    assert workflow_dict["description"] == "Remediation workflow for Remediation plan for 1 vulnerabilities"
    assert workflow_dict["plan_id"] == "PLAN-20250301-12345678"
    assert len(workflow_dict["steps"]) == 2
    assert workflow_dict["steps"][0]["id"] == "STEP-12345678"
    assert workflow_dict["steps"][1]["id"] == "STEP-87654321"
    assert workflow_dict["status"] == WorkflowStepStatus.PENDING
    assert workflow_dict["current_step_index"] == 0
    assert workflow_dict["metadata"]["repository_url"] == "https://github.com/example/repo"
    assert workflow_dict["metadata"]["commit_sha"] == "abcdef1234567890"
    assert workflow_dict["metadata"]["auto_apply"] == False

def test_remediation_workflow_from_dict():
    """
    Test creating a remediation workflow from a dictionary
    """
    step1_dict = {
        "id": "STEP-12345678",
        "name": "Remediate CVE-2023-1234",
        "description": "Apply remediation for CVE-2023-1234",
        "step_type": WorkflowStepType.REMEDIATION,
        "action_id": "ACTION-20250301-12345678",
        "status": WorkflowStepStatus.PENDING,
        "requires_approval": True,
        "approval_roles": [ApprovalRole.SECURITY_ADMIN.value, ApprovalRole.DEVELOPER.value],
        "auto_approve_policy": None,
        "result": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    }
    
    step2_dict = {
        "id": "STEP-87654321",
        "name": "Verify CVE-2023-1234",
        "description": "Verify remediation for CVE-2023-1234",
        "step_type": WorkflowStepType.VERIFICATION,
        "action_id": "ACTION-20250301-12345678",
        "status": WorkflowStepStatus.PENDING,
        "requires_approval": False,
        "approval_roles": [],
        "auto_approve_policy": None,
        "result": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {
            "vulnerability_id": "CVE-2023-1234",
            "strategy": RemediationStrategy.AUTOMATED
        }
    }
    
    workflow_dict = {
        "id": "WORKFLOW-20250301-12345678",
        "name": "Workflow for Remediation Plan for example/repo@abcdef12",
        "description": "Remediation workflow for Remediation plan for 1 vulnerabilities",
        "plan_id": "PLAN-20250301-12345678",
        "steps": [step1_dict, step2_dict],
        "status": WorkflowStepStatus.PENDING,
        "current_step_index": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "metadata": {
            "repository_url": "https://github.com/example/repo",
            "commit_sha": "abcdef1234567890",
            "auto_apply": False
        }
    }
    
    workflow = RemediationWorkflow.from_dict(workflow_dict)
    
    assert workflow.id == "WORKFLOW-20250301-12345678"
    assert workflow.name == "Workflow for Remediation Plan for example/repo@abcdef12"
    assert workflow.description == "Remediation workflow for Remediation plan for 1 vulnerabilities"
    assert workflow.plan_id == "PLAN-20250301-12345678"
    assert len(workflow.steps) == 2
    assert workflow.steps[0].id == "STEP-12345678"
    assert workflow.steps[1].id == "STEP-87654321"
    assert workflow.status == WorkflowStepStatus.PENDING
    assert workflow.current_step_index == 0
    assert workflow.metadata["repository_url"] == "https://github.com/example/repo"
    assert workflow.metadata["commit_sha"] == "abcdef1234567890"
    assert workflow.metadata["auto_apply"] == False

def test_workflow_service_initialization(workflow_service):
    """
    Test initializing the workflow service
    """
    assert workflow_service is not None
    assert workflow_service.workflows_dir is not None
    assert os.path.exists(workflow_service.workflows_dir)

@pytest.mark.asyncio
async def test_workflow_service_create_workflow_for_plan(workflow_service, sample_plan):
    """
    Test creating a workflow for a plan
    """
    workflow = await workflow_service.create_workflow_for_plan(sample_plan)
    
    assert workflow is not None
    assert workflow.plan_id == sample_plan.id
    assert len(workflow.steps) == 2
    assert workflow.steps[0].step_type == WorkflowStepType.REMEDIATION
    assert workflow.steps[1].step_type == WorkflowStepType.VERIFICATION
    assert workflow.status == WorkflowStepStatus.PENDING
    assert workflow.current_step_index == 0
    assert workflow.metadata["repository_url"] == sample_plan.metadata["repository_url"]
    assert workflow.metadata["commit_sha"] == sample_plan.metadata["commit_sha"]
    assert workflow.metadata["auto_apply"] == sample_plan.metadata["auto_apply"]
