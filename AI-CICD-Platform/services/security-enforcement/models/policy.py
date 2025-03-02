from enum import Enum
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
import uuid


class PolicyType(str, Enum):
    """Types of security policies"""
    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PolicyEnforcementMode(str, Enum):
    """Enforcement modes for policies"""
    BLOCKING = "blocking"  # Fails the pipeline
    WARNING = "warning"    # Warns but allows the pipeline to continue
    AUDIT = "audit"        # Only logs the violation


class PolicyStatus(str, Enum):
    """Status of a policy"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class PolicyEnvironment(str, Enum):
    """Environment where a policy applies"""
    ALL = "all"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class PolicyConditionOperator(str, Enum):
    """Operators for policy conditions"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    REGEX_MATCH = "regex_match"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions"""
    AND = "and"
    OR = "or"


class PolicyCondition(BaseModel):
    """A condition for a policy rule"""
    field: str = Field(..., description="The field to evaluate")
    operator: PolicyConditionOperator = Field(..., description="The operator to apply")
    value: Optional[Any] = Field(None, description="The value to compare against")
    
    @validator('value', pre=True, always=True)
    def validate_value(cls, v, values):
        """Validate that value is provided for operators that require it"""
        operator = values.get('operator')
        if operator in [
            PolicyConditionOperator.EXISTS, 
            PolicyConditionOperator.NOT_EXISTS
        ]:
            return None
        if v is None:
            raise ValueError(f"Value must be provided for operator {operator}")
        return v


class PolicyConditionGroup(BaseModel):
    """A group of conditions with a logical operator"""
    operator: LogicalOperator = Field(LogicalOperator.AND, description="Logical operator to combine conditions")
    conditions: List[Union["PolicyConditionGroup", PolicyCondition]] = Field(
        ..., description="List of conditions or condition groups"
    )


class PolicyRule(BaseModel):
    """A rule within a policy"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the rule")
    name: str = Field(..., description="Name of the rule")
    description: str = Field(..., description="Description of the rule")
    severity: PolicySeverity = Field(..., description="Severity of the rule violation")
    condition: PolicyConditionGroup = Field(..., description="Condition that triggers the rule")
    remediation_steps: Optional[List[str]] = Field(None, description="Steps to remediate the violation")


class PolicyException(BaseModel):
    """An exception to a policy"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the exception")
    policy_id: str = Field(..., description="ID of the policy this exception applies to")
    rule_ids: List[str] = Field(..., description="IDs of the rules this exception applies to")
    reason: str = Field(..., description="Reason for the exception")
    approved_by: str = Field(..., description="Person who approved the exception")
    approved_at: datetime = Field(default_factory=datetime.utcnow, description="When the exception was approved")
    expires_at: Optional[datetime] = Field(None, description="When the exception expires")
    conditions: Optional[PolicyConditionGroup] = Field(None, description="Conditions when this exception applies")


class PolicyTemplate(BaseModel):
    """A template for creating policies"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the template")
    name: str = Field(..., description="Name of the template")
    description: str = Field(..., description="Description of the template")
    type: PolicyType = Field(..., description="Type of policy this template creates")
    rules: List[PolicyRule] = Field(..., description="Rules included in this template")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters that can be customized")
    version: str = Field(..., description="Version of the template")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the template was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the template was last updated")


class Policy(BaseModel):
    """A security policy definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the policy")
    name: str = Field(..., description="Name of the policy")
    description: str = Field(..., description="Description of the policy")
    type: PolicyType = Field(..., description="Type of policy")
    rules: List[PolicyRule] = Field(..., description="Rules that make up this policy")
    enforcement_mode: PolicyEnforcementMode = Field(..., description="How this policy is enforced")
    status: PolicyStatus = Field(PolicyStatus.ACTIVE, description="Status of this policy")
    environments: List[PolicyEnvironment] = Field([PolicyEnvironment.ALL], description="Environments where this policy applies")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the policy")
    version: str = Field("1.0.0", description="Version of the policy")
    parent_policy_id: Optional[str] = Field(None, description="ID of the parent policy if this inherits from another policy")
    template_id: Optional[str] = Field(None, description="ID of the template this policy was created from")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the policy was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the policy was last updated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the policy")


class PolicyEvaluationResult(BaseModel):
    """Result of evaluating a policy against a target"""
    policy_id: str = Field(..., description="ID of the policy that was evaluated")
    policy_name: str = Field(..., description="Name of the policy that was evaluated")
    policy_type: PolicyType = Field(..., description="Type of the policy that was evaluated")
    passed: bool = Field(..., description="Whether the policy passed evaluation")
    rule_results: List[Dict[str, Any]] = Field(..., description="Results for each rule in the policy")
    exceptions_applied: List[str] = Field(default_factory=list, description="IDs of exceptions that were applied")
    evaluation_time: datetime = Field(default_factory=datetime.utcnow, description="When the policy was evaluated")
    target: Dict[str, Any] = Field(..., description="The target that was evaluated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the evaluation")


class PolicyViolation(BaseModel):
    """A violation of a policy rule"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the violation")
    policy_id: str = Field(..., description="ID of the policy that was violated")
    rule_id: str = Field(..., description="ID of the rule that was violated")
    severity: PolicySeverity = Field(..., description="Severity of the violation")
    description: str = Field(..., description="Description of the violation")
    target: Dict[str, Any] = Field(..., description="The target that was evaluated")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="When the violation was detected")
    remediation_steps: Optional[List[str]] = Field(None, description="Steps to remediate the violation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the violation")


class PolicyChangeRequest(BaseModel):
    """A request to change a policy"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the change request")
    policy_id: str = Field(..., description="ID of the policy to change")
    requested_by: str = Field(..., description="Person who requested the change")
    requested_at: datetime = Field(default_factory=datetime.utcnow, description="When the change was requested")
    changes: Dict[str, Any] = Field(..., description="Changes to apply to the policy")
    reason: str = Field(..., description="Reason for the change")
    status: str = Field("pending", description="Status of the change request")
    approved_by: Optional[str] = Field(None, description="Person who approved the change")
    approved_at: Optional[datetime] = Field(None, description="When the change was approved")
    implemented_at: Optional[datetime] = Field(None, description="When the change was implemented")


class PolicyComplianceReport(BaseModel):
    """A report on policy compliance"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the report")
    target: Dict[str, Any] = Field(..., description="The target that was evaluated")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When the report was generated")
    policies_evaluated: List[str] = Field(..., description="IDs of policies that were evaluated")
    policies_passed: List[str] = Field(..., description="IDs of policies that passed evaluation")
    policies_failed: List[str] = Field(..., description="IDs of policies that failed evaluation")
    violations: List[PolicyViolation] = Field(..., description="Violations that were detected")
    exceptions_applied: List[str] = Field(default_factory=list, description="IDs of exceptions that were applied")
    summary: Dict[str, Any] = Field(..., description="Summary of the compliance report")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the report")


# Resolve forward references for PolicyConditionGroup
PolicyConditionGroup.update_forward_refs()
