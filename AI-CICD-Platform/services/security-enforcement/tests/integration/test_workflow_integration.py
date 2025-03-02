"""
Workflow integration tests for the Automated Remediation system.
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
    sample_remediation_request,
    sample_remediation_plan,
    sample_remediation_workflow,
    sample_approval_request,
    sample_snapshot,
    sample_rollback_operation
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
    WorkflowStepStatus,
    WorkflowStep,
    RemediationWorkflow
)
from services.approval_service import ApprovalService, ApprovalRole, ApprovalStatus
from services.rollback_service import RollbackService, RollbackType, RollbackStatus

class TestWorkflowIntegration:
    """Workflow integration tests for the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_workflow_creation_from_plan(self, workflow_service, sample_remediation_plan):
        """Test creating a workflow from a remediation plan."""
        # Create a workflow
        workflow = await workflow_service.create_workflow_for_plan(sample_remediation_plan)
        
        # Verify the workflow was created
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.status == WorkflowStepStatus.PENDING
        assert workflow.plan_id == sample_remediation_plan.id
        assert len(workflow.steps) > 0
        
        # Verify the workflow steps
        for i, action in enumerate(sample_remediation_plan.actions):
            # Each action should have a remediation step and a verification step
            remediation_step = workflow.steps[i * 2]
            verification_step = workflow.steps[i * 2 + 1]
            
            assert remediation_step.step_type == WorkflowStepType.REMEDIATION
            assert remediation_step.action_id == action.id
            assert remediation_step.status == WorkflowStepStatus.PENDING
            
            assert verification_step.step_type == WorkflowStepType.VERIFICATION
            assert verification_step.action_id == action.id
            assert verification_step.status == WorkflowStepStatus.PENDING

    @pytest.mark.asyncio
    async def test_workflow_step_execution(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        rollback_service,
        sample_remediation_workflow
    ):
        """Test executing a workflow step."""
        # Execute the current step
        success, result = await workflow_service.execute_workflow_step(
            sample_remediation_workflow,
            remediation_service,
            approval_service,
            rollback_service
        )
        
        # Verify the result
        assert success is True
        assert result is not None
        assert "step" in result
        
        # Verify the step status was updated
        updated_workflow = await workflow_service.get_workflow(sample_remediation_workflow.id)
        assert updated_workflow is not None
        
        # If the step required approval, it should be waiting for approval
        if sample_remediation_workflow.steps[0].requires_approval:
            assert updated_workflow.steps[0].status == WorkflowStepStatus.WAITING_FOR_APPROVAL
            assert "approval_request_id" in result.get("step", {}).get("result", {})
        else:
            # Otherwise, it should be completed and the workflow should have moved to the next step
            assert updated_workflow.current_step_index > 0

    @pytest.mark.asyncio
    async def test_workflow_approval_integration(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_workflow,
        sample_approval_request
    ):
        """Test the integration between workflow and approval service."""
        # Approve the request
        success, request = await approval_service.approve_request(
            sample_approval_request.id,
            "test-approver",
            "Approved for testing"
        )
        
        # Verify the approval
        assert success is True
        assert request is not None
        assert request.status == ApprovalStatus.APPROVED
        
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
        
        # Find the step that was approved
        step_index = None
        for i, step in enumerate(updated_workflow.steps):
            if step.id == request.step_id:
                step_index = i
                break
        
        assert step_index is not None
        
        # The step should be completed and the workflow should have moved to the next step
        assert updated_workflow.steps[step_index].status == WorkflowStepStatus.COMPLETED
        assert updated_workflow.current_step_index > step_index

    @pytest.mark.asyncio
    async def test_workflow_rejection_integration(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_workflow,
        sample_approval_request
    ):
        """Test the integration between workflow and approval service for rejection."""
        # Reject the request
        success, request = await approval_service.reject_request(
            sample_approval_request.id,
            "test-approver",
            "Rejected for testing"
        )
        
        # Verify the rejection
        assert success is True
        assert request is not None
        assert request.status == ApprovalStatus.REJECTED
        
        # Handle the rejection result in the workflow
        success, result = await workflow_service.handle_approval_result(
            request.workflow_id,
            request.step_id,
            False,
            request.approver,
            request.comments,
            remediation_service
        )
        
        # Verify the result
        assert success is False
        assert result is not None
        
        # Verify the step status was updated
        updated_workflow = await workflow_service.get_workflow(request.workflow_id)
        assert updated_workflow is not None
        
        # Find the step that was rejected
        step_index = None
        for i, step in enumerate(updated_workflow.steps):
            if step.id == request.step_id:
                step_index = i
                break
        
        assert step_index is not None
        
        # The step should be rejected and the workflow should be failed
        assert updated_workflow.steps[step_index].status == WorkflowStepStatus.APPROVAL_REJECTED
        assert updated_workflow.status == WorkflowStepStatus.FAILED

    @pytest.mark.asyncio
    async def test_workflow_rollback_integration(
        self,
        workflow_service,
        rollback_service,
        sample_remediation_workflow,
        sample_rollback_operation
    ):
        """Test the integration between workflow and rollback service."""
        # Create a rollback step
        rollback_step = WorkflowStep(
            id=f"STEP-{datetime.utcnow().strftime('%Y%m%d')}-{os.urandom(4).hex()}",
            name=f"Rollback {sample_rollback_operation.action_id}",
            description=f"Rollback remediation for {sample_rollback_operation.action_id}",
            step_type=WorkflowStepType.ROLLBACK,
            action_id=sample_rollback_operation.action_id,
            status=WorkflowStepStatus.PENDING,
            requires_approval=False,
            approval_roles=[],
            auto_approve_policy=None,
            metadata={
                "rollback_operation_id": sample_rollback_operation.id
            }
        )
        
        # Add the rollback step to the workflow
        workflow = sample_remediation_workflow
        workflow.steps.append(rollback_step)
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
        assert updated_workflow.steps[-1].status == WorkflowStepStatus.COMPLETED
        
        # Verify the rollback operation was executed
        updated_operation = await rollback_service.get_rollback_operation(sample_rollback_operation.id)
        assert updated_operation is not None
        assert updated_operation.status == RollbackStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_complete_workflow_execution(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        rollback_service,
        sample_remediation_request
    ):
        """Test executing a complete workflow."""
        # Create a plan
        plan = await remediation_service.create_remediation_plan(sample_remediation_request)
        
        # Create a workflow
        workflow = await workflow_service.create_workflow_for_plan(plan)
        
        # Execute all steps in the workflow
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
                # Get the approval request ID
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
        
        # Verify the workflow is completed
        assert workflow.status == WorkflowStepStatus.COMPLETED
        
        # Verify all steps are completed
        for step in workflow.steps:
            assert step.status == WorkflowStepStatus.COMPLETED

