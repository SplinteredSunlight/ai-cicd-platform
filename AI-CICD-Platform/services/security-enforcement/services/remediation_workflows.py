import os
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
import asyncio
import logging

from ..models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from ..services.approval_service import ApprovalService, ApprovalRole, ApprovalStatus
from ..services.rollback_service import RollbackService, RollbackType, RollbackStatus

logger = logging.getLogger(__name__)

class WorkflowStepType(str, Enum):
    """
    Types of workflow steps
    """
    REMEDIATION = "REMEDIATION"  # Execute a remediation action
    VERIFICATION = "VERIFICATION"  # Verify a remediation action
    APPROVAL = "APPROVAL"  # Get approval for a remediation action
    ROLLBACK = "ROLLBACK"  # Rollback a remediation action
    NOTIFICATION = "NOTIFICATION"  # Send a notification
    CUSTOM = "CUSTOM"  # Custom step

class WorkflowStepStatus(str, Enum):
    """
    Status of a workflow step
    """
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"

class WorkflowStep:
    """
    A step in a remediation workflow
    """
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        step_type: WorkflowStepType,
        action_id: str,
        status: WorkflowStepStatus = WorkflowStepStatus.PENDING,
        requires_approval: bool = False,
        approval_roles: List[ApprovalRole] = None,
        auto_approve_policy: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.step_type = step_type
        self.action_id = action_id
        self.status = status
        self.requires_approval = requires_approval
        self.approval_roles = approval_roles or []
        self.auto_approve_policy = auto_approve_policy
        self.result = result or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "step_type": self.step_type,
            "action_id": self.action_id,
            "status": self.status,
            "requires_approval": self.requires_approval,
            "approval_roles": [role.value for role in self.approval_roles],
            "auto_approve_policy": self.auto_approve_policy,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            step_type=WorkflowStepType(data["step_type"]),
            action_id=data["action_id"],
            status=WorkflowStepStatus(data["status"]),
            requires_approval=data["requires_approval"],
            approval_roles=[ApprovalRole(role) for role in data["approval_roles"]],
            auto_approve_policy=data.get("auto_approve_policy"),
            result=data.get("result", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )

class RemediationWorkflow:
    """
    A workflow for remediation
    """
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        plan_id: str,
        steps: List[WorkflowStep],
        status: WorkflowStepStatus = WorkflowStepStatus.PENDING,
        current_step_index: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.plan_id = plan_id
        self.steps = steps
        self.status = status
        self.current_step_index = current_step_index
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.completed_at = completed_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "plan_id": self.plan_id,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status,
            "current_step_index": self.current_step_index,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemediationWorkflow':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            plan_id=data["plan_id"],
            steps=[WorkflowStep.from_dict(step) for step in data["steps"]],
            status=WorkflowStepStatus(data["status"]),
            current_step_index=data["current_step_index"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            metadata=data.get("metadata", {})
        )

