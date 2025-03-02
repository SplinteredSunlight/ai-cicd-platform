"""
Comprehensive integration test suite for the Automated Remediation system.

This test suite provides comprehensive integration tests for the Automated Remediation system,
covering end-to-end workflows, component interactions, data persistence, performance,
and error handling scenarios.
"""

import os
import sys
import pytest
import json
import asyncio
import time
import random
from datetime import datetime, timedelta
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
    mock_http_client,
    temp_data_dir,
    mock_settings
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
from templates.remediation_templates import RemediationTemplateService, TemplateType


class TestEndToEndRemediation:
    """End-to-end tests for the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_complete_remediation_lifecycle(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        mock_template_service
    ):
        """
        Test the complete lifecycle of a remediation process from creation to rollback.
        
        This test covers:
        1. Creating a remediation request
        2. Creating a remediation plan
        3. Creating a workflow
        4. Executing the workflow with approval steps
        5. Verifying the remediation
        6. Creating a snapshot
        7. Rolling back the remediation
        8. Verifying the rollback
        """
        # Step 1: Create a remediation request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001", "CVE-2023-0002"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user",
                "priority": "high"
            }
        )

        # Step 2: Create a remediation plan
        plan = await remediation_service.create_remediation_plan(request)
        assert plan is not None
        assert plan.id is not None
        assert plan.status == RemediationStatus.PENDING
        assert len(plan.actions) > 0

        # Step 3: Create a workflow
        workflow = await workflow_service.create_workflow_for_plan(plan)
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.status == WorkflowStepStatus.PENDING
        assert len(workflow.steps) > 0

        # Step 4: Execute the workflow with approval steps
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
            assert result is not None

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
                assert request is not None
                assert request.status == ApprovalStatus.APPROVED

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
                assert result is not None

            # Reload the workflow to get the updated state
            workflow = await workflow_service.get_workflow(workflow.id)

        # Step 5: Verify the workflow is completed
        assert workflow.status == WorkflowStepStatus.COMPLETED
        
        # Verify the plan is completed
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
                "repository_url": request.repository_url,
                "commit_sha": request.commit_sha
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
                "repository_url": request.repository_url,
                "commit_sha": request.commit_sha,
                "reason": "Testing rollback"
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
    async def test_auto_apply_remediation(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service
    ):
        """
        Test the auto-apply remediation workflow without manual approvals.
        
        This test covers:
        1. Creating a remediation request with auto_apply=True
        2. Creating a remediation plan
        3. Creating a workflow
        4. Executing the workflow without approval steps
        5. Verifying the remediation
        """
        # Step 1: Create a remediation request with auto_apply=True
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001"],
            auto_apply=True,
            metadata={
                "environment": "development",
                "requester": "test-user",
                "priority": "high"
            }
        )

        # Step 2: Create a remediation plan
        plan = await remediation_service.create_remediation_plan(request)
        assert plan is not None
        assert plan.id is not None
        assert plan.status == RemediationStatus.PENDING
        assert len(plan.actions) > 0

        # Step 3: Create a workflow
        workflow = await workflow_service.create_workflow_for_plan(plan)
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.status == WorkflowStepStatus.PENDING
        assert len(workflow.steps) > 0

        # Make sure no steps require approval
        for step in workflow.steps:
            step.requires_approval = False
        await workflow_service._save_workflow(workflow)

        # Step 4: Execute the workflow without approval steps
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
            assert result is not None

            # Reload the workflow to get the updated state
            workflow = await workflow_service.get_workflow(workflow.id)

        # Step 5: Verify the workflow is completed
        assert workflow.status == WorkflowStepStatus.COMPLETED
        
        # Verify the plan is completed
        updated_plan = await remediation_service.get_remediation_plan(plan.id)
        assert updated_plan.status == RemediationStatus.COMPLETED


class TestComponentInteractions:
    """Tests for interactions between different components of the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_remediation_template_workflow_integration(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        mock_template_service
    ):
        """
        Test the integration between remediation templates, workflow, and approval services.
        
        This test covers:
        1. Finding templates for a vulnerability
        2. Creating an action from a template
        3. Creating a plan with the action
        4. Creating a workflow for the plan
        5. Executing the workflow with approval
        """
        # Step 1: Find templates for a vulnerability
        vulnerability_id = "CVE-2023-0001"
        templates = await remediation_service.find_templates_for_vulnerability(vulnerability_id)
        assert templates is not None
        assert len(templates) > 0

        # Step 2: Create an action from a template
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

        assert action is not None
        assert action.vulnerability_id == vulnerability_id
        assert action.strategy == RemediationStrategy.AUTOMATED
        assert action.source == RemediationSource.TEMPLATE

        # Step 3: Create a plan with the action
        plan = RemediationPlan(
            id=f"PLAN-{datetime.utcnow().strftime('%Y%m%d')}-{os.urandom(4).hex()}",
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            target="https://github.com/test/repo@abcdef123456",
            actions=[action],
            status=RemediationStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )

        # Save the plan
        await remediation_service._save_plan(plan)

        # Step 4: Create a workflow for the plan
        workflow = await workflow_service.create_workflow_for_plan(plan)
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.status == WorkflowStepStatus.PENDING
        assert len(workflow.steps) > 0

        # Make the first step require approval
        workflow.steps[0].requires_approval = True
        workflow.steps[0].approval_roles = [ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER]
        await workflow_service._save_workflow(workflow)

        # Step 5: Execute the workflow with approval
        # Execute the first step
        success, result = await workflow_service.execute_workflow_step(
            workflow,
            remediation_service,
            approval_service,
            rollback_service
        )

        assert success is True
        assert result is not None
        assert "step" in result
        assert result["step"]["status"] == WorkflowStepStatus.WAITING_FOR_APPROVAL

        # Get the approval request ID
        approval_request_id = result["step"]["result"]["approval_request_id"]
        assert approval_request_id is not None

        # Approve the request
        success, request = await approval_service.approve_request(
            approval_request_id,
            "test-approver",
            "Approved for testing"
        )

        assert success is True
        assert request is not None
        assert request.status == ApprovalStatus.APPROVED

        # Handle the approval result
        success, result = await workflow_service.handle_approval_result(
            workflow.id,
            workflow.steps[0].id,
            True,
            "test-approver",
            "Approved for testing",
            remediation_service
        )

        assert success is True
        assert result is not None

        # Reload the workflow to get the updated state
        workflow = await workflow_service.get_workflow(workflow.id)
        assert workflow.steps[0].status == WorkflowStepStatus.COMPLETED
        assert workflow.current_step_index > 0

    @pytest.mark.asyncio
    async def test_api_service_integration(
        self,
        mock_fastapi_app,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service
    ):
        """
        Test the integration between API endpoints and services.
        
        This test covers:
        1. Creating a plan via API
        2. Getting the plan via API
        3. Executing the plan via API
        4. Approving a request via API
        5. Creating and executing a rollback via API
        """
        # Step 1: Create a plan via API
        sample_request = {
            "repository_url": "https://github.com/test/repo",
            "commit_sha": "abcdef123456",
            "vulnerabilities": ["CVE-2023-0001", "CVE-2023-0002"],
            "auto_apply": False,
            "metadata": {
                "environment": "development",
                "requester": "test-user"
            }
        }

        response = mock_fastapi_app.post("/remediation/plans", json=sample_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plan" in data
        assert "workflow" in data

        # Get the plan ID and workflow ID
        plan_id = data["plan"]["id"]
        workflow_id = data["workflow"]["id"]

        # Step 2: Get the plan via API
        response = mock_fastapi_app.get(f"/remediation/plans/{plan_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plan" in data
        assert data["plan"]["id"] == plan_id

        # Step 3: Execute the workflow step via API
        response = mock_fastapi_app.post(f"/remediation/workflows/{workflow_id}/execute-step")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert "workflow" in data
        assert data["workflow"]["id"] == workflow_id

        # Check if the step requires approval
        workflow = data["workflow"]
        step = workflow["steps"][0]
        if step["status"] == WorkflowStepStatus.WAITING_FOR_APPROVAL:
            # Step 4: Approve the request via API
            approval_request_id = step["result"]["approval_request_id"]
            response = mock_fastapi_app.post(
                f"/remediation/approvals/{approval_request_id}/approve",
                json={"approver": "test-approver", "comments": "Approved for testing"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "request" in data
            assert data["request"]["id"] == approval_request_id
            assert data["request"]["status"] == ApprovalStatus.APPROVED

        # Step 5: Create a snapshot for rollback
        # First, create a snapshot
        snapshot = await rollback_service.create_snapshot(
            workflow_id=workflow_id,
            action_id=step["action_id"],
            path="package.json",
            content=json.dumps({
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {
                    "example-dependency": "1.0.0"
                }
            }, indent=2),
            metadata={
                "repository_url": sample_request["repository_url"],
                "commit_sha": sample_request["commit_sha"]
            }
        )

        # Create a rollback operation via API
        response = mock_fastapi_app.post(
            "/remediation/rollbacks",
            json={
                "workflow_id": workflow_id,
                "action_id": step["action_id"],
                "snapshot_id": snapshot.id,
                "rollback_type": RollbackType.FULL,
                "metadata": {
                    "repository_url": sample_request["repository_url"],
                    "commit_sha": sample_request["commit_sha"]
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "operation" in data
        operation_id = data["operation"]["id"]

        # Execute the rollback via API
        response = mock_fastapi_app.post(f"/remediation/rollbacks/{operation_id}/execute")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["success"] is True


class TestDataPersistenceAndRecovery:
    """Tests for data persistence and recovery."""

    @pytest.mark.asyncio
    async def test_service_restart_data_persistence(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_plan,
        sample_remediation_workflow,
        sample_approval_request,
        sample_snapshot,
        sample_rollback_operation,
        temp_data_dir
    ):
        """
        Test data persistence across service restarts.
        
        This test covers:
        1. Creating objects with the original services
        2. Creating new service instances (simulating a restart)
        3. Retrieving objects with the new services
        4. Verifying the objects are the same
        """
        # Get the IDs of all objects
        plan_id = sample_remediation_plan.id
        workflow_id = sample_remediation_workflow.id
        approval_id = sample_approval_request.id
        snapshot_id = sample_snapshot.id
        operation_id = sample_rollback_operation.id

        # Create new service instances (simulating a restart)
        new_remediation_service = RemediationService()
        new_remediation_service.base_dir = temp_data_dir
        new_remediation_service.plans_dir = os.path.join(temp_data_dir, "plans")
        new_remediation_service.actions_dir = os.path.join(temp_data_dir, "actions")
        new_remediation_service.results_dir = os.path.join(temp_data_dir, "results")

        new_workflow_service = RemediationWorkflowService()
        new_workflow_service.base_dir = temp_data_dir
        new_workflow_service.workflows_dir = os.path.join(temp_data_dir, "workflows")

        new_approval_service = ApprovalService()
        new_approval_service.base_dir = temp_data_dir
        new_approval_service.requests_dir = os.path.join(temp_data_dir, "approvals")

        new_rollback_service = RollbackService()
        new_rollback_service.base_dir = temp_data_dir
        new_rollback_service.snapshots_dir = os.path.join(temp_data_dir, "snapshots")
        new_rollback_service.operations_dir = os.path.join(temp_data_dir, "rollbacks")

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
    async def test_concurrent_operations_data_integrity(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_plan
    ):
        """
        Test data integrity during concurrent operations.
        
        This test covers:
        1. Performing multiple concurrent operations on the same objects
        2. Verifying data integrity after concurrent operations
        """
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
                auto_approve_policy=None,
                metadata={}
            ),
            rollback_service.create_snapshot(
                workflow_id=workflow.id,
                action_id=workflow.steps[0].action_id,
                path="package.json",
                content="{}",
                metadata={}
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


class TestPerformanceAndLoad:
    """Tests for system performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_remediation_plans(
        self,
        remediation_service,
        workflow_service
    ):
        """
        Test creating and executing multiple remediation plans concurrently.
        
        This test covers:
        1. Creating multiple remediation requests
        2. Creating plans concurrently
        3. Creating workflows concurrently
        4. Executing plans concurrently
        5. Verifying all plans were executed successfully
        """
        # Create multiple remediation requests
        requests = []
        for i in range(5):  # Create 5 requests
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

    @pytest.mark.asyncio
    async def test_performance_under_load(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service
    ):
        """
        Test system performance under load.
        
        This test covers:
        1. Creating a large number of remediation requests
        2. Measuring the time to create plans
        3. Measuring the time to create workflows
        4. Measuring the time to execute plans
        """
        # Number of requests to create
        num_requests = 10

        # Create multiple remediation requests
        requests = []
        for i in range(num_requests):
            request = RemediationRequest(
                repository_url=f"https://github.com/test/repo-{i}",
                commit_sha=f"abcdef{i}",
                vulnerabilities=["CVE-2023-0001"],
                auto_apply=True,
                metadata={
                    "environment": "development",
                    "requester": f"test-user-{i}"
                }
            )
            requests.append(request)

        # Measure time to create plans
        start_time = time.time()
        plans = await asyncio.gather(*[
            remediation_service.create_remediation_plan(request)
            for request in requests
        ])
        plan_creation_time = time.time() - start_time

        # Verify all plans were created
        assert len(plans) == num_requests
        for plan in plans:
            assert plan is not None
            assert plan.id is not None

        # Measure time to create workflows
        start_time = time.time()
        workflows = await asyncio.gather(*[
            workflow_service.create_workflow_for_plan(plan)
            for plan in plans
        ])
        workflow_creation_time = time.time() - start_time

        # Verify all workflows were created
        assert len(workflows) == num_requests
        for workflow in workflows:
            assert workflow is not None
            assert workflow.id is not None

        # Measure time to execute plans
        start_time = time.time()
        results = await asyncio.gather(*[
            remediation_service.execute_remediation_plan(plan.id)
            for plan in plans
        ])
        plan_execution_time = time.time() - start_time

        # Verify all plans were executed
        assert len(results) == num_requests
        for result_list in results:
            assert result_list is not None
            assert len(result_list) > 0
            for result in result_list:
                assert result.success is True

        # Print performance metrics
        print(f"Performance metrics for {num_requests} requests:")
        print(f"Plan creation time: {plan_creation_time:.2f} seconds")
        print(f"Workflow creation time: {workflow_creation_time:.2f} seconds")
        print(f"Plan execution time: {plan_execution_time:.2f} seconds")
        print(f"Average time per request: {(plan_creation_time + workflow_creation_time + plan_execution_time) / num_requests:.2f} seconds")

        # Assert performance is within acceptable limits
        # These thresholds should be adjusted based on the expected performance of the system
        assert plan_creation_time < num_requests * 0.5  # 0.5 seconds per plan
        assert workflow_creation_time < num_requests * 0.5  # 0.5 seconds per workflow
        assert plan_execution_time < num_requests * 1.0  # 1.0 seconds per plan execution


class TestErrorHandlingAndEdgeCases:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handle_invalid_remediation_request(
        self,
        remediation_service
    ):
        """
        Test handling invalid remediation requests.
        
        This test covers:
        1. Creating a remediation request with invalid data
        2. Verifying that the system properly handles the error
        """
        # Create an invalid remediation request (missing required fields)
        with pytest.raises(Exception):
            request = RemediationRequest(
                repository_url="https://github.com/test/repo",
                # Missing commit_sha
                vulnerabilities=["CVE-2023-0001"],
                auto_apply=False,
                metadata={}
            )
            await remediation_service.create_remediation_plan(request)

        # Create an invalid remediation request (invalid vulnerability ID)
        with pytest.raises(Exception):
            request = RemediationRequest(
                repository_url="https://github.com/test/repo",
                commit_sha="abcdef123456",
                vulnerabilities=["INVALID-ID"],
                auto_apply=False,
                metadata={}
            )
            await remediation_service.create_remediation_plan(request)

    @pytest.mark.asyncio
    async def test_handle_nonexistent_resources(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service
    ):
        """
        Test handling requests for nonexistent resources.
        
        This test covers:
        1. Requesting nonexistent plans, actions, workflows, etc.
        2. Verifying that the system properly handles the errors
        """
        # Request a nonexistent plan
        with pytest.raises(Exception):
            await remediation_service.get_remediation_plan("nonexistent-plan")

        # Request a nonexistent action
        with pytest.raises(Exception):
            await remediation_service.get_remediation_action("nonexistent-action")

        # Request a nonexistent workflow
        with pytest.raises(Exception):
            await workflow_service.get_workflow("nonexistent-workflow")

        # Request a nonexistent approval request
        with pytest.raises(Exception):
            await approval_service.get_approval_request("nonexistent-request")

        # Request a nonexistent snapshot
        with pytest.raises(Exception):
            await rollback_service.get_snapshot("nonexistent-snapshot")

        # Request a nonexistent rollback operation
        with pytest.raises(Exception):
            await rollback_service.get_rollback_operation("nonexistent-operation")

    @pytest.mark.asyncio
    async def test_handle_workflow_execution_errors(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        sample_remediation_workflow
    ):
        """
        Test handling errors during workflow execution.
        
        This test covers:
        1. Simulating errors during workflow execution
        2. Verifying that the system properly handles the errors
        """
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
    async def test_handle_approval_rejection(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        sample_remediation_workflow,
        sample_approval_request
    ):
        """
        Test handling approval rejections.
        
        This test covers:
        1. Rejecting an approval request
        2. Verifying that the workflow is properly updated
        """
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
    async def test_handle_rollback_errors(
        self,
        workflow_service,
        rollback_service,
        sample_remediation_workflow,
        sample_rollback_operation
    ):
        """
        Test handling errors during rollback operations.
        
        This test covers:
        1. Simulating errors during rollback operations
        2. Verifying that the system properly handles the errors
        """
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
