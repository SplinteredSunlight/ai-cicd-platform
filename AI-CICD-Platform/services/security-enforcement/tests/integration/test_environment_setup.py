"""
Test environment setup for the Automated Remediation system integration tests.

This module provides utilities for setting up and tearing down the test environment
for integration tests, including initializing all remediation components, setting up
test data directories and files, and creating mock services for external dependencies.
"""

import os
import sys
import pytest
import json
import asyncio
import shutil
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
from templates.remediation_templates import RemediationTemplateService, TemplateType


class TestEnvironmentSetup:
    """Tests for the test environment setup."""

    @pytest.fixture
    def test_env_dir(self):
        """Create a temporary directory for the test environment."""
        test_dir = os.path.join(os.path.dirname(__file__), "data", "test_env")
        os.makedirs(test_dir, exist_ok=True)
        yield test_dir
        # Clean up after the test
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

    @pytest.mark.asyncio
    async def test_service_initialization(
        self,
        test_env_dir
    ):
        """Test initializing all remediation services."""
        # Create service instances with the test environment directory
        remediation_service = RemediationService()
        workflow_service = RemediationWorkflowService()
        approval_service = ApprovalService()
        rollback_service = RollbackService()
        
        # Override data directories to use the test environment directory
        remediation_service.base_dir = test_env_dir
        remediation_service.plans_dir = os.path.join(test_env_dir, "plans")
        remediation_service.actions_dir = os.path.join(test_env_dir, "actions")
        remediation_service.results_dir = os.path.join(test_env_dir, "results")
        
        workflow_service.base_dir = test_env_dir
        workflow_service.workflows_dir = os.path.join(test_env_dir, "workflows")
        
        approval_service.base_dir = test_env_dir
        approval_service.requests_dir = os.path.join(test_env_dir, "approvals")
        
        rollback_service.base_dir = test_env_dir
        rollback_service.snapshots_dir = os.path.join(test_env_dir, "snapshots")
        rollback_service.operations_dir = os.path.join(test_env_dir, "rollbacks")
        
        # Create directories
        os.makedirs(remediation_service.plans_dir, exist_ok=True)
        os.makedirs(remediation_service.actions_dir, exist_ok=True)
        os.makedirs(remediation_service.results_dir, exist_ok=True)
        os.makedirs(workflow_service.workflows_dir, exist_ok=True)
        os.makedirs(approval_service.requests_dir, exist_ok=True)
        os.makedirs(rollback_service.snapshots_dir, exist_ok=True)
        os.makedirs(rollback_service.operations_dir, exist_ok=True)
        
        # Verify directories were created
        assert os.path.exists(remediation_service.plans_dir)
        assert os.path.exists(remediation_service.actions_dir)
        assert os.path.exists(remediation_service.results_dir)
        assert os.path.exists(workflow_service.workflows_dir)
        assert os.path.exists(approval_service.requests_dir)
        assert os.path.exists(rollback_service.snapshots_dir)
        assert os.path.exists(rollback_service.operations_dir)
        
        # Create a template service mock
        template_service = AsyncMock()
        remediation_service.template_service = template_service
        
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
        
        # Create a sample request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001", "CVE-2023-0002", "CVE-2023-0003"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Create a plan
        plan = await remediation_service.create_remediation_plan(request)
        
        # Verify the plan was created
        assert plan is not None
        assert plan.id is not None
        assert plan.status == RemediationStatus.PENDING
        assert plan.target == f"{request.repository_url}@{request.commit_sha}"
        assert len(plan.actions) > 0
        
        # Create a workflow
        workflow = await workflow_service.create_workflow_for_plan(plan)
        
        # Verify the workflow was created
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.status == WorkflowStepStatus.PENDING
        assert workflow.plan_id == plan.id
        assert len(workflow.steps) > 0
        
        # Create an approval request
        approval_request = await approval_service.create_approval_request(
            workflow_id=workflow.id,
            step_id=workflow.steps[0].id,
            action_id=workflow.steps[0].action_id,
            required_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
            auto_approve_policy=None
        )
        
        # Verify the approval request was created
        assert approval_request is not None
        assert approval_request.id is not None
        assert approval_request.workflow_id == workflow.id
        assert approval_request.step_id == workflow.steps[0].id
        assert approval_request.action_id == workflow.steps[0].action_id
        assert approval_request.status == ApprovalStatus.PENDING
        
        # Create a snapshot
        snapshot = await rollback_service.create_snapshot(
            workflow_id=workflow.id,
            action_id=workflow.steps[0].action_id,
            path="package.json",
            content=json.dumps({
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {
                    "example-dependency": "1.0.0"
                }
            }, indent=2)
        )
        
        # Verify the snapshot was created
        assert snapshot is not None
        assert snapshot.id is not None
        assert snapshot.workflow_id == workflow.id
        assert snapshot.action_id == workflow.steps[0].action_id
        assert snapshot.path == "package.json"
        
        # Create a rollback operation
        rollback_operation = await rollback_service.create_rollback_operation(
            workflow_id=workflow.id,
            action_id=workflow.steps[0].action_id,
            snapshot_id=snapshot.id,
            rollback_type=RollbackType.FULL
        )
        
        # Verify the rollback operation was created
        assert rollback_operation is not None
        assert rollback_operation.id is not None
        assert rollback_operation.workflow_id == workflow.id
        assert rollback_operation.action_id == workflow.steps[0].action_id
        assert rollback_operation.snapshot_id == snapshot.id
        assert rollback_operation.rollback_type == RollbackType.FULL
        assert rollback_operation.status == RollbackStatus.PENDING

    @pytest.mark.asyncio
    async def test_test_data_setup(
        self,
        test_env_dir
    ):
        """Test setting up test data directories and files."""
        # Create test data directories
        test_data_dir = os.path.join(test_env_dir, "data")
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Create test data files
        # 1. Sample vulnerability
        vulnerability_file = os.path.join(test_data_dir, "sample_vulnerability.json")
        with open(vulnerability_file, "w") as f:
            json.dump({
                "id": "CVE-2023-0001",
                "title": "Test Vulnerability 1",
                "description": "A test vulnerability in a dependency that can be exploited to execute arbitrary code.",
                "severity": "HIGH",
                "cvss_score": 8.5,
                "affected_component": "example-dependency@1.0.0",
                "fix_version": "1.1.0",
                "references": [
                    "https://example.com/cve-2023-0001",
                    "https://github.com/example/dependency/security/advisories/GHSA-1234-5678-9012"
                ],
                "metadata": {
                    "cwe": "CWE-78",
                    "affected_versions": ">=1.0.0 <1.1.0",
                    "exploit_available": True,
                    "exploit_maturity": "proof-of-concept",
                    "patch_available": True
                }
            }, f, indent=2)
        
        # 2. Sample package.json
        package_file = os.path.join(test_data_dir, "sample_package.json")
        with open(package_file, "w") as f:
            json.dump({
                "name": "test-project",
                "version": "1.0.0",
                "description": "A test project for remediation integration tests",
                "main": "index.js",
                "scripts": {
                    "test": "jest",
                    "start": "node index.js"
                },
                "dependencies": {
                    "example-dependency": "1.0.0",
                    "secure-library": "2.0.0",
                    "another-package": "3.1.0"
                },
                "devDependencies": {
                    "jest": "29.0.0",
                    "eslint": "8.0.0"
                },
                "repository": {
                    "type": "git",
                    "url": "https://github.com/test/repo"
                },
                "author": "Test Author",
                "license": "MIT"
            }, f, indent=2)
        
        # 3. Sample remediation template
        template_file = os.path.join(test_data_dir, "sample_template.json")
        with open(template_file, "w") as f:
            json.dump({
                "id": "TEMPLATE-DEPENDENCY-UPDATE",
                "name": "Dependency Update",
                "description": "Update a dependency to a fixed version",
                "template_type": "DEPENDENCY_UPDATE",
                "vulnerability_types": ["CVE", "DEPENDENCY"],
                "steps": [
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
                    },
                    {
                        "name": "Verify update",
                        "description": "Verify the dependency was updated correctly",
                        "action": "VERIFY",
                        "parameters": {
                            "file_path": "${file_path}",
                            "dependency_name": "${dependency_name}",
                            "fixed_version": "${fixed_version}"
                        }
                    }
                ],
                "variables": {
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
                "strategy": "AUTOMATED",
                "created_at": "2025-03-02T00:00:00Z",
                "updated_at": "2025-03-02T00:00:00Z",
                "metadata": {
                    "built_in": True,
                    "supported_package_managers": ["npm", "pip", "maven", "gradle"]
                }
            }, f, indent=2)
        
        # Verify test data files were created
        assert os.path.exists(vulnerability_file)
        assert os.path.exists(package_file)
        assert os.path.exists(template_file)
        
        # Verify test data files can be loaded
        with open(vulnerability_file, "r") as f:
            vulnerability_data = json.load(f)
            assert vulnerability_data["id"] == "CVE-2023-0001"
        
        with open(package_file, "r") as f:
            package_data = json.load(f)
            assert package_data["name"] == "test-project"
            assert package_data["dependencies"]["example-dependency"] == "1.0.0"
        
        with open(template_file, "r") as f:
            template_data = json.load(f)
            assert template_data["id"] == "TEMPLATE-DEPENDENCY-UPDATE"
            assert len(template_data["steps"]) == 3

    @pytest.mark.asyncio
    async def test_mock_services_setup(
        self,
        test_env_dir
    ):
        """Test setting up mock services for external dependencies."""
        # Create a mock HTTP client
        http_client = AsyncMock()
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        http_client.get.return_value = mock_response
        http_client.post.return_value = mock_response
        
        # Create a mock template service
        template_service = AsyncMock()
        
        # Mock find_templates_for_vulnerability
        template_service.find_templates_for_vulnerability.return_value = [
            MagicMock(
                id="TEMPLATE-DEPENDENCY-UPDATE",
                name="Dependency Update",
                description="Update a dependency to a fixed version",
                template_type=TemplateType.DEPENDENCY_UPDATE,
                vulnerability_types=["CVE", "DEPENDENCY"],
                steps=[],
                variables={},
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
            steps=[],
            status=RemediationStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={}
        )
        
        # Create a remediation service with the mock template service
        remediation_service = RemediationService()
        remediation_service.base_dir = test_env_dir
        remediation_service.plans_dir = os.path.join(test_env_dir, "plans")
        remediation_service.actions_dir = os.path.join(test_env_dir, "actions")
        remediation_service.results_dir = os.path.join(test_env_dir, "results")
        os.makedirs(remediation_service.plans_dir, exist_ok=True)
        os.makedirs(remediation_service.actions_dir, exist_ok=True)
        os.makedirs(remediation_service.results_dir, exist_ok=True)
        
        # Set the mock template service
        remediation_service.template_service = template_service
        
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
        
        # Create a plan
        plan = await remediation_service.create_remediation_plan(request)
        
        # Verify the plan was created
        assert plan is not None
        assert plan.id is not None
        assert len(plan.actions) > 0
        
        # Verify the template service was called
        template_service.find_templates_for_vulnerability.assert_called_once_with("CVE-2023-0001")
        template_service.create_action_from_template.assert_called_once()
        
        # Test HTTP client mock
        response = await http_client.get("https://example.com/api")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        response = await http_client.post("https://example.com/api", json={"data": "test"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
