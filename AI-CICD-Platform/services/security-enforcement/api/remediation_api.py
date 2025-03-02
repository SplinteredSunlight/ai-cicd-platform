from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from typing import List, Dict, Any, Optional
import asyncio

from ..models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStatus
)
from ..services.remediation_service import RemediationService
from ..services.remediation_workflows import RemediationWorkflowService
from ..services.approval_service import ApprovalService, ApprovalRole
from ..services.rollback_service import RollbackService, RollbackType

# Create services
remediation_service = RemediationService()
workflow_service = RemediationWorkflowService()
approval_service = ApprovalService()
rollback_service = RollbackService()

def create_remediation_router() -> APIRouter:
    """
    Create a FastAPI router for remediation endpoints
    """
    router = APIRouter(prefix="/remediation", tags=["remediation"])
    
    @router.post("/plans", response_model=Dict[str, Any])
    async def create_plan(request: Dict[str, Any] = Body(...)):
        """
        Create a remediation plan
        """
        try:
            # Convert request to RemediationRequest
            remediation_request = RemediationRequest(
                repository_url=request["repository_url"],
                commit_sha=request["commit_sha"],
                vulnerabilities=request["vulnerabilities"],
                auto_apply=request.get("auto_apply", False),
                metadata=request.get("metadata", {})
            )
            
            # Create the plan
            plan = await remediation_service.create_remediation_plan(remediation_request)
            
            # Create a workflow for the plan
            workflow = await workflow_service.create_workflow_for_plan(plan)
            
            return {
                "success": True,
                "plan": plan.to_dict(),
                "workflow": workflow.to_dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/plans", response_model=Dict[str, Any])
    async def get_plans():
        """
        Get all remediation plans
        """
        try:
            plans = await remediation_service.get_all_remediation_plans()
            return {
                "success": True,
                "plans": [plan.to_dict() for plan in plans]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/plans/{plan_id}", response_model=Dict[str, Any])
    async def get_plan(plan_id: str = Path(...)):
        """
        Get a remediation plan by ID
        """
        try:
            plan = await remediation_service.get_remediation_plan(plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
            
            return {
                "success": True,
                "plan": plan.to_dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/plans/{plan_id}/actions", response_model=Dict[str, Any])
    async def get_plan_actions(plan_id: str = Path(...)):
        """
        Get all actions for a plan
        """
        try:
            actions = await remediation_service.get_actions_for_plan(plan_id)
            return {
                "success": True,
                "actions": [action.to_dict() for action in actions]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/plans/{plan_id}/execute", response_model=Dict[str, Any])
    async def execute_plan(
        plan_id: str = Path(...),
        execution_context: Optional[Dict[str, Any]] = Body(None)
    ):
        """
        Execute a remediation plan
        """
        try:
            # Get the plan
            plan = await remediation_service.get_remediation_plan(plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
            
            # Execute the plan
            results = await remediation_service.execute_remediation_plan(
                plan_id,
                execution_context
            )
            
            return {
                "success": True,
                "results": [result.to_dict() for result in results]
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/actions/{action_id}", response_model=Dict[str, Any])
    async def get_action(action_id: str = Path(...)):
        """
        Get a remediation action by ID
        """
        try:
            action = await remediation_service.get_remediation_action(action_id)
            if not action:
                raise HTTPException(status_code=404, detail=f"Action not found: {action_id}")
            
            return {
                "success": True,
                "action": action.to_dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/actions/{action_id}/execute", response_model=Dict[str, Any])
    async def execute_action(
        action_id: str = Path(...),
        execution_context: Optional[Dict[str, Any]] = Body(None)
    ):
        """
        Execute a remediation action
        """
        try:
            # Execute the action
            result = await remediation_service.execute_remediation_action(
                action_id,
                execution_context
            )
            
            return {
                "success": True,
                "result": result.to_dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/workflows", response_model=Dict[str, Any])
    async def get_workflows():
        """
        Get all remediation workflows
        """
        try:
            workflows = await workflow_service.get_all_workflows()
            return {
                "success": True,
                "workflows": [workflow.to_dict() for workflow in workflows]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
    async def get_workflow(workflow_id: str = Path(...)):
        """
        Get a remediation workflow by ID
        """
        try:
            workflow = await workflow_service.get_workflow(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
            
            return {
                "success": True,
                "workflow": workflow.to_dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/workflows/{workflow_id}/execute-step", response_model=Dict[str, Any])
    async def execute_workflow_step(workflow_id: str = Path(...)):
        """
        Execute the current step in a workflow
        """
        try:
            # Get the workflow
            workflow = await workflow_service.get_workflow(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
            
            # Execute the current step
            success, result = await workflow_service.execute_workflow_step(
                workflow,
                remediation_service,
                approval_service,
                rollback_service
            )
            
            return {
                "success": success,
                "result": result,
                "workflow": workflow.to_dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/approvals/{request_id}/approve", response_model=Dict[str, Any])
    async def approve_request(
        request_id: str = Path(...),
        approver: str = Body(..., embed=True),
        comments: Optional[str] = Body(None, embed=True)
    ):
        """
        Approve an approval request
        """
        try:
            # Approve the request
            success, request = await approval_service.approve_request(
                request_id,
                approver,
                comments
            )
            
            if not success:
                return {
                    "success": False,
                    "message": f"Failed to approve request: {request.comments}",
                    "request": request.to_dict()
                }
            
            # Handle the approval result in the workflow
            workflow_id = request.workflow_id
            step_id = request.step_id
            
            result = {
                "success": True,
                "message": "Approval request approved",
                "request": request.to_dict()
            }
            
            # If the request is for a workflow step, handle the approval result
            if workflow_id and step_id:
                success, workflow_result = await workflow_service.handle_approval_result(
                    workflow_id,
                    step_id,
                    True,
                    approver,
                    comments,
                    remediation_service
                )
                
                result["workflow_result"] = workflow_result
                result["workflow_success"] = success
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/approvals/{request_id}/reject", response_model=Dict[str, Any])
    async def reject_request(
        request_id: str = Path(...),
        approver: str = Body(..., embed=True),
        comments: Optional[str] = Body(None, embed=True)
    ):
        """
        Reject an approval request
        """
        try:
            # Reject the request
            success, request = await approval_service.reject_request(
                request_id,
                approver,
                comments
            )
            
            if not success:
                return {
                    "success": False,
                    "message": f"Failed to reject request: {request.comments}",
                    "request": request.to_dict()
                }
            
            # Handle the rejection result in the workflow
            workflow_id = request.workflow_id
            step_id = request.step_id
            
            result = {
                "success": True,
                "message": "Approval request rejected",
                "request": request.to_dict()
            }
            
            # If the request is for a workflow step, handle the rejection result
            if workflow_id and step_id:
                success, workflow_result = await workflow_service.handle_approval_result(
                    workflow_id,
                    step_id,
                    False,
                    approver,
                    comments
                )
                
                result["workflow_result"] = workflow_result
                result["workflow_success"] = success
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/rollbacks", response_model=Dict[str, Any])
    async def create_rollback(
        workflow_id: str = Body(...),
        action_id: str = Body(...),
        snapshot_id: str = Body(...),
        rollback_type: str = Body(...),
        metadata: Optional[Dict[str, Any]] = Body(None)
    ):
        """
        Create a rollback operation
        """
        try:
            # Create the rollback operation
            operation = await rollback_service.create_rollback_operation(
                workflow_id,
                action_id,
                snapshot_id,
                RollbackType(rollback_type),
                metadata
            )
            
            return {
                "success": True,
                "operation": operation.to_dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/rollbacks/{operation_id}/execute", response_model=Dict[str, Any])
    async def execute_rollback(
        operation_id: str = Path(...),
        target_path: Optional[str] = Body(None, embed=True)
    ):
        """
        Execute a rollback operation
        """
        try:
            # Execute the rollback
            result = await rollback_service.perform_rollback(
                operation_id,
                target_path
            )
            
            return {
                "success": result["success"],
                "result": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/rollbacks/{operation_id}/verify", response_model=Dict[str, Any])
    async def verify_rollback(operation_id: str = Path(...)):
        """
        Verify a rollback operation
        """
        try:
            # Verify the rollback
            result = await rollback_service.verify_rollback(operation_id)
            
            return {
                "success": result["success"],
                "result": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router

def get_remediation_routes():
    """
    Get the remediation routes
    """
    return [
        {
            "path": "/remediation/plans",
            "methods": ["GET", "POST"],
            "description": "Manage remediation plans"
        },
        {
            "path": "/remediation/plans/{plan_id}",
            "methods": ["GET"],
            "description": "Get a remediation plan by ID"
        },
        {
            "path": "/remediation/plans/{plan_id}/actions",
            "methods": ["GET"],
            "description": "Get all actions for a plan"
        },
        {
            "path": "/remediation/plans/{plan_id}/execute",
            "methods": ["POST"],
            "description": "Execute a remediation plan"
        },
        {
            "path": "/remediation/actions/{action_id}",
            "methods": ["GET"],
            "description": "Get a remediation action by ID"
        },
        {
            "path": "/remediation/actions/{action_id}/execute",
            "methods": ["POST"],
            "description": "Execute a remediation action"
        },
        {
            "path": "/remediation/workflows",
            "methods": ["GET"],
            "description": "Get all remediation workflows"
        },
        {
            "path": "/remediation/workflows/{workflow_id}",
            "methods": ["GET"],
            "description": "Get a remediation workflow by ID"
        },
        {
            "path": "/remediation/workflows/{workflow_id}/execute-step",
            "methods": ["POST"],
            "description": "Execute the current step in a workflow"
        },
        {
            "path": "/remediation/approvals/{request_id}/approve",
            "methods": ["POST"],
            "description": "Approve an approval request"
        },
        {
            "path": "/remediation/approvals/{request_id}/reject",
            "methods": ["POST"],
            "description": "Reject an approval request"
        },
        {
            "path": "/remediation/rollbacks",
            "methods": ["POST"],
            "description": "Create a rollback operation"
        },
        {
            "path": "/remediation/rollbacks/{operation_id}/execute",
            "methods": ["POST"],
            "description": "Execute a rollback operation"
        },
        {
            "path": "/remediation/rollbacks/{operation_id}/verify",
            "methods": ["POST"],
            "description": "Verify a rollback operation"
        }
    ]
