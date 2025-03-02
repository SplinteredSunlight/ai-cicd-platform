"""
Error handling and edge case tests for the Automated Remediation system.

These tests verify that the system properly handles errors and edge cases,
ensuring robustness and reliability in production environments.
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
    mock_http_client,
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


class TestErrorHandling:
    """Tests for error handling in the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_invalid_remediation_request(self, remediation_service):
        """Test handling of invalid remediation requests."""
        # Create an invalid request with missing required fields
        invalid_request = RemediationRequest(
            repository_url="",  # Empty repository URL
            commit_sha="abcdef123456",
            vulnerabilities=[],  # Empty vulnerabilities list
            auto_apply=False,
            metadata={}
        )
        
        # Attempt to create a plan with the invalid request
        with pytest.raises(Exception) as excinfo:
            await remediation_service.create_remediation_plan(invalid_request)
        
        # Verify the error message
        assert "repository_url" in str(excinfo.value).lower() or "vulnerabilities" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_vulnerability(self, remediation_service, mock_template_service):
        """Test handling of nonexistent vulnerabilities."""
        # Mock the template service to return no templates
        mock_template_service.find_templates_for_vulnerability.return_value = []
        
        # Create a request with a nonexistent vulnerability
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["NONEXISTENT-CVE"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Create a plan (should succeed but with no actions)
        plan = await remediation_service.create_remediation_plan(request)
        
        # Verify the plan was created but has no actions
        assert plan is not None
        assert plan.id is not None
        assert len(plan.actions) == 0
        
        # Verify the template service was called correctly
        mock_template_service.find_templates_for_vulnerability.assert_called_once_with("NONEXISTENT-CVE")

    @pytest.mark.asyncio
    async def test_invalid_template_variables(self, remediation_service, mock_template_service):
        """Test handling of invalid template variables."""
        # Mock the template service to return a template
        mock_template_service.find_templates_for_vulnerability.return_value = [
            MagicMock(
                id="TEMPLATE-DEPENDENCY-UPDATE",
                name="Dependency Update",
                description="Update a dependency to a fixed version",
                template_type="DEPENDENCY_UPDATE",
                vulnerability_types=["CVE", "DEPENDENCY"],
                steps=[],
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
                    }
                },
                strategy=RemediationStrategy.AUTOMATED
            )
        ]
        
        # Mock create_action_from_template to raise an exception for invalid variables
        mock_template_service.create_action_from_template.side_effect = ValueError("Missing required variable: file_path")
        
        # Create a request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Create a plan (should succeed but with no actions due to template error)
        plan = await remediation_service.create_remediation_plan(request)
        
        # Verify the plan was created but has no actions
        assert plan is not None
        assert plan.id is not None
        assert len(plan.actions) == 0

    @pytest.mark.asyncio
    async def test_nonexistent_plan(self, remediation_service):
        """Test handling of nonexistent plans."""
        # Attempt to get a nonexistent plan
        nonexistent_plan = await remediation_service.get_remediation_plan("NONEXISTENT-PLAN")
        
        # Verify the result is None
        assert nonexistent_plan is None
        
        # Attempt to execute a nonexistent plan
        with pytest.raises(Exception) as excinfo:
            await remediation_service.execute_remediation_plan("NONEXISTENT-PLAN")
        
        # Verify the error message
        assert "not found" in str(excinfo.value).lower() or "does not exist" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_action(self, remediation_service):
        """Test handling of nonexistent actions."""
        # Attempt to get a nonexistent action
        nonexistent_action = await remediation_service.get_remediation_action("NONEXISTENT-ACTION")
        
        # Verify the result is None
        assert nonexistent_action is None
        
        # Attempt to execute a nonexistent action
        with pytest.raises(Exception) as excinfo:
            await remediation_service.execute_remediation_action("NONEXISTENT-ACTION")
        
        # Verify the error message
        assert "not found" in str(excinfo.value).lower() or "does not exist" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_workflow(self, workflow_service):
        """Test handling of nonexistent workflows."""
        # Attempt to get a nonexistent workflow
        nonexistent_workflow = await workflow_service.get_workflow("NONEXISTENT-WORKFLOW")
        
        # Verify the result is None
        assert nonexistent_workflow is None
        
        # Attempt to execute a step in a nonexistent workflow
        with pytest.raises(Exception) as excinfo:
            await workflow_service.execute_workflow_step(
                None,  # Nonexistent workflow
                None,  # remediation_service not needed for this test
                None,  # approval_service not needed for this test
                None   # rollback_service not needed for this test
            )
        
        # Verify the error message
        assert "workflow" in str(excinfo.value).lower() and ("none" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower())

    @pytest.mark.asyncio
    async def test_nonexistent_approval_request(self, approval_service):
        """Test handling of nonexistent approval requests."""
        # Attempt to get a nonexistent approval request
        nonexistent_request = await approval_service.get_approval_request("NONEXISTENT-REQUEST")
        
        # Verify the result is None
        assert nonexistent_request is None
        
        # Attempt to approve a nonexistent request
        with pytest.raises(Exception) as excinfo:
            await approval_service.approve_request(
                "NONEXISTENT-REQUEST",
                "test-approver",
                "Approved for testing"
            )
        
        # Verify the error message
        assert "not found" in str(excinfo.value).lower() or "does not exist" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_snapshot(self, rollback_service):
        """Test handling of nonexistent snapshots."""
        # Attempt to get a nonexistent snapshot
        nonexistent_snapshot = await rollback_service.get_snapshot("NONEXISTENT-SNAPSHOT")
        
        # Verify the result is None
        assert nonexistent_snapshot is None

    @pytest.mark.asyncio
    async def test_nonexistent_rollback_operation(self, rollback_service):
        """Test handling of nonexistent rollback operations."""
        # Attempt to get a nonexistent rollback operation
        nonexistent_operation = await rollback_service.get_rollback_operation("NONEXISTENT-OPERATION")
        
        # Verify the result is None
        assert nonexistent_operation is None
        
        # Attempt to perform a nonexistent rollback operation
        with pytest.raises(Exception) as excinfo:
            await rollback_service.perform_rollback("NONEXISTENT-OPERATION")
        
        # Verify the error message
        assert "not found" in str(excinfo.value).lower() or "does not exist" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_action_execution_failure(self, remediation_service, sample_remediation_plan):
        """Test handling of action execution failures."""
        # Get an action from the plan
        action = sample_remediation_plan.actions[0]
        
        # Mock the execute_action method to raise an exception
        with patch.object(
            remediation_service,
            '_execute_action',
            side_effect=Exception("Action execution failed")
        ):
            # Execute the action
            result = await remediation_service.execute_remediation_action(action.id)
            
            # Verify the result indicates failure
            assert result is not None
            assert result.action_id == action.id
            assert result.success is False
            assert result.status == RemediationStatus.FAILED
            assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_workflow_step_execution_failure(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        rollback_service,
        sample_remediation_workflow
    ):
        """Test handling of workflow step execution failures."""
        # Mock the remediation service to raise an exception
        with patch.object(
            remediation_service,
            'execute_remediation_action',
            side_effect=Exception("Step execution failed")
        ):
            # Execute the current step
            success, result = await workflow_service.execute_workflow_step(
                sample_remediation_workflow,
                remediation_service,
                approval_service,
                rollback_service
            )
            
            # Verify the result indicates failure
            assert success is False
            assert result is not None
            assert "message" in result
            assert "failed" in result["message"].lower()
            
            # Verify the step status was updated
            updated_workflow = await workflow_service.get_workflow(sample_remediation_workflow.id)
            assert updated_workflow is not None
            assert updated_workflow.steps[0].status == WorkflowStepStatus.FAILED
            assert updated_workflow.status == WorkflowStepStatus.FAILED

    @pytest.mark.asyncio
    async def test_approval_rejection(
        self,
        workflow_service,
        remediation_service,
        approval_service,
        sample_remediation_workflow,
        sample_approval_request
    ):
        """Test handling of approval rejections."""
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
        
        # Verify the result indicates failure
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
    async def test_rollback_failure(
        self,
        rollback_service,
        sample_rollback_operation
    ):
        """Test handling of rollback failures."""
        # Mock the _perform_rollback method to raise an exception
        with patch.object(
            rollback_service,
            '_perform_rollback',
            side_effect=Exception("Rollback failed")
        ):
            # Perform the rollback
            result = await rollback_service.perform_rollback(sample_rollback_operation.id)
            
            # Verify the result indicates failure
            assert result is not None
            assert result["success"] is False
            assert "error" in result
            assert "failed" in result["error"].lower()
            
            # Verify the operation status was updated
            updated_operation = await rollback_service.get_rollback_operation(sample_rollback_operation.id)
            assert updated_operation is not None
            assert updated_operation.status == RollbackStatus.FAILED


