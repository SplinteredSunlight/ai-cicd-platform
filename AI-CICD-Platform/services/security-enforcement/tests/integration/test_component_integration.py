"""
Component integration tests for the Automated Remediation system.

These tests verify the integration between different components of the Automated Remediation system,
including the remediation service, workflow system, approval service, rollback service, 
templates system, and API endpoints.
"""

import os
import sys
import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from ..integration.conftest import (
    remediation_service,
    workflow_service,
    approval_service,
    rollback_service,
    mock_template_service,
    sample_remediation_request,
    sample_remediation_plan,
    sample_remediation_workflow,
    sample_approval_request,
    sample_snapshot,
    sample_rollback_operation,
    mock_fastapi_app,
    mock_http_client
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
from templates.remediation_templates import RemediationTemplateService, TemplateType


class TestRemediationTemplateIntegration:
    """Tests for the integration between remediation service and templates system."""

    @pytest.mark.asyncio
    async def test_template_service_integration(self, remediation_service, mock_template_service):
        """Test the integration between remediation service and template service."""
        # Create a vulnerability ID
        vulnerability_id = "CVE-2023-0001"
        
        # Mock the template service to return a template
        mock_template_service.find_templates_for_vulnerability.return_value = [
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
        
        # Find templates for the vulnerability
        templates = await remediation_service.find_templates_for_vulnerability(vulnerability_id)
        
        # Verify the templates were found
        assert templates is not None
        assert len(templates) > 0
        assert templates[0].id == "TEMPLATE-DEPENDENCY-UPDATE"
        
        # Create an action from the template
        action = await remediation_service.create_action_from_template(
            vulnerability_id=vulnerability_id,
            template_id=templates[0].id,
            variables={
                "file_path": "package.json",
                "dependency_name": "example-dependency",
                "current_version": "1.0.0",
                "fixed_version": "1.1.0"
            }
        )
        
        # Verify the action was created
        assert action is not None
        assert action.vulnerability_id == vulnerability_id
        assert action.strategy == RemediationStrategy.AUTOMATED
        assert action.source == RemediationSource.TEMPLATE
        assert len(action.steps) > 0
        
        # Verify the template service was called correctly
        mock_template_service.find_templates_for_vulnerability.assert_called_once_with(vulnerability_id)
        mock_template_service.create_action_from_template.assert_called_once()


class TestWorkflowApprovalIntegration:
    """Tests for the integration between workflow system and approval service."""

    @pytest.mark.asyncio
    async def test_workflow_approval_integration(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_workflow
    ):
        """Test the integration between workflow system and approval service."""
        # Create a step that requires approval
        step = sample_remediation_workflow.steps[0]
        step.requires_approval = True
        step.approval_roles = [ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER]
        await workflow_service._save_workflow(sample_remediation_workflow)
        
        # Execute the step to create an approval request
        success, result = await workflow_service.execute_workflow_step(
            sample_remediation_workflow,
            remediation_service,
            approval_service,
            None  # rollback_service not needed
        )
        
        # Verify the step is waiting for approval
        assert success is True
        assert "step" in result
        assert result["step"]["status"] == WorkflowStepStatus.WAITING_FOR_APPROVAL
        assert "approval_request_id" in result["step"]["result"]
        
        # Get the approval request
        approval_request_id = result["step"]["result"]["approval_request_id"]
        request = await approval_service.get_approval_request(approval_request_id)
        
        # Verify the approval request
        assert request is not None
        assert request.workflow_id == sample_remediation_workflow.id
        assert request.step_id == step.id
        assert request.action_id == step.action_id
        assert request.status == ApprovalStatus.PENDING
        assert set(request.required_roles) == set([ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER])
        
        # Approve the request
        success, updated_request = await approval_service.approve_request(
            approval_request_id,
            "test-approver",
            "Approved for testing"
        )
        
        # Verify the approval
        assert success is True
        assert updated_request is not None
        assert updated_request.status == ApprovalStatus.APPROVED
        assert updated_request.approver == "test-approver"
        assert updated_request.comments == "Approved for testing"
        
        # Handle the approval result in the workflow
        success, result = await workflow_service.handle_approval_result(
            request.workflow_id,
            request.step_id,
            True,
            request.approver,
            request.comments,
            remediation_service
        )
        
        # Verify the result
        assert success is True
        assert result is not None
        
        # Verify the step status was updated
        updated_workflow = await workflow_service.get_workflow(request.workflow_id)
        assert updated_workflow is not None
        assert updated_workflow.steps[0].status == WorkflowStepStatus.COMPLETED
        assert updated_workflow.current_step_index > 0


class TestWorkflowRollbackIntegration:
    """Tests for the integration between workflow system and rollback service."""

    @pytest.mark.asyncio
    async def test_workflow_rollback_integration(
        self,
        workflow_service,
        rollback_service,
        sample_remediation_workflow,
        sample_rollback_operation
    ):
        """Test the integration between workflow system and rollback service."""
        # Create a rollback step
        rollback_step = WorkflowStepType.ROLLBACK
        step_id = f"STEP-{datetime.utcnow().strftime('%Y%m%d')}-{os.urandom(4).hex()}"
        
        # Add a rollback step to the workflow
        workflow = sample_remediation_workflow
        workflow.steps.append({
            "id": step_id,
            "name": f"Rollback {sample_rollback_operation.action_id}",
            "description": f"Rollback remediation for {sample_rollback_operation.action_id}",
            "step_type": rollback_step,
            "action_id": sample_rollback_operation.action_id,
            "status": WorkflowStepStatus.PENDING,
            "requires_approval": False,
            "approval_roles": [],
            "auto_approve_policy": None,
            "metadata": {
                "rollback_operation_id": sample_rollback_operation.id
            }
        })
        workflow.current_step_index = len(workflow.steps) - 1
        await workflow_service._save_workflow(workflow)
        
        # Execute the rollback step
        success, result = await workflow_service.execute_workflow_step(
            workflow,
            None,  # remediation_service not needed for rollback
            None,  # approval_service not needed for rollback
            rollback_service
        )
        
        # Verify the result
        assert success is True
        assert result is not None
        assert "step" in result
        
        # Verify the step status was updated
        updated_workflow = await workflow_service.get_workflow(workflow.id)
        assert updated_workflow is not None
        assert updated_workflow.steps[-1]["status"] == WorkflowStepStatus.COMPLETED
        
        # Verify the rollback operation was executed
        updated_operation = await rollback_service.get_rollback_operation(sample_rollback_operation.id)
        assert updated_operation is not None
        assert updated_operation.status == RollbackStatus.COMPLETED


class TestApiServiceIntegration:
    """Tests for the integration between API endpoints and services."""

    def test_api_remediation_service_integration(self, mock_fastapi_app, remediation_service):
        """Test the integration between API endpoints and remediation service."""
        # Create a sample request
        sample_request = {
            "repository_url": "https://github.com/test/repo",
            "commit_sha": "abcdef123456",
            "vulnerabilities": ["CVE-2023-0001", "CVE-2023-0002", "CVE-2023-0003"],
            "auto_apply": False,
            "metadata": {
                "environment": "development",
                "requester": "test-user"
            }
        }
        
        # Send request to create a plan
        response = mock_fastapi_app.post("/remediation/plans", json=sample_request)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plan" in data
        assert "workflow" in data
        
        # Get the plan ID
        plan_id = data["plan"]["id"]
        
        # Get the plan by ID
        response = mock_fastapi_app.get(f"/remediation/plans/{plan_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plan" in data
        assert data["plan"]["id"] == plan_id
        
        # Execute the plan
        response = mock_fastapi_app.post(f"/remediation/plans/{plan_id}/execute")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert len(data["results"]) > 0


class TestEndToEndComponentIntegration:
    """End-to-end tests for the integration of all components."""

    @pytest.mark.asyncio
    async def test_end_to_end_component_integration(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_request
    ):
        """Test the end-to-end integration of all components."""
        # Step 1: Create a remediation plan
        plan = await remediation_service.create_remediation_plan(sample_remediation_request)
        assert plan is not None
        assert plan.id is not None
        
        # Step 2: Create a workflow for the plan
        workflow = await workflow_service.create_workflow_for_plan(plan)
        assert workflow is not None
        assert workflow.id is not None
        
        # Step 3: Execute the workflow steps
        # For each step in the workflow
        while workflow.current_step_index < len(workflow.steps):
            # Execute the current step
            success, result = await workflow_service.execute_workflow_step(
                workflow,
                remediation_service,
                approval_service,
                rollback_service
            )
            
            assert success is True
            
            # If the step is waiting for approval, approve it
            current_step = workflow.steps[workflow.current_step_index]
            if current_step.status == WorkflowStepStatus.WAITING_FOR_APPROVAL:
                # Get the approval request
                approval_request_id = current_step.result.get("approval_request_id")
                assert approval_request_id is not None
                
                # Approve the request
                success, request = await approval_service.approve_request(
                    approval_request_id,
                    "test-approver",
                    "Approved for testing"
                )
                
                assert success is True
                
                # Handle the approval result
                success, result = await workflow_service.handle_approval_result(
                    workflow.id,
                    current_step.id,
                    True,
                    "test-approver",
                    "Approved for testing",
                    remediation_service
                )
                
                assert success is True
            
            # Reload the workflow to get the updated state
            workflow = await workflow_service.get_workflow(workflow.id)
        
        # Step 4: Verify the workflow is completed
        assert workflow.status == WorkflowStepStatus.COMPLETED
        
        # Step 5: Verify the plan is completed
        updated_plan = await remediation_service.get_remediation_plan(plan.id)
        assert updated_plan.status == RemediationStatus.COMPLETED
        
        # Step 6: Create a snapshot for rollback
        step = workflow.steps[0]
        snapshot = await rollback_service.create_snapshot(
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
                "repository_url": sample_remediation_request.repository_url,
                "commit_sha": sample_remediation_request.commit_sha
            }
        )
        
        assert snapshot is not None
        assert snapshot.id is not None
        
        # Step 7: Create a rollback operation
        operation = await rollback_service.create_rollback_operation(
            workflow_id=workflow.id,
            action_id=step.action_id,
            snapshot_id=snapshot.id,
            rollback_type=RollbackType.FULL,
            metadata={
                "repository_url": sample_remediation_request.repository_url,
                "commit_sha": sample_remediation_request.commit_sha
            }
        )
        
        assert operation is not None
        assert operation.id is not None
        
        # Step 8: Perform the rollback
        result = await rollback_service.perform_rollback(operation.id)
        assert result["success"] is True
        
        # Step 9: Verify the rollback
        verify_result = await rollback_service.verify_rollback(operation.id)
        assert verify_result["success"] is True
        
        # Step 10: Update the plan status to rolled back
        updated_plan = await remediation_service.update_remediation_plan_status(
            plan.id,
            RemediationStatus.ROLLED_BACK
        )
        
        assert updated_plan is not None
        assert updated_plan.status == RemediationStatus.ROLLED_BACK