class TestWorkflowErrorHandling:
    """Tests for workflow error handling."""

    @pytest.mark.asyncio
    async def test_handle_step_execution_error(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        rollback_service,
        sample_remediation_workflow
    ):
        """Test handling an error during step execution."""
        # Mock the remediation service to raise an exception
        with patch.object(
            remediation_service,
            'execute_remediation_action',
            side_effect=Exception("Test error")
        ):
            # Execute the current step
            success, result = await workflow_service.execute_workflow_step(
                sample_remediation_workflow,
                remediation_service,
                approval_service,
                rollback_service
            )
            
            # Verify the result
            assert success is False
            assert result is not None
            assert "message" in result
            assert "error" in result["message"].lower()
            
            # Verify the step status was updated
            updated_workflow = await workflow_service.get_workflow(sample_remediation_workflow.id)
            assert updated_workflow is not None
            assert updated_workflow.steps[0].status == WorkflowStepStatus.FAILED
            assert updated_workflow.status == WorkflowStepStatus.FAILED

    @pytest.mark.asyncio
    async def test_handle_approval_error(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_workflow,
        sample_approval_request
    ):
        """Test handling an error during approval."""
        # Mock the approval service to raise an exception
        with patch.object(
            approval_service,
            'approve_request',
            side_effect=Exception("Test error")
        ):
            try:
                # Approve the request
                await approval_service.approve_request(
                    sample_approval_request.id,
                    "test-approver",
                    "Approved for testing"
                )
            except Exception:
                pass
            
            # Verify the workflow is not affected
            updated_workflow = await workflow_service.get_workflow(sample_approval_request.workflow_id)
            assert updated_workflow is not None
            assert updated_workflow.status == sample_remediation_workflow.status

    @pytest.mark.asyncio
    async def test_handle_rollback_error(
        self,
        workflow_service,
        rollback_service,
        sample_remediation_workflow,
        sample_rollback_operation
    ):
        """Test handling an error during rollback."""
        # Create a rollback step
        rollback_step = WorkflowStep(
            id=f"STEP-{datetime.utcnow().strftime('%Y%m%d')}-{os.urandom(4).hex()}",
            name=f"Rollback {sample_rollback_operation.action_id}",
            description=f"Rollback remediation for {sample_rollback_operation.action_id}",
            step_type=WorkflowStepType.ROLLBACK,
            action_id=sample_rollback_operation.action_id,
            status=WorkflowStepStatus.PENDING,
            requires_approval=False,
            approval_roles=[],
            auto_approve_policy=None,
            metadata={
                "rollback_operation_id": sample_rollback_operation.id
            }
        )
        
        # Add the rollback step to the workflow
        workflow = sample_remediation_workflow
        workflow.steps.append(rollback_step)
        workflow.current_step_index = len(workflow.steps) - 1
        await workflow_service._save_workflow(workflow)
        
        # Mock the rollback service to raise an exception
        with patch.object(
            rollback_service,
            'perform_rollback',
            side_effect=Exception("Test error")
        ):
            # Execute the rollback step
            success, result = await workflow_service.execute_workflow_step(
                workflow,
                None,  # remediation_service not needed for rollback
                None,  # approval_service not needed for rollback
                rollback_service
            )
            
            # Verify the result
            assert success is False
            assert result is not None
            assert "message" in result
            assert "error" in result["message"].lower()
            
            # Verify the step status was updated
            updated_workflow = await workflow_service.get_workflow(workflow.id)
            assert updated_workflow is not None
            assert updated_workflow.steps[-1].status == WorkflowStepStatus.FAILED
            assert updated_workflow.status == WorkflowStepStatus.FAILED

