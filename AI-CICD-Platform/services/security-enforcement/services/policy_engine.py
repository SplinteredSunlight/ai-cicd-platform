import re
import yaml
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import structlog
from pathlib import Path

from ..models.policy import (
    Policy,
    PolicyRule,
    PolicyCondition,
    PolicyConditionGroup,
    PolicyConditionOperator,
    LogicalOperator,
    PolicyException,
    PolicyEvaluationResult,
    PolicyViolation,
    PolicyType,
    PolicySeverity,
    PolicyEnforcementMode
)

logger = structlog.get_logger()

class PolicyEngine:
    """
    Core engine for evaluating policies against targets
    """
    
    def __init__(self):
        self.exceptions = {}  # policy_id -> list of exceptions
    
    def load_policy_from_yaml(self, yaml_content: str) -> Policy:
        """
        Load a policy from YAML content
        
        Args:
            yaml_content: YAML string containing policy definition
            
        Returns:
            Policy object
        """
        try:
            policy_dict = yaml.safe_load(yaml_content)
            return self._parse_policy_dict(policy_dict)
        except Exception as e:
            logger.error("Failed to load policy from YAML", error=str(e))
            raise ValueError(f"Invalid policy YAML: {str(e)}")
    
    def load_policy_from_file(self, file_path: Union[str, Path]) -> Policy:
        """
        Load a policy from a YAML file
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Policy object
        """
        try:
            with open(file_path, 'r') as f:
                return self.load_policy_from_yaml(f.read())
        except Exception as e:
            logger.error("Failed to load policy from file", file=str(file_path), error=str(e))
            raise ValueError(f"Failed to load policy from {file_path}: {str(e)}")
    
    def _parse_policy_dict(self, policy_dict: Dict[str, Any]) -> Policy:
        """
        Parse a policy dictionary into a Policy object
        
        Args:
            policy_dict: Dictionary containing policy definition
            
        Returns:
            Policy object
        """
        # Extract rules
        rules = []
        for rule_dict in policy_dict.get('rules', []):
            rule = self._parse_rule_dict(rule_dict)
            rules.append(rule)
        
        # Create policy
        policy_data = {
            'id': policy_dict.get('id'),
            'name': policy_dict.get('name'),
            'description': policy_dict.get('description'),
            'type': policy_dict.get('type'),
            'rules': rules,
            'enforcement_mode': policy_dict.get('enforcement_mode'),
            'status': policy_dict.get('status', 'active'),
            'environments': policy_dict.get('environments', ['all']),
            'tags': policy_dict.get('tags', []),
            'version': policy_dict.get('version', '1.0.0'),
            'parent_policy_id': policy_dict.get('parent_policy_id'),
            'template_id': policy_dict.get('template_id'),
            'metadata': policy_dict.get('metadata', {})
        }
        
        # Remove None values
        policy_data = {k: v for k, v in policy_data.items() if v is not None}
        
        return Policy(**policy_data)
    
    def _parse_rule_dict(self, rule_dict: Dict[str, Any]) -> PolicyRule:
        """
        Parse a rule dictionary into a PolicyRule object
        
        Args:
            rule_dict: Dictionary containing rule definition
            
        Returns:
            PolicyRule object
        """
        # Parse condition
        condition = self._parse_condition_dict(rule_dict.get('condition', {}))
        
        # Create rule
        rule_data = {
            'id': rule_dict.get('id'),
            'name': rule_dict.get('name'),
            'description': rule_dict.get('description'),
            'severity': rule_dict.get('severity'),
            'condition': condition,
            'remediation_steps': rule_dict.get('remediation_steps')
        }
        
        # Remove None values
        rule_data = {k: v for k, v in rule_data.items() if v is not None}
        
        return PolicyRule(**rule_data)
    
    def _parse_condition_dict(self, condition_dict: Dict[str, Any]) -> PolicyConditionGroup:
        """
        Parse a condition dictionary into a PolicyConditionGroup object
        
        Args:
            condition_dict: Dictionary containing condition definition
            
        Returns:
            PolicyConditionGroup object
        """
        if 'operator' in condition_dict and condition_dict['operator'] in ['and', 'or']:
            # This is a condition group
            conditions = []
            for cond in condition_dict.get('conditions', []):
                if 'operator' in cond and cond['operator'] in ['and', 'or']:
                    # Nested condition group
                    conditions.append(self._parse_condition_dict(cond))
                else:
                    # Simple condition
                    conditions.append(PolicyCondition(
                        field=cond.get('field'),
                        operator=cond.get('operator'),
                        value=cond.get('value')
                    ))
            
            return PolicyConditionGroup(
                operator=condition_dict.get('operator', 'and'),
                conditions=conditions
            )
        else:
            # This is a simple condition wrapped in a group
            condition = PolicyCondition(
                field=condition_dict.get('field'),
                operator=condition_dict.get('operator'),
                value=condition_dict.get('value')
            )
            
            return PolicyConditionGroup(
                operator=LogicalOperator.AND,
                conditions=[condition]
            )
    
    def policy_to_yaml(self, policy: Policy) -> str:
        """
        Convert a Policy object to YAML
        
        Args:
            policy: Policy object
            
        Returns:
            YAML string
        """
        policy_dict = policy.dict(exclude_none=True)
        return yaml.dump(policy_dict, sort_keys=False)
    
    def policy_to_json(self, policy: Policy) -> str:
        """
        Convert a Policy object to JSON
        
        Args:
            policy: Policy object
            
        Returns:
            JSON string
        """
        policy_dict = policy.dict(exclude_none=True)
        return json.dumps(policy_dict, indent=2)
    
    def register_exception(self, exception: PolicyException):
        """
        Register a policy exception
        
        Args:
            exception: PolicyException object
        """
        if exception.policy_id not in self.exceptions:
            self.exceptions[exception.policy_id] = []
        
        self.exceptions[exception.policy_id].append(exception)
        logger.info("Registered policy exception", 
                   policy_id=exception.policy_id, 
                   exception_id=exception.id)
    
    def evaluate_policy(self, policy: Policy, target: Dict[str, Any]) -> PolicyEvaluationResult:
        """
        Evaluate a policy against a target
        
        Args:
            policy: Policy to evaluate
            target: Target to evaluate against (e.g., a CI/CD pipeline context)
            
        Returns:
            PolicyEvaluationResult object
        """
        logger.info("Evaluating policy", 
                   policy_id=policy.id, 
                   policy_name=policy.name,
                   target_type=target.get('type'))
        
        # Check if policy is active
        if policy.status != 'active':
            logger.info("Skipping inactive policy", 
                       policy_id=policy.id, 
                       status=policy.status)
            return PolicyEvaluationResult(
                policy_id=policy.id,
                policy_name=policy.name,
                policy_type=policy.type,
                passed=True,  # Inactive policies are considered passed
                rule_results=[],
                evaluation_time=datetime.utcnow(),
                target=target,
                metadata={'skipped': True, 'reason': f"Policy status is {policy.status}"}
            )
        
        # Check if policy applies to the current environment
        current_env = target.get('environment', 'all')
        if current_env not in policy.environments and 'all' not in policy.environments:
            logger.info("Policy does not apply to environment", 
                       policy_id=policy.id, 
                       environment=current_env)
            return PolicyEvaluationResult(
                policy_id=policy.id,
                policy_name=policy.name,
                policy_type=policy.type,
                passed=True,  # Policies that don't apply are considered passed
                rule_results=[],
                evaluation_time=datetime.utcnow(),
                target=target,
                metadata={'skipped': True, 'reason': f"Policy does not apply to environment {current_env}"}
            )
        
        # Evaluate each rule
        rule_results = []
        exceptions_applied = []
        
        for rule in policy.rules:
            # Check if there's an exception for this rule
            exception = self._find_applicable_exception(policy.id, rule.id, target)
            
            if exception:
                # Exception applies, skip rule evaluation
                logger.info("Exception applied to rule", 
                           policy_id=policy.id, 
                           rule_id=rule.id,
                           exception_id=exception.id)
                rule_results.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'passed': True,
                    'exception_applied': exception.id,
                    'severity': rule.severity
                })
                exceptions_applied.append(exception.id)
                continue
            
            # Evaluate rule
            rule_passed = self._evaluate_condition_group(rule.condition, target)
            
            rule_results.append({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'passed': rule_passed,
                'exception_applied': None,
                'severity': rule.severity
            })
        
        # Policy passes if all rules pass
        all_passed = all(result['passed'] for result in rule_results)
        
        return PolicyEvaluationResult(
            policy_id=policy.id,
            policy_name=policy.name,
            policy_type=policy.type,
            passed=all_passed,
            rule_results=rule_results,
            exceptions_applied=exceptions_applied,
            evaluation_time=datetime.utcnow(),
            target=target,
            metadata={}
        )
    
    def _find_applicable_exception(self, policy_id: str, rule_id: str, target: Dict[str, Any]) -> Optional[PolicyException]:
        """
        Find an applicable exception for a rule
        
        Args:
            policy_id: ID of the policy
            rule_id: ID of the rule
            target: Target being evaluated
            
        Returns:
            PolicyException object if an exception applies, None otherwise
        """
        if policy_id not in self.exceptions:
            return None
        
        now = datetime.utcnow()
        
        for exception in self.exceptions[policy_id]:
            # Check if exception applies to this rule
            if rule_id not in exception.rule_ids:
                continue
            
            # Check if exception has expired
            if exception.expires_at and exception.expires_at < now:
                continue
            
            # Check if exception conditions apply
            if exception.conditions:
                if not self._evaluate_condition_group(exception.conditions, target):
                    continue
            
            # Exception applies
            return exception
        
        return None
    
    def _evaluate_condition_group(self, group: PolicyConditionGroup, target: Dict[str, Any]) -> bool:
        """
        Evaluate a condition group against a target
        
        Args:
            group: PolicyConditionGroup to evaluate
            target: Target to evaluate against
            
        Returns:
            True if the condition group is satisfied, False otherwise
        """
        results = []
        
        for condition in group.conditions:
            if isinstance(condition, PolicyConditionGroup):
                # Nested condition group
                result = self._evaluate_condition_group(condition, target)
            else:
                # Simple condition
                result = self._evaluate_condition(condition, target)
            
            results.append(result)
        
        if group.operator == LogicalOperator.AND:
            return all(results)
        else:  # OR
            return any(results)
    
    def _evaluate_condition(self, condition: PolicyCondition, target: Dict[str, Any]) -> bool:
        """
        Evaluate a condition against a target
        
        Args:
            condition: PolicyCondition to evaluate
            target: Target to evaluate against
            
        Returns:
            True if the condition is satisfied, False otherwise
        """
        # Extract field value from target using dot notation
        field_value = self._get_field_value(target, condition.field)
        
        # Evaluate based on operator
        if condition.operator == PolicyConditionOperator.EQUALS:
            return field_value == condition.value
        
        elif condition.operator == PolicyConditionOperator.NOT_EQUALS:
            return field_value != condition.value
        
        elif condition.operator == PolicyConditionOperator.CONTAINS:
            if isinstance(field_value, list):
                return condition.value in field_value
            elif isinstance(field_value, str):
                return condition.value in field_value
            return False
        
        elif condition.operator == PolicyConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, list):
                return condition.value not in field_value
            elif isinstance(field_value, str):
                return condition.value not in field_value
            return True
        
        elif condition.operator == PolicyConditionOperator.STARTS_WITH:
            if isinstance(field_value, str):
                return field_value.startswith(condition.value)
            return False
        
        elif condition.operator == PolicyConditionOperator.ENDS_WITH:
            if isinstance(field_value, str):
                return field_value.endswith(condition.value)
            return False
        
        elif condition.operator == PolicyConditionOperator.GREATER_THAN:
            if field_value is None:
                return False
            return field_value > condition.value
        
        elif condition.operator == PolicyConditionOperator.LESS_THAN:
            if field_value is None:
                return False
            return field_value < condition.value
        
        elif condition.operator == PolicyConditionOperator.REGEX_MATCH:
            if isinstance(field_value, str):
                return bool(re.match(condition.value, field_value))
            return False
        
        elif condition.operator == PolicyConditionOperator.EXISTS:
            return field_value is not None
        
        elif condition.operator == PolicyConditionOperator.NOT_EXISTS:
            return field_value is None
        
        # Unknown operator
        logger.warning("Unknown condition operator", operator=condition.operator)
        return False
    
    def _get_field_value(self, target: Dict[str, Any], field_path: str) -> Any:
        """
        Get a field value from a target using dot notation
        
        Args:
            target: Target to extract value from
            field_path: Path to the field (e.g., "metadata.name")
            
        Returns:
            Field value or None if not found
        """
        parts = field_path.split('.')
        value = target
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def get_policy_violations(self, evaluation_result: PolicyEvaluationResult) -> List[PolicyViolation]:
        """
        Get policy violations from an evaluation result
        
        Args:
            evaluation_result: PolicyEvaluationResult object
            
        Returns:
            List of PolicyViolation objects
        """
        if evaluation_result.passed:
            return []
        
        violations = []
        
        for rule_result in evaluation_result.rule_results:
            if not rule_result['passed'] and not rule_result.get('exception_applied'):
                # Find the rule
                policy = None
                rule = None
                
                # This would normally be fetched from a policy store
                # For now, we'll just create a stub
                
                violation = PolicyViolation(
                    policy_id=evaluation_result.policy_id,
                    rule_id=rule_result['rule_id'],
                    severity=rule_result['severity'],
                    description=f"Violation of rule {rule_result['rule_name']}",
                    target=evaluation_result.target,
                    remediation_steps=[]  # Would be populated from the rule
                )
                
                violations.append(violation)
        
        return violations
    
    def should_block_pipeline(self, evaluation_results: List[PolicyEvaluationResult]) -> Tuple[bool, List[PolicyViolation]]:
        """
        Determine if a pipeline should be blocked based on policy evaluation results
        
        Args:
            evaluation_results: List of PolicyEvaluationResult objects
            
        Returns:
            Tuple of (should_block, violations)
        """
        should_block = False
        all_violations = []
        
        for result in evaluation_results:
            if not result.passed:
                violations = self.get_policy_violations(result)
                all_violations.extend(violations)
                
                # Check if this is a blocking policy
                if result.metadata.get('enforcement_mode') == PolicyEnforcementMode.BLOCKING:
                    should_block = True
        
        return should_block, all_violations
