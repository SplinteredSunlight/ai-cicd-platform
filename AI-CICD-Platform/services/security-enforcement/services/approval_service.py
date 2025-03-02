import os
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
import asyncio
import logging

logger = logging.getLogger(__name__)

class ApprovalRole(str, Enum):
    """
    Roles that can approve remediation actions
    """
    SECURITY_ADMIN = "SECURITY_ADMIN"
    DEVELOPER = "DEVELOPER"
    DEVOPS = "DEVOPS"
    MANAGER = "MANAGER"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    CUSTOM = "CUSTOM"

class ApprovalStatus(str, Enum):
    """
    Status of an approval request
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class ApprovalRequest:
    """
    A request for approval
    """
    def __init__(
        self,
        id: str,
        workflow_id: str,
        step_id: str,
        action_id: str,
        required_roles: List[ApprovalRole],
        auto_approve_policy: Optional[str],
        status: ApprovalStatus = ApprovalStatus.PENDING,
        approver: Optional[str] = None,
        comments: Optional[str] = None,
        approval_time: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.action_id = action_id
        self.required_roles = required_roles
        self.auto_approve_policy = auto_approve_policy
        self.status = status
        self.approver = approver
        self.comments = comments
        self.approval_time = approval_time
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at or (self.created_at + timedelta(hours=24))
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "action_id": self.action_id,
            "required_roles": [role.value for role in self.required_roles],
            "auto_approve_policy": self.auto_approve_policy,
            "status": self.status,
            "approver": self.approver,
            "comments": self.comments,
            "approval_time": self.approval_time.isoformat() if self.approval_time else None,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalRequest':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            step_id=data["step_id"],
            action_id=data["action_id"],
            required_roles=[ApprovalRole(role) for role in data["required_roles"]],
            auto_approve_policy=data.get("auto_approve_policy"),
            status=ApprovalStatus(data["status"]),
            approver=data.get("approver"),
            comments=data.get("comments"),
            approval_time=datetime.fromisoformat(data["approval_time"]) if data.get("approval_time") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            metadata=data.get("metadata", {})
        )

class ApprovalService:
    """
    Service for managing approval requests
    """
    def __init__(self):
        """
        Initialize the approval service
        """
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.requests_dir = os.path.join(self.base_dir, "approvals")
        
        # Create directories if they don't exist
        os.makedirs(self.requests_dir, exist_ok=True)
    
    async def create_approval_request(
        self,
        workflow_id: str,
        step_id: str,
        action_id: str,
        required_roles: List[ApprovalRole],
        auto_approve_policy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_hours: int = 24
    ) -> ApprovalRequest:
        """
        Create an approval request
        """
        # Generate a unique ID for the request
        request_id = f"APPROVAL-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create the request
        request = ApprovalRequest(
            id=request_id,
            workflow_id=workflow_id,
            step_id=step_id,
            action_id=action_id,
            required_roles=required_roles,
            auto_approve_policy=auto_approve_policy,
            status=ApprovalStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            metadata=metadata or {}
        )
        
        # Save the request
        await self._save_request(request)
        
        return request
    
    async def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Get an approval request by ID
        """
        request_path = os.path.join(self.requests_dir, f"{request_id}.json")
        
        if not os.path.exists(request_path):
            return None
        
        try:
            with open(request_path, "r") as f:
                request_data = json.load(f)
            
            request = ApprovalRequest.from_dict(request_data)
            
            return request
        except Exception as e:
            logger.error(f"Error loading approval request {request_id}: {str(e)}")
            return None
    
    async def get_all_approval_requests(self) -> List[ApprovalRequest]:
        """
        Get all approval requests
        """
        requests = []
        
        for filename in os.listdir(self.requests_dir):
            if filename.endswith(".json"):
                request_id = filename[:-5]  # Remove .json extension
                request = await self.get_approval_request(request_id)
                
                if request:
                    requests.append(request)
        
        return requests
    
    async def get_pending_approval_requests(self) -> List[ApprovalRequest]:
        """
        Get all pending approval requests
        """
        requests = await self.get_all_approval_requests()
        
        return [request for request in requests if request.status == ApprovalStatus.PENDING]
    
    async def get_approval_requests_for_workflow(self, workflow_id: str) -> List[ApprovalRequest]:
        """
        Get all approval requests for a workflow
        """
        requests = await self.get_all_approval_requests()
        
        return [request for request in requests if request.workflow_id == workflow_id]
    
    async def get_approval_requests_for_step(self, workflow_id: str, step_id: str) -> List[ApprovalRequest]:
        """
        Get all approval requests for a workflow step
        """
        requests = await self.get_all_approval_requests()
        
        return [request for request in requests if request.workflow_id == workflow_id and request.step_id == step_id]
    
    async def approve_request(
        self,
        request_id: str,
        approver: str,
        comments: Optional[str] = None
    ) -> Tuple[bool, ApprovalRequest]:
        """
        Approve an approval request
        """
        request = await self.get_approval_request(request_id)
        
        if not request:
            return False, ApprovalRequest(
                id=request_id,
                workflow_id="",
                step_id="",
                action_id="",
                required_roles=[],
                auto_approve_policy=None,
                status=ApprovalStatus.PENDING,
                comments=f"Request not found: {request_id}"
            )
        
        if request.status != ApprovalStatus.PENDING:
            return False, request
        
        # Check if the request is expired
        if await self.is_request_expired(request_id):
            request.status = ApprovalStatus.EXPIRED
            await self._save_request(request)
            return False, request
        
        # Approve the request
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.comments = comments
        request.approval_time = datetime.utcnow()
        
        # Save the request
        await self._save_request(request)
        
        return True, request
    
    async def reject_request(
        self,
        request_id: str,
        approver: str,
        comments: Optional[str] = None
    ) -> Tuple[bool, ApprovalRequest]:
        """
        Reject an approval request
        """
        request = await self.get_approval_request(request_id)
        
        if not request:
            return False, ApprovalRequest(
                id=request_id,
                workflow_id="",
                step_id="",
                action_id="",
                required_roles=[],
                auto_approve_policy=None,
                status=ApprovalStatus.PENDING,
                comments=f"Request not found: {request_id}"
            )
        
        if request.status != ApprovalStatus.PENDING:
            return False, request
        
        # Check if the request is expired
        if await self.is_request_expired(request_id):
            request.status = ApprovalStatus.EXPIRED
            await self._save_request(request)
            return False, request
        
        # Reject the request
        request.status = ApprovalStatus.REJECTED
        request.approver = approver
        request.comments = comments
        request.approval_time = datetime.utcnow()
        
        # Save the request
        await self._save_request(request)
        
        return True, request
    
    async def cancel_request(
        self,
        request_id: str,
        comments: Optional[str] = None
    ) -> Tuple[bool, ApprovalRequest]:
        """
        Cancel an approval request
        """
        request = await self.get_approval_request(request_id)
        
        if not request:
            return False, ApprovalRequest(
                id=request_id,
                workflow_id="",
                step_id="",
                action_id="",
                required_roles=[],
                auto_approve_policy=None,
                status=ApprovalStatus.PENDING,
                comments=f"Request not found: {request_id}"
            )
        
        if request.status != ApprovalStatus.PENDING:
            return False, request
        
        # Cancel the request
        request.status = ApprovalStatus.CANCELLED
        request.comments = comments
        
        # Save the request
        await self._save_request(request)
        
        return True, request
    
    async def is_request_expired(self, request_id: str) -> bool:
        """
        Check if an approval request is expired
        """
        request = await self.get_approval_request(request_id)
        
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        return datetime.utcnow() > request.expires_at
    
    async def check_auto_approve_policy(
        self,
        request_id: str,
        policy_context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a request can be auto-approved based on policy
        """
        request = await self.get_approval_request(request_id)
        
        if not request or not request.auto_approve_policy:
            return False, None
        
        # TODO: Implement policy evaluation
        # For now, just return False
        return False, None
    
    async def _save_request(self, request: ApprovalRequest) -> None:
        """
        Save an approval request to disk
        """
        request_path = os.path.join(self.requests_dir, f"{request.id}.json")
        
        # Convert the request to a dictionary
        request_dict = request.to_dict()
        
        # Save the request
        with open(request_path, "w") as f:
            json.dump(request_dict, f, indent=2)