class TestEdgeCases:
    """Tests for edge cases in the Automated Remediation system."""

    @pytest.mark.asyncio
    async def test_empty_plan(self, remediation_service, workflow_service):
        """Test handling of empty remediation plans (no actions)."""
        # Create a request with a vulnerability that has no templates
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["NO-TEMPLATE-CVE"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Mock the find_templates_for_vulnerability method to return no templates
        with patch.object(
            remediation_service,
            'find_templates_for_vulnerability',
            return_value=[]
        ):
            # Create a plan
            plan = await remediation_service.create_remediation_plan(request)
            
            # Verify the plan was created but has no actions
            assert plan is not None
            assert plan.id is not None
            assert len(plan.actions) == 0
            
            # Create a workflow for the empty plan
            workflow = await workflow_service.create_workflow_for_plan(plan)
            
            # Verify the workflow was created but has no steps
            assert workflow is not None
            assert workflow.id is not None
            assert len(workflow.steps) == 0
            assert workflow.status == WorkflowStepStatus.COMPLETED  # Empty workflow is considered completed

    @pytest.mark.asyncio
    async def test_large_plan(self, remediation_service):
        """Test handling of large remediation plans (many vulnerabilities)."""
        # Create a request with many vulnerabilities
        num_vulnerabilities = 100
        vulnerabilities = [f"CVE-2023-{i:04d}" for i in range(num_vulnerabilities)]
        
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=vulnerabilities,
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Mock the find_templates_for_vulnerability method to return a template for each vulnerability
        with patch.object(
            remediation_service,
            'find_templates_for_vulnerability',
            return_value=[
                MagicMock(
                    id="TEMPLATE-DEPENDENCY-UPDATE",
                    name="Dependency Update",
                    description="Update a dependency to a fixed version",
                    template_type="DEPENDENCY_UPDATE",
                    vulnerability_types=["CVE", "DEPENDENCY"],
                    steps=[],
                    variables={},
                    strategy=RemediationStrategy.AUTOMATED
                )
            ]
        ), patch.object(
            remediation_service,
            'create_action_from_template',
            return_value=RemediationAction(
                id="ACTION-TEST",
                vulnerability_id="CVE-TEST",
                name="Test Action",
                description="Test action for testing",
                strategy=RemediationStrategy.AUTOMATED,
                source=RemediationSource.TEMPLATE,
                steps=[],
                status=RemediationStatus.PENDING,
                created_at=datetime.utcnow(),
                metadata={}
            )
        ):
            # Create a plan
            plan = await remediation_service.create_remediation_plan(request)
            
            # Verify the plan was created with the expected number of actions
            assert plan is not None
            assert plan.id is not None
            assert len(plan.actions) == num_vulnerabilities

    @pytest.mark.asyncio
    async def test_duplicate_vulnerabilities(self, remediation_service):
        """Test handling of duplicate vulnerabilities in a request."""
        # Create a request with duplicate vulnerabilities
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001", "CVE-2023-0001", "CVE-2023-0002", "CVE-2023-0002"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Mock the find_templates_for_vulnerability method to return a template
        with patch.object(
            remediation_service,
            'find_templates_for_vulnerability',
            return_value=[
                MagicMock(
                    id="TEMPLATE-DEPENDENCY-UPDATE",
                    name="Dependency Update",
                    description="Update a dependency to a fixed version",
                    template_type="DEPENDENCY_UPDATE",
                    vulnerability_types=["CVE", "DEPENDENCY"],
                    steps=[],
                    variables={},
                    strategy=RemediationStrategy.AUTOMATED
                )
            ]
        ), patch.object(
            remediation_service,
            'create_action_from_template',
            side_effect=[
                RemediationAction(
                    id=f"ACTION-{i}",
                    vulnerability_id=f"CVE-2023-000{i}",
                    name=f"Test Action {i}",
                    description=f"Test action {i} for testing",
                    strategy=RemediationStrategy.AUTOMATED,
                    source=RemediationSource.TEMPLATE,
                    steps=[],
                    status=RemediationStatus.PENDING,
                    created_at=datetime.utcnow(),
                    metadata={}
                )
                for i in range(1, 3)
            ]
        ):
            # Create a plan
            plan = await remediation_service.create_remediation_plan(request)
            
            # Verify the plan was created with deduplicated vulnerabilities
            assert plan is not None
            assert plan.id is not None
            assert len(plan.actions) == 2  # Only 2 unique vulnerabilities

    @pytest.mark.asyncio
    async def test_concurrent_approval_requests(
        self,
        workflow_service,
        approval_service,
        sample_remediation_workflow
    ):
        """Test handling of concurrent approval requests for the same step."""
        # Create a step that requires approval
        step = sample_remediation_workflow.steps[0]
        step.requires_approval = True
        step.approval_roles = [ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER]
        await workflow_service._save_workflow(sample_remediation_workflow)
        
        # Create multiple approval requests for the same step concurrently
        num_requests = 5
        create_tasks = []
        for _ in range(num_requests):
            task = approval_service.create_approval_request(
                workflow_id=sample_remediation_workflow.id,
                step_id=step.id,
                action_id=step.action_id,
                required_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
                auto_approve_policy=None
            )
            create_tasks.append(task)
        
        # Execute all create tasks concurrently
        requests = await asyncio.gather(*create_tasks)
        
        # Verify all requests were created
        assert len(requests) == num_requests
        for request in requests:
            assert request is not None
            assert request.id is not None
            assert request.workflow_id == sample_remediation_workflow.id
            assert request.step_id == step.id
            assert request.action_id == step.action_id
            
        # Get all approval requests for the step
        all_requests = await approval_service.get_approval_requests_for_step(
            sample_remediation_workflow.id,
            step.id
        )
        
        # Verify all requests were retrieved
        assert all_requests is not None
        assert len(all_requests) == num_requests

    @pytest.mark.asyncio
    async def test_invalid_file_paths(self, rollback_service, sample_remediation_workflow):
        """Test handling of invalid file paths in snapshots."""
        # Attempt to create a snapshot with an invalid file path
        with pytest.raises(Exception) as excinfo:
            await rollback_service.create_snapshot(
                workflow_id=sample_remediation_workflow.id,
                action_id=sample_remediation_workflow.steps[0].action_id,
                path="../../../etc/passwd",  # Path traversal attempt
                content="test content"
            )
        
        # Verify the error message
        assert "path" in str(excinfo.value).lower() and ("invalid" in str(excinfo.value).lower() or "traversal" in str(excinfo.value).lower())

    @pytest.mark.asyncio
    async def test_very_large_content(self, rollback_service, sample_remediation_workflow):
        """Test handling of very large content in snapshots."""
        # Create a large content string (10 MB)
        large_content = "x" * (10 * 1024 * 1024)
        
        # Create a snapshot with large content
        snapshot = await rollback_service.create_snapshot(
            workflow_id=sample_remediation_workflow.id,
            action_id=sample_remediation_workflow.steps[0].action_id,
            path="large-file.txt",
            content=large_content
        )
        
        # Verify the snapshot was created
        assert snapshot is not None
        assert snapshot.id is not None
        assert snapshot.path == "large-file.txt"
        
        # Retrieve the snapshot
        retrieved_snapshot = await rollback_service.get_snapshot(snapshot.id)
        
        # Verify the snapshot was retrieved with the correct content
        assert retrieved_snapshot is not None
        assert retrieved_snapshot.id == snapshot.id
        assert retrieved_snapshot.path == snapshot.path
        assert len(retrieved_snapshot.content) == len(large_content)
