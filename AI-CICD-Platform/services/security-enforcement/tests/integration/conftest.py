import pytest
import sys
import os
import tempfile
import json
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from models.vulnerability import (
    Vulnerability, 
    VulnerabilityReport, 
    SeverityLevel
)
from services.remediation_service import RemediationService
from services.remediation_workflows import RemediationWorkflowService, WorkflowStepType, WorkflowStepStatus
from services.approval_service import ApprovalService, ApprovalRole, ApprovalStatus
from services.rollback_service import RollbackService, RollbackType, RollbackStatus
from templates.remediation_templates import RemediationTemplateService, TemplateType
from config import get_settings, Environment

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_settings():
    """
    Create a mock for the settings.
    """
    with patch('config.get_settings') as mock_get_settings:
        settings = get_settings()
        settings.environment = Environment.DEVELOPMENT
        settings.artifact_storage_path = tempfile.mkdtemp()
        mock_get_settings.return_value = settings
        yield settings

@pytest.fixture
def temp_data_dir():
    """
    Create a temporary directory for test data.
    """
    temp_dir = tempfile.TemporaryDirectory()
    yield temp_dir.name
    temp_dir.cleanup()

@pytest.fixture
def sample_vulnerabilities():
    """
    Create a list of sample vulnerabilities for testing.
    """
    return [
        Vulnerability(
            id="CVE-2023-0001",
            title="Test Vulnerability 1",
            description="Test description 1",
            severity=SeverityLevel.HIGH,
            cvss_score=8.5,
            affected_component="test-component@1.0.0",
            fix_version="1.1.0",
            references=["https://example.com/cve-2023-0001"]
        ),
        Vulnerability(
            id="CVE-2023-0002",
            title="Test Vulnerability 2",
            description="Test description 2",
            severity=SeverityLevel.MEDIUM,
            cvss_score=5.5,
            affected_component="test-component@2.0.0",
            fix_version="2.1.0",
            references=["https://example.com/cve-2023-0002"]
        ),
        Vulnerability(
            id="CVE-2023-0003",
            title="Test Vulnerability 3",
            description="Test description 3",
            severity=SeverityLevel.LOW,
            cvss_score=3.5,
            affected_component="test-component@3.0.0",
            fix_version="3.1.0",
            references=["https://example.com/cve-2023-0003"]
        )
    ]

@pytest.fixture
def sample_remediation_request():
    """
    Create a sample remediation request for testing.
    """
    return RemediationRequest(
        repository_url="https://github.com/test/repo",
        commit_sha="abcdef123456",
        vulnerabilities=["CVE-2023-0001", "CVE-2023-0002", "CVE-2023-0003"],
        auto_apply=False,
        metadata={
            "environment": "development",
            "requester": "test-user"
        }
    )

@pytest.fixture
def mock_template_service():
    """
    Create a mock template service.
    """
    with patch('services.remediation_service.RemediationTemplateService') as mock:
        template_service = AsyncMock()
        mock.return_value = template_service
        
        # Mock find_templates_for_vulnerability
        template_service.find_templates_for_vulnerability.return_value = [
            MagicMock(
                id="TEMPLATE-DEPENDENCY-UPDATE",
                name="Dependency Update",
                description="Update a dependency to a fixed version",
                template_type=TemplateType.DEPENDENCY_UPDATE,
                vulnerability_types=["CVE", "DEPENDENCY"],
                steps=[
                    {
                        "name": "Identify dependency file",
                        "description": "Identify the file containing the dependency",
                        "action": "IDENTIFY",
                        "parameters": {
                            "file_path": "${file_path}"
                        }
                    },
                    {
                        "name": "Update dependency version",
                        "description": "Update the dependency to the fixed version",
                        "action": "UPDATE",
                        "parameters": {
                            "file_path": "${file_path}",
                            "dependency_name": "${dependency_name}",
                            "current_version": "${current_version}",
                            "fixed_version": "${fixed_version}"
                        }
                    }
                ],
                variables={
                    "file_path": {
                        "description": "Path to the dependency file",
                        "type": "string",
                        "required": True
                    },
                    "dependency_name": {
                        "description": "Name of the dependency",
                        "type": "string",
                        "required": True
                    },
                    "current_version": {
                        "description": "Current version of the dependency",
                        "type": "string",
                        "required": True
                    },
                    "fixed_version": {
                        "description": "Fixed version of the dependency",
                        "type": "string",
                        "required": True
                    }
                },
                strategy=RemediationStrategy.AUTOMATED
            )
        ]
        
        # Mock create_action_from_template
        template_service.create_action_from_template.return_value = RemediationAction(
            id="ACTION-20250302-12345678",
            vulnerability_id="CVE-2023-0001",
            name="Remediate CVE-2023-0001",
            description="Remediation for CVE-2023-0001 using template Dependency Update",
            strategy=RemediationStrategy.AUTOMATED,
            source=RemediationSource.TEMPLATE,
            steps=[
                {
                    "name": "Identify dependency file",
                    "description": "Identify the file containing the dependency",
                    "action": "IDENTIFY",
                    "parameters": {
                        "file_path": "package.json"
                    }
                },
                {
                    "name": "Update dependency version",
                    "description": "Update the dependency to the fixed version",
                    "action": "UPDATE",
                    "parameters": {
                        "file_path": "package.json",
                        "dependency_name": "example-dependency",
                        "current_version": "1.0.0",
                        "fixed_version": "1.1.0"
                    }
                }
            ],
            status=RemediationStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={
                "template_id": "TEMPLATE-DEPENDENCY-UPDATE",
                "template_name": "Dependency Update",
                "template_type": TemplateType.DEPENDENCY_UPDATE,
                "variables": {
                    "file_path": "package.json",
                    "dependency_name": "example-dependency",
                    "current_version": "1.0.0",
                    "fixed_version": "1.1.0"
                }
            }
        )
        
        yield template_service

