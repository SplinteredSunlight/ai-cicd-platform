import os
import json
import yaml
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog
from pathlib import Path
import asyncio

from ..models.policy import (
    Policy,
    PolicyEvaluationResult,
    PolicyViolation,
    PolicyEnforcementMode,
    PolicySeverity,
    PolicyEnvironment
)
from .policy_engine import PolicyEngine

logger = structlog.get_logger()

class PolicyEnforcer:
    """
    Service for enforcing policies in CI/CD pipelines
    """
    
    def __init__(self, policy_engine: Optional[PolicyEngine] = None, policy_dir: Optional[str] = None):
        """
        Initialize the policy enforcer
        
        Args:
            policy_engine: PolicyEngine instance to use
            policy_dir: Directory containing policy files
        """
        self.policy_engine = policy_engine or PolicyEngine()
        self.policy_dir = policy_dir or os.environ.get('POLICY_DIR', '/etc/security-policies')
        self.policies = {}  # id -> Policy
        
        # Create policy directory if it doesn't exist
        os.makedirs(self.policy_dir, exist_ok=True)
    
    async def load_policies(self) -> Dict[str, Policy]:
        """
        Load all policies from the policy directory
        
        Returns:
            Dictionary of policy ID to Policy object
        """
        policies = {}
        
        try:
            policy_files = [f for f in os.listdir(self.policy_dir) if f.endswith(('.yaml', '.yml'))]
            
            for filename in policy_files:
                file_path = os.path.join(self.policy_dir, filename)
                try:
                    policy = self.policy_engine.load_policy_from_file(file_path)
                    policies[policy.id] = policy
                    logger.info("Loaded policy", policy_id=policy.id, policy_name=policy.name, file=filename)
                except Exception as e:
                    logger.error("Failed to load policy", file=filename, error=str(e))
            
            self.policies = policies
            return policies
        
        except Exception as e:
            logger.error("Failed to load policies", error=str(e))
            return {}
    
    async def enforce_policies(
        self,
        target: Dict[str, Any],
        policy_ids: Optional[List[str]] = None,
        policy_types: Optional[List[str]] = None,
        environment: Optional[str] = None
    ) -> Tuple[bool, List[PolicyEvaluationResult], List[PolicyViolation]]:
        """
        Enforce policies on a target
        
        Args:
            target: Target to evaluate policies against
            policy_ids: Optional list of policy IDs to enforce
            policy_types: Optional list of policy types to enforce
            environment: Optional environment to enforce policies for
            
        Returns:
            Tuple of (passed, evaluation_results, violations)
        """
        # Make sure policies are loaded
        if not self.policies:
            await self.load_policies()
        
        # Set environment in target if provided
        if environment:
            target['environment'] = environment
        
        # Filter policies to enforce
        policies_to_enforce = self._filter_policies(policy_ids, policy_types, environment)
        
        if not policies_to_enforce:
            logger.warning("No policies to enforce", 
                          policy_ids=policy_ids, 
                          policy_types=policy_types,
                          environment=environment)
            return True, [], []
        
        # Evaluate policies
        evaluation_results = []
        
        for policy in policies_to_enforce:
            result = self.policy_engine.evaluate_policy(policy, target)
            evaluation_results.append(result)
        
        # Check if pipeline should be blocked
        should_block, violations = self.policy_engine.should_block_pipeline(evaluation_results)
        
        # Log results
        passed = not should_block
        logger.info("Policy enforcement completed", 
                   passed=passed,
                   policies_evaluated=len(evaluation_results),
                   violations=len(violations))
        
        return passed, evaluation_results, violations
    
    def _filter_policies(
        self,
        policy_ids: Optional[List[str]] = None,
        policy_types: Optional[List[str]] = None,
        environment: Optional[str] = None
    ) -> List[Policy]:
        """
        Filter policies based on criteria
        
        Args:
            policy_ids: Optional list of policy IDs to filter by
            policy_types: Optional list of policy types to filter by
            environment: Optional environment to filter by
            
        Returns:
            List of Policy objects
        """
        filtered_policies = list(self.policies.values())
        
        # Filter by ID if provided
        if policy_ids:
            filtered_policies = [p for p in filtered_policies if p.id in policy_ids]
        
        # Filter by type if provided
        if policy_types:
            filtered_policies = [p for p in filtered_policies if p.type in policy_types]
        
        # Filter by environment if provided
        if environment:
            filtered_policies = [
                p for p in filtered_policies 
                if environment in p.environments or PolicyEnvironment.ALL in p.environments
            ]
        
        # Only include active policies
        filtered_policies = [p for p in filtered_policies if p.status == 'active']
        
        return filtered_policies
    
    async def enforce_pipeline_policies(
        self,
        pipeline_context: Dict[str, Any],
        repository_url: str,
        commit_sha: str,
        environment: str = 'development'
    ) -> Dict[str, Any]:
        """
        Enforce policies for a CI/CD pipeline
        
        Args:
            pipeline_context: Context information about the pipeline
            repository_url: URL of the repository
            commit_sha: Commit SHA being built
            environment: Environment the pipeline is running in
            
        Returns:
            Dictionary with enforcement results
        """
        # Prepare target for policy evaluation
        target = {
            'type': 'pipeline',
            'repository_url': repository_url,
            'commit_sha': commit_sha,
            'environment': environment,
            'pipeline': pipeline_context
        }
        
        # Enforce policies
        passed, results, violations = await self.enforce_policies(
            target=target,
            policy_types=['security', 'compliance', 'operational'],
            environment=environment
        )
        
        # Prepare response
        response = {
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'repository_url': repository_url,
            'commit_sha': commit_sha,
            'environment': environment,
            'policies_evaluated': len(results),
            'policies_passed': sum(1 for r in results if r.passed),
            'policies_failed': sum(1 for r in results if not r.passed),
            'violations': [v.dict() for v in violations],
            'results': [r.dict() for r in results]
        }
        
        # Log detailed results
        logger.info("Pipeline policy enforcement completed", 
                   passed=passed,
                   repository=repository_url,
                   commit=commit_sha,
                   environment=environment,
                   policies_evaluated=len(results),
                   policies_passed=sum(1 for r in results if r.passed),
                   policies_failed=sum(1 for r in results if not r.passed),
                   violations=len(violations))
        
        return response
    
    async def enforce_deployment_policies(
        self,
        deployment_context: Dict[str, Any],
        repository_url: str,
        commit_sha: str,
        environment: str
    ) -> Dict[str, Any]:
        """
        Enforce policies for a deployment
        
        Args:
            deployment_context: Context information about the deployment
            repository_url: URL of the repository
            commit_sha: Commit SHA being deployed
            environment: Environment being deployed to
            
        Returns:
            Dictionary with enforcement results
        """
        # Prepare target for policy evaluation
        target = {
            'type': 'deployment',
            'repository_url': repository_url,
            'commit_sha': commit_sha,
            'environment': environment,
            'deployment': deployment_context
        }
        
        # Enforce policies
        passed, results, violations = await self.enforce_policies(
            target=target,
            policy_types=['security', 'compliance', 'operational'],
            environment=environment
        )
        
        # Prepare response
        response = {
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'repository_url': repository_url,
            'commit_sha': commit_sha,
            'environment': environment,
            'policies_evaluated': len(results),
            'policies_passed': sum(1 for r in results if r.passed),
            'policies_failed': sum(1 for r in results if not r.passed),
            'violations': [v.dict() for v in violations],
            'results': [r.dict() for r in results]
        }
        
        # Log detailed results
        logger.info("Deployment policy enforcement completed", 
                   passed=passed,
                   repository=repository_url,
                   commit=commit_sha,
                   environment=environment,
                   policies_evaluated=len(results),
                   policies_passed=sum(1 for r in results if r.passed),
                   policies_failed=sum(1 for r in results if not r.passed),
                   violations=len(violations))
        
        return response
    
    async def enforce_artifact_policies(
        self,
        artifact_context: Dict[str, Any],
        repository_url: str,
        commit_sha: str,
        artifact_url: str,
        environment: str = 'development'
    ) -> Dict[str, Any]:
        """
        Enforce policies for an artifact
        
        Args:
            artifact_context: Context information about the artifact
            repository_url: URL of the repository
            commit_sha: Commit SHA the artifact was built from
            artifact_url: URL of the artifact
            environment: Environment the artifact is for
            
        Returns:
            Dictionary with enforcement results
        """
        # Prepare target for policy evaluation
        target = {
            'type': 'artifact',
            'repository_url': repository_url,
            'commit_sha': commit_sha,
            'artifact_url': artifact_url,
            'environment': environment,
            'artifact': artifact_context
        }
        
        # Enforce policies
        passed, results, violations = await self.enforce_policies(
            target=target,
            policy_types=['security', 'compliance', 'operational'],
            environment=environment
        )
        
        # Prepare response
        response = {
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'repository_url': repository_url,
            'commit_sha': commit_sha,
            'artifact_url': artifact_url,
            'environment': environment,
            'policies_evaluated': len(results),
            'policies_passed': sum(1 for r in results if r.passed),
            'policies_failed': sum(1 for r in results if not r.passed),
            'violations': [v.dict() for v in violations],
            'results': [r.dict() for r in results]
        }
        
        # Log detailed results
        logger.info("Artifact policy enforcement completed", 
                   passed=passed,
                   repository=repository_url,
                   commit=commit_sha,
                   artifact=artifact_url,
                   environment=environment,
                   policies_evaluated=len(results),
                   policies_passed=sum(1 for r in results if r.passed),
                   policies_failed=sum(1 for r in results if not r.passed),
                   violations=len(violations))
        
        return response
    
    async def register_policy_exception(
        self,
        policy_id: str,
        rule_ids: List[str],
        reason: str,
        approved_by: str,
        expires_at: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register an exception for a policy
        
        Args:
            policy_id: ID of the policy
            rule_ids: IDs of the rules to exempt
            reason: Reason for the exception
            approved_by: Person who approved the exception
            expires_at: When the exception expires
            conditions: Conditions when the exception applies
            
        Returns:
            Dictionary with the exception details
        """
        from ..models.policy import PolicyException, PolicyConditionGroup
        
        # Create exception
        exception = PolicyException(
            policy_id=policy_id,
            rule_ids=rule_ids,
            reason=reason,
            approved_by=approved_by,
            expires_at=expires_at,
            conditions=PolicyConditionGroup(**conditions) if conditions else None
        )
        
        # Register with policy engine
        self.policy_engine.register_exception(exception)
        
        # Log exception
        logger.info("Registered policy exception", 
                   policy_id=policy_id,
                   rule_ids=rule_ids,
                   exception_id=exception.id,
                   approved_by=approved_by,
                   expires_at=expires_at.isoformat() if expires_at else None)
        
        return exception.dict()
