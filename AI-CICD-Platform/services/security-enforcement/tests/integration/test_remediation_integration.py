"""
Integration tests for the Automated Remediation system.
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
    WorkflowStepStatus
)
from services.approval_service import ApprovalService, ApprovalRole, ApprovalStatus
from services.rollback_service import RollbackService, RollbackType, RollbackStatus

class TestRemediationIntegration:
    """Integration tests for the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_create_remediation_plan(self, remediation_service, sample_remediation_request):
        """Test creating a remediation plan."""
        # Create a plan
        plan = await remediation_service.create_remediation_plan(sample_remediation_request)
        
        # Verify the plan was created
        assert plan is not None
        assert plan.id is not None
        assert plan.status == RemediationStatus.PENDING
        assert plan.target == f"{sample_remediation_request.repository_url}@{sample_remediation_request.commit_sha}"
        assert len(plan.actions) > 0
        
        # Verify the plan was saved
        saved_plan = await remediation_service.get_remediation_plan(plan.id)
        assert saved_plan is not None
        assert saved_plan.id == plan.id
        assert saved_plan.status == plan.status
        assert saved_plan.target == plan.target
        assert len(saved_plan.actions) == len(plan.actions)

    @pytest.mark.asyncio
    async def test_create_workflow_for_plan(self, workflow_service, sample_remediation_plan):
        """Test creating a workflow for a remediation plan."""
        # Create a workflow
        workflow = await workflow_service.create_workflow_for_plan(sample_remediation_plan)
        
        # Verify the workflow was created
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.status == WorkflowStepStatus.PENDING
        assert workflow.plan_id == sample_remediation_plan.id
        assert len(workflow.steps) > 0
        
        # Verify the workflow was saved
        saved_workflow = await workflow_service.get_workflow(workflow.id)
        assert saved_workflow is not None
        assert saved_workflow.id == workflow.id
        assert saved_workflow.status == workflow.status
        assert saved_workflow.plan_id == workflow.plan_id
        assert len(saved_workflow.steps) == len(workflow.steps)

    @pytest.mark.asyncio
    async def test_execute_remediation_action(self, remediation_service, sample_remediation_plan):
        """Test executing a remediation action."""
        # Get an action from the plan
        action = sample_remediation_plan.actions[0]
        
        # Execute the action
        result = await remediation_service.execute_remediation_action(action.id)
        
        # Verify the result
        assert result is not None
        assert result.action_id == action.id
        assert result.vulnerability_id == action.vulnerability_id
        assert result.success is True
        assert result.status == RemediationStatus.COMPLETED
        
        # Verify the action status was updated
        updated_action = await remediation_service.get_remediation_action(action.id)
        assert updated_action is not None
        assert updated_action.status == RemediationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_remediation_plan(self, remediation_service, sample_remediation_plan):
        """Test executing a remediation plan."""
        # Execute the plan
        results = await remediation_service.execute_remediation_plan(sample_remediation_plan.id)
        
        # Verify the results
        assert results is not None
        assert len(results) == len(sample_remediation_plan.actions)
        for result in results:
            assert result.success is True
            assert result.status == RemediationStatus.COMPLETED
        
        # Verify the plan status was updated
        updated_plan = await remediation_service.get_remediation_plan(sample_remediation_plan.id)
        assert updated_plan is not None
        assert updated_plan.status == RemediationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_workflow_step(
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
    async def test_approval_workflow(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_workflow,
        sample_approval_request
    ):
        """Test the approval workflow."""
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
        assert request.approver == "test-approver"
        assert request.comments == "Approved for testing"
        
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
    async def test_rollback_workflow(
        self,
        rollback_service,
        sample_rollback_operation
    ):
        """Test the rollback workflow."""
        # Perform the rollback
        result = await rollback_service.perform_rollback(sample_rollback_operation.id)
        
        # Verify the result
        assert result is not None
        assert result["success"] is True
        
        # Verify the operation status was updated
        updated_operation = await rollback_service.get_rollback_operation(sample_rollback_operation.id)
        assert updated_operation is not None
        assert updated_operation.status == RollbackStatus.COMPLETED
        
        # Verify the rollback
        verify_result = await rollback_service.verify_rollback(sample_rollback_operation.id)
        assert verify_result is not None
        assert verify_result["success"] is True
        
        # Verify the operation status was updated
        updated_operation = await rollback_service.get_rollback_operation(sample_rollback_operation.id)
        assert updated_operation is not None
        assert updated_operation.status == RollbackStatus.VERIFIED

class TestEndToEndRemediation:
    """End-to-end tests for the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_end_to_end_remediation_workflow(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_request
    ):
        """Test the end-to-end remediation workflow."""
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

    @pytest.mark.asyncio
    async def test_concurrent_remediation_operations(
        self,
        remediation_service,
        workflow_service,
        sample_remediation_request
    ):
        """Test concurrent remediation operations."""
        # Create multiple remediation requests
        requests = []
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
            requests.append(request)
        
        # Create plans concurrently
        plans = await asyncio.gather(*[
            remediation_service.create_remediation_plan(request)
            for request in requests
        ])
        
        # Verify all plans were created
        assert len(plans) == len(requests)
        for plan in plans:
            assert plan is not None
            assert plan.id is not None
        
        # Create workflows concurrently
        workflows = await asyncio.gather(*[
            workflow_service.create_workflow_for_plan(plan)
            for plan in plans
        ])
        
        # Verify all workflows were created
        assert len(workflows) == len(plans)
        for workflow in workflows:
            assert workflow is not None
            assert workflow.id is not None
        
        # Execute plans concurrently
        results = await asyncio.gather(*[
            remediation_service.execute_remediation_plan(plan.id)
            for plan in plans
        ])
        
        # Verify all plans were executed
        assert len(results) == len(plans)
        for result_list in results:
            assert result_list is not None
            assert len(result_list) > 0
            for result in result_list:
                assert result.success is True
        
        # Verify all plans are completed
        updated_plans = await asyncio.gather(*[
            remediation_service.get_remediation_plan(plan.id)
            for plan in plans
        ])
        
        for updated_plan in updated_plans:
            assert updated_plan is not None
            assert updated_plan.status == RemediationStatus.COMPLETED

class TestDataPersistenceAndRecovery:
    """Tests for data persistence and recovery."""

    @pytest.mark.asyncio
    async def test_data_persistence(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_plan,
        sample_remediation_workflow,
        sample_approval_request,
        sample_snapshot,
        sample_rollback_operation
    ):
        """Test data persistence across service restarts."""
        # Get the IDs of all objects
        plan_id = sample_remediation_plan.id
        workflow_id = sample_remediation_workflow.id
        approval_id = sample_approval_request.id
        snapshot_id = sample_snapshot.id
        operation_id = sample_rollback_operation.id
        
        # Create new service instances (simulating a restart)
        new_remediation_service = RemediationService()
        new_remediation_service.base_dir = remediation_service.base_dir
        new_remediation_service.plans_dir = remediation_service.plans_dir
        new_remediation_service.actions_dir = remediation_service.actions_dir
        new_remediation_service.results_dir = remediation_service.results_dir
        
        new_workflow_service = RemediationWorkflowService()
        new_workflow_service.base_dir = workflow_service.base_dir
        new_workflow_service.workflows_dir = workflow_service.workflows_dir
        
        new_approval_service = ApprovalService()
        new_approval_service.base_dir = approval_service.base_dir
        new_approval_service.requests_dir = approval_service.requests_dir
        
        new_rollback_service = RollbackService()
        new_rollback_service.base_dir = rollback_service.base_dir
        new_rollback_service.snapshots_dir = rollback_service.snapshots_dir
        new_rollback_service.operations_dir = rollback_service.operations_dir
        
        # Retrieve all objects from the new services
        plan = await new_remediation_service.get_remediation_plan(plan_id)
        workflow = await new_workflow_service.get_workflow(workflow_id)
        approval = await new_approval_service.get_approval_request(approval_id)
        snapshot = await new_rollback_service.get_snapshot(snapshot_id)
        operation = await new_rollback_service.get_rollback_operation(operation_id)
        
        # Verify all objects were retrieved
        assert plan is not None
        assert plan.id == plan_id
        assert workflow is not None
        assert workflow.id == workflow_id
        assert approval is not None
        assert approval.id == approval_id
        assert snapshot is not None
        assert snapshot.id == snapshot_id
        assert operation is not None
        assert operation.id == operation_id
        
        # Verify the relationships between objects
        assert workflow.plan_id == plan.id
        assert approval.workflow_id == workflow.id
        assert operation.workflow_id == workflow.id
        assert operation.snapshot_id == snapshot.id

    @pytest.mark.asyncio
    async def test_data_integrity_during_concurrent_operations(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_plan
    ):
        """Test data integrity during concurrent operations."""
        # Create a workflow for the plan
        workflow = await workflow_service.create_workflow_for_plan(sample_remediation_plan)
        
        # Perform multiple concurrent operations on the same objects
        # 1. Update plan status
        # 2. Update workflow status
        # 3. Execute an action
        # 4. Create an approval request
        # 5. Create a snapshot
        
        results = await asyncio.gather(
            remediation_service.update_remediation_plan_status(
                sample_remediation_plan.id,
                RemediationStatus.IN_PROGRESS
            ),
            workflow_service.update_workflow_status(
                workflow.id,
                WorkflowStepStatus.IN_PROGRESS
            ),
            remediation_service.execute_remediation_action(
                sample_remediation_plan.actions[0].id
            ),
            approval_service.create_approval_request(
                workflow_id=workflow.id,
                step_id=workflow.steps[0].id,
                action_id=workflow.steps[0].action_id,
                required_roles=[ApprovalRole.SECURITY_ADMIN],
                auto_approve_policy=None
            ),
            rollback_service.create_snapshot(
                workflow_id=workflow.id,
                action_id=workflow.steps[0].action_id,
                path="package.json",
                content="{}"
            )
        )
        
        # Verify all operations completed successfully
        for result in results:
            assert result is not None
        
        # Verify data integrity
        updated_plan = await remediation_service.get_remediation_plan(sample_remediation_plan.id)
        updated_workflow = await workflow_service.get_workflow(workflow.id)
        updated_action = await remediation_service.get_remediation_action(sample_remediation_plan.actions[0].id)
        
        assert updated_plan is not None
        assert updated_plan.status == RemediationStatus.IN_PROGRESS
        assert updated_workflow is not None
        assert updated_workflow.status == WorkflowStepStatus.IN_PROGRESS
        assert updated_action is not None
        assert updated_action.status == RemediationStatus.COMPLETED
