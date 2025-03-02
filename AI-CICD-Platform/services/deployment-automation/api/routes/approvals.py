from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# Import models and services (to be implemented)
# from ...models.approval import ApprovalWorkflow, ApprovalWorkflowCreate, ApprovalWorkflowUpdate
# from ...services.approval_workflow import ApprovalWorkflowService

# Create router
router = APIRouter()

# Mock data for initial development
MOCK_APPROVALS = [
    {
        "id": "1",
        "name": "Production Deployment Approval",
        "description": "Approval workflow for production deployments",
        "levels": [
            {
                "id": "1",
                "name": "QA Approval",
                "description": "Approval from QA team",
                "requiredApprovers": 1,
                "approverRoles": ["qa"],
                "timeoutMinutes": 60,
                "order": 1
            },
            {
                "id": "2",
                "name": "Security Approval",
                "description": "Approval from security team",
                "requiredApprovers": 1,
                "approverRoles": ["security"],
                "timeoutMinutes": 120,
                "order": 2
            },
            {
                "id": "3",
                "name": "Management Approval",
                "description": "Approval from management",
                "requiredApprovers": 1,
                "approverRoles": ["manager"],
                "timeoutMinutes": 240,
                "order": 3
            }
        ],
        "autoApprovalCriteria": [
            {
                "id": "1",
                "name": "Dev Environment Auto-Approval",
                "description": "Auto-approve deployments to dev environment",
                "environments": ["dev"]
            }
        ],
        "createdAt": "2025-03-01T12:00:00Z",
        "updatedAt": "2025-03-01T12:00:00Z"
    }
]

MOCK_APPROVAL_REQUESTS = [
    {
        "id": "1",
        "workflowId": "1",
        "deploymentId": "1",
        "pipelineId": "1",
        "environmentId": "3",  # production
        "status": "pending",
        "levels": [
            {
                "levelId": "1",
                "status": "approved",
                "approvers": [
                    {
                        "userId": "qa-user",
                        "status": "approved",
                        "timestamp": "2025-03-01T12:10:00Z",
                        "comments": "Looks good to me"
                    }
                ],
                "startTime": "2025-03-01T12:00:00Z",
                "endTime": "2025-03-01T12:10:00Z"
            },
            {
                "levelId": "2",
                "status": "pending",
                "approvers": [
                    {
                        "userId": "security-user",
                        "status": "pending"
                    }
                ],
                "startTime": "2025-03-01T12:10:00Z"
            }
        ],
        "createdAt": "2025-03-01T12:00:00Z",
        "updatedAt": "2025-03-01T12:10:00Z"
    }
]

@router.get("/workflows", response_model=List[Dict[str, Any]])
async def get_approval_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all approval workflows.
    """
    # In a real implementation, this would query the database
    # For now, return mock data
    return MOCK_APPROVALS

@router.post("/workflows", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_approval_workflow(
    # workflow: ApprovalWorkflowCreate
    workflow: Dict[str, Any]
):
    """
    Create a new approval workflow.
    """
    # In a real implementation, this would create a new workflow in the database
    # For now, return mock data
    new_workflow = {
        "id": str(uuid.uuid4()),
        "name": workflow.get("name", "New Approval Workflow"),
        "description": workflow.get("description", ""),
        "levels": workflow.get("levels", []),
        "autoApprovalCriteria": workflow.get("autoApprovalCriteria", []),
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }
    return new_workflow

@router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_approval_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow to get")
):
    """
    Get an approval workflow by ID.
    """
    # In a real implementation, this would query the database
    # For now, return mock data
    for workflow in MOCK_APPROVALS:
        if workflow["id"] == workflow_id:
            return workflow
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval workflow with ID {workflow_id} not found"
    )

@router.put("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def update_approval_workflow(
    # workflow: ApprovalWorkflowUpdate,
    workflow: Dict[str, Any],
    workflow_id: str = Path(..., description="The ID of the workflow to update")
):
    """
    Update an approval workflow.
    """
    # In a real implementation, this would update the workflow in the database
    # For now, return mock data
    for w in MOCK_APPROVALS:
        if w["id"] == workflow_id:
            updated_workflow = {**w, **workflow, "updatedAt": datetime.utcnow().isoformat()}
            return updated_workflow
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval workflow with ID {workflow_id} not found"
    )

@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_approval_workflow(
    workflow_id: str = Path(..., description="The ID of the workflow to delete")
):
    """
    Delete an approval workflow.
    """
    # In a real implementation, this would delete the workflow from the database
    # For now, just check if it exists in mock data
    for i, workflow in enumerate(MOCK_APPROVALS):
        if workflow["id"] == workflow_id:
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval workflow with ID {workflow_id} not found"
    )

@router.get("/requests", response_model=List[Dict[str, Any]])
async def get_approval_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get all approval requests.
    """
    # In a real implementation, this would query the database
    # For now, return mock data
    if status:
        return [r for r in MOCK_APPROVAL_REQUESTS if r["status"] == status]
    return MOCK_APPROVAL_REQUESTS

