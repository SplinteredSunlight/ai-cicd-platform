import os
import json
import uuid
from datetime import datetime
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
from ..templates.remediation_templates import RemediationTemplateService

logger = logging.getLogger(__name__)

class RemediationService:
    """
    Service for managing remediation actions and plans
    """
    def __init__(self):
        """
        Initialize the remediation service
        """
        self.base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.plans_dir = os.path.join(self.base_dir, "plans")
        self.actions_dir = os.path.join(self.base_dir, "actions")
        self.results_dir = os.path.join(self.base_dir, "results")
        
        # Create directories if they don't exist
        os.makedirs(self.plans_dir, exist_ok=True)
        os.makedirs(self.actions_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize the template service
        self.template_service = RemediationTemplateService()
    
    async def create_remediation_plan(
        self,
        request: RemediationRequest
    ) -> RemediationPlan:
        """
        Create a remediation plan for a repository
        """
        # Generate a unique ID for the plan
        plan_id = f"PLAN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create actions for each vulnerability
        actions = []
        for vuln_id in request.vulnerabilities:
            # Find templates for the vulnerability
            templates = self.template_service.find_templates_for_vulnerability(vuln_id)
            
            if not templates:
                logger.warning(f"No templates found for vulnerability {vuln_id}")
                continue
            
            # Use the first template for now
            # TODO: Implement more sophisticated template selection
            template = templates[0]
            
            # Create variables for the template
            # TODO: Implement more sophisticated variable generation
            variables = {
                "file_path": "package.json",
                "dependency_name": "example-dependency",
                "current_version": "1.0.0",
                "fixed_version": "1.1.0"
            }
            
            # Create an action from the template
            action = self.template_service.create_action_from_template(
                template.id,
                vuln_id,
                variables
            )
            
            # Save the action
            await self._save_action(action)
            
            actions.append(action)
        
        # Create the plan
        plan = RemediationPlan(
            id=plan_id,
            name=f"Remediation Plan for {request.repository_url.split('/')[-1]}@{request.commit_sha[:8]}",
            description=f"Remediation plan for {len(actions)} vulnerabilities",
            target=f"{request.repository_url}@{request.commit_sha}",
            actions=actions,
            status=RemediationStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={
                "repository_url": request.repository_url,
                "commit_sha": request.commit_sha,
                "auto_apply": request.auto_apply
            }
        )
        
        # Save the plan
        await self._save_plan(plan)
        
        return plan
    
    async def get_remediation_plan(self, plan_id: str) -> Optional[RemediationPlan]:
        """
        Get a remediation plan by ID
        """
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        
        if not os.path.exists(plan_path):
            return None
        
        try:
            with open(plan_path, "r") as f:
                plan_data = json.load(f)
            
            # Load actions
            actions = []
            for action_data in plan_data["actions"]:
                action = await self.get_remediation_action(action_data["id"])
                if action:
                    actions.append(action)
            
            # Create the plan
            plan = RemediationPlan(
                id=plan_data["id"],
                name=plan_data["name"],
                description=plan_data["description"],
                target=plan_data["target"],
                actions=actions,
                status=RemediationStatus(plan_data["status"]),
                created_at=datetime.fromisoformat(plan_data["created_at"]),
                updated_at=datetime.fromisoformat(plan_data["updated_at"]) if plan_data.get("updated_at") else None,
                completed_at=datetime.fromisoformat(plan_data["completed_at"]) if plan_data.get("completed_at") else None,
                metadata=plan_data.get("metadata", {})
            )
            
            return plan
        except Exception as e:
            logger.error(f"Error loading plan {plan_id}: {str(e)}")
            return None
    
    async def get_all_remediation_plans(self) -> List[RemediationPlan]:
        """
        Get all remediation plans
        """
        plans = []
        
        for filename in os.listdir(self.plans_dir):
            if filename.endswith(".json"):
                plan_id = filename[:-5]  # Remove .json extension
                plan = await self.get_remediation_plan(plan_id)
                
                if plan:
                    plans.append(plan)
        
        return plans
    
    async def update_remediation_plan_status(
        self,
        plan_id: str,
        status: RemediationStatus,
        completed_at: Optional[datetime] = None
    ) -> Optional[RemediationPlan]:
        """
        Update the status of a remediation plan
        """
        plan = await self.get_remediation_plan(plan_id)
        
        if not plan:
            return None
        
        plan.status = status
        plan.updated_at = datetime.utcnow()
        
        if completed_at:
            plan.completed_at = completed_at
        elif status in [RemediationStatus.COMPLETED, RemediationStatus.FAILED, RemediationStatus.ROLLED_BACK]:
            plan.completed_at = datetime.utcnow()
        
        await self._save_plan(plan)
        
        return plan
    
    async def get_remediation_action(self, action_id: str) -> Optional[RemediationAction]:
        """
        Get a remediation action by ID
        """
        action_path = os.path.join(self.actions_dir, f"{action_id}.json")
        
        if not os.path.exists(action_path):
            return None
        
        try:
            with open(action_path, "r") as f:
                action_data = json.load(f)
            
            action = RemediationAction.from_dict(action_data)
            
            return action
        except Exception as e:
            logger.error(f"Error loading action {action_id}: {str(e)}")
            return None
    
    async def get_actions_for_plan(self, plan_id: str) -> List[RemediationAction]:
        """
        Get all actions for a plan
        """
        plan = await self.get_remediation_plan(plan_id)
        
        if not plan:
            return []
        
        return plan.actions
    
    async def update_remediation_action_status(
        self,
        action_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[RemediationAction]:
        """
        Update the status of a remediation action
        """
        action = await self.get_remediation_action(action_id)
        
        if not action:
            return None
        
        action.status = status
        action.updated_at = datetime.utcnow()
        
        if result:
            # Save the result
            result_id = f"RESULT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
            result_obj = RemediationResult(
                action_id=action_id,
                vulnerability_id=action.vulnerability_id,
                success=status == RemediationStatus.COMPLETED,
                status=RemediationStatus(status),
                message=result.get("message", ""),
                details=result,
                created_at=datetime.utcnow()
            )
            
            await self._save_result(result_obj)
            
            # Update the action with the result ID
            action.metadata["result_id"] = result_id
        
        await self._save_action(action)
        
        return action
    
    async def execute_remediation_action(
        self,
        action_id: str,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> RemediationResult:
        """
        Execute a remediation action
        """
        action = await self.get_remediation_action(action_id)
        
        if not action:
            raise ValueError(f"Action not found: {action_id}")
        
        # Update the action status
        await self.update_remediation_action_status(
            action_id,
            RemediationStatus.IN_PROGRESS
        )
        
        try:
            # Execute the action steps
            # TODO: Implement actual execution logic
            
            # For now, just simulate success
            success = True
            message = "Remediation action executed successfully"
            details = {
                "execution_context": execution_context or {},
                "steps_executed": len(action.steps),
                "steps_succeeded": len(action.steps)
            }
            
            # Update the action status
            await self.update_remediation_action_status(
                action_id,
                RemediationStatus.COMPLETED if success else RemediationStatus.FAILED,
                {
                    "message": message,
                    "details": details
                }
            )
            
            # Create the result
            result = RemediationResult(
                action_id=action_id,
                vulnerability_id=action.vulnerability_id,
                success=success,
                status=RemediationStatus.COMPLETED if success else RemediationStatus.FAILED,
                message=message,
                details=details,
                created_at=datetime.utcnow()
            )
            
            # Save the result
            await self._save_result(result)
            
            return result
        except Exception as e:
            logger.error(f"Error executing action {action_id}: {str(e)}")
            
            # Update the action status
            await self.update_remediation_action_status(
                action_id,
                RemediationStatus.FAILED,
                {
                    "message": f"Error executing action: {str(e)}",
                    "details": {
                        "error": str(e),
                        "execution_context": execution_context or {}
                    }
                }
            )
            
            # Create the result
            result = RemediationResult(
                action_id=action_id,
                vulnerability_id=action.vulnerability_id,
                success=False,
                status=RemediationStatus.FAILED,
                message=f"Error executing action: {str(e)}",
                details={
                    "error": str(e),
                    "execution_context": execution_context or {}
                },
                created_at=datetime.utcnow()
            )
            
            # Save the result
            await self._save_result(result)
            
            return result
    
    async def execute_remediation_plan(
        self,
        plan_id: str,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> List[RemediationResult]:
        """
        Execute a remediation plan
        """
        plan = await self.get_remediation_plan(plan_id)
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        # Update the plan status
        await self.update_remediation_plan_status(
            plan_id,
            RemediationStatus.IN_PROGRESS
        )
        
        results = []
        
        try:
            # Execute each action in the plan
            for action in plan.actions:
                result = await self.execute_remediation_action(
                    action.id,
                    execution_context
                )
                
                results.append(result)
            
            # Check if all actions succeeded
            all_succeeded = all(result.success for result in results)
            
            # Update the plan status
            await self.update_remediation_plan_status(
                plan_id,
                RemediationStatus.COMPLETED if all_succeeded else RemediationStatus.FAILED
            )
            
            return results
        except Exception as e:
            logger.error(f"Error executing plan {plan_id}: {str(e)}")
            
            # Update the plan status
            await self.update_remediation_plan_status(
                plan_id,
                RemediationStatus.FAILED
            )
            
            # Create a result for the error
            error_result = RemediationResult(
                action_id="",
                vulnerability_id="",
                success=False,
                status=RemediationStatus.FAILED,
                message=f"Error executing plan: {str(e)}",
                details={
                    "error": str(e),
                    "execution_context": execution_context or {}
                },
                created_at=datetime.utcnow()
            )
            
            results.append(error_result)
            
            return results
    
    async def get_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Get remediation actions for a vulnerability
        """
        actions = []
        
        for filename in os.listdir(self.actions_dir):
            if filename.endswith(".json"):
                action_id = filename[:-5]  # Remove .json extension
                action = await self.get_remediation_action(action_id)
                
                if action and action.vulnerability_id == vulnerability_id:
                    actions.append(action)
        
        return actions
    
    async def _save_plan(self, plan: RemediationPlan) -> None:
        """
        Save a remediation plan to disk
        """
        plan_path = os.path.join(self.plans_dir, f"{plan.id}.json")
        
        # Convert the plan to a dictionary
        plan_dict = plan.to_dict()
        
        # Save the plan
        with open(plan_path, "w") as f:
            json.dump(plan_dict, f, indent=2)
    
    async def _save_action(self, action: RemediationAction) -> None:
        """
        Save a remediation action to disk
        """
        action_path = os.path.join(self.actions_dir, f"{action.id}.json")
        
        # Convert the action to a dictionary
        action_dict = action.to_dict()
        
        # Save the action
        with open(action_path, "w") as f:
            json.dump(action_dict, f, indent=2)
    
    async def _save_result(self, result: RemediationResult) -> None:
        """
        Save a remediation result to disk
        """
        result_path = os.path.join(self.results_dir, f"{result.action_id}.json")
        
        # Convert the result to a dictionary
        result_dict = result.to_dict()
        
        # Save the result
        with open(result_path, "w") as f:
            json.dump(result_dict, f, indent=2)
