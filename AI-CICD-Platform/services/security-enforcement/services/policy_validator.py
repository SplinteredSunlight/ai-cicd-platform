import os
import yaml
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import structlog
from pathlib import Path
import asyncio
import copy

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
from .policy_engine import PolicyEngine

logger = structlog.get_logger()

class PolicyValidator:
    """
    Service for validating and testing policies
    """
    
    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        """
        Initialize the policy validator
        
        Args:
            policy_engine: PolicyEngine instance to use
        """
        self.policy_engine = policy_engine or PolicyEngine()
    
    async def validate_policy_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """
        Validate a policy YAML string
        
        Args:
            yaml_content: YAML string containing policy definition
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Check YAML syntax
            try:
                policy_dict = yaml.safe_load(yaml_content)
                if not isinstance(policy_dict, dict):
                    return {
                        'valid': False,
                        'errors': ['YAML content must be a dictionary']
                    }
            except Exception as e:
                return {
                    'valid': False,
                    'errors': [f'Invalid YAML syntax: {str(e)}']
                }
            
            # Validate required fields
            errors = []
            
            if 'name' not in policy_dict:
                errors.append('Missing required field: name')
            
            if 'description' not in policy_dict:
                errors.append('Missing required field: description')
            
            if 'type' not in policy_dict:
                errors.append('Missing required field: type')
            elif policy_dict['type'] not in ['security', 'compliance', 'operational']:
                errors.append(f'Invalid policy type: {policy_dict["type"]}')
            
            if 'rules' not in policy_dict or not isinstance(policy_dict['rules'], list):
                errors.append('Missing required field: rules (must be a list)')
            elif len(policy_dict['rules']) == 0:
                errors.append('Policy must have at least one rule')
            
            if 'enforcement_mode' not in policy_dict:
                errors.append('Missing required field: enforcement_mode')
            elif policy_dict['enforcement_mode'] not in ['blocking', 'warning', 'audit']:
                errors.append(f'Invalid enforcement mode: {policy_dict["enforcement_mode"]}')
            
            # Validate rules
            if 'rules' in policy_dict and isinstance(policy_dict['rules'], list):
                for i, rule in enumerate(policy_dict['rules']):
                    rule_errors = self._validate_rule(rule, i)
                    errors.extend(rule_errors)
            
            # Try to parse the policy
            if not errors:
                try:
                    policy = self.policy_engine.load_policy_from_yaml(yaml_content)
                except Exception as e:
                    errors.append(f'Failed to parse policy: {str(e)}')
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
        
        except Exception as e:
            logger.error("Policy validation failed", error=str(e))
            return {
                'valid': False,
                'errors': [f'Validation failed: {str(e)}']
            }
    
    def _validate_rule(self, rule: Dict[str, Any], index: int) -> List[str]:
        """
        Validate a rule dictionary
        
        Args:
            rule: Rule dictionary
            index: Index of the rule in the rules list
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if 'name' not in rule:
            errors.append(f'Rule {index}: Missing required field: name')
        
        if 'description' not in rule:
            errors.append(f'Rule {index}: Missing required field: description')
        
        if 'severity' not in rule:
            errors.append(f'Rule {index}: Missing required field: severity')
        elif rule['severity'] not in ['critical', 'high', 'medium', 'low', 'info']:
            errors.append(f'Rule {index}: Invalid severity: {rule["severity"]}')
        
        if 'condition' not in rule:
            errors.append(f'Rule {index}: Missing required field: condition')
        else:
            condition_errors = self._validate_condition(rule['condition'], f'Rule {index}')
            errors.extend(condition_errors)
        
        return errors
    
    def _validate_condition(self, condition: Dict[str, Any], prefix: str) -> List[str]:
        """
        Validate a condition dictionary
        
        Args:
            condition: Condition dictionary
            prefix: Prefix for error messages
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if 'operator' in condition and condition['operator'] in ['and', 'or']:
            # This is a condition group
            if 'conditions' not in condition or not isinstance(condition['conditions'], list):
                errors.append(f'{prefix}: Condition group missing "conditions" list')
            elif len(condition['conditions']) == 0:
                errors.append(f'{prefix}: Condition group must have at least one condition')
            else:
                for i, cond in enumerate(condition['conditions']):
                    if 'operator' in cond and cond['operator'] in ['and', 'or']:
                        # Nested condition group
                        nested_errors = self._validate_condition(cond, f'{prefix}, Nested group {i}')
                        errors.extend(nested_errors)
                    else:
                        # Simple condition
                        if 'field' not in cond:
                            errors.append(f'{prefix}, Condition {i}: Missing required field: field')
                        
                        if 'operator' not in cond:
                            errors.append(f'{prefix}, Condition {i}: Missing required field: operator')
                        elif cond['operator'] not in [
                            'equals', 'not_equals', 'contains', 'not_contains', 
                            'starts_with', 'ends_with', 'greater_than', 'less_than', 
                            'regex_match', 'exists', 'not_exists'
                        ]:
                            errors.append(f'{prefix}, Condition {i}: Invalid operator: {cond["operator"]}')
                        
                        # Check if value is required
                        if cond.get('operator') not in ['exists', 'not_exists'] and 'value' not in cond:
                            errors.append(f'{prefix}, Condition {i}: Missing required field: value for operator {cond.get("operator")}')
        else:
            # This is a simple condition
            if 'field' not in condition:
                errors.append(f'{prefix}: Missing required field: field')
            
            if 'operator' not in condition:
                errors.append(f'{prefix}: Missing required field: operator')
            elif condition['operator'] not in [
                'equals', 'not_equals', 'contains', 'not_contains', 
                'starts_with', 'ends_with', 'greater_than', 'less_than', 
                'regex_match', 'exists', 'not_exists'
            ]:
                errors.append(f'{prefix}: Invalid operator: {condition["operator"]}')
            
            # Check if value is required
            if condition.get('operator') not in ['exists', 'not_exists'] and 'value' not in condition:
                errors.append(f'{prefix}: Missing required field: value for operator {condition.get("operator")}')
        
        return errors
    
    async def simulate_policy_evaluation(
        self,
        policy_yaml: str,
        target: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate policy evaluation against a target
        
        Args:
            policy_yaml: YAML string containing policy definition
            target: Target to evaluate against
            
        Returns:
            Dictionary with simulation results
        """
        try:
            # Validate policy first
            validation_result = await self.validate_policy_yaml(policy_yaml)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': 'Policy validation failed',
                    'errors': validation_result['errors']
                }
            
            # Load policy
            policy = self.policy_engine.load_policy_from_yaml(policy_yaml)
            
            # Evaluate policy
            evaluation_result = self.policy_engine.evaluate_policy(policy, target)
            
            # Get violations
            violations = self.policy_engine.get_policy_violations(evaluation_result)
            
            return {
                'success': True,
                'passed': evaluation_result.passed,
                'policy_id': policy.id,
                'policy_name': policy.name,
                'policy_type': policy.type,
                'rule_results': evaluation_result.rule_results,
                'violations': [v.dict() for v in violations],
                'target': target
            }
        
        except Exception as e:
            logger.error("Policy simulation failed", error=str(e))
            return {
                'success': False,
                'message': f'Simulation failed: {str(e)}'
            }
    
    async def test_policy_with_scenarios(
        self,
        policy_yaml: str,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Test a policy against multiple scenarios
        
        Args:
            policy_yaml: YAML string containing policy definition
            scenarios: List of test scenarios, each with a target and expected result
            
        Returns:
            Dictionary with test results
        """
        try:
            # Validate policy first
            validation_result = await self.validate_policy_yaml(policy_yaml)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': 'Policy validation failed',
                    'errors': validation_result['errors']
                }
            
            # Load policy
            policy = self.policy_engine.load_policy_from_yaml(policy_yaml)
            
            # Run scenarios
            scenario_results = []
            
            for i, scenario in enumerate(scenarios):
                target = scenario.get('target', {})
                expected_result = scenario.get('expected_result', True)
                
                # Evaluate policy
                evaluation_result = self.policy_engine.evaluate_policy(policy, target)
                
                # Check if result matches expectation
                passed = evaluation_result.passed == expected_result
                
                scenario_results.append({
                    'scenario': i + 1,
                    'description': scenario.get('description', f'Scenario {i + 1}'),
                    'passed': passed,
                    'expected_result': expected_result,
                    'actual_result': evaluation_result.passed,
                    'rule_results': evaluation_result.rule_results
                })
            
            # Overall test passed if all scenarios passed
            all_passed = all(result['passed'] for result in scenario_results)
            
            return {
                'success': True,
                'policy_id': policy.id,
                'policy_name': policy.name,
                'all_scenarios_passed': all_passed,
                'scenarios_passed': sum(1 for result in scenario_results if result['passed']),
                'scenarios_failed': sum(1 for result in scenario_results if not result['passed']),
                'scenario_results': scenario_results
            }
        
        except Exception as e:
            logger.error("Policy testing failed", error=str(e))
            return {
                'success': False,
                'message': f'Testing failed: {str(e)}'
            }
    
    async def analyze_policy_impact(
        self,
        policy_yaml: str,
        targets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze the impact of a policy on a set of targets
        
        Args:
            policy_yaml: YAML string containing policy definition
            targets: List of targets to evaluate against
            
        Returns:
            Dictionary with impact analysis results
        """
        try:
            # Validate policy first
            validation_result = await self.validate_policy_yaml(policy_yaml)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': 'Policy validation failed',
                    'errors': validation_result['errors']
                }
            
            # Load policy
            policy = self.policy_engine.load_policy_from_yaml(policy_yaml)
            
            # Evaluate policy against each target
            results = []
            
            for target in targets:
                evaluation_result = self.policy_engine.evaluate_policy(policy, target)
                violations = self.policy_engine.get_policy_violations(evaluation_result)
                
                results.append({
                    'target_id': target.get('id', 'unknown'),
                    'target_type': target.get('type', 'unknown'),
                    'passed': evaluation_result.passed,
                    'violations': len(violations),
                    'rule_results': evaluation_result.rule_results
                })
            
            # Calculate impact statistics
            targets_passed = sum(1 for result in results if result['passed'])
            targets_failed = sum(1 for result in results if not result['passed'])
            
            # Calculate rule impact
            rule_impact = {}
            for rule in policy.rules:
                rule_failures = 0
                for result in results:
                    for rule_result in result['rule_results']:
                        if rule_result['rule_id'] == rule.id and not rule_result['passed']:
                            rule_failures += 1
                            break
                
                rule_impact[rule.id] = {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'severity': rule.severity,
                    'targets_failed': rule_failures,
                    'failure_rate': rule_failures / len(targets) if targets else 0
                }
            
            return {
                'success': True,
                'policy_id': policy.id,
                'policy_name': policy.name,
                'targets_evaluated': len(targets),
                'targets_passed': targets_passed,
                'targets_failed': targets_failed,
                'pass_rate': targets_passed / len(targets) if targets else 0,
                'rule_impact': list(rule_impact.values()),
                'results': results
            }
        
        except Exception as e:
            logger.error("Policy impact analysis failed", error=str(e))
            return {
                'success': False,
                'message': f'Impact analysis failed: {str(e)}'
            }
    
    async def generate_policy_template(
        self,
        policy_type: str,
        name: str,
        description: str,
        enforcement_mode: str = 'warning'
    ) -> Dict[str, Any]:
        """
        Generate a policy template
        
        Args:
            policy_type: Type of policy (security, compliance, operational)
            name: Name of the policy
            description: Description of the policy
            enforcement_mode: Enforcement mode (blocking, warning, audit)
            
        Returns:
            Dictionary with the generated template
        """
        try:
            if policy_type not in ['security', 'compliance', 'operational']:
                return {
                    'success': False,
                    'message': f'Invalid policy type: {policy_type}'
                }
            
            if enforcement_mode not in ['blocking', 'warning', 'audit']:
                return {
                    'success': False,
                    'message': f'Invalid enforcement mode: {enforcement_mode}'
                }
            
            # Generate template based on policy type
            template = {
                'id': f'policy-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'name': name,
                'description': description,
                'type': policy_type,
                'enforcement_mode': enforcement_mode,
                'status': 'draft',
                'environments': ['all'],
                'rules': []
            }
            
            # Add example rules based on policy type
            if policy_type == 'security':
                template['rules'] = [
                    {
                        'id': f'rule-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-1',
                        'name': 'Require secure connections',
                        'description': 'Ensures that all connections use secure protocols',
                        'severity': 'high',
                        'condition': {
                            'operator': 'and',
                            'conditions': [
                                {
                                    'field': 'artifact.protocols',
                                    'operator': 'contains',
                                    'value': 'https'
                                },
                                {
                                    'field': 'artifact.protocols',
                                    'operator': 'not_contains',
                                    'value': 'http'
                                }
                            ]
                        },
                        'remediation_steps': [
                            'Configure your application to use HTTPS instead of HTTP',
                            'Update your infrastructure to redirect HTTP to HTTPS'
                        ]
                    }
                ]
            elif policy_type == 'compliance':
                template['rules'] = [
                    {
                        'id': f'rule-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-1',
                        'name': 'Data encryption at rest',
                        'description': 'Ensures that all data is encrypted at rest',
                        'severity': 'high',
                        'condition': {
                            'field': 'artifact.encryption.at_rest',
                            'operator': 'equals',
                            'value': True
                        },
                        'remediation_steps': [
                            'Configure your storage to use encryption at rest',
                            'Update your application to use encrypted storage'
                        ]
                    }
                ]
            elif policy_type == 'operational':
                template['rules'] = [
                    {
                        'id': f'rule-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-1',
                        'name': 'Resource limits defined',
                        'description': 'Ensures that resource limits are defined',
                        'severity': 'medium',
                        'condition': {
                            'operator': 'and',
                            'conditions': [
                                {
                                    'field': 'deployment.resources.limits',
                                    'operator': 'exists'
                                },
                                {
                                    'field': 'deployment.resources.limits.cpu',
                                    'operator': 'exists'
                                },
                                {
                                    'field': 'deployment.resources.limits.memory',
                                    'operator': 'exists'
                                }
                            ]
                        },
                        'remediation_steps': [
                            'Define resource limits in your deployment configuration',
                            'Set appropriate CPU and memory limits'
                        ]
                    }
                ]
            
            # Convert to YAML
            yaml_content = yaml.dump(template, sort_keys=False)
            
            return {
                'success': True,
                'template': template,
                'yaml': yaml_content
            }
        
        except Exception as e:
            logger.error("Policy template generation failed", error=str(e))
            return {
                'success': False,
                'message': f'Template generation failed: {str(e)}'
            }
