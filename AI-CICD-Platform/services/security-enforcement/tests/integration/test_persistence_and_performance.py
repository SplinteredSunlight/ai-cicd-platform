"""
Data persistence and performance tests for the Automated Remediation system.

These tests verify data persistence across service restarts, data integrity during concurrent operations,
and system performance under load.
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
    temp_data_dir
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


class TestDataPersistence:
    """Tests for data persistence across service restarts."""

    @pytest.mark.asyncio
    async def test_data_persistence_across_restarts(
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
    async def test_data_versioning(
        self,
        remediation_service,
        sample_remediation_plan
    ):
        """Test data versioning and history tracking."""
        # Get the original plan
        original_plan = sample_remediation_plan
        
        # Update the plan status multiple times to create versions
        statuses = [
            RemediationStatus.IN_PROGRESS,
            RemediationStatus.COMPLETED,
            RemediationStatus.ROLLED_BACK
        ]
        
        updated_plans = []
        for status in statuses:
            updated_plan = await remediation_service.update_remediation_plan_status(
                original_plan.id,
                status
            )
            updated_plans.append(updated_plan)
            
            # Add a small delay to ensure different timestamps
            await asyncio.sleep(0.1)
        
        # Verify the final status
        final_plan = await remediation_service.get_remediation_plan(original_plan.id)
        assert final_plan.status == RemediationStatus.ROLLED_BACK
        
        # Check if history is tracked (if the service supports it)
        if hasattr(remediation_service, 'get_remediation_plan_history'):
            history = await remediation_service.get_remediation_plan_history(original_plan.id)
            assert history is not None
            assert len(history) >= len(statuses)
            
            # Verify the history contains all status changes
            history_statuses = [entry.status for entry in history]
            for status in statuses:
                assert status in history_statuses

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


class TestPerformanceAndLoad:
    """Tests for system performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_plan_creation(
        self,
        remediation_service,
        temp_data_dir
    ):
        """Test creating multiple remediation plans concurrently."""
        # Create multiple remediation requests
        num_requests = 10
        requests = []
        for i in range(num_requests):
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
        
        # Measure the time to create plans concurrently
        start_time = time.time()
        plans = await asyncio.gather(*[
            remediation_service.create_remediation_plan(request)
            for request in requests
        ])
        end_time = time.time()
        
        # Verify all plans were created
        assert len(plans) == num_requests
        for plan in plans:
            assert plan is not None
            assert plan.id is not None
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_plan = total_time / num_requests
        
        # Log performance metrics
        print(f"Created {num_requests} plans in {total_time:.2f} seconds")
        print(f"Average time per plan: {avg_time_per_plan:.2f} seconds")
        
        # Verify plans can be retrieved
        retrieved_plans = await asyncio.gather(*[
            remediation_service.get_remediation_plan(plan.id)
            for plan in plans
        ])
        
        assert len(retrieved_plans) == num_requests
        for plan in retrieved_plans:
            assert plan is not None
            assert plan.id is not None

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        temp_data_dir
    ):
        """Test executing multiple workflows concurrently."""
        # Create multiple plans and workflows
        num_workflows = 5
        plans = []
        workflows = []
        
        for i in range(num_workflows):
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
            plans.append(plan)
            
            # Create a workflow
            workflow = await workflow_service.create_workflow_for_plan(plan)
            workflows.append(workflow)
        
        # Measure the time to execute workflow steps concurrently
        start_time = time.time()
        results = await asyncio.gather(*[
            workflow_service.execute_workflow_step(
                workflow,
                remediation_service,
                approval_service,
                rollback_service
            )
            for workflow in workflows
        ])
        end_time = time.time()
        
        # Verify all steps were executed
        assert len(results) == num_workflows
        for success, result in results:
            assert success is True
            assert result is not None
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_workflow = total_time / num_workflows
        
        # Log performance metrics
        print(f"Executed {num_workflows} workflow steps in {total_time:.2f} seconds")
        print(f"Average time per workflow step: {avg_time_per_workflow:.2f} seconds")
        
        # Verify workflows were updated
        updated_workflows = await asyncio.gather(*[
            workflow_service.get_workflow(workflow.id)
            for workflow in workflows
        ])
        
        assert len(updated_workflows) == num_workflows
        for workflow in updated_workflows:
            assert workflow is not None
            assert workflow.id is not None

    @pytest.mark.asyncio
    async def test_system_resource_usage(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        temp_data_dir
    ):
        """Test system resource usage during operations."""
        # Create a large number of plans and workflows
        num_plans = 20
        plans = []
        workflows = []
        
        # Measure memory usage before
        import psutil
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create plans and workflows
        for i in range(num_plans):
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
            plans.append(plan)
            
            # Create a workflow
            workflow = await workflow_service.create_workflow_for_plan(plan)
            workflows.append(workflow)
        
        # Measure memory usage after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = memory_after - memory_before
        
        # Log resource usage
        print(f"Memory usage before: {memory_before:.2f} MB")
        print(f"Memory usage after: {memory_after:.2f} MB")
        print(f"Memory increase: {memory_diff:.2f} MB")
        print(f"Average memory per plan/workflow: {memory_diff/num_plans:.2f} MB")
        
        # Verify all plans and workflows were created
        assert len(plans) == num_plans
        assert len(workflows) == num_plans
        
        # Clean up to free memory
        plans = None
        workflows = None
        import gc
        gc.collect()

    @pytest.mark.asyncio
    async def test_race_conditions(
        self,
        remediation_service,
        workflow_service,
        approval_service,
        rollback_service,
        temp_data_dir
    ):
        """Test for race conditions during concurrent operations."""
        # Create a plan and workflow
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001", "CVE-2023-0002"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        plan = await remediation_service.create_remediation_plan(request)
        workflow = await workflow_service.create_workflow_for_plan(plan)
        
        # Perform multiple concurrent updates to the same objects
        num_updates = 10
        
        # Update plan status concurrently
        plan_statuses = [
            RemediationStatus.IN_PROGRESS,
            RemediationStatus.COMPLETED,
            RemediationStatus.FAILED,
            RemediationStatus.ROLLED_BACK
        ]
        plan_update_tasks = []
        for _ in range(num_updates):
            status = random.choice(plan_statuses)
            task = remediation_service.update_remediation_plan_status(
                plan.id,
                status
            )
            plan_update_tasks.append(task)
        
        # Update workflow status concurrently
        workflow_statuses = [
            WorkflowStepStatus.IN_PROGRESS,
            WorkflowStepStatus.COMPLETED,
            WorkflowStepStatus.FAILED,
            WorkflowStepStatus.WAITING_FOR_APPROVAL
        ]
        workflow_update_tasks = []
        for _ in range(num_updates):
            status = random.choice(workflow_statuses)
            task = workflow_service.update_workflow_status(
                workflow.id,
                status
            )
            workflow_update_tasks.append(task)
        
        # Execute all updates concurrently
        await asyncio.gather(
            *plan_update_tasks,
            *workflow_update_tasks
        )
        
        # Verify the objects are still in a valid state
        updated_plan = await remediation_service.get_remediation_plan(plan.id)
        updated_workflow = await workflow_service.get_workflow(workflow.id)
        
        assert updated_plan is not None
        assert updated_plan.id == plan.id
        assert updated_plan.status in plan_statuses
        
        assert updated_workflow is not None
        assert updated_workflow.id == workflow.id
        assert updated_workflow.status in workflow_statuses