class RemediationWorkflowService:
    """
    Service for managing remediation workflows
    """
    def __init__(self):
        """
        Initialize the workflow service
        """
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.workflows_dir = os.path.join(self.base_dir, "workflows")
        
        # Create directories if they don't exist
        os.makedirs(self.workflows_dir, exist_ok=True)
    
    async def create_workflow_for_plan(self, plan: RemediationPlan) -> RemediationWorkflow:
        """
        Create a workflow for a remediation plan
        """
        # Generate a unique ID for the workflow
        workflow_id = f"WORKFLOW-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create steps for each action in the plan
        steps = []
        for action in plan.actions:
            # Create a remediation step
            remediation_step_id = f"STEP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
            remediation_step = WorkflowStep(
                id=remediation_step_id,
                name=f"Remediate {action.vulnerability_id}",
                description=f"Apply remediation for {action.vulnerability_id}",
                step_type=WorkflowStepType.REMEDIATION,
                action_id=action.id,
                status=WorkflowStepStatus.PENDING,
                requires_approval=True,
                approval_roles=[ApprovalRole.SECURITY_ADMIN, ApprovalRole.DEVELOPER],
                auto_approve_policy=None,
                created_at=datetime.utcnow(),
                metadata={
                    "vulnerability_id": action.vulnerability_id,
                    "strategy": action.strategy
                }
            )
            steps.append(remediation_step)
            
            # Create a verification step
            verification_step_id = f"STEP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
            verification_step = WorkflowStep(
                id=verification_step_id,
                name=f"Verify {action.vulnerability_id}",
                description=f"Verify remediation for {action.vulnerability_id}",
                step_type=WorkflowStepType.VERIFICATION,
                action_id=action.id,
                status=WorkflowStepStatus.PENDING,
                requires_approval=False,
                approval_roles=[],
                auto_approve_policy=None,
                created_at=datetime.utcnow(),
                metadata={
                    "vulnerability_id": action.vulnerability_id,
                    "strategy": action.strategy
                }
            )
            steps.append(verification_step)
        
        # Create the workflow
        workflow = RemediationWorkflow(
            id=workflow_id,
            name=f"Workflow for {plan.name}",
            description=f"Remediation workflow for {plan.description}",
            plan_id=plan.id,
            steps=steps,
            status=WorkflowStepStatus.PENDING,
            current_step_index=0,
            created_at=datetime.utcnow(),
            metadata=plan.metadata
        )
        
        # Save the workflow
        await self._save_workflow(workflow)
        
        return workflow
    
    async def get_workflow(self, workflow_id: str) -> Optional[RemediationWorkflow]:
        """
        Get a workflow by ID
        """
        workflow_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
        
        if not os.path.exists(workflow_path):
            return None
        
        try:
            with open(workflow_path, "r") as f:
                workflow_data = json.load(f)
            
            workflow = RemediationWorkflow.from_dict(workflow_data)
            
            return workflow
        except Exception as e:
            logger.error(f"Error loading workflow {workflow_id}: {str(e)}")
            return None
    
    async def get_all_workflows(self) -> List[RemediationWorkflow]:
        """
        Get all workflows
        """
        workflows = []
        
        for filename in os.listdir(self.workflows_dir):
            if filename.endswith(".json"):
                workflow_id = filename[:-5]  # Remove .json extension
                workflow = await self.get_workflow(workflow_id)
                
                if workflow:
                    workflows.append(workflow)
        
        return workflows
    
    async def get_workflows_for_plan(self, plan_id: str) -> List[RemediationWorkflow]:
        """
        Get all workflows for a plan
        """
        workflows = await self.get_all_workflows()
        
        return [workflow for workflow in workflows if workflow.plan_id == plan_id]
    
    async def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStepStatus,
        completed_at: Optional[datetime] = None
    ) -> Optional[RemediationWorkflow]:
        """
        Update the status of a workflow
        """
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        workflow.status = status
        workflow.updated_at = datetime.utcnow()
        
        if completed_at:
            workflow.completed_at = completed_at
        elif status in [WorkflowStepStatus.COMPLETED, WorkflowStepStatus.FAILED, WorkflowStepStatus.CANCELLED]:
            workflow.completed_at = datetime.utcnow()
        
        await self._save_workflow(workflow)
        
        return workflow
    
    async def update_step_status(
        self,
        workflow_id: str,
        step_id: str,
        status: WorkflowStepStatus,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[RemediationWorkflow]:
        """
        Update the status of a workflow step
        """
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        # Find the step
        step_index = None
        for i, step in enumerate(workflow.steps):
            if step.id == step_id:
                step_index = i
                break
        
        if step_index is None:
            return None
        
        # Update the step
        workflow.steps[step_index].status = status
        workflow.steps[step_index].updated_at = datetime.utcnow()
        
        if result:
            workflow.steps[step_index].result = result
        
        # Save the workflow
        await self._save_workflow(workflow)
        
        return workflow
    
    async def execute_workflow_step(
        self,
        workflow: RemediationWorkflow,
        remediation_service,
        approval_service,
        rollback_service
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute the current step in a workflow
        """
        if workflow.current_step_index >= len(workflow.steps):
            return False, {
                "success": False,
                "message": "No more steps to execute"
            }
        
        # Get the current step
        step = workflow.steps[workflow.current_step_index]
        
        # Check if the step is already completed
        if step.status in [WorkflowStepStatus.COMPLETED, WorkflowStepStatus.FAILED, WorkflowStepStatus.SKIPPED, WorkflowStepStatus.CANCELLED]:
            # Move to the next step
            workflow.current_step_index += 1
            workflow.updated_at = datetime.utcnow()
            await self._save_workflow(workflow)
            
            return True, {
                "success": True,
                "message": f"Step {step.id} already {step.status}, moving to next step",
                "step": step.to_dict()
            }
        
        # Check if the step is waiting for approval
        if step.status == WorkflowStepStatus.WAITING_FOR_APPROVAL:
            return True, {
                "success": True,
                "message": f"Step {step.id} is waiting for approval",
                "step": step.to_dict()
            }
        
        # Update the step status
        step.status = WorkflowStepStatus.IN_PROGRESS
        step.updated_at = datetime.utcnow()
        await self._save_workflow(workflow)
        
        try:
            # Execute the step based on its type
            if step.step_type == WorkflowStepType.REMEDIATION:
                # Check if the step requires approval
                if step.requires_approval:
                    # Create an approval request
                    request = await approval_service.create_approval_request(
                        workflow_id=workflow.id,
                        step_id=step.id,
                        action_id=step.action_id,
                        required_roles=step.approval_roles,
                        auto_approve_policy=step.auto_approve_policy,
                        metadata=step.metadata
                    )
                    
                    # Update the step status
                    step.status = WorkflowStepStatus.WAITING_FOR_APPROVAL
                    step.updated_at = datetime.utcnow()
                    step.result = {
                        "approval_request_id": request.id,
                        "message": "Waiting for approval"
                    }
                    await self._save_workflow(workflow)
                    
                    return True, {
                        "success": True,
                        "message": f"Step {step.id} is waiting for approval",
                        "step": step.to_dict(),
                        "approval_request": request.to_dict()
                    }
                
                # Execute the remediation action
                result = await remediation_service.execute_remediation_action(
                    step.action_id
                )
                
                # Update the step status
                step.status = WorkflowStepStatus.COMPLETED if result.success else WorkflowStepStatus.FAILED
                step.updated_at = datetime.utcnow()
                step.result = {
                    "success": result.success,
                    "message": result.message,
                    "details": result.details
                }
                
                # If the step failed, update the workflow status
                if step.status == WorkflowStepStatus.FAILED:
                    workflow.status = WorkflowStepStatus.FAILED
                    workflow.updated_at = datetime.utcnow()
                    workflow.completed_at = datetime.utcnow()
                else:
                    # Move to the next step
                    workflow.current_step_index += 1
                    workflow.updated_at = datetime.utcnow()
                    
                    # Check if we've completed all steps
                    if workflow.current_step_index >= len(workflow.steps):
                        workflow.status = WorkflowStepStatus.COMPLETED
                        workflow.completed_at = datetime.utcnow()
                
                await self._save_workflow(workflow)
                
                return True, {
                    "success": True,
                    "message": f"Step {step.id} executed",
                    "step": step.to_dict(),
                    "result": result.to_dict()
                }
            
            elif step.step_type == WorkflowStepType.VERIFICATION:
                # TODO: Implement verification logic
                
                # For now, just simulate success
                success = True
                message = "Verification completed successfully"
                details = {
                    "action_id": step.action_id,
                    "verification_type": "simulated"
                }
                
                # Update the step status
                step.status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED
                step.updated_at = datetime.utcnow()
                step.result = {
                    "success": success,
                    "message": message,
                    "details": details
                }
                
                # If the step failed, update the workflow status
                if step.status == WorkflowStepStatus.FAILED:
                    workflow.status = WorkflowStepStatus.FAILED
                    workflow.updated_at = datetime.utcnow()
                    workflow.completed_at = datetime.utcnow()
                else:
                    # Move to the next step
                    workflow.current_step_index += 1
                    workflow.updated_at = datetime.utcnow()
                    
                    # Check if we've completed all steps
                    if workflow.current_step_index >= len(workflow.steps):
                        workflow.status = WorkflowStepStatus.COMPLETED
                        workflow.completed_at = datetime.utcnow()
                
                await self._save_workflow(workflow)
                
                return True, {
                    "success": True,
                    "message": f"Step {step.id} executed",
                    "step": step.to_dict(),
                    "result": {
                        "success": success,
                        "message": message,
                        "details": details
                    }
                }
            
            elif step.step_type == WorkflowStepType.ROLLBACK:
                # Execute the rollback operation
                result = await rollback_service.perform_rollback(
                    step.metadata.get("rollback_operation_id")
                )
                
                # Update the step status
                step.status = WorkflowStepStatus.COMPLETED if result["success"] else WorkflowStepStatus.FAILED
                step.updated_at = datetime.utcnow()
                step.result = result
                
                # If the step failed, update the workflow status
                if step.status == WorkflowStepStatus.FAILED:
                    workflow.status = WorkflowStepStatus.FAILED
                    workflow.updated_at = datetime.utcnow()
                    workflow.completed_at = datetime.utcnow()
                else:
                    # Move to the next step
                    workflow.current_step_index += 1
                    workflow.updated_at = datetime.utcnow()
                    
                    # Check if we've completed all steps
                    if workflow.current_step_index >= len(workflow.steps):
                        workflow.status = WorkflowStepStatus.COMPLETED
                        workflow.completed_at = datetime.utcnow()
                
                await self._save_workflow(workflow)
                
                return True, {
                    "success": True,
                    "message": f"Step {step.id} executed",
                    "step": step.to_dict(),
                    "result": result
                }
            
            elif step.step_type == WorkflowStepType.NOTIFICATION:
                # TODO: Implement notification logic
                
                # For now, just simulate success
                success = True
                message = "Notification sent successfully"
                details = {
                    "notification_type": step.metadata.get("notification_type", "email"),
                    "recipients": step.metadata.get("recipients", [])
                }
                
                # Update the step status
                step.status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED
                step.updated_at = datetime.utcnow()
                step.result = {
                    "success": success,
                    "message": message,
                    "details": details
                }
                
                # Move to the next step
                workflow.current_step_index += 1
                workflow.updated_at = datetime.utcnow()
                
                # Check if we've completed all steps
                if workflow.current_step_index >= len(workflow.steps):
                    workflow.status = WorkflowStepStatus.COMPLETED
                    workflow.completed_at = datetime.utcnow()
                
                await self._save_workflow(workflow)
                
                return True, {
                    "success": True,
                    "message": f"Step {step.id} executed",
                    "step": step.to_dict(),
                    "result": {
                        "success": success,
                        "message": message,
                        "details": details
                    }
                }
            
            elif step.step_type == WorkflowStepType.CUSTOM:
                # TODO: Implement custom step logic
                
                # For now, just simulate success
                success = True
                message = "Custom step executed successfully"
                details = {
                    "custom_type": step.metadata.get("custom_type", "unknown"),
                    "parameters": step.metadata.get("parameters", {})
                }
                
                # Update the step status
                step.status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED
                step.updated_at = datetime.utcnow()
                step.result = {
                    "success": success,
                    "message": message,
                    "details": details
                }
                
                # Move to the next step
                workflow.current_step_index += 1
                workflow.updated_at = datetime.utcnow()
                
                # Check if we've completed all steps
                if workflow.current_step_index >= len(workflow.steps):
                    workflow.status = WorkflowStepStatus.COMPLETED
                    workflow.completed_at = datetime.utcnow()
                
                await self._save_workflow(workflow)
                
                return True, {
                    "success": True,
                    "message": f"Step {step.id} executed",
                    "step": step.to_dict(),
                    "result": {
                        "success": success,
                        "message": message,
                        "details": details
                    }
                }
            
            else:
                # Unknown step type
                step.status = WorkflowStepStatus.FAILED
                step.updated_at = datetime.utcnow()
                step.result = {
                    "success": False,
                    "message": f"Unknown step type: {step.step_type}"
                }
                
                # Update the workflow status
                workflow.status = WorkflowStepStatus.FAILED
                workflow.updated_at = datetime.utcnow()
                workflow.completed_at = datetime.utcnow()
                
                await self._save_workflow(workflow)
                
                return False, {
                    "success": False,
                    "message": f"Unknown step type: {step.step_type}",
                    "step": step.to_dict()
                }
        
        except Exception as e:
            logger.error(f"Error executing workflow step {step.id}: {str(e)}")
            
            # Update the step status
            step.status = WorkflowStepStatus.FAILED
            step.updated_at = datetime.utcnow()
            step.result = {
                "success": False,
                "message": f"Error executing step: {str(e)}",
                "details": {
                    "error": str(e)
                }
            }
            
            # Update the workflow status
            workflow.status = WorkflowStepStatus.FAILED
            workflow.updated_at = datetime.utcnow()
            workflow.completed_at = datetime.utcnow()
            
            await self._save_workflow(workflow)
            
            return False, {
                "success": False,
                "message": f"Error executing step: {str(e)}",
                "step": step.to_dict()
            }
    
    async def handle_approval_result(
        self,
        workflow_id: str,
        step_id: str,
        approved: bool,
        approver: str,
        comments: Optional[str] = None,
        remediation_service = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Handle the result of an approval request
        """
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            return False, {
                "success": False,
                "message": f"Workflow not found: {workflow_id}"
            }
        
        # Find the step
        step_index = None
        for i, step in enumerate(workflow.steps):
            if step.id == step_id:
                step_index = i
                break
        
        if step_index is None:
            return False, {
                "success": False,
                "message": f"Step not found: {step_id}"
            }
        
        # Get the step
        step = workflow.steps[step_index]
        
        # Check if the step is waiting for approval
        if step.status != WorkflowStepStatus.WAITING_FOR_APPROVAL:
            return False, {
                "success": False,
                "message": f"Step {step_id} is not waiting for approval"
            }
        
        if approved:
            # Update the step status
            step.status = WorkflowStepStatus.IN_PROGRESS
            step.updated_at = datetime.utcnow()
            step.result = {
                "approval_result": "approved",
                "approver": approver,
                "comments": comments
            }
            
            # Save the workflow
            await self._save_workflow(workflow)
            
            # If this is a remediation step, execute the action
            if step.step_type == WorkflowStepType.REMEDIATION and remediation_service:
                try:
                    # Execute the remediation action
                    result = await remediation_service.execute_remediation_action(
                        step.action_id
                    )
                    
                    # Update the step status
                    step.status = WorkflowStepStatus.COMPLETED if result.success else WorkflowStepStatus.FAILED
                    step.updated_at = datetime.utcnow()
                    step.result = {
                        "approval_result": "approved",
                        "approver": approver,
                        "comments": comments,
                        "execution_result": {
                            "success": result.success,
                            "message": result.message,
                            "details": result.details
                        }
                    }
                    
                    # If the step failed, update the workflow status
                    if step.status == WorkflowStepStatus.FAILED:
                        workflow.status = WorkflowStepStatus.FAILED
                        workflow.updated_at = datetime.utcnow()
                        workflow.completed_at = datetime.utcnow()
                    else:
                        # Move to the next step
                        workflow.current_step_index += 1
                        workflow.updated_at = datetime.utcnow()
                        
                        # Check if we've completed all steps
                        if workflow.current_step_index >= len(workflow.steps):
                            workflow.status = WorkflowStepStatus.COMPLETED
                            workflow.completed_at = datetime.utcnow()
                    
                    await self._save_workflow(workflow)
                    
                    return True, {
                        "success": True,
                        "message": f"Step {step_id} approved and executed",
                        "step": step.to_dict(),
                        "result": result.to_dict()
                    }
                
                except Exception as e:
                    logger.error(f"Error executing remediation action {step.action_id}: {str(e)}")
                    
                    # Update the step status
                    step.status = WorkflowStepStatus.FAILED
                    step.updated_at = datetime.utcnow()
                    step.result = {
                        "approval_result": "approved",
                        "approver": approver,
                        "comments": comments,
                        "execution_result": {
                            "success": False,
                            "message": f"Error executing remediation action: {str(e)}",
                            "details": {
                                "error": str(e)
                            }
                        }
                    }
                    
                    # Update the workflow status
                    workflow.status = WorkflowStepStatus.FAILED
                    workflow.updated_at = datetime.utcnow()
                    workflow.completed_at = datetime.utcnow()
                    
                    await self._save_workflow(workflow)
                    
                    return False, {
                        "success": False,
                        "message": f"Error executing remediation action: {str(e)}",
                        "step": step.to_dict()
                    }
            
            return True, {
                "success": True,
                "message": f"Step {step_id} approved",
                "step": step.to_dict()
            }
        
        else:
            # Update the step status
            step.status = WorkflowStepStatus.APPROVAL_REJECTED
            step.updated_at = datetime.utcnow()
            step.result = {
                "approval_result": "rejected",
                "approver": approver,
                "comments": comments
            }
            
            # Update the workflow status
            workflow.status = WorkflowStepStatus.FAILED
            workflow.updated_at = datetime.utcnow()
            workflow.completed_at = datetime.utcnow()
            
            await self._save_workflow(workflow)
            
            return False, {
                "success": False,
                "message": f"Step {step_id} rejected",
                "step": step.to_dict()
            }
    
    async def _save_workflow(self, workflow: RemediationWorkflow) -> None:
        """
        Save a workflow to disk
        """
        workflow_path = os.path.join(self.workflows_dir, f"{workflow.id}.json")
        
        # Convert the workflow to a dictionary
        workflow_dict = workflow.to_dict()
        
        # Save the workflow
        with open(workflow_path, "w") as f:
            json.dump(workflow_dict, f, indent=2)
