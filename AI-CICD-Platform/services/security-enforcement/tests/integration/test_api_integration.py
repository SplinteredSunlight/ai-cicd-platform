"""
API integration tests for the Automated Remediation system.
"""

import os
import sys
import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ..integration.conftest import (
    remediation_service,
    workflow_service,
    approval_service,
    rollback_service,
    sample_remediation_request,
    sample_remediation_plan,
    sample_remediation_workflow,
    sample_approval_request,
    sample_snapshot,
    sample_rollback_operation,
    mock_fastapi_app
)

from models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from services.remediation_service import RemediationService
from services.remediation_workflows import (
    RemediationWorkflowService,
    WorkflowStepType,
    WorkflowStepStatus
)
from services.approval_service import ApprovalService, ApprovalRole, ApprovalStatus
from services.rollback_service import RollbackService, RollbackType, RollbackStatus
from api.remediation_api import create_remediation_router

class TestRemediationAPI:
    """API integration tests for the Automated Remediation system."""

    @pytest.fixture
    def api_client(self):
        """Create a FastAPI test client."""
        app = FastAPI()
        
        # Patch the services to use our test instances
        with patch('api.remediation_api.remediation_service') as mock_remediation_service, \
             patch('api.remediation_api.workflow_service') as mock_workflow_service, \
             patch('api.remediation_api.approval_service') as mock_approval_service, \
             patch('api.remediation_api.rollback_service') as mock_rollback_service:
            
            # Set up the mocks
            mock_remediation_service.return_value = self.remediation_service
            mock_workflow_service.return_value = self.workflow_service
            mock_approval_service.return_value = self.approval_service
            mock_rollback_service.return_value = self.rollback_service
            
            # Create the router
            router = create_remediation_router()
            app.include_router(router)
            
            # Create the test client
            client = TestClient(app)
            yield client

    def setup_method(self, method):
        """Set up test method."""
        # Create temporary directories
        self.temp_dir = os.path.join(os.path.dirname(__file__), "data", "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create service instances
        self.remediation_service = RemediationService()
        self.workflow_service = RemediationWorkflowService()
        self.approval_service = ApprovalService()
        self.rollback_service = RollbackService()
        
        # Override data directories
        self.remediation_service.base_dir = self.temp_dir
        self.remediation_service.plans_dir = os.path.join(self.temp_dir, "plans")
        self.remediation_service.actions_dir = os.path.join(self.temp_dir, "actions")
        self.remediation_service.results_dir = os.path.join(self.temp_dir, "results")
        
        self.workflow_service.base_dir = self.temp_dir
        self.workflow_service.workflows_dir = os.path.join(self.temp_dir, "workflows")
        
        self.approval_service.base_dir = self.temp_dir
        self.approval_service.requests_dir = os.path.join(self.temp_dir, "approvals")
        
        self.rollback_service.base_dir = self.temp_dir
        self.rollback_service.snapshots_dir = os.path.join(self.temp_dir, "snapshots")
        self.rollback_service.operations_dir = os.path.join(self.temp_dir, "rollbacks")
        
        # Create directories
        os.makedirs(self.remediation_service.plans_dir, exist_ok=True)
        os.makedirs(self.remediation_service.actions_dir, exist_ok=True)
        os.makedirs(self.remediation_service.results_dir, exist_ok=True)
        os.makedirs(self.workflow_service.workflows_dir, exist_ok=True)
        os.makedirs(self.approval_service.requests_dir, exist_ok=True)
        os.makedirs(self.rollback_service.snapshots_dir, exist_ok=True)
        os.makedirs(self.rollback_service.operations_dir, exist_ok=True)
        
        # Create sample data
        self.sample_request = {
            "repository_url": "https://github.com/test/repo",
            "commit_sha": "abcdef123456",
            "vulnerabilities": ["CVE-2023-0001", "CVE-2023-0002", "CVE-2023-0003"],
            "auto_apply": False,
            "metadata": {
                "environment": "development",
                "requester": "test-user"
            }
        }
        
        # Mock the template service
        self.mock_template_service = AsyncMock()
        self.remediation_service.template_service = self.mock_template_service
        
        # Mock find_templates_for_vulnerability
        self.mock_template_service.find_templates_for_vulnerability.return_value = [
            MagicMock(
                id="TEMPLATE-DEPENDENCY-UPDATE",
                name="Dependency Update",
                description="Update a dependency to a fixed version",
                template_type="DEPENDENCY_UPDATE",
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
        self.mock_template_service.create_action_from_template.return_value = RemediationAction(
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
                "template_type": "DEPENDENCY_UPDATE",
                "variables": {
                    "file_path": "package.json",
                    "dependency_name": "example-dependency",
                    "current_version": "1.0.0",
                    "fixed_version": "1.1.0"
                }
            }
        )

    def teardown_method(self, method):
        """Clean up after test method."""
        # Clean up temporary directories
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_plan(self, api_client):
        """Test creating a remediation plan via API."""
        # Send request to create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plan" in data
        assert "workflow" in data
        
        # Verify plan data
        plan = data["plan"]
        assert plan["id"] is not None
        assert plan["status"] == RemediationStatus.PENDING
        assert plan["target"] == f"{self.sample_request['repository_url']}@{self.sample_request['commit_sha']}"
        assert len(plan["actions"]) > 0
        
        # Verify workflow data
        workflow = data["workflow"]
        assert workflow["id"] is not None
        assert workflow["status"] == WorkflowStepStatus.PENDING
        assert workflow["plan_id"] == plan["id"]
        assert len(workflow["steps"]) > 0

    def test_get_plans(self, api_client):
        """Test getting all remediation plans via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        
        # Get all plans
        response = api_client.get("/remediation/plans")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plans" in data
        assert len(data["plans"]) > 0

    def test_get_plan_by_id(self, api_client):
        """Test getting a remediation plan by ID via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        plan_id = response.json()["plan"]["id"]
        
        # Get the plan by ID
        response = api_client.get(f"/remediation/plans/{plan_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plan" in data
        assert data["plan"]["id"] == plan_id

    def test_get_plan_actions(self, api_client):
        """Test getting actions for a plan via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        plan_id = response.json()["plan"]["id"]
        
        # Get the plan actions
        response = api_client.get(f"/remediation/plans/{plan_id}/actions")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "actions" in data
        assert len(data["actions"]) > 0

    def test_execute_plan(self, api_client):
        """Test executing a remediation plan via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        plan_id = response.json()["plan"]["id"]
        
        # Execute the plan
        response = api_client.post(f"/remediation/plans/{plan_id}/execute")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert len(data["results"]) > 0
        
        # Verify results
        for result in data["results"]:
            assert result["success"] is True
            assert result["status"] == RemediationStatus.COMPLETED

    def test_get_action_by_id(self, api_client):
        """Test getting a remediation action by ID via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        action_id = response.json()["plan"]["actions"][0]["id"]
        
        # Get the action by ID
        response = api_client.get(f"/remediation/actions/{action_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "action" in data
        assert data["action"]["id"] == action_id

    def test_execute_action(self, api_client):
        """Test executing a remediation action via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        action_id = response.json()["plan"]["actions"][0]["id"]
        
        # Execute the action
        response = api_client.post(f"/remediation/actions/{action_id}/execute")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["action_id"] == action_id
        assert data["result"]["success"] is True
        assert data["result"]["status"] == RemediationStatus.COMPLETED

    def test_get_workflows(self, api_client):
        """Test getting all remediation workflows via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        
        # Get all workflows
        response = api_client.get("/remediation/workflows")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflows" in data
        assert len(data["workflows"]) > 0

    def test_get_workflow_by_id(self, api_client):
        """Test getting a remediation workflow by ID via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        
        # Get the workflow by ID
        response = api_client.get(f"/remediation/workflows/{workflow_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow" in data
        assert data["workflow"]["id"] == workflow_id

    def test_execute_workflow_step(self, api_client):
        """Test executing a workflow step via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        
        # Execute the workflow step
        response = api_client.post(f"/remediation/workflows/{workflow_id}/execute-step")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert "workflow" in data
        assert data["workflow"]["id"] == workflow_id

    def test_approve_request(self, api_client):
        """Test approving a request via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        
        # Execute the workflow step to create an approval request
        response = api_client.post(f"/remediation/workflows/{workflow_id}/execute-step")
        assert response.status_code == 200
        
        # Get the approval request ID
        workflow = response.json()["workflow"]
        step = workflow["steps"][0]
        if step["status"] == WorkflowStepStatus.WAITING_FOR_APPROVAL:
            approval_request_id = step["result"]["approval_request_id"]
            
            # Approve the request
            response = api_client.post(
                f"/remediation/approvals/{approval_request_id}/approve",
                json={"approver": "test-approver", "comments": "Approved for testing"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "request" in data
            assert data["request"]["id"] == approval_request_id
            assert data["request"]["status"] == ApprovalStatus.APPROVED
            assert data["request"]["approver"] == "test-approver"
            assert data["request"]["comments"] == "Approved for testing"

    def test_reject_request(self, api_client):
        """Test rejecting a request via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        
        # Execute the workflow step to create an approval request
        response = api_client.post(f"/remediation/workflows/{workflow_id}/execute-step")
        assert response.status_code == 200
        
        # Get the approval request ID
        workflow = response.json()["workflow"]
        step = workflow["steps"][0]
        if step["status"] == WorkflowStepStatus.WAITING_FOR_APPROVAL:
            approval_request_id = step["result"]["approval_request_id"]
            
            # Reject the request
            response = api_client.post(
                f"/remediation/approvals/{approval_request_id}/reject",
                json={"approver": "test-approver", "comments": "Rejected for testing"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "request" in data
            assert data["request"]["id"] == approval_request_id
            assert data["request"]["status"] == ApprovalStatus.REJECTED
            assert data["request"]["approver"] == "test-approver"
            assert data["request"]["comments"] == "Rejected for testing"

    def test_create_rollback(self, api_client):
        """Test creating a rollback operation via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        action_id = response.json()["plan"]["actions"][0]["id"]
        
        # Create a snapshot
        snapshot = asyncio.run(self.rollback_service.create_snapshot(
            workflow_id=workflow_id,
            action_id=action_id,
            path="package.json",
            content=json.dumps({
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {
                    "example-dependency": "1.0.0"
                }
            }, indent=2),
            metadata={
                "repository_url": self.sample_request["repository_url"],
                "commit_sha": self.sample_request["commit_sha"]
            }
        ))
        
        # Create a rollback operation
        response = api_client.post(
            "/remediation/rollbacks",
            json={
                "workflow_id": workflow_id,
                "action_id": action_id,
                "snapshot_id": snapshot.id,
                "rollback_type": RollbackType.FULL,
                "metadata": {
                    "repository_url": self.sample_request["repository_url"],
                    "commit_sha": self.sample_request["commit_sha"]
                }
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "operation" in data
        assert data["operation"]["workflow_id"] == workflow_id
        assert data["operation"]["action_id"] == action_id
        assert data["operation"]["snapshot_id"] == snapshot.id
        assert data["operation"]["rollback_type"] == RollbackType.FULL

    def test_execute_rollback(self, api_client):
        """Test executing a rollback operation via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        action_id = response.json()["plan"]["actions"][0]["id"]
        
        # Create a snapshot
        snapshot = asyncio.run(self.rollback_service.create_snapshot(
            workflow_id=workflow_id,
            action_id=action_id,
            path="package.json",
            content=json.dumps({
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {
                    "example-dependency": "1.0.0"
                }
            }, indent=2),
            metadata={
                "repository_url": self.sample_request["repository_url"],
                "commit_sha": self.sample_request["commit_sha"]
            }
        ))
        
        # Create a rollback operation
        operation = asyncio.run(self.rollback_service.create_rollback_operation(
            workflow_id=workflow_id,
            action_id=action_id,
            snapshot_id=snapshot.id,
            rollback_type=RollbackType.FULL,
            metadata={
                "repository_url": self.sample_request["repository_url"],
                "commit_sha": self.sample_request["commit_sha"]
            }
        ))
        
        # Execute the rollback
        response = api_client.post(f"/remediation/rollbacks/{operation.id}/execute")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["success"] is True

    def test_verify_rollback(self, api_client):
        """Test verifying a rollback operation via API."""
        # First create a plan
        response = api_client.post("/remediation/plans", json=self.sample_request)
        assert response.status_code == 200
        workflow_id = response.json()["workflow"]["id"]
        action_id = response.json()["plan"]["actions"][0]["id"]
        
        # Create a snapshot
        snapshot = asyncio.run(self.rollback_service.create_snapshot(
            workflow_id=workflow_id,
            action_id=action_id,
            path="package.json",
            content=json.dumps({
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {
                    "example-dependency": "1.0.0"
                }
            }, indent=2),
            metadata={
                "repository_url": self.sample_request["repository_url"],
                "commit_sha": self.sample_request["commit_sha"]
            }
        ))
        
        # Create a rollback operation
        operation = asyncio.run(self.rollback_service.create_rollback_operation(
            workflow_id=workflow_id,
            action_id=action_id,
            snapshot_id=snapshot.id,
            rollback_type=RollbackType.FULL,
            metadata={
                "repository_url": self.sample_request["repository_url"],
                "commit_sha": self.sample_request["commit_sha"]
            }
        ))
        
        # Execute the rollback
        asyncio.run(self.rollback_service.perform_rollback(operation.id))
        
        # Verify the rollback
        response = api_client.post(f"/remediation/rollbacks/{operation.id}/verify")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["success"] is True

class TestAPIErrorHandling:
    """Tests for API error handling."""

    @pytest.fixture
    def api_client(self):
        """Create a FastAPI test client."""
        app = FastAPI()
        
        # Create the router
        router = create_remediation_router()
        app.include_router(router)
        
        # Create the test client
        client = TestClient(app)
        yield client

    def test_get_nonexistent_plan(self, api_client):
        """Test getting a nonexistent plan."""
        response = api_client.get("/remediation/plans/nonexistent-plan")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_nonexistent_action(self, api_client):
        """Test getting a nonexistent action."""
        response = api_client.get("/remediation/actions/nonexistent-action")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_nonexistent_workflow(self, api_client):
        """Test getting a nonexistent workflow."""
        response = api_client.get("/remediation/workflows/nonexistent-workflow")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_execute_nonexistent_plan(self, api_client):
        """Test executing a nonexistent plan."""
        response = api_client.post("/remediation/plans/nonexistent-plan/execute")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_execute_nonexistent_action(self, api_client):
        """Test executing a nonexistent action."""
        response = api_client.post("/remediation/actions/nonexistent-action/execute")
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_execute_nonexistent_workflow_step(self, api_client):
        """Test executing a step in a nonexistent workflow."""
        response = api_client.post("/remediation/workflows/nonexistent-workflow/execute-step")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_approve_nonexistent_request(self, api_client):
        """Test approving a nonexistent request."""
        response = api_client.post(
            "/remediation/approvals/nonexistent-request/approve",
            json={"approver": "test-approver", "comments": "Approved for testing"}
        )
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_reject_nonexistent_request(self, api_client):
        """Test rejecting a nonexistent request."""
        response = api_client.post(
            "/remediation/approvals/nonexistent-request/reject",
            json={"approver": "test-approver", "comments": "Rejected for testing"}
        )
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_execute_nonexistent_rollback(self, api_client):
        """Test executing a nonexistent rollback operation."""
        response = api_client.post("/remediation/rollbacks/nonexistent-rollback/execute")
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_verify_nonexistent_rollback(self, api_client):
        """Test verifying a nonexistent rollback operation."""
        response = api_client.post("/remediation/rollbacks/nonexistent-rollback/verify")
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_invalid_request_body(self, api_client):
        """Test sending an invalid request body."""
        response = api_client.post("/remediation/plans", json={})
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_missing_required_field(self, api_client):
        """Test sending a request with a missing required field."""
        # Missing vulnerabilities field
        response = api_client.post("/remediation/plans", json={
            "repository_url": "https://github.com/test/repo",
            "commit_sha": "abcdef123456"
        })
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_invalid_field_type(self, api_client):
        """Test sending a request with an invalid field type."""
        # vulnerabilities should be a list, not a string
        response = api_client.post("/remediation/plans", json={
            "repository_url": "https://github.com/test/repo",
            "commit_sha": "abcdef123456",
            "vulnerabilities": "CVE-2023-0001"
        })
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
