"""
Approval Workflow Service

This module implements the approval workflow service, which is responsible for
managing approval processes for deployments.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from models.approval import (
    ApprovalPolicy,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalNotification,
    ApprovalRole,
    ApprovalAuditLog,
    ApprovalTemplate,
    ApprovalSchedule
)

# Configure logging
logger = logging.getLogger(__name__)

class ApprovalWorkflow:
    """
    Service for managing approval workflows for deployments.
    """
    
    def __init__(self):
        """
        Initialize the approval workflow service.
        """
        logger.info("Initializing ApprovalWorkflow service")
        # In a real implementation, these would be loaded from a database
        self.policies = {}
        self.requests = {}
        self.decisions = {}
        self.notifications = {}
        self.roles = {}
        self.audit_logs = {}
        self.templates = {}
        self.schedules = {}
        
        # Initialize with some default roles and policies
        self._initialize_default_roles()
        self._initialize_default_policies()
        self._initialize_default_templates()
    
    def _initialize_default_roles(self):
        """
        Initialize default approval roles.
        """
        # Developer role
        developer_role = ApprovalRole(
            id=str(uuid.uuid4()),
            name="developer",
            description="Developer role with basic approval permissions",
            permissions=["approve_development"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # QA Lead role
        qa_lead_role = ApprovalRole(
            id=str(uuid.uuid4()),
            name="qa_lead",
            description="QA Lead role with testing approval permissions",
            permissions=["approve_development", "approve_staging"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Operations Lead role
        ops_lead_role = ApprovalRole(
            id=str(uuid.uuid4()),
            name="ops_lead",
            description="Operations Lead role with infrastructure approval permissions",
            permissions=["approve_development", "approve_staging", "approve_production_infrastructure"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Manager role
        manager_role = ApprovalRole(
            id=str(uuid.uuid4()),
            name="manager",
            description="Manager role with business approval permissions",
            permissions=["approve_development", "approve_staging", "approve_production_business"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Admin role
        admin_role = ApprovalRole(
            id=str(uuid.uuid4()),
            name="admin",
            description="Admin role with all approval permissions",
            permissions=["approve_development", "approve_staging", "approve_production_infrastructure", "approve_production_business", "manage_approvals"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add roles to the in-memory store
        self.roles[developer_role.id] = developer_role
        self.roles[qa_lead_role.id] = qa_lead_role
        self.roles[ops_lead_role.id] = ops_lead_role
        self.roles[manager_role.id] = manager_role
        self.roles[admin_role.id] = admin_role
    
    def _initialize_default_policies(self):
        """
        Initialize default approval policies.
        """
        # Development environment policy
        dev_policy = ApprovalPolicy(
            id=str(uuid.uuid4()),
            name="Development Approval Policy",
            description="Policy for approving deployments to development environments",
            environment="development",
            required_approvals=1,
            required_roles=["developer"],
            auto_approve_criteria={
                "source_branch": "^feature/.*$",
                "target_environment": "development",
                "change_size": "small"
            },
            timeout_minutes=1440,  # 24 hours
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Staging environment policy
        staging_policy = ApprovalPolicy(
            id=str(uuid.uuid4()),
            name="Staging Approval Policy",
            description="Policy for approving deployments to staging environments",
            environment="staging",
            required_approvals=2,
            required_roles=["qa_lead", "ops_lead"],
            auto_approve_criteria={
                "source_branch": "^release/.*$",
                "target_environment": "staging",
                "all_tests_passed": True
            },
            timeout_minutes=2880,  # 48 hours
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Production environment policy
        prod_policy = ApprovalPolicy(
            id=str(uuid.uuid4()),
            name="Production Approval Policy",
            description="Policy for approving deployments to production environments",
            environment="production",
            required_approvals=3,
            required_roles=["qa_lead", "ops_lead", "manager"],
            auto_approve_criteria=None,  # No auto-approval for production
            timeout_minutes=4320,  # 72 hours
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add policies to the in-memory store
        self.policies[dev_policy.id] = dev_policy
        self.policies[staging_policy.id] = staging_policy
        self.policies[prod_policy.id] = prod_policy
    
    def _initialize_default_templates(self):
        """
        Initialize default approval templates.
        """
        # Standard approval template
        standard_template = ApprovalTemplate(
            id=str(uuid.uuid4()),
            name="Standard Approval Template",
            description="Standard template for approval requests",
            required_approvals=1,
            required_roles=["developer"],
            timeout_minutes=1440,  # 24 hours
            notification_settings={
                "channels": ["email"],
                "reminder_interval_minutes": 240  # 4 hours
            },
            form_fields=[
                {
                    "name": "reason",
                    "label": "Reason for Deployment",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "risk_assessment",
                    "label": "Risk Assessment",
                    "type": "select",
                    "options": ["Low", "Medium", "High"],
                    "required": True
                },
                {
                    "name": "additional_notes",
                    "label": "Additional Notes",
                    "type": "textarea",
                    "required": False
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Production approval template
        production_template = ApprovalTemplate(
            id=str(uuid.uuid4()),
            name="Production Approval Template",
            description="Template for production approval requests",
            required_approvals=3,
            required_roles=["qa_lead", "ops_lead", "manager"],
            timeout_minutes=4320,  # 72 hours
            notification_settings={
                "channels": ["email", "slack"],
                "reminder_interval_minutes": 480  # 8 hours
            },
            form_fields=[
                {
                    "name": "reason",
                    "label": "Reason for Production Deployment",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "risk_assessment",
                    "label": "Risk Assessment",
                    "type": "select",
                    "options": ["Low", "Medium", "High"],
                    "required": True
                },
                {
                    "name": "testing_evidence",
                    "label": "Testing Evidence",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "rollback_plan",
                    "label": "Rollback Plan",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "business_impact",
                    "label": "Business Impact",
                    "type": "textarea",
                    "required": True
                },
                {
                    "name": "additional_notes",
                    "label": "Additional Notes",
                    "type": "textarea",
                    "required": False
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add templates to the in-memory store
        self.templates[standard_template.id] = standard_template
        self.templates[production_template.id] = production_template
    
    def get_policies(self, environment: Optional[str] = None) -> List[ApprovalPolicy]:
        """
        Get all approval policies, optionally filtered by environment.
        
        Args:
            environment (Optional[str]): Environment to filter by
            
        Returns:
            List[ApprovalPolicy]: List of approval policies
        """
        if environment:
            return [policy for policy in self.policies.values() if policy.environment == environment]
        else:
            return list(self.policies.values())
    
    def get_policy(self, policy_id: str) -> Optional[ApprovalPolicy]:
        """
        Get an approval policy by ID.
        
        Args:
            policy_id (str): Policy ID
            
        Returns:
            Optional[ApprovalPolicy]: Approval policy if found, None otherwise
        """
        return self.policies.get(policy_id)
    
    def create_policy(self, policy: ApprovalPolicy) -> ApprovalPolicy:
        """
        Create a new approval policy.
        
        Args:
            policy (ApprovalPolicy): Approval policy to create
            
        Returns:
            ApprovalPolicy: Created approval policy
        """
        if not policy.id:
            policy.id = str(uuid.uuid4())
        
        policy.created_at = datetime.now().isoformat()
        policy.updated_at = datetime.now().isoformat()
        
        self.policies[policy.id] = policy
        logger.info(f"Created approval policy: {policy.id}")
        
        return policy
    
    def update_policy(self, policy_id: str, policy: ApprovalPolicy) -> Optional[ApprovalPolicy]:
        """
        Update an existing approval policy.
        
        Args:
            policy_id (str): Policy ID
            policy (ApprovalPolicy): Updated approval policy
            
        Returns:
            Optional[ApprovalPolicy]: Updated approval policy if found, None otherwise
        """
        if policy_id not in self.policies:
            return None
        
        policy.id = policy_id
        policy.updated_at = datetime.now().isoformat()
        
        self.policies[policy_id] = policy
        logger.info(f"Updated approval policy: {policy_id}")
        
        return policy
    
    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete an approval policy.
        
        Args:
            policy_id (str): Policy ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if policy_id not in self.policies:
            return False
        
        del self.policies[policy_id]
        logger.info(f"Deleted approval policy: {policy_id}")
        
        return True
    
    def create_request(self, deployment_id: str, environment: str, requester: str, details: Dict[str, Any]) -> ApprovalRequest:
        """
        Create a new approval request.
        
        Args:
            deployment_id (str): Deployment ID
            environment (str): Target environment
            requester (str): User ID of the requester
            details (Dict[str, Any]): Additional details for the request
            
        Returns:
            ApprovalRequest: Created approval request
        """
        # Find the appropriate policy for the environment
        policies = self.get_policies(environment)
        if not policies:
            # Use a default policy if none exists for the environment
            policy = ApprovalPolicy(
                id=str(uuid.uuid4()),
                name=f"Default {environment.capitalize()} Policy",
                description=f"Default policy for {environment} environment",
                environment=environment,
                required_approvals=1,
                required_roles=["developer"],
                auto_approve_criteria=None,
                timeout_minutes=1440,  # 24 hours
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        else:
            policy = policies[0]
        
        # Create a new request ID
        request_id = str(uuid.uuid4())
        
        # Calculate expiration time
        expiration_time = datetime.now() + timedelta(minutes=policy.timeout_minutes)
        
        # Create the request
        request = ApprovalRequest(
            id=request_id,
            deployment_id=deployment_id,
            policy_id=policy.id,
            environment=environment,
            requester=requester,
            status="pending",
            details=details,
            required_approvals=policy.required_approvals,
            required_roles=policy.required_roles,
            approvals=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            expires_at=expiration_time.isoformat()
        )
        
        self.requests[request_id] = request
        logger.info(f"Created approval request: {request_id}")
        
        # Check for auto-approval
        if policy.auto_approve_criteria and self._check_auto_approve_criteria(request, policy.auto_approve_criteria):
            self.auto_approve_request(request_id)
        else:
            # Send notifications to approvers
            self._send_approval_notifications(request)
        
        return request
    
    def _check_auto_approve_criteria(self, request: ApprovalRequest, criteria: Dict[str, Any]) -> bool:
        """
        Check if a request meets the auto-approval criteria.
        
        Args:
            request (ApprovalRequest): Approval request
            criteria (Dict[str, Any]): Auto-approval criteria
            
        Returns:
            bool: True if the request meets the criteria, False otherwise
        """
        # In a real implementation, this would check the criteria against the request details
        # For now, we just return False to disable auto-approval
        return False
    
    def _send_approval_notifications(self, request: ApprovalRequest):
        """
        Send notifications to approvers for a request.
        
        Args:
            request (ApprovalRequest): Approval request
        """
        # In a real implementation, this would send notifications to approvers
        # For now, we just log the notification
        logger.info(f"Sending approval notifications for request: {request.id}")
        
        # Create a notification record
        notification = ApprovalNotification(
            id=str(uuid.uuid4()),
            request_id=request.id,
            recipients=request.required_roles,
            channel="email",
            status="sent",
            content={
                "subject": f"Approval Request for {request.environment} Deployment",
                "body": f"A new approval request has been created for deployment {request.deployment_id} to {request.environment}."
            },
            created_at=datetime.now().isoformat()
        )
        
        self.notifications[notification.id] = notification
    
    def auto_approve_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Auto-approve an approval request.
        
        Args:
            request_id (str): Request ID
            
        Returns:
            Optional[ApprovalRequest]: Updated approval request if found, None otherwise
        """
        request = self.get_request(request_id)
        if not request:
            return None
        
        # Create an auto-approval decision
        decision = ApprovalDecision(
            id=str(uuid.uuid4()),
            request_id=request_id,
            approver="system",
            decision="approved",
            reason="Auto-approved based on policy criteria",
            created_at=datetime.now().isoformat()
        )
        
        self.decisions[decision.id] = decision
        
        # Update the request
        request.approvals.append(decision.id)
        request.status = "approved"
        request.updated_at = datetime.now().isoformat()
        
        self.requests[request_id] = request
        logger.info(f"Auto-approved request: {request_id}")
        
        # Create an audit log entry
        self._create_audit_log(request_id, "system", "auto_approve", {
            "reason": "Auto-approved based on policy criteria"
        })
        
        return request
    
    def get_requests(self, deployment_id: Optional[str] = None, environment: Optional[str] = None, status: Optional[str] = None) -> List[ApprovalRequest]:
        """
        Get all approval requests, optionally filtered by deployment ID, environment, or status.
        
        Args:
            deployment_id (Optional[str]): Deployment ID to filter by
            environment (Optional[str]): Environment to filter by
            status (Optional[str]): Status to filter by
            
        Returns:
            List[ApprovalRequest]: List of approval requests
        """
        requests = list(self.requests.values())
        
        if deployment_id:
            requests = [req for req in requests if req.deployment_id == deployment_id]
        
        if environment:
            requests = [req for req in requests if req.environment == environment]
        
        if status:
            requests = [req for req in requests if req.status == status]
        
        return requests
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Get an approval request by ID.
        
        Args:
            request_id (str): Request ID
            
        Returns:
            Optional[ApprovalRequest]: Approval request if found, None otherwise
        """
        return self.requests.get(request_id)
    
    def approve_request(self, request_id: str, approver: str, reason: str) -> Optional[ApprovalRequest]:
        """
        Approve an approval request.
        
        Args:
            request_id (str): Request ID
            approver (str): User ID of the approver
            reason (str): Reason for approval
            
        Returns:
            Optional[ApprovalRequest]: Updated approval request if found, None otherwise
        """
        request = self.get_request(request_id)
        if not request:
            return None
        
        # Check if the request is already approved or rejected
        if request.status != "pending":
            logger.warning(f"Cannot approve request {request_id}: status is {request.status}")
            return request
        
        # Create an approval decision
        decision = ApprovalDecision(
            id=str(uuid.uuid4()),
            request_id=request_id,
            approver=approver,
            decision="approved",
            reason=reason,
            created_at=datetime.now().isoformat()
        )
        
        self.decisions[decision.id] = decision
        
        # Update the request
        request.approvals.append(decision.id)
        
        # Check if we have enough approvals
        if len(request.approvals) >= request.required_approvals:
            request.status = "approved"
        
        request.updated_at = datetime.now().isoformat()
        
        self.requests[request_id] = request
        logger.info(f"Approved request: {request_id} by {approver}")
        
        # Create an audit log entry
        self._create_audit_log(request_id, approver, "approve", {
            "reason": reason
        })
        
        return request
    
    def reject_request(self, request_id: str, approver: str, reason: str) -> Optional[ApprovalRequest]:
        """
        Reject an approval request.
        
        Args:
            request_id (str): Request ID
            approver (str): User ID of the approver
            reason (str): Reason for rejection
            
        Returns:
            Optional[ApprovalRequest]: Updated approval request if found, None otherwise
        """
        request = self.get_request(request_id)
        if not request:
            return None
        
        # Check if the request is already approved or rejected
        if request.status != "pending":
            logger.warning(f"Cannot reject request {request_id}: status is {request.status}")
            return request
        
        # Create a rejection decision
        decision = ApprovalDecision(
            id=str(uuid.uuid4()),
            request_id=request_id,
            approver=approver,
            decision="rejected",
            reason=reason,
            created_at=datetime.now().isoformat()
        )
        
        self.decisions[decision.id] = decision
        
        # Update the request
        request.status = "rejected"
        request.updated_at = datetime.now().isoformat()
        
        self.requests[request_id] = request
        logger.info(f"Rejected request: {request_id} by {approver}")
        
        # Create an audit log entry
        self._create_audit_log(request_id, approver, "reject", {
            "reason": reason
        })
        
        return request
    
    def cancel_request(self, request_id: str, user: str, reason: str) -> Optional[ApprovalRequest]:
        """
        Cancel an approval request.
        
        Args:
            request_id (str): Request ID
            user (str): User ID of the canceller
            reason (str): Reason for cancellation
            
        Returns:
            Optional[ApprovalRequest]: Updated approval request if found, None otherwise
        """
        request = self.get_request(request_id)
        if not request:
            return None
        
        # Check if the request is already approved, rejected, or cancelled
        if request.status not in ["pending", "approved"]:
            logger.warning(f"Cannot cancel request {request_id}: status is {request.status}")
            return request
        
        # Update the request
        request.status = "cancelled"
        request.updated_at = datetime.now().isoformat()
        
        self.requests[request_id] = request
        logger.info(f"Cancelled request: {request_id} by {user}")
        
        # Create an audit log entry
        self._create_audit_log(request_id, user, "cancel", {
            "reason": reason
        })
        
        return request
    
    def get_decisions(self, request_id: Optional[str] = None) -> List[ApprovalDecision]:
        """
        Get all approval decisions, optionally filtered by request ID.
        
        Args:
            request_id (Optional[str]): Request ID to filter by
            
        Returns:
            List[ApprovalDecision]: List of approval decisions
        """
        if request_id:
            return [decision for decision in self.decisions.values() if decision.request_id == request_id]
        else:
            return list(self.decisions.values())
    
    def get_decision(self, decision_id: str) -> Optional[ApprovalDecision]:
        """
        Get an approval decision by ID.
        
        Args:
            decision_id (str): Decision ID
            
        Returns:
            Optional[ApprovalDecision]: Approval decision if found, None otherwise
        """
        return self.decisions.get(decision_id)
    
    def get_roles(self) -> List[ApprovalRole]:
        """
        Get all approval roles.
        
        Returns:
            List[ApprovalRole]: List of approval roles
        """
        return list(self.roles.values())
    
    def get_role(self, role_id: str) -> Optional[ApprovalRole]:
        """
        Get an approval role by ID.
        
        Args:
            role_id (str): Role ID
            
        Returns:
            Optional[ApprovalRole]: Approval role if found, None otherwise
        """
        return self.roles.get(role_id)
    
    def create_role(self, role: ApprovalRole) -> ApprovalRole:
        """
        Create a new approval role.
        
        Args:
            role (ApprovalRole): Approval role to create
            
        Returns:
            ApprovalRole: Created approval role
        """
        if not role.id:
            role.id = str(uuid.uuid4())
        
        role.created_at = datetime.now().isoformat()
        role.updated_at = datetime.now().isoformat()
        
        self.roles[role.id] = role
        logger.info(f"Created approval role: {role.id}")
        
        return role
    
    def update_role(self, role_id: str, role: ApprovalRole) -> Optional[ApprovalRole]:
        """
        Update an existing approval role.
        
        Args:
            role_id (str): Role ID
            role (ApprovalRole): Updated approval role
            
        Returns:
            Optional[ApprovalRole]: Updated approval role if found, None otherwise
        """
        if role_id not in self.roles:
            return None
        
        role.id = role_id
        role.updated_at = datetime.now().isoformat()
        
        self.roles[role_id] = role
        logger.info(f"Updated approval role: {role_id}")
        
        return role
    
    def delete_role(self, role_id: str) -> bool:
        """
        Delete an approval role.
        
        Args:
            role_id (str): Role ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if role_id not in self.roles:
            return False
        
        del self.roles[role_id]
        logger.info(f"Deleted approval role: {role_id}")
        
        return True
    
    def _create_audit_log(self, request_id: str, user: str, action: str, details: Dict[str, Any]) -> ApprovalAuditLog:
        """
        Create an audit log entry for an approval action.
        
        Args:
            request_id (str): Request ID
            user (str): User ID
            action (str): Action performed
            details (Dict[str, Any]): Additional details
            
        Returns:
            ApprovalAuditLog: Created audit log entry
        """
        log_id = str(uuid.uuid4())
        
        log = ApprovalAuditLog(
            id=log_id,
            request_id=request_id,
            user=user,
            action=action,
            details=details,
            timestamp=datetime.now().isoformat()
        )
        
        self.audit_logs[log_id] = log
        logger.info(f"Created audit log: {log_id}")
        
        return log
    
    def get_audit_logs(self, request_id: Optional[str] = None, user: Optional[str] = None, action: Optional[str] = None) -> List[ApprovalAuditLog]:
        """
        Get all audit logs, optionally filtered by request ID, user, or action.
        
        Args:
            request_id (Optional[str]): Request ID to filter by
            user (Optional[str]): User ID to filter by
            action (Optional[str]): Action to filter by
            
        Returns:
            List[ApprovalAuditLog]: List of audit logs
        """
        logs = list(self.audit_logs.values())
        
        if request_id:
            logs = [log for log in logs if log.request_id == request_id]
        
        if user:
            logs = [log for log in logs if log.user == user]
        
        if action:
            logs = [log for log in logs if log.action == action]
        
        return logs
    
    def get_templates(self) -> List[ApprovalTemplate]:
        """
        Get all approval templates.
        
        Returns:
            List[ApprovalTemplate]: List of approval templates
        """
        return list(self.templates.values())
    
    def get_template(self, template_id: str) -> Optional[ApprovalTemplate]:
        """
        Get an approval template by ID.
        
        Args:
            template_id (str): Template ID
            
        Returns:
            Optional[ApprovalTemplate]: Approval template if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def create_template(self, template: ApprovalTemplate) -> ApprovalTemplate:
        """
        Create a new approval template.
        
        Args:
            template (ApprovalTemplate): Approval template to create
            
        Returns:
            ApprovalTemplate: Created approval template
        """
        if not template.id:
            template.id = str(uuid.uuid4())
        
        template.created_at = datetime.now().isoformat()
        template.updated_at = datetime.now().isoformat()
        
        self.templates[template.id] = template
        logger.info(f"Created approval template: {template.id}")
        
        return template
    
    def update_template(self, template_id: str, template: ApprovalTemplate) -> Optional[ApprovalTemplate]:
        """
        Update an existing approval template.
        
        Args:
            template_id (str): Template ID
            template (ApprovalTemplate): Updated approval template
            
        Returns:
            Optional[ApprovalTemplate]: Updated approval template if found, None otherwise
        """
        if template_id not in self.templates:
            return None
        
        template.id = template_id
        template.updated_at = datetime.now().isoformat()
        
        self.templates[template_id] = template
        logger.info(f"Updated approval template: {template_id}")
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete an approval template.
        
        Args:
            template_id (str): Template ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if template_id not in self.templates:
            return False
        
        del self.templates[template_id]
        logger.info(f"Deleted approval template: {template_id}")
        
        return True
    
    def create_schedule(self, schedule: ApprovalSchedule) -> ApprovalSchedule:
        """
        Create a new approval schedule.
        
        Args:
            schedule (ApprovalSchedule): Approval schedule to create
            
        Returns:
            ApprovalSchedule: Created approval schedule
        """
        if not schedule.id:
            schedule.id = str(uuid.uuid4())
        
        schedule.created_at = datetime.now().isoformat()
        schedule.updated_at = datetime.now().isoformat()
        
        self.schedules[schedule.id] = schedule
        logger.info(f"Created approval schedule: {schedule.id}")
        
        return schedule
    
    def get_schedules(self) -> List[ApprovalSchedule]:
        """
        Get all approval schedules.
        
        Returns:
            List[ApprovalSchedule]: List of approval schedules
        """
        return list(self.schedules.values())
    
    def get_schedule(self, schedule_id: str) -> Optional[ApprovalSchedule]:
        """
        Get an approval schedule by ID.
        
        Args:
            schedule_id (str): Schedule ID
            
        Returns:
            Optional[ApprovalSchedule]: Approval schedule if found, None otherwise
        """
        return self.schedules.get(schedule_id)
