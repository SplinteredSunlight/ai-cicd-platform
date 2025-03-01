import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Set
import structlog
import uuid
import os
import json

from ..models.vulnerability import Vulnerability, SeverityLevel
from ..models.vulnerability_database import (
    VulnerabilityDatabaseEntry,
    VulnerabilitySource,
    VulnerabilityStatus
)
from ..models.remediation import (
    RemediationAction,
    RemediationPlan,
    RemediationRequest,
    RemediationResult,
    RemediationStrategy,
    RemediationStatus,
    RemediationSource
)
from ..config import get_settings
from .vulnerability_database import VulnerabilityDatabase
from .ncp_integration import NCPIntegration
from .cert_integration import CERTIntegration
from .oval_integration import OVALIntegration
from .epss_integration import EPSSIntegration
from .scap_integration import SCAPIntegration

logger = structlog.get_logger()

class RemediationService:
    """
    Service for automated remediation of vulnerabilities
    """
    
    def __init__(self, vuln_db: Optional[VulnerabilityDatabase] = None):
        self.settings = get_settings()
        self.vuln_db = vuln_db or VulnerabilityDatabase()
        
        # Initialize integrations
        self.ncp_integration = NCPIntegration()
        self.cert_integration = CERTIntegration()
        self.oval_integration = OVALIntegration()
        self.epss_integration = EPSSIntegration()
        self.scap_integration = SCAPIntegration()
        
        # Create directory for remediation plans
        self.plans_dir = os.path.join(self.settings.artifact_storage_path, "remediation_plans")
        os.makedirs(self.plans_dir, exist_ok=True)
    
    async def generate_remediation_plan(self, request: RemediationRequest) -> RemediationPlan:
        """
        Generate a remediation plan for vulnerabilities
        
        Args:
            request: Remediation request
            
        Returns:
            Remediation plan
        """
        try:
            # Generate a unique ID for the plan
            plan_id = f"PLAN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
            
            # Create a plan
            plan = RemediationPlan(
                id=plan_id,
                name=f"Remediation Plan for {request.repository_url}",
                description=f"Automated remediation plan for {request.repository_url} at commit {request.commit_sha}",
                target=f"{request.repository_url}@{request.commit_sha}",
                actions=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status=RemediationStatus.PENDING,
                metadata={
                    "repository_url": request.repository_url,
                    "commit_sha": request.commit_sha,
                    "artifact_url": request.artifact_url,
                    "auto_apply": request.auto_apply
                }
            )
            
            # Get vulnerabilities to remediate
            vulnerabilities = await self._get_vulnerabilities_to_remediate(request)
            
            # Generate remediation actions for each vulnerability
            for vulnerability in vulnerabilities:
                actions = await self._generate_remediation_actions(vulnerability.vulnerability.id)
                
                # Add actions to the plan
                plan.actions.extend(actions)
            
            # Save the plan
            await self._save_remediation_plan(plan)
            
            # Apply the plan if requested
            if request.auto_apply:
                await self.apply_remediation_plan(plan.id)
            
            return plan
        
        except Exception as e:
            logger.error("Error generating remediation plan", error=str(e))
            raise
    
    async def _get_vulnerabilities_to_remediate(self, request: RemediationRequest) -> List[VulnerabilityDatabaseEntry]:
        """
        Get vulnerabilities to remediate based on the request
        
        Args:
            request: Remediation request
            
        Returns:
            List of vulnerabilities to remediate
        """
        # If specific vulnerability IDs are provided, use those
        if request.vulnerability_ids:
            vulnerabilities = []
            for vuln_id in request.vulnerability_ids:
                vuln = await self.vuln_db.get_vulnerability(vuln_id)
                if vuln:
                    vulnerabilities.append(vuln)
            return vulnerabilities
        
        # Otherwise, search for vulnerabilities based on severity
        from ..models.vulnerability_database import VulnerabilityDatabaseQuery
        
        # Build query
        query = VulnerabilityDatabaseQuery(
            status=[VulnerabilityStatus.ACTIVE],
            limit=100
        )
        
        # Add severity filter if provided
        if request.max_severity:
            # Include all severities up to max_severity
            severities = []
            for severity in SeverityLevel:
                if severity.value <= request.max_severity.value:
                    severities.append(severity)
            query.severity = severities
        
        # Search for vulnerabilities
        vulnerabilities = await self.vuln_db.search_vulnerabilities(query)
        
        return vulnerabilities
    
    async def _generate_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Generate remediation actions for a vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability
            
        Returns:
            List of remediation actions
        """
        # Fetch remediation actions from all integrations
        tasks = [
            self.ncp_integration.fetch_remediation_actions(vulnerability_id),
            self.cert_integration.fetch_remediation_actions(vulnerability_id),
            self.oval_integration.fetch_remediation_actions(vulnerability_id),
            self.epss_integration.fetch_remediation_actions(vulnerability_id),
            self.scap_integration.fetch_remediation_actions(vulnerability_id)
        ]
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect actions
        actions = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Error fetching remediation actions", error=str(result))
                continue
            
            actions.extend(result)
        
        # Deduplicate actions
        deduplicated_actions = self._deduplicate_actions(actions)
        
        return deduplicated_actions
    
    def _deduplicate_actions(self, actions: List[RemediationAction]) -> List[RemediationAction]:
        """
        Deduplicate remediation actions
        
        Args:
            actions: List of remediation actions
            
        Returns:
            Deduplicated list of remediation actions
        """
        # Use a set to track unique descriptions
        seen_descriptions = set()
        deduplicated = []
        
        for action in actions:
            # Create a key for deduplication
            key = (action.vulnerability_id, action.strategy, action.description)
            
            if key not in seen_descriptions:
                seen_descriptions.add(key)
                deduplicated.append(action)
        
        return deduplicated
    
    async def _save_remediation_plan(self, plan: RemediationPlan) -> None:
        """
        Save a remediation plan to disk
        
        Args:
            plan: Remediation plan
        """
        plan_path = os.path.join(self.plans_dir, f"{plan.id}.json")
        
        with open(plan_path, "w") as f:
            f.write(plan.json(indent=2))
    
    async def get_remediation_plan(self, plan_id: str) -> Optional[RemediationPlan]:
        """
        Get a remediation plan by ID
        
        Args:
            plan_id: ID of the remediation plan
            
        Returns:
            Remediation plan, or None if not found
        """
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        
        if not os.path.exists(plan_path):
            return None
        
        with open(plan_path, "r") as f:
            plan_data = json.load(f)
            return RemediationPlan(**plan_data)
    
    async def apply_remediation_plan(self, plan_id: str) -> List[RemediationResult]:
        """
        Apply a remediation plan
        
        Args:
            plan_id: ID of the remediation plan
            
        Returns:
            List of remediation results
        """
        # Get the plan
        plan = await self.get_remediation_plan(plan_id)
        if not plan:
            raise ValueError(f"Remediation plan {plan_id} not found")
        
        # Update plan status
        plan.status = RemediationStatus.IN_PROGRESS
        plan.updated_at = datetime.utcnow()
        await self._save_remediation_plan(plan)
        
        # Apply each action
        results = []
        for action in plan.actions:
            result = await self._apply_remediation_action(action)
            results.append(result)
            
            # Update action status
            action.status = result.status
            action.updated_at = datetime.utcnow()
        
        # Update plan status
        if all(result.success for result in results):
            plan.status = RemediationStatus.COMPLETED
        else:
            plan.status = RemediationStatus.FAILED
        
        plan.updated_at = datetime.utcnow()
        await self._save_remediation_plan(plan)
        
        return results
    
    async def _apply_remediation_action(self, action: RemediationAction) -> RemediationResult:
        """
        Apply a remediation action
        
        Args:
            action: Remediation action
            
        Returns:
            Remediation result
        """
        try:
            # In a real implementation, this would apply the remediation action
            # For now, we'll just simulate success
            
            # Update vulnerability status in the database
            await self.vuln_db.update_vulnerability_status(
                action.vulnerability_id,
                VulnerabilityStatus.MITIGATED,
                f"Automatically mitigated by remediation action {action.id}"
            )
            
            return RemediationResult(
                action_id=action.id,
                vulnerability_id=action.vulnerability_id,
                success=True,
                status=RemediationStatus.COMPLETED,
                message=f"Successfully applied remediation action: {action.description}",
                details={
                    "strategy": action.strategy,
                    "steps": action.steps,
                    "source": action.source
                }
            )
        
        except Exception as e:
            logger.error("Error applying remediation action", error=str(e))
            
            return RemediationResult(
                action_id=action.id,
                vulnerability_id=action.vulnerability_id,
                success=False,
                status=RemediationStatus.FAILED,
                message=f"Failed to apply remediation action: {str(e)}",
                details={
                    "strategy": action.strategy,
                    "steps": action.steps,
                    "source": action.source,
                    "error": str(e)
                }
            )
    
    async def get_remediation_actions(self, vulnerability_id: str) -> List[RemediationAction]:
        """
        Get remediation actions for a vulnerability
        
        Args:
            vulnerability_id: ID of the vulnerability
            
        Returns:
            List of remediation actions
        """
        return await self._generate_remediation_actions(vulnerability_id)
    
    async def get_all_remediation_plans(self) -> List[RemediationPlan]:
        """
        Get all remediation plans
        
        Returns:
            List of remediation plans
        """
        plans = []
        
        for filename in os.listdir(self.plans_dir):
            if filename.endswith(".json"):
                plan_path = os.path.join(self.plans_dir, filename)
                
                with open(plan_path, "r") as f:
                    plan_data = json.load(f)
                    plans.append(RemediationPlan(**plan_data))
        
        return plans
