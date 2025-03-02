import pytest
import os
import json
from datetime import datetime, timedelta
import asyncio

from ..services.approval_service import (
    ApprovalService,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalRole
)

@pytest.fixture
def approval_service():
    """
    Create an approval service for testing
    """
    return ApprovalService()

def test_approval_role_enum():
    """
    Test the ApprovalRole enum
    """
    assert ApprovalRole.SECURITY_ADMIN == "SECURITY_ADMIN"
    assert ApprovalRole.DEVELOPER == "DEVELOPER"
    assert ApprovalRole.DEVOPS == "DEVOPS"
    assert ApprovalRole.MANAGER == "MANAGER"
    assert ApprovalRole.COMPLIANCE_OFFICER == "COMPLIANCE_OFFICER"
    assert ApprovalRole.CUSTOM == "CUSTOM"

def test_approval_status_enum():
    """
    Test the ApprovalStatus enum
    """
    assert ApprovalStatus.PENDING == "PENDING"
    assert ApprovalStatus.APPROVED == "APPROVED"
    assert ApprovalStatus.REJECTED == "REJECTED"
    assert ApprovalStatus.EXPIRED == "EXPIRED"
    assert ApprovalStatus.CANCELLED == "CANCELLED"

def test_approval_request_creation():
    """
    Test creating an approval request
    """
    request = ApprovalRequest(
        id="APPROVAL-20250301-12345678",
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        status=ApprovalStatus.PENDING,
        approver=None,
        comments=None,
        approval_time=None,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        }
    )
    
    assert request.id == "APPROVAL-20250301-12345678"
    assert request.workflow_id == "WORKFLOW-20250301-12345678"
    assert request.step_id == "STEP-12345678"
    assert request.action_id == "ACTION-20250301-12345678"
    assert ApprovalRole.SECURITY_ADMIN in request.required_roles
    assert ApprovalRole.DEVELOPER in request.required_roles
    assert request.auto_approve_policy is None
    assert request.status == ApprovalStatus.PENDING
    assert request.approver is None
    assert request.comments is None
    assert request.approval_time is None
    assert request.created_at is not None
    assert request.expires_at is not None
    assert request.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert request.metadata["severity"] == "HIGH"

def test_approval_request_to_dict():
    """
    Test converting an approval request to a dictionary
    """
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=24)
    
    request = ApprovalRequest(
        id="APPROVAL-20250301-12345678",
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        status=ApprovalStatus.PENDING,
        approver=None,
        comments=None,
        approval_time=None,
        created_at=created_at,
        expires_at=expires_at,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        }
    )
    
    request_dict = request.to_dict()
    
    assert request_dict["id"] == "APPROVAL-20250301-12345678"
    assert request_dict["workflow_id"] == "WORKFLOW-20250301-12345678"
    assert request_dict["step_id"] == "STEP-12345678"
    assert request_dict["action_id"] == "ACTION-20250301-12345678"
    assert ApprovalRole.SECURITY_ADMIN.value in request_dict["required_roles"]
    assert ApprovalRole.DEVELOPER.value in request_dict["required_roles"]
    assert request_dict["auto_approve_policy"] is None
    assert request_dict["status"] == ApprovalStatus.PENDING
    assert request_dict["approver"] is None
    assert request_dict["comments"] is None
    assert request_dict["approval_time"] is None
    assert request_dict["created_at"] == created_at.isoformat()
    assert request_dict["expires_at"] == expires_at.isoformat()
    assert request_dict["metadata"]["vulnerability_id"] == "CVE-2023-1234"
    assert request_dict["metadata"]["severity"] == "HIGH"

def test_approval_request_from_dict():
    """
    Test creating an approval request from a dictionary
    """
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(hours=24)
    
    request_dict = {
        "id": "APPROVAL-20250301-12345678",
        "workflow_id": "WORKFLOW-20250301-12345678",
        "step_id": "STEP-12345678",
        "action_id": "ACTION-20250301-12345678",
        "required_roles": [ApprovalRole.SECURITY_ADMIN.value, ApprovalRole.DEVELOPER.value],
        "auto_approve_policy": None,
        "status": ApprovalStatus.PENDING,
        "approver": None,
        "comments": None,
        "approval_time": None,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "metadata": {
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        }
    }
    
    request = ApprovalRequest.from_dict(request_dict)
    
    assert request.id == "APPROVAL-20250301-12345678"
    assert request.workflow_id == "WORKFLOW-20250301-12345678"
    assert request.step_id == "STEP-12345678"
    assert request.action_id == "ACTION-20250301-12345678"
    assert ApprovalRole.SECURITY_ADMIN in request.required_roles
    assert ApprovalRole.DEVELOPER in request.required_roles
    assert request.auto_approve_policy is None
    assert request.status == ApprovalStatus.PENDING
    assert request.approver is None
    assert request.comments is None
    assert request.approval_time is None
    assert request.created_at.isoformat() == created_at.isoformat()
    assert request.expires_at.isoformat() == expires_at.isoformat()
    assert request.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert request.metadata["severity"] == "HIGH"

def test_approval_service_initialization(approval_service):
    """
    Test initializing the approval service
    """
    assert approval_service is not None
    assert approval_service.requests_dir is not None
    assert os.path.exists(approval_service.requests_dir)

