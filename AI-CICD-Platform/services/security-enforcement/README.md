# Security Enforcement Service

The Security Enforcement service provides security scanning, vulnerability detection, policy enforcement, and automated remediation capabilities for the AI-CICD-Platform.

## Features

- **Security Scanning**: Scan repositories, artifacts, and code for security vulnerabilities
- **Vulnerability Database**: Maintain a database of known vulnerabilities and their status
- **Policy Enforcement**: Define and enforce security policies for CI/CD pipelines
- **Compliance Reporting**: Generate compliance reports for various standards
- **Automated Remediation**: Automatically fix or mitigate detected security issues

## Automated Remediation

The automated remediation feature provides the following capabilities:

### Remediation Engine

- Auto-fix capabilities for common vulnerabilities (dependency issues, misconfigurations, etc.)
- Plugin architecture for different remediation strategies
- Remediation templates for common security issues
- Support for custom remediation scripts
- Remediation verification mechanisms

### Remediation Workflows

- Workflow definitions for different vulnerability types
- Staged remediation for complex issues
- Support for manual intervention points in workflows
- Notification mechanisms for workflow status
- Audit logging for remediation actions

### Approval Mechanisms

- Approval workflows for security patches
- Role-based approval permissions
- Support for automated approvals based on policy rules
- Approval notifications and reminders
- Approval audit logging

### Rollback Capabilities

- Snapshot mechanisms before applying remediation
- Rollback procedures for failed remediation
- Support for partial rollbacks
- Rollback verification
- Rollback audit logging

### Policy Integration

- Integration with the policy engine for policy-driven remediation
- Policy-based approval rules
- Policy compliance verification after remediation
- Support for policy exceptions during remediation
- Policy-based prioritization for remediation actions

## API Endpoints

The service provides the following API endpoints for automated remediation:

### Remediation Plans

- `POST /remediation/plans`: Create a new remediation plan
- `GET /remediation/plans`: Get all remediation plans
- `GET /remediation/plans/{plan_id}`: Get a specific remediation plan
- `GET /remediation/plans/{plan_id}/actions`: Get all actions for a plan
- `POST /remediation/plans/{plan_id}/execute`: Execute a remediation plan

### Remediation Actions

- `GET /remediation/actions/{action_id}`: Get a specific remediation action
- `POST /remediation/actions/{action_id}/execute`: Execute a remediation action

### Remediation Workflows

- `GET /remediation/workflows`: Get all remediation workflows
- `GET /remediation/workflows/{workflow_id}`: Get a specific remediation workflow
- `POST /remediation/workflows/{workflow_id}/execute-step`: Execute the current step in a workflow

### Approval Mechanisms

- `POST /remediation/approvals/{request_id}/approve`: Approve an approval request
- `POST /remediation/approvals/{request_id}/reject`: Reject an approval request

### Rollback Capabilities

- `POST /remediation/rollbacks`: Create a rollback operation
- `POST /remediation/rollbacks/{operation_id}/execute`: Execute a rollback operation
- `POST /remediation/rollbacks/{operation_id}/verify`: Verify a rollback operation

## Usage

### Creating a Remediation Plan

```python
import requests
import json

# Create a remediation plan
response = requests.post(
    "http://localhost:8002/remediation/plans",
    json={
        "repository_url": "https://github.com/example/repo",
        "commit_sha": "abcdef123456",
        "vulnerabilities": ["CVE-2023-1234", "CVE-2023-5678"],
        "auto_apply": False,
        "metadata": {
            "priority": "high",
            "requester": "security-team"
        }
    }
)

# Get the plan ID
plan = response.json()["plan"]
plan_id = plan["id"]
```

### Executing a Remediation Plan

```python
# Execute the plan
response = requests.post(
    f"http://localhost:8002/remediation/plans/{plan_id}/execute",
    json={
        "execution_context": {
            "environment": "staging",
            "executor": "automated-system"
        }
    }
)

# Get the results
results = response.json()["results"]
```

### Working with Workflows

```python
# Get a workflow
response = requests.get(
    f"http://localhost:8002/remediation/workflows/{workflow_id}"
)

workflow = response.json()["workflow"]

# Execute the current step
response = requests.post(
    f"http://localhost:8002/remediation/workflows/{workflow_id}/execute-step"
)

result = response.json()["result"]
```

### Approving a Request

```python
# Approve a request
response = requests.post(
    f"http://localhost:8002/remediation/approvals/{request_id}/approve",
    json={
        "approver": "security-admin",
        "comments": "Approved after code review"
    }
)

result = response.json()
```

### Creating and Executing a Rollback

```python
# Create a rollback operation
response = requests.post(
    "http://localhost:8002/remediation/rollbacks",
    json={
        "workflow_id": workflow_id,
        "action_id": action_id,
        "snapshot_id": snapshot_id,
        "rollback_type": "FULL",
        "metadata": {
            "reason": "Failed verification"
        }
    }
)

operation = response.json()["operation"]
operation_id = operation["id"]

# Execute the rollback
response = requests.post(
    f"http://localhost:8002/remediation/rollbacks/{operation_id}/execute",
    json={
        "target_path": "/path/to/target"
    }
)

result = response.json()["result"]