class TestDataMigrationAndVersioning:
    """Tests for data migration and versioning."""

    @pytest.mark.asyncio
    async def test_data_migration(
        self,
        remediation_service,
        workflow_service,
        temp_data_dir
    ):
        """Test data migration between different versions."""
        # Create a plan with the current version
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001", "CVE-2023-0002"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user",
                "version": "1.0.0"  # Current version
            }
        )
        plan = await remediation_service.create_remediation_plan(request)
        
        # Simulate an older version of the plan by modifying its structure
        # This is a simplified example - in a real scenario, you would need to
        # implement proper migration logic in the service
        plan_path = os.path.join(remediation_service.plans_dir, f"{plan.id}.json")
        with open(plan_path, "r") as f:
            plan_data = json.load(f)
        
        # Modify the plan data to simulate an older version
        plan_data["metadata"]["version"] = "0.9.0"  # Older version
        # Remove a field that was added in version 1.0.0
        if "created_at" in plan_data:
            del plan_data["created_at"]
        
        # Write the modified plan back to disk
        with open(plan_path, "w") as f:
            json.dump(plan_data, f)
        
        # Try to load the plan with the current version of the service
        # If the service has proper migration logic, it should handle the older version
        migrated_plan = await remediation_service.get_remediation_plan(plan.id)
        
        # Verify the plan was loaded successfully
        assert migrated_plan is not None
        assert migrated_plan.id == plan.id
        
        # Verify the plan has been migrated to the current version
        # This assumes the service adds missing fields during migration
        assert hasattr(migrated_plan, "created_at")
        
        # If the service stores the version in the plan, verify it was updated
        if hasattr(migrated_plan, "version"):
            assert migrated_plan.version == "1.0.0"  # Current version
        elif "version" in migrated_plan.metadata:
            assert migrated_plan.metadata["version"] == "1.0.0"  # Current version