@pytest.mark.asyncio
async def test_approval_service_create_approval_request(approval_service):
    """
    Test creating an approval request
    """
    request = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        },
        expires_in_hours=24
    )
    
    assert request is not None
    assert request.workflow_id == "WORKFLOW-20250301-12345678"
    assert request.step_id == "STEP-12345678"
    assert request.action_id == "ACTION-20250301-12345678"
    assert ApprovalRole.SECURITY_ADMIN in request.required_roles
    assert ApprovalRole.DEVELOPER in request.required_roles
    assert request.auto_approve_policy is None
    assert request.status == ApprovalStatus.PENDING
    assert request.approver is None
    assert request.comments is None
    assert request.approval_time is None
    assert request.created_at is not None
    assert request.expires_at is not None
    assert request.metadata["vulnerability_id"] == "CVE-2023-1234"
    assert request.metadata["severity"] == "HIGH"
    
    # Check that the request was saved
    saved_request = await approval_service.get_approval_request(request.id)
    assert saved_request is not None
    assert saved_request.id == request.id

@pytest.mark.asyncio
async def test_approval_service_get_all_approval_requests(approval_service):
    """
    Test getting all approval requests
    """
    # Create a few requests
    request1 = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        },
        expires_in_hours=24
    )
    
    request2 = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-87654321",
        step_id="STEP-87654321",
        action_id="ACTION-20250301-87654321",
        required_roles=[ApprovalRole.DEVELOPER],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-5678",
            "severity": "MEDIUM"
        },
        expires_in_hours=24
    )
    
    # Get all requests
    requests = await approval_service.get_all_approval_requests()
    
    assert requests is not None
    assert len(requests) >= 2
    
    # Check that our requests are in the list
    request_ids = [r.id for r in requests]
    assert request1.id in request_ids
    assert request2.id in request_ids

@pytest.mark.asyncio
async def test_approval_service_approve_request(approval_service):
    """
    Test approving an approval request
    """
    # Create a request
    request = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        },
        expires_in_hours=24
    )
    
    # Approve the request
    success, approved_request = await approval_service.approve_request(
        request.id,
        "security-admin",
        "Approved after review"
    )
    
    assert success is True
    assert approved_request is not None
    assert approved_request.id == request.id
    assert approved_request.status == ApprovalStatus.APPROVED
    assert approved_request.approver == "security-admin"
    assert approved_request.comments == "Approved after review"
    assert approved_request.approval_time is not None
    
    # Check that the request was updated
    updated_request = await approval_service.get_approval_request(request.id)
    assert updated_request is not None
    assert updated_request.id == request.id
    assert updated_request.status == ApprovalStatus.APPROVED
    assert updated_request.approver == "security-admin"
    assert updated_request.comments == "Approved after review"
    assert updated_request.approval_time is not None

@pytest.mark.asyncio
async def test_approval_service_reject_request(approval_service):
    """
    Test rejecting an approval request
    """
    # Create a request
    request = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        },
        expires_in_hours=24
    )
    
    # Reject the request
    success, rejected_request = await approval_service.reject_request(
        request.id,
        "security-admin",
        "Rejected due to policy violation"
    )
    
    assert success is True
    assert rejected_request is not None
    assert rejected_request.id == request.id
    assert rejected_request.status == ApprovalStatus.REJECTED
    assert rejected_request.approver == "security-admin"
    assert rejected_request.comments == "Rejected due to policy violation"
    assert rejected_request.approval_time is not None
    
    # Check that the request was updated
    updated_request = await approval_service.get_approval_request(request.id)
    assert updated_request is not None
    assert updated_request.id == request.id
    assert updated_request.status == ApprovalStatus.REJECTED
    assert updated_request.approver == "security-admin"
    assert updated_request.comments == "Rejected due to policy violation"
    assert updated_request.approval_time is not None

@pytest.mark.asyncio
async def test_approval_service_cancel_request(approval_service):
    """
    Test cancelling an approval request
    """
    # Create a request
    request = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        },
        expires_in_hours=24
    )
    
    # Cancel the request
    success, cancelled_request = await approval_service.cancel_request(
        request.id,
        "Request no longer needed"
    )
    
    assert success is True
    assert cancelled_request is not None
    assert cancelled_request.id == request.id
    assert cancelled_request.status == ApprovalStatus.CANCELLED
    assert cancelled_request.comments == "Request no longer needed"
    
    # Check that the request was updated
    updated_request = await approval_service.get_approval_request(request.id)
    assert updated_request is not None
    assert updated_request.id == request.id
    assert updated_request.status == ApprovalStatus.CANCELLED
    assert updated_request.comments == "Request no longer needed"

@pytest.mark.asyncio
async def test_approval_service_is_request_expired(approval_service):
    """
    Test checking if a request is expired
    """
    # Create a request that expires in 1 hour
    request = await approval_service.create_approval_request(
        workflow_id="WORKFLOW-20250301-12345678",
        step_id="STEP-12345678",
        action_id="ACTION-20250301-12345678",
        required_roles=[ApprovalRole.SECURITY_ADMIN],
        auto_approve_policy=None,
        metadata={
            "vulnerability_id": "CVE-2023-1234",
            "severity": "HIGH"
        },
        expires_in_hours=1
    )
    
    # Check that the request is not expired
    is_expired = await approval_service.is_request_expired(request.id)
    assert is_expired is False
    
    # Manually set the expiration time to the past
    request.expires_at = datetime.utcnow() - timedelta(hours=1)
    await approval_service._save_request(request)
    
    # Check that the request is now expired
    is_expired = await approval_service.is_request_expired(request.id)
    assert is_expired is True
