"""
Target Integrator Service

This module implements the target integrator service, which is responsible for
integrating with various deployment targets such as Kubernetes, cloud providers,
and on-premises environments.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from models.target import (
    DeploymentTarget,
    TargetCredential,
    TargetEnvironment,
    DeploymentOperation,
    TargetTemplate,
    TargetGroup,
    TargetHealthStatus,
    TargetMetadata,
    TargetCapability,
    TargetConstraint
)

# Configure logging
logger = logging.getLogger(__name__)

class TargetIntegrator:
    """
    Service for integrating with various deployment targets.
    """
    
    def __init__(self):
        """
        Initialize the target integrator service.
        """
        logger.info("Initializing TargetIntegrator service")
        # In a real implementation, these would be loaded from a database
        self.targets = {}
        self.credentials = {}
        self.environments = {}
        self.operations = {}
        self.templates = {}
        self.groups = {}
        self.health_statuses = {}
        self.metadata = {}
        self.capabilities = {}
        self.constraints = {}
        
        # Initialize with some default targets and templates
        self._initialize_default_templates()
        self._initialize_default_targets()
    
    def _initialize_default_templates(self):
        """
        Initialize default target templates.
        """
        # Kubernetes template
        kubernetes_template = TargetTemplate(
            id=str(uuid.uuid4()),
            name="Kubernetes Cluster",
            description="Template for Kubernetes cluster targets",
            type="kubernetes",
            provider="generic",
            properties_template={
                "cluster_name": "",
                "namespace": "default",
                "context": "",
                "config_path": "",
                "in_cluster": False
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # AWS ECS template
        aws_ecs_template = TargetTemplate(
            id=str(uuid.uuid4()),
            name="AWS ECS",
            description="Template for AWS ECS targets",
            type="ecs",
            provider="aws",
            properties_template={
                "cluster_name": "",
                "region": "us-west-2",
                "service_name": "",
                "task_definition": "",
                "launch_type": "FARGATE"
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # AWS Lambda template
        aws_lambda_template = TargetTemplate(
            id=str(uuid.uuid4()),
            name="AWS Lambda",
            description="Template for AWS Lambda targets",
            type="serverless",
            provider="aws",
            properties_template={
                "function_name": "",
                "region": "us-west-2",
                "runtime": "nodejs14.x",
                "handler": "index.handler",
                "memory_size": 128,
                "timeout": 30
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Azure AKS template
        azure_aks_template = TargetTemplate(
            id=str(uuid.uuid4()),
            name="Azure AKS",
            description="Template for Azure AKS targets",
            type="kubernetes",
            provider="azure",
            properties_template={
                "cluster_name": "",
                "resource_group": "",
                "subscription_id": "",
                "namespace": "default"
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # GCP GKE template
        gcp_gke_template = TargetTemplate(
            id=str(uuid.uuid4()),
            name="GCP GKE",
            description="Template for GCP GKE targets",
            type="kubernetes",
            provider="gcp",
            properties_template={
                "cluster_name": "",
                "project_id": "",
                "zone": "us-central1-a",
                "namespace": "default"
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # On-premises VM template
        onprem_vm_template = TargetTemplate(
            id=str(uuid.uuid4()),
            name="On-premises VM",
            description="Template for on-premises VM targets",
            type="vm",
            provider="on-premises",
            properties_template={
                "hostname": "",
                "port": 22,
                "username": "",
                "use_key": True,
                "key_path": ""
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add templates to the in-memory store
        self.templates[kubernetes_template.id] = kubernetes_template
        self.templates[aws_ecs_template.id] = aws_ecs_template
        self.templates[aws_lambda_template.id] = aws_lambda_template
        self.templates[azure_aks_template.id] = azure_aks_template
        self.templates[gcp_gke_template.id] = gcp_gke_template
        self.templates[onprem_vm_template.id] = onprem_vm_template
    
    def _initialize_default_targets(self):
        """
        Initialize default deployment targets.
        """
        # Development Kubernetes target
        dev_k8s_target = DeploymentTarget(
            id=str(uuid.uuid4()),
            name="Development Kubernetes",
            type="kubernetes",
            provider="generic",
            region="local",
            properties={
                "cluster_name": "dev-cluster",
                "namespace": "development",
                "context": "dev-context",
                "config_path": "~/.kube/config",
                "in_cluster": False
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Staging Kubernetes target
        staging_k8s_target = DeploymentTarget(
            id=str(uuid.uuid4()),
            name="Staging Kubernetes",
            type="kubernetes",
            provider="aws",
            region="us-west-2",
            properties={
                "cluster_name": "staging-cluster",
                "namespace": "staging",
                "context": "staging-context",
                "config_path": "~/.kube/config",
                "in_cluster": False
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Production Kubernetes target
        prod_k8s_target = DeploymentTarget(
            id=str(uuid.uuid4()),
            name="Production Kubernetes",
            type="kubernetes",
            provider="aws",
            region="us-west-2",
            properties={
                "cluster_name": "prod-cluster",
                "namespace": "production",
                "context": "prod-context",
                "config_path": "~/.kube/config",
                "in_cluster": False
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add targets to the in-memory store
        self.targets[dev_k8s_target.id] = dev_k8s_target
        self.targets[staging_k8s_target.id] = staging_k8s_target
        self.targets[prod_k8s_target.id] = prod_k8s_target
        
        # Create environments for the targets
        dev_env = TargetEnvironment(
            id=str(uuid.uuid4()),
            name="Development",
            type="development",
            target_id=dev_k8s_target.id,
            properties={
                "resource_limits": {
                    "cpu": "500m",
                    "memory": "512Mi"
                },
                "auto_scaling": {
                    "enabled": False
                }
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        staging_env = TargetEnvironment(
            id=str(uuid.uuid4()),
            name="Staging",
            type="staging",
            target_id=staging_k8s_target.id,
            properties={
                "resource_limits": {
                    "cpu": "1000m",
                    "memory": "1Gi"
                },
                "auto_scaling": {
                    "enabled": True,
                    "min_replicas": 2,
                    "max_replicas": 5
                }
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        prod_env = TargetEnvironment(
            id=str(uuid.uuid4()),
            name="Production",
            type="production",
            target_id=prod_k8s_target.id,
            properties={
                "resource_limits": {
                    "cpu": "2000m",
                    "memory": "2Gi"
                },
                "auto_scaling": {
                    "enabled": True,
                    "min_replicas": 3,
                    "max_replicas": 10
                }
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Add environments to the in-memory store
        self.environments[dev_env.id] = dev_env
        self.environments[staging_env.id] = staging_env
        self.environments[prod_env.id] = prod_env
    
    def get_templates(self, provider: Optional[str] = None, target_type: Optional[str] = None) -> List[TargetTemplate]:
        """
        Get all target templates, optionally filtered by provider or target type.
        
        Args:
            provider (Optional[str]): Provider to filter by
            target_type (Optional[str]): Target type to filter by
            
        Returns:
            List[TargetTemplate]: List of target templates
        """
        templates = list(self.templates.values())
        
        if provider:
            templates = [t for t in templates if t.provider == provider]
        
        if target_type:
            templates = [t for t in templates if t.type == target_type]
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[TargetTemplate]:
        """
        Get a target template by ID.
        
        Args:
            template_id (str): Template ID
            
        Returns:
            Optional[TargetTemplate]: Target template if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def create_template(self, template: TargetTemplate) -> TargetTemplate:
        """
        Create a new target template.
        
        Args:
            template (TargetTemplate): Target template to create
            
        Returns:
            TargetTemplate: Created target template
        """
        if not template.id:
            template.id = str(uuid.uuid4())
        
        template.created_at = datetime.now().isoformat()
        template.updated_at = datetime.now().isoformat()
        
        self.templates[template.id] = template
        logger.info(f"Created target template: {template.id}")
        
        return template
    
    def update_template(self, template_id: str, template: TargetTemplate) -> Optional[TargetTemplate]:
        """
        Update an existing target template.
        
        Args:
            template_id (str): Template ID
            template (TargetTemplate): Updated target template
            
        Returns:
            Optional[TargetTemplate]: Updated target template if found, None otherwise
        """
        if template_id not in self.templates:
            return None
        
        template.id = template_id
        template.updated_at = datetime.now().isoformat()
        
        self.templates[template_id] = template
        logger.info(f"Updated target template: {template_id}")
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a target template.
        
        Args:
            template_id (str): Template ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if template_id not in self.templates:
            return False
        
        del self.templates[template_id]
        logger.info(f"Deleted target template: {template_id}")
        
        return True
    
    def get_targets(self, provider: Optional[str] = None, target_type: Optional[str] = None, region: Optional[str] = None) -> List[DeploymentTarget]:
        """
        Get all deployment targets, optionally filtered by provider, target type, or region.
        
        Args:
            provider (Optional[str]): Provider to filter by
            target_type (Optional[str]): Target type to filter by
            region (Optional[str]): Region to filter by
            
        Returns:
            List[DeploymentTarget]: List of deployment targets
        """
        targets = list(self.targets.values())
        
        if provider:
            targets = [t for t in targets if t.provider == provider]
        
        if target_type:
            targets = [t for t in targets if t.type == target_type]
        
        if region:
            targets = [t for t in targets if t.region == region]
        
        return targets
    
    def get_target(self, target_id: str) -> Optional[DeploymentTarget]:
        """
        Get a deployment target by ID.
        
        Args:
            target_id (str): Target ID
            
        Returns:
            Optional[DeploymentTarget]: Deployment target if found, None otherwise
        """
        return self.targets.get(target_id)
    
    def create_target(self, target: DeploymentTarget) -> DeploymentTarget:
        """
        Create a new deployment target.
        
        Args:
            target (DeploymentTarget): Deployment target to create
            
        Returns:
            DeploymentTarget: Created deployment target
        """
        if not target.id:
            target.id = str(uuid.uuid4())
        
        target.created_at = datetime.now().isoformat()
        target.updated_at = datetime.now().isoformat()
        
        self.targets[target.id] = target
        logger.info(f"Created deployment target: {target.id}")
        
        return target
    
    def update_target(self, target_id: str, target: DeploymentTarget) -> Optional[DeploymentTarget]:
        """
        Update an existing deployment target.
        
        Args:
            target_id (str): Target ID
            target (DeploymentTarget): Updated deployment target
            
        Returns:
            Optional[DeploymentTarget]: Updated deployment target if found, None otherwise
        """
        if target_id not in self.targets:
            return None
        
        target.id = target_id
        target.updated_at = datetime.now().isoformat()
        
        self.targets[target_id] = target
        logger.info(f"Updated deployment target: {target_id}")
        
        return target
    
    def delete_target(self, target_id: str) -> bool:
        """
        Delete a deployment target.
        
        Args:
            target_id (str): Target ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if target_id not in self.targets:
            return False
        
        # Delete all environments associated with the target
        environments_to_delete = [env_id for env_id, env in self.environments.items() if env.target_id == target_id]
        for env_id in environments_to_delete:
            del self.environments[env_id]
        
        # Delete all credentials associated with the target
        credentials_to_delete = [cred_id for cred_id, cred in self.credentials.items() if cred.target_id == target_id]
        for cred_id in credentials_to_delete:
            del self.credentials[cred_id]
        
        del self.targets[target_id]
        logger.info(f"Deleted deployment target: {target_id}")
        
        return True
    
    def create_credential(self, target_id: str, credential_type: str, value: Dict[str, Any], description: str = "") -> TargetCredential:
        """
        Create a credential for a deployment target.
        
        Args:
            target_id (str): Target ID
            credential_type (str): Credential type
            value (Dict[str, Any]): Credential value
            description (str, optional): Credential description
            
        Returns:
            TargetCredential: Created credential
        """
        # Create a new credential ID
        credential_id = str(uuid.uuid4())
        
        # Create the credential
        credential = TargetCredential(
            id=credential_id,
            target_id=target_id,
            type=credential_type,
            value=value,
            description=description,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.credentials[credential_id] = credential
        logger.info(f"Created target credential: {credential_id}")
        
        return credential
    
    def get_credentials(self, target_id: Optional[str] = None, credential_type: Optional[str] = None) -> List[TargetCredential]:
        """
        Get all credentials, optionally filtered by target ID or credential type.
        
        Args:
            target_id (Optional[str]): Target ID to filter by
            credential_type (Optional[str]): Credential type to filter by
            
        Returns:
            List[TargetCredential]: List of credentials
        """
        credentials = list(self.credentials.values())
        
        if target_id:
            credentials = [c for c in credentials if c.target_id == target_id]
        
        if credential_type:
            credentials = [c for c in credentials if c.type == credential_type]
        
        return credentials
    
    def get_credential(self, credential_id: str) -> Optional[TargetCredential]:
        """
        Get a credential by ID.
        
        Args:
            credential_id (str): Credential ID
            
        Returns:
            Optional[TargetCredential]: Credential if found, None otherwise
        """
        return self.credentials.get(credential_id)
    
    def update_credential(self, credential_id: str, value: Dict[str, Any], description: Optional[str] = None) -> Optional[TargetCredential]:
        """
        Update an existing credential.
        
        Args:
            credential_id (str): Credential ID
            value (Dict[str, Any]): Updated credential value
            description (Optional[str]): Updated credential description
            
        Returns:
            Optional[TargetCredential]: Updated credential if found, None otherwise
        """
        credential = self.get_credential(credential_id)
        if not credential:
            return None
        
        credential.value = value
        if description is not None:
            credential.description = description
        
        credential.updated_at = datetime.now().isoformat()
        
        self.credentials[credential_id] = credential
        logger.info(f"Updated target credential: {credential_id}")
        
        return credential
    
    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete a credential.
        
        Args:
            credential_id (str): Credential ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if credential_id not in self.credentials:
            return False
        
        del self.credentials[credential_id]
        logger.info(f"Deleted target credential: {credential_id}")
        
        return True
    
    def get_environments(self, target_id: Optional[str] = None, environment_type: Optional[str] = None) -> List[TargetEnvironment]:
        """
        Get all environments, optionally filtered by target ID or environment type.
        
        Args:
            target_id (Optional[str]): Target ID to filter by
            environment_type (Optional[str]): Environment type to filter by
            
        Returns:
            List[TargetEnvironment]: List of environments
        """
        environments = list(self.environments.values())
        
        if target_id:
            environments = [e for e in environments if e.target_id == target_id]
        
        if environment_type:
            environments = [e for e in environments if e.type == environment_type]
        
        return environments
    
    def get_environment(self, environment_id: str) -> Optional[TargetEnvironment]:
        """
        Get an environment by ID.
        
        Args:
            environment_id (str): Environment ID
            
        Returns:
            Optional[TargetEnvironment]: Environment if found, None otherwise
        """
        return self.environments.get(environment_id)
    
    def create_environment(self, environment: TargetEnvironment) -> TargetEnvironment:
        """
        Create a new environment.
        
        Args:
            environment (TargetEnvironment): Environment to create
            
        Returns:
            TargetEnvironment: Created environment
        """
        if not environment.id:
            environment.id = str(uuid.uuid4())
        
        environment.created_at = datetime.now().isoformat()
        environment.updated_at = datetime.now().isoformat()
        
        self.environments[environment.id] = environment
        logger.info(f"Created target environment: {environment.id}")
        
        return environment
    
    def update_environment(self, environment_id: str, environment: TargetEnvironment) -> Optional[TargetEnvironment]:
        """
        Update an existing environment.
        
        Args:
            environment_id (str): Environment ID
            environment (TargetEnvironment): Updated environment
            
        Returns:
            Optional[TargetEnvironment]: Updated environment if found, None otherwise
        """
        if environment_id not in self.environments:
            return None
        
        environment.id = environment_id
        environment.updated_at = datetime.now().isoformat()
        
        self.environments[environment_id] = environment
        logger.info(f"Updated target environment: {environment_id}")
        
        return environment
    
    def delete_environment(self, environment_id: str) -> bool:
        """
        Delete an environment.
        
        Args:
            environment_id (str): Environment ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if environment_id not in self.environments:
            return False
        
        del self.environments[environment_id]
        logger.info(f"Deleted target environment: {environment_id}")
        
        return True
    
    def execute_operation(self, target_id: str, environment_id: str, operation_type: str, parameters: Dict[str, Any]) -> DeploymentOperation:
        """
        Execute an operation on a deployment target.
        
        Args:
            target_id (str): Target ID
            environment_id (str): Environment ID
            operation_type (str): Operation type
            parameters (Dict[str, Any]): Operation parameters
            
        Returns:
            DeploymentOperation: Created operation
        """
        # Create a new operation ID
        operation_id = str(uuid.uuid4())
        
        # Create the operation
        operation = DeploymentOperation(
            id=operation_id,
            target_id=target_id,
            environment_id=environment_id,
            type=operation_type,
            status="pending",
            parameters=parameters,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.operations[operation_id] = operation
        logger.info(f"Created deployment operation: {operation_id}")
        
        # In a real implementation, this would trigger the actual operation
        # For now, we just return the operation object
        return operation
    
    def get_operations(self, target_id: Optional[str] = None, environment_id: Optional[str] = None, status: Optional[str] = None) -> List[DeploymentOperation]:
        """
        Get all operations, optionally filtered by target ID, environment ID, or status.
        
        Args:
            target_id (Optional[str]): Target ID to filter by
            environment_id (Optional[str]): Environment ID to filter by
            status (Optional[str]): Status to filter by
            
        Returns:
            List[DeploymentOperation]: List of operations
        """
        operations = list(self.operations.values())
        
        if target_id:
            operations = [o for o in operations if o.target_id == target_id]
        
        if environment_id:
            operations = [o for o in operations if o.environment_id == environment_id]
        
        if status:
            operations = [o for o in operations if o.status == status]
        
        return operations
    
    def get_operation(self, operation_id: str) -> Optional[DeploymentOperation]:
        """
        Get an operation by ID.
        
        Args:
            operation_id (str): Operation ID
            
        Returns:
            Optional[DeploymentOperation]: Operation if found, None otherwise
        """
        return self.operations.get(operation_id)
    
    def update_operation(self, operation_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Optional[DeploymentOperation]:
        """
        Update the status of an operation.
        
        Args:
            operation_id (str): Operation ID
            status (str): New status
            result (Optional[Dict[str, Any]]): Operation result
            
        Returns:
            Optional[DeploymentOperation]: Updated operation if found, None otherwise
        """
        operation = self.get_operation(operation_id)
        if not operation:
            return None
        
        operation.status = status
        operation.updated_at = datetime.now().isoformat()
        
        if status == "running" and not operation.started_at:
            operation.started_at = datetime.now().isoformat()
        
        if status in ["completed", "failed", "cancelled"]:
            operation.completed_at = datetime.now().isoformat()
        
        if result:
            operation.result = result
        
        self.operations[operation_id] = operation
        logger.info(f"Updated deployment operation: {operation_id}, status: {status}")
        
        return operation
    
    def create_group(self, name: str, description: str, target_ids: List[str]) -> TargetGroup:
        """
        Create a group of deployment targets.
        
        Args:
            name (str): Group name
            description (str): Group description
            target_ids (List[str]): List of target IDs
            
        Returns:
            TargetGroup: Created target group
        """
        # Create a new group ID
        group_id = str(uuid.uuid4())
        
        # Create the group
        group = TargetGroup(
            id=group_id,
            name=name,
            description=description,
            target_ids=target_ids,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.groups[group_id] = group
        logger.info(f"Created target group: {group_id}")
        
        return group
    
    def get_groups(self) -> List[TargetGroup]:
        """
        Get all target groups.
        
        Returns:
            List[TargetGroup]: List of target groups
        """
        return list(self.groups.values())
    
    def get_group(self, group_id: str) -> Optional[TargetGroup]:
        """
        Get a target group by ID.
        
        Args:
            group_id (str): Group ID
            
        Returns:
            Optional[TargetGroup]: Target group if found, None otherwise
        """
        return self.groups.get(group_id)
    
    def update_group(self, group_id: str, name: Optional[str] = None, description: Optional[str] = None, target_ids: Optional[List[str]] = None) -> Optional[TargetGroup]:
        """
        Update an existing target group.
        
        Args:
            group_id (str): Group ID
            name (Optional[str]): Updated group name
            description (Optional[str]): Updated group description
            target_ids (Optional[List[str]]): Updated list of target IDs
            
        Returns:
            Optional[TargetGroup]: Updated target group if found, None otherwise
        """
        group = self.get_group(group_id)
        if not group:
            return None
        
        if name is not None:
            group.name = name
        
        if description is not None:
            group.description = description
        
        if target_ids is not None:
            group.target_ids = target_ids
        
        group.updated_at = datetime.now().isoformat()
        
        self.groups[group_id] = group
        logger.info(f"Updated target group: {group_id}")
        
        return group
    
    def delete_group(self, group_id: str) -> bool:
        """
        Delete a target group.
        
        Args:
            group_id (str): Group ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        if group_id not in self.groups:
            return False
        
        del self.groups[group_id]
        logger.info(f"Deleted target group: {group_id}")
        
        return True
    
    def check_health(self, target_id: str) -> TargetHealthStatus:
        """
        Check the health of a deployment target.
        
        Args:
            target_id (str): Target ID
            
        Returns:
            TargetHealthStatus: Target health status
        """
        # In a real implementation, this would perform actual health checks
        # For now, we just create a mock health status
        health_id = str(uuid.uuid4())
        
        health_status = TargetHealthStatus(
            id=health_id,
            target_id=target_id,
            status="healthy",
            checks=[
                {
                    "name": "Connectivity",
                    "status": "passed",
                    "details": "Target is reachable"
                },
                {
                    "name": "Authentication",
                    "status": "passed",
                    "details": "Authentication successful"
                },
                {
                    "name": "Resources",
                    "status": "passed",
                    "details": "Sufficient resources available"
                }
            ],
            timestamp=datetime.now().isoformat()
        )
        
        self.health_statuses[health_id] = health_status
        logger.info(f"Created target health status: {health_id}")
        
        return health_status
    
    def get_health_statuses(self, target_id: Optional[str] = None) -> List[TargetHealthStatus]:
        """
        Get all health statuses, optionally filtered by target ID.
        
        Args:
            target_id (Optional[str]): Target ID to filter by
            
        Returns:
            List[TargetHealthStatus]: List of health statuses
        """
        if target_id:
            return [hs for hs in self.health_statuses.values() if hs.target_id == target_id]
        else:
            return list(self.health_statuses.values())
    
    def get_health_status(self, health_id: str) -> Optional[TargetHealthStatus]:
        """
        Get a health status by ID.
        
        Args:
            health_id (str): Health status ID
            
        Returns:
            Optional[TargetHealthStatus]: Health status if found, None otherwise
        """
        return self.health_statuses.get(health_id)
    
    def get_metadata(self, target_id: str) -> Optional[TargetMetadata]:
        """
        Get metadata for a deployment target.
        
        Args:
            target_id (str): Target ID
            
        Returns:
            Optional[TargetMetadata]: Target metadata if found, None otherwise
        """
        return self.metadata.get(target_id)
    
    def set_metadata(self, target_id: str, key: str, value: Any) -> TargetMetadata:
        """
        Set metadata for a deployment target.
        
        Args:
            target_id (str): Target ID
            key (str): Metadata key
            value (Any): Metadata value
            
        Returns:
            TargetMetadata: Updated target metadata
        """
        metadata = self.get_metadata(target_id)
        if not metadata:
            metadata = TargetMetadata(
                id=target_id,
                data={},
                updated_at=datetime.now().isoformat()
            )
        
        metadata.data[key] = value
        metadata.updated_at = datetime.now().isoformat()
        
        self.metadata[target_id] = metadata
        logger.info(f"Set target metadata: {target_id}.{key}")
        
        return metadata
    
    def get_capabilities(self, target_id: str) -> List[TargetCapability]:
        """
        Get capabilities for a deployment target.
        
        Args:
            target_id (str): Target ID
            
        Returns:
            List[TargetCapability]: List of target capabilities
        """
        return [cap for cap in self.capabilities.values() if cap.target_id == target_id]
    
    def add_capability(self, target_id: str, name: str, description: str, properties: Dict[str, Any]) -> TargetCapability:
        """
        Add a capability to a deployment target.
        
        Args:
            target_id (str): Target ID
            name (str): Capability name
            description (str): Capability description
            properties (Dict[str, Any]): Capability properties
            
        Returns:
            TargetCapability: Created target capability
        """
        # Create a new capability ID
        capability_id = str(uuid.uuid4())
        
        # Create the capability
        capability = TargetCapability(
            id=capability_id,
            target_id=target_id,
            name=name,
            description=description,
            properties=properties,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.capabilities[capability_id] = capability
        logger.info(f"Added target capability: {capability_id}")
        
        return capability
    
    def remove_capability(self, capability_id: str) -> bool:
        """
        Remove a capability from a deployment target.
        
        Args:
            capability_id (str): Capability ID
            
        Returns:
            bool: True if removed, False if not found
        """
        if capability_id not in self.capabilities:
            return False
        
        del self.capabilities[capability_id]
        logger.info(f"Removed target capability: {capability_id}")
        
        return True
    
    def get_constraints(self, target_id: str) -> List[TargetConstraint]:
        """
        Get constraints for a deployment target.
        
        Args:
            target_id (str): Target ID
            
        Returns:
            List[TargetConstraint]: List of target constraints
        """
        return [con for con in self.constraints.values() if con.target_id == target_id]
    
    def add_constraint(self, target_id: str, name: str, description: str, rule: Dict[str, Any]) -> TargetConstraint:
        """
        Add a constraint to a deployment target.
        
        Args:
            target_id (str): Target ID
            name (str): Constraint name
            description (str): Constraint description
            rule (Dict[str, Any]): Constraint rule
            
        Returns:
            TargetConstraint: Created target constraint
        """
        # Create a new constraint ID
        constraint_id = str(uuid.uuid4())
        
        # Create the constraint
        constraint = TargetConstraint(
            id=constraint_id,
            target_id=target_id,
            name=name,
            description=description,
            rule=rule,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.constraints[constraint_id] = constraint
        logger.info(f"Added target constraint: {constraint_id}")
        
        return constraint
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """
        Remove a constraint from a deployment target.
        
        Args:
            constraint_id (str): Constraint ID
            
        Returns:
            bool: True if removed, False if not found
        """
        if constraint_id not in self.constraints:
            return False
        
        del self.constraints[constraint_id]
        logger.info(f"Removed target constraint: {constraint_id}")
        
        return True