@pytest.fixture
def remediation_service(temp_data_dir, mock_template_service):
    """
    Create a remediation service for testing.
    """
    service = RemediationService()
    
    # Override data directories to use temporary directory
    service.base_dir = temp_data_dir
    service.plans_dir = os.path.join(temp_data_dir, "plans")
    service.actions_dir = os.path.join(temp_data_dir, "actions")
    service.results_dir = os.path.join(temp_data_dir, "results")
    
    # Create directories
    os.makedirs(service.plans_dir, exist_ok=True)
    os.makedirs(service.actions_dir, exist_ok=True)
    os.makedirs(service.results_dir, exist_ok=True)
    
    # Set template service
    service.template_service = mock_template_service
    
    return service

@pytest.fixture
def workflow_service(temp_data_dir):
    """
    Create a workflow service for testing.
    """
    service = RemediationWorkflowService()
    
    # Override data directories to use temporary directory
    service.base_dir = temp_data_dir
    service.workflows_dir = os.path.join(temp_data_dir, "workflows")
    
    # Create directories
    os.makedirs(service.workflows_dir, exist_ok=True)
    
    return service

@pytest.fixture
def approval_service(temp_data_dir):
    """
    Create an approval service for testing.
    """
    service = ApprovalService()
    
    # Override data directories to use temporary directory
    service.base_dir = temp_data_dir
    service.requests_dir = os.path.join(temp_data_dir, "approvals")
    
    # Create directories
    os.makedirs(service.requests_dir, exist_ok=True)
    
    return service

@pytest.fixture
def rollback_service(temp_data_dir):
    """
    Create a rollback service for testing.
    """
    service = RollbackService()
    
    # Override data directories to use temporary directory
    service.base_dir = temp_data_dir
    service.snapshots_dir = os.path.join(temp_data_dir, "snapshots")
    service.operations_dir = os.path.join(temp_data_dir, "rollbacks")
    
    # Create directories
    os.makedirs(service.snapshots_dir, exist_ok=True)
    os.makedirs(service.operations_dir, exist_ok=True)
    
    return service

@pytest.fixture
def mock_http_client():
    """
    Create a mock for HTTP clients.
    """
    with patch('httpx.AsyncClient') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_instance.get.return_value = mock_response
        mock_instance.post.return_value = mock_response
        
        yield mock_instance

@pytest.fixture
def sample_remediation_plan(remediation_service, sample_remediation_request):
    """
    Create a sample remediation plan for testing.
    """
    async def _create_plan():
        return await remediation_service.create_remediation_plan(sample_remediation_request)
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_create_plan())

@pytest.fixture
def sample_remediation_workflow(workflow_service, sample_remediation_plan):
    """
    Create a sample remediation workflow for testing.
    """
    async def _create_workflow():
        return await workflow_service.create_workflow_for_plan(sample_remediation_plan)
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_create_workflow())

@pytest.fixture
def sample_approval_request(approval_service, sample_remediation_workflow):
    """
    Create a sample approval request for testing.
    """
    async def _create_request():
        workflow = sample_remediation_workflow
        step = workflow.steps[0]
        return await approval_service.create_approval_request(
            workflow_id=workflow.id,
            step_id=step.id,
            action_id=step.action_id,
            required_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
            auto_approve_policy=None,
            metadata=step.metadata
        )
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_create_request())

@pytest.fixture
def sample_snapshot(rollback_service, sample_remediation_workflow):
    """
    Create a sample snapshot for testing.
    """
    async def _create_snapshot():
        workflow = sample_remediation_workflow
        step = workflow.steps[0]
        return await rollback_service.create_snapshot(
            workflow_id=workflow.id,
            action_id=step.action_id,
            path="package.json",
            content=json.dumps({
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {
                    "example-dependency": "1.0.0"
                }
            }, indent=2),
            metadata={
                "repository_url": "https://github.com/test/repo",
                "commit_sha": "abcdef123456"
            }
        )
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_create_snapshot())

@pytest.fixture
def sample_rollback_operation(rollback_service, sample_remediation_workflow, sample_snapshot):
    """
    Create a sample rollback operation for testing.
    """
    async def _create_operation():
        workflow = sample_remediation_workflow
        step = workflow.steps[0]
        return await rollback_service.create_rollback_operation(
            workflow_id=workflow.id,
            action_id=step.action_id,
            snapshot_id=sample_snapshot.id,
            rollback_type=RollbackType.FULL,
            metadata={
                "repository_url": "https://github.com/test/repo",
                "commit_sha": "abcdef123456"
            }
        )
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_create_operation())

@pytest.fixture
def mock_fastapi_app():
    """
    Create a mock FastAPI app for testing.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.remediation_api import create_remediation_router
    
    app = FastAPI()
    app.include_router(create_remediation_router())
    
    return TestClient(app)