class TestWorkflowConcurrency:
    """Tests for workflow concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        rollback_service,
        sample_remediation_request
    ):
        """Test executing multiple workflows concurrently."""
        # Create multiple plans
        plans = []
        for i in range(3):
            request = RemediationRequest(
                repository_url=f"https://github.com/test/repo-{i}",
                commit_sha=f"abcdef{i}",
                vulnerabilities=["CVE-2023-0001", "CVE-2023-0002"],
                auto_apply=False,
                metadata={
                    "environment": "development",
                    "requester": f"test-user-{i}"
                }
            )
            plan = await remediation_service.create_remediation_plan(request)
            plans.append(plan)
        
        # Create workflows for each plan
        workflows = []
        for plan in plans:
            workflow = await workflow_service.create_workflow_for_plan(plan)
            workflows.append(workflow)
        
        # Execute the first step of each workflow concurrently
        results = await asyncio.gather(*[
            workflow_service.execute_workflow_step(
                workflow,
                remediation_service,
                approval_service,
                rollback_service
            )
            for workflow in workflows
        ])
        
        # Verify all results
        for success, result in results:
            assert success is True
            assert result is not None
            assert "step" in result
        
        # Verify all workflows were updated
        for workflow in workflows:
            updated_workflow = await workflow_service.get_workflow(workflow.id)
            assert updated_workflow is not None
            
            # If the step required approval, it should be waiting for approval
            if workflow.steps[0].requires_approval:
                assert updated_workflow.steps[0].status == WorkflowStepStatus.WAITING_FOR_APPROVAL
            else:
                # Otherwise, it should be completed and the workflow should have moved to the next step
                assert updated_workflow.current_step_index > 0

    @pytest.mark.asyncio
    async def test_concurrent_approval_handling(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_request
    ):
        """Test handling multiple approvals concurrently."""
        # Create multiple plans and workflows
        workflows = []
        approval_requests = []
        
        for i in range(3):
            # Create a plan
            request = RemediationRequest(
                repository_url=f"https://github.com/test/repo-{i}",
                commit_sha=f"abcdef{i}",
                vulnerabilities=["CVE-2023-0001", "CVE-2023-0002"],
                auto_apply=False,
                metadata={
                    "environment": "development",
                    "requester": f"test-user-{i}"
                }
            )
            plan = await remediation_service.create_remediation_plan(request)
            
            # Create a workflow
            workflow = await workflow_service.create_workflow_for_plan(plan)
            workflows.append(workflow)
            
            # Make sure the first step requires approval
            workflow.steps[0].requires_approval = True
            await workflow_service._save_workflow(workflow)
            
            # Execute the first step to create an approval request
            success, result = await workflow_service.execute_workflow_step(
                workflow,
                remediation_service,
                approval_service,
                None  # rollback_service not needed
            )
            
            assert success is True
            assert workflow.steps[0].status == WorkflowStepStatus.WAITING_FOR_APPROVAL
            
            # Get the approval request ID
            approval_request_id = result["step"]["result"]["approval_request_id"]
            approval_request = await approval_service.get_approval_request(approval_request_id)
            approval_requests.append(approval_request)
        
        # Approve all requests concurrently
        approve_results = await asyncio.gather(*[
            approval_service.approve_request(
                request.id,
                f"test-approver-{i}",
                f"Approved for testing {i}"
            )
            for i, request in enumerate(approval_requests)
        ])
        
        # Verify all approvals
        for success, request in approve_results:
            assert success is True
            assert request is not None
            assert request.status == ApprovalStatus.APPROVED
        
        # Handle all approval results concurrently
        handle_results = await asyncio.gather(*[
            workflow_service.handle_approval_result(
                request.workflow_id,
                request.step_id,
                True,
                request.approver,
                request.comments,
                remediation_service
            )
            for request in [result[1] for result in approve_results]
        ])
        
        # Verify all results
        for success, result in handle_results:
            assert success is True
            assert result is not None
        
        # Verify all workflows were updated
        for workflow in workflows:
            updated_workflow = await workflow_service.get_workflow(workflow.id)
            assert updated_workflow is not None
            assert updated_workflow.steps[0].status == WorkflowStepStatus.COMPLETED
            assert updated_workflow.current_step_index > 0
