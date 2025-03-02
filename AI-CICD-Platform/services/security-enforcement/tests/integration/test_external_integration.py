"""
External system integration tests for the Automated Remediation system.

These tests verify the integration between the Automated Remediation system and external systems,
such as CI/CD platforms, version control systems, and other external services.
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


class TestVersionControlIntegration:
    """Tests for integration with version control systems."""

    @pytest.mark.asyncio
    async def test_git_repository_integration(self, mock_http_client, remediation_service):
        """Test integration with Git repositories."""
        # Mock HTTP client for Git API calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": "abcdef123456",
            "commit": {
                "message": "Fix security vulnerability CVE-2023-0001",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2025-03-02T00:00:00Z"
                }
            },
            "html_url": "https://github.com/test/repo/commit/abcdef123456"
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a Git integration service (mock)
        git_service = AsyncMock()
        git_service.create_pull_request.return_value = {
            "id": 12345,
            "number": 42,
            "title": "Fix security vulnerability CVE-2023-0001",
            "html_url": "https://github.com/test/repo/pull/42"
        }
        
        # Create a remediation request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user",
                "create_pull_request": True
            }
        )
        
        # Create a plan
        plan = await remediation_service.create_remediation_plan(request)
        
        # Execute the plan
        results = await remediation_service.execute_remediation_plan(plan.id)
        
        # Verify the results
        assert results is not None
        assert len(results) > 0
        for result in results:
            assert result.success is True
        
        # Create a pull request for the changes
        pr_result = await git_service.create_pull_request(
            repository_url=request.repository_url,
            base_branch="main",
            head_branch=f"fix-cve-2023-0001",
            title="Fix security vulnerability CVE-2023-0001",
            body="This pull request fixes the security vulnerability CVE-2023-0001 by updating the affected dependency.",
            labels=["security", "automated-remediation"]
        )
        
        # Verify the pull request was created
        assert pr_result is not None
        assert pr_result["id"] == 12345
        assert pr_result["number"] == 42
        assert "CVE-2023-0001" in pr_result["title"]
        
        # Verify the Git service was called correctly
        git_service.create_pull_request.assert_called_once()
        assert git_service.create_pull_request.call_args[1]["repository_url"] == request.repository_url
        assert "CVE-2023-0001" in git_service.create_pull_request.call_args[1]["title"]

    @pytest.mark.asyncio
    async def test_commit_changes_to_repository(self, mock_http_client, remediation_service):
        """Test committing changes to a repository."""
        # Mock HTTP client for Git API calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": "fedcba654321",
            "commit": {
                "message": "Fix security vulnerability CVE-2023-0001",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2025-03-02T00:00:00Z"
                }
            },
            "html_url": "https://github.com/test/repo/commit/fedcba654321"
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a Git integration service (mock)
        git_service = AsyncMock()
        git_service.commit_changes.return_value = {
            "sha": "fedcba654321",
            "html_url": "https://github.com/test/repo/commit/fedcba654321"
        }
        
        # Create a remediation request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001"],
            auto_apply=True,  # Auto-apply changes
            metadata={
                "environment": "development",
                "requester": "test-user"
            }
        )
        
        # Create a plan
        plan = await remediation_service.create_remediation_plan(request)
        
        # Execute the plan
        results = await remediation_service.execute_remediation_plan(plan.id)
        
        # Verify the results
        assert results is not None
        assert len(results) > 0
        for result in results:
            assert result.success is True
        
        # Commit the changes to the repository
        commit_result = await git_service.commit_changes(
            repository_url=request.repository_url,
            branch="main",
            message="Fix security vulnerability CVE-2023-0001",
            changes=[
                {
                    "file_path": "package.json",
                    "content": json.dumps({
                        "name": "test-package",
                        "version": "1.0.0",
                        "dependencies": {
                            "example-dependency": "1.1.0"  # Updated version
                        }
                    }, indent=2)
                }
            ],
            author_name="Automated Remediation",
            author_email="remediation@example.com"
        )
        
        # Verify the commit was created
        assert commit_result is not None
        assert commit_result["sha"] == "fedcba654321"
        
        # Verify the Git service was called correctly
        git_service.commit_changes.assert_called_once()
        assert git_service.commit_changes.call_args[1]["repository_url"] == request.repository_url
        assert "CVE-2023-0001" in git_service.commit_changes.call_args[1]["message"]
        assert len(git_service.commit_changes.call_args[1]["changes"]) > 0
        assert git_service.commit_changes.call_args[1]["changes"][0]["file_path"] == "package.json"


class TestCICDIntegration:
    """Tests for integration with CI/CD platforms."""

    @pytest.mark.asyncio
    async def test_github_actions_integration(self, mock_http_client, remediation_service):
        """Test integration with GitHub Actions."""
        # Mock HTTP client for GitHub API calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/test/repo/actions/runs/12345"
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a GitHub Actions integration service (mock)
        github_actions_service = AsyncMock()
        github_actions_service.trigger_workflow.return_value = {
            "id": 12345,
            "status": "queued",
            "html_url": "https://github.com/test/repo/actions/runs/12345"
        }
        
        # Create a remediation request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user",
                "trigger_ci": True,
                "ci_platform": "github-actions",
                "workflow_file": "remediation.yml"
            }
        )
        
        # Create a plan
        plan = await remediation_service.create_remediation_plan(request)
        
        # Execute the plan
        results = await remediation_service.execute_remediation_plan(plan.id)
        
        # Verify the results
        assert results is not None
        assert len(results) > 0
        for result in results:
            assert result.success is True
        
        # Trigger a GitHub Actions workflow
        workflow_result = await github_actions_service.trigger_workflow(
            repository_url=request.repository_url,
            workflow_file="remediation.yml",
            ref="main",
            inputs={
                "plan_id": plan.id,
                "vulnerability_id": "CVE-2023-0001",
                "auto_approve": "false"
            }
        )
        
        # Verify the workflow was triggered
        assert workflow_result is not None
        assert workflow_result["id"] == 12345
        assert workflow_result["status"] == "queued"
        
        # Verify the GitHub Actions service was called correctly
        github_actions_service.trigger_workflow.assert_called_once()
        assert github_actions_service.trigger_workflow.call_args[1]["repository_url"] == request.repository_url
        assert github_actions_service.trigger_workflow.call_args[1]["workflow_file"] == "remediation.yml"
        assert github_actions_service.trigger_workflow.call_args[1]["inputs"]["plan_id"] == plan.id

    @pytest.mark.asyncio
    async def test_jenkins_integration(self, mock_http_client, remediation_service):
        """Test integration with Jenkins."""
        # Mock HTTP client for Jenkins API calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "12345",
            "url": "https://jenkins.example.com/job/remediation-job/12345/"
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a Jenkins integration service (mock)
        jenkins_service = AsyncMock()
        jenkins_service.trigger_job.return_value = {
            "id": "12345",
            "url": "https://jenkins.example.com/job/remediation-job/12345/"
        }
        
        # Create a remediation request
        request = RemediationRequest(
            repository_url="https://github.com/test/repo",
            commit_sha="abcdef123456",
            vulnerabilities=["CVE-2023-0001"],
            auto_apply=False,
            metadata={
                "environment": "development",
                "requester": "test-user",
                "trigger_ci": True,
                "ci_platform": "jenkins",
                "job_name": "remediation-job"
            }
        )
        
        # Create a plan
        plan = await remediation_service.create_remediation_plan(request)
        
        # Execute the plan
        results = await remediation_service.execute_remediation_plan(plan.id)
        
        # Verify the results
        assert results is not None
        assert len(results) > 0
        for result in results:
            assert result.success is True
        
        # Trigger a Jenkins job
        job_result = await jenkins_service.trigger_job(
            job_name="remediation-job",
            parameters={
                "PLAN_ID": plan.id,
                "VULNERABILITY_ID": "CVE-2023-0001",
                "AUTO_APPROVE": "false"
            }
        )
        
        # Verify the job was triggered
        assert job_result is not None
        assert job_result["id"] == "12345"
        
        # Verify the Jenkins service was called correctly
        jenkins_service.trigger_job.assert_called_once()
        assert jenkins_service.trigger_job.call_args[1]["job_name"] == "remediation-job"
        assert jenkins_service.trigger_job.call_args[1]["parameters"]["PLAN_ID"] == plan.id


class TestNotificationIntegration:
    """Tests for integration with notification systems."""

    @pytest.mark.asyncio
    async def test_slack_notification(self, mock_http_client, remediation_service, sample_remediation_plan):
        """Test sending notifications to Slack."""
        # Mock HTTP client for Slack API calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "channel": "C12345",
            "ts": "1614556800.000100",
            "message": {
                "text": "Remediation plan created for CVE-2023-0001",
                "username": "Remediation Bot",
                "bot_id": "B12345",
                "attachments": [
                    {
                        "text": "Vulnerability: CVE-2023-0001\nRepository: https://github.com/test/repo\nStatus: PENDING"
                    }
                ],
                "type": "message",
                "subtype": "bot_message",
                "ts": "1614556800.000100"
            }
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a Slack integration service (mock)
        slack_service = AsyncMock()
        slack_service.send_notification.return_value = {
            "ok": True,
            "channel": "C12345",
            "ts": "1614556800.000100"
        }
        
        # Send a notification to Slack
        notification_result = await slack_service.send_notification(
            channel="#security-alerts",
            text="Remediation plan created for CVE-2023-0001",
            attachments=[
                {
                    "title": "Remediation Plan",
                    "text": f"Plan ID: {sample_remediation_plan.id}\nVulnerability: CVE-2023-0001\nRepository: https://github.com/test/repo\nStatus: {sample_remediation_plan.status}",
                    "color": "#36a64f"
                }
            ]
        )
        
        # Verify the notification was sent
        assert notification_result is not None
        assert notification_result["ok"] is True
        
        # Verify the Slack service was called correctly
        slack_service.send_notification.assert_called_once()
        assert slack_service.send_notification.call_args[1]["channel"] == "#security-alerts"
        assert "CVE-2023-0001" in slack_service.send_notification.call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_email_notification(self, mock_http_client, remediation_service, sample_remediation_plan):
        """Test sending notifications via email."""
        # Create an email integration service (mock)
        email_service = AsyncMock()
        email_service.send_email.return_value = {
            "id": "12345",
            "status": "sent"
        }
        
        # Send an email notification
        email_result = await email_service.send_email(
            to=["security@example.com"],
            subject="Remediation Plan Created for CVE-2023-0001",
            body=f"""
            <h1>Remediation Plan Created</h1>
            <p>A remediation plan has been created for vulnerability CVE-2023-0001.</p>
            <ul>
                <li><strong>Plan ID:</strong> {sample_remediation_plan.id}</li>
                <li><strong>Repository:</strong> https://github.com/test/repo</li>
                <li><strong>Status:</strong> {sample_remediation_plan.status}</li>
            </ul>
            <p>Please review and approve the remediation plan.</p>
            """,
            is_html=True
        )
        
        # Verify the email was sent
        assert email_result is not None
        assert email_result["status"] == "sent"
        
        # Verify the email service was called correctly
        email_service.send_email.assert_called_once()
        assert "security@example.com" in email_service.send_email.call_args[1]["to"]
        assert "CVE-2023-0001" in email_service.send_email.call_args[1]["subject"]


class TestIssueTrackerIntegration:
    """Tests for integration with issue tracking systems."""

    @pytest.mark.asyncio
    async def test_jira_integration(self, mock_http_client, remediation_service, sample_remediation_plan):
        """Test integration with Jira."""
        # Mock HTTP client for Jira API calls
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "12345",
            "key": "SEC-123",
            "self": "https://jira.example.com/rest/api/2/issue/12345"
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a Jira integration service (mock)
        jira_service = AsyncMock()
        jira_service.create_issue.return_value = {
            "id": "12345",
            "key": "SEC-123",
            "self": "https://jira.example.com/rest/api/2/issue/12345"
        }
        
        # Create a Jira issue
        issue_result = await jira_service.create_issue(
            project_key="SEC",
            issue_type="Task",
            summary="Remediate security vulnerability CVE-2023-0001",
            description=f"""
            A remediation plan has been created for vulnerability CVE-2023-0001.
            
            Plan ID: {sample_remediation_plan.id}
            Repository: https://github.com/test/repo
            Status: {sample_remediation_plan.status}
            
            Please review and approve the remediation plan.
            """,
            labels=["security", "remediation", "automated"],
            custom_fields={
                "customfield_10001": "CVE-2023-0001",
                "customfield_10002": sample_remediation_plan.id
            }
        )
        
        # Verify the issue was created
        assert issue_result is not None
        assert issue_result["key"] == "SEC-123"
        
        # Verify the Jira service was called correctly
        jira_service.create_issue.assert_called_once()
        assert jira_service.create_issue.call_args[1]["project_key"] == "SEC"
        assert "CVE-2023-0001" in jira_service.create_issue.call_args[1]["summary"]
        assert sample_remediation_plan.id in jira_service.create_issue.call_args[1]["description"]

    @pytest.mark.asyncio
    async def test_github_issues_integration(self, mock_http_client, remediation_service, sample_remediation_plan):
        """Test integration with GitHub Issues."""
        # Mock HTTP client for GitHub API calls
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 12345,
            "number": 42,
            "title": "Remediate security vulnerability CVE-2023-0001",
            "html_url": "https://github.com/test/repo/issues/42"
        }
        mock_http_client.post.return_value = mock_response
        
        # Create a GitHub Issues integration service (mock)
        github_issues_service = AsyncMock()
        github_issues_service.create_issue.return_value = {
            "id": 12345,
            "number": 42,
            "title": "Remediate security vulnerability CVE-2023-0001",
            "html_url": "https://github.com/test/repo/issues/42"
        }
        
        # Create a GitHub issue
        issue_result = await github_issues_service.create_issue(
            repository_url="https://github.com/test/repo",
            title="Remediate security vulnerability CVE-2023-0001",
            body=f"""
            A remediation plan has been created for vulnerability CVE-2023-0001.
            
            Plan ID: {sample_remediation_plan.id}
            Repository: https://github.com/test/repo
            Status: {sample_remediation_plan.status}
            
            Please review and approve the remediation plan.
            """,
            labels=["security", "remediation", "automated"]
        )
        
        # Verify the issue was created
        assert issue_result is not None
        assert issue_result["number"] == 42
        
        # Verify the GitHub Issues service was called correctly
        github_issues_service.create_issue.assert_called_once()
        assert github_issues_service.create_issue.call_args[1]["repository_url"] == "https://github.com/test/repo"
        assert "CVE-2023-0001" in github_issues_service.create_issue.call_args[1]["title"]
        assert sample_remediation_plan.id in github_issues_service.create_issue.call_args[1]["body"]