@router.get("/requests/{request_id}", response_model=Dict[str, Any])
async def get_approval_request(
    request_id: str = Path(..., description="The ID of the approval request to get")
):
    """
    Get an approval request by ID.
    """
    # In a real implementation, this would query the database
    # For now, return mock data
    for request in MOCK_APPROVAL_REQUESTS:
        if request["id"] == request_id:
            return request
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval request with ID {request_id} not found"
    )

@router.post("/requests/{request_id}/approve", response_model=Dict[str, Any])
async def approve_request(
    # approval: ApprovalAction
    approval: Dict[str, Any],
    request_id: str = Path(..., description="The ID of the approval request to approve")
):
    """
    Approve an approval request.
    """
    # In a real implementation, this would update the approval request in the database
    # For now, return mock data
    for request in MOCK_APPROVAL_REQUESTS:
        if request["id"] == request_id:
            # Find the current pending level
            for level in request["levels"]:
                if level["status"] == "pending":
                    # Find the current user's approval
                    for approver in level["approvers"]:
                        if approver["userId"] == approval.get("userId", "current-user"):
                            approver["status"] = "approved"
                            approver["timestamp"] = datetime.utcnow().isoformat()
                            approver["comments"] = approval.get("comments", "")
                            
                            # Check if all required approvers have approved
                            if all(a["status"] == "approved" for a in level["approvers"]):
                                level["status"] = "approved"
                                level["endTime"] = datetime.utcnow().isoformat()
                                
                                # Move to the next level or complete the request
                                next_level_index = request["levels"].index(level) + 1
                                if next_level_index < len(request["levels"]):
                                    request["levels"][next_level_index]["status"] = "pending"
                                    request["levels"][next_level_index]["startTime"] = datetime.utcnow().isoformat()
                                else:
                                    request["status"] = "approved"
                            
                            request["updatedAt"] = datetime.utcnow().isoformat()
                            return request
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval level found for this request"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval request with ID {request_id} not found"
    )

@router.post("/requests/{request_id}/reject", response_model=Dict[str, Any])
async def reject_request(
    # rejection: ApprovalAction
    rejection: Dict[str, Any],
    request_id: str = Path(..., description="The ID of the approval request to reject")
):
    """
    Reject an approval request.
    """
    # In a real implementation, this would update the approval request in the database
    # For now, return mock data
    for request in MOCK_APPROVAL_REQUESTS:
        if request["id"] == request_id:
            # Find the current pending level
            for level in request["levels"]:
                if level["status"] == "pending":
                    # Find the current user's approval
                    for approver in level["approvers"]:
                        if approver["userId"] == rejection.get("userId", "current-user"):
                            approver["status"] = "rejected"
                            approver["timestamp"] = datetime.utcnow().isoformat()
                            approver["comments"] = rejection.get("comments", "")
                            
                            # Reject the level and the entire request
                            level["status"] = "rejected"
                            level["endTime"] = datetime.utcnow().isoformat()
                            request["status"] = "rejected"
                            
                            request["updatedAt"] = datetime.utcnow().isoformat()
                            return request
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval level found for this request"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval request with ID {request_id} not found"
    )
