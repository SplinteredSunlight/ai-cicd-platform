import os
import yaml
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import uuid

from ..models.policy import (
    Policy,
    PolicyRule,
    PolicyType,
    PolicySeverity,
    PolicyEnforcementMode,
    PolicyStatus,
    PolicyEnvironment
)

logger = structlog.get_logger()

class PolicyTemplates:
    """
    Service for managing policy templates
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the policy templates service
        
        Args:
            template_dir: Directory containing policy templates
        """
        self.template_dir = template_dir or os.environ.get('POLICY_TEMPLATE_DIR', '/etc/security-policies/templates')
        
        # Create template directory if it doesn't exist
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Load built-in templates
        self.templates = self._load_built_in_templates()
        
        # Load custom templates
        self._load_custom_templates()
    
    def _load_built_in_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load built-in policy templates
        
        Returns:
            Dictionary of policy templates
        """
        # Define built-in templates
        return {
            # Security Templates
            'secure-container': self._create_secure_container_template(),
            'secure-kubernetes': self._create_secure_kubernetes_template(),
            'secure-cloud': self._create_secure_cloud_template(),
            'secure-web-app': self._create_secure_web_app_template(),
            'secure-api': self._create_secure_api_template(),
            
            # Compliance Templates
            'pci-dss': self._create_pci_dss_template(),
            'hipaa': self._create_hipaa_template(),
            'gdpr': self._create_gdpr_template(),
            'nist-800-53': self._create_nist_template(),
            'soc2': self._create_soc2_template(),
            
            # Operational Templates
            'resource-limits': self._create_resource_limits_template(),
            'high-availability': self._create_high_availability_template(),
            'disaster-recovery': self._create_disaster_recovery_template(),
            'monitoring': self._create_monitoring_template(),
            'logging': self._create_logging_template()
        }
    
    def _load_custom_templates(self):
        """
        Load custom policy templates from the template directory
        """
        try:
            if not os.path.exists(self.template_dir):
                return
            
            template_files = [f for f in os.listdir(self.template_dir) if f.endswith(('.yaml', '.yml'))]
            
            for filename in template_files:
                try:
                    file_path = os.path.join(self.template_dir, filename)
                    
                    with open(file_path, 'r') as f:
                        template_data = yaml.safe_load(f.read())
                        
                        # Extract template ID
                        template_id = template_data.get('id')
                        if not template_id:
                            logger.warning("Template missing ID", file=filename)
                            continue
                        
                        # Add to templates
                        self.templates[template_id] = template_data
                        logger.info("Loaded custom template", template_id=template_id, file=filename)
                
                except Exception as e:
                    logger.error("Failed to load template", file=filename, error=str(e))
        
        except Exception as e:
            logger.error("Failed to load custom templates", error=str(e))
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a policy template by ID
        
        Args:
            template_id: ID of the template
            
        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        template_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List policy templates with optional filtering
        
        Args:
            template_type: Optional template type to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            List of template dictionaries
        """
        templates = []
        
        for template_id, template in self.templates.items():
            # Apply filters
            if template_type and template.get('type') != template_type:
                continue
            
            if tags:
                template_tags = template.get('tags', [])
                if not all(tag in template_tags for tag in tags):
                    continue
            
            # Add to list
            templates.append(template)
        
        return templates
    
    def create_policy_from_template(
        self,
        template_id: str,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a policy from a template
        
        Args:
            template_id: ID of the template
            name: Name for the new policy
            description: Description for the new policy
            parameters: Optional parameters to customize the policy
            
        Returns:
            Policy dictionary
        """
        # Get template
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Create policy ID
        policy_id = f"policy-{uuid.uuid4()}"
        
        # Create policy from template
        policy = {
            'id': policy_id,
            'name': name,
            'description': description,
            'type': template.get('type', 'security'),
            'enforcement_mode': template.get('enforcement_mode', 'warning'),
            'status': 'active',
            'environments': template.get('environments', ['all']),
            'tags': template.get('tags', []),
            'version': '1.0.0',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'template_id': template_id,
            'rules': self._customize_rules(template.get('rules', []), parameters or {})
        }
        
        return policy
    
    def _customize_rules(
        self,
        rules: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Customize rules with parameters
        
        Args:
            rules: List of rule dictionaries
            parameters: Parameters to customize the rules
            
        Returns:
            List of customized rule dictionaries
        """
        customized_rules = []
        
        for rule in rules:
            # Create a copy of the rule
            customized_rule = rule.copy()
            
            # Generate a new rule ID
            customized_rule['id'] = f"rule-{uuid.uuid4()}"
            
            # Apply parameters
            for param_key, param_value in parameters.items():
                # Check if this parameter applies to this rule
                if param_key.startswith('rule.') and '.' in param_key[5:]:
                    # Extract rule name and field
                    parts = param_key.split('.')
                    if len(parts) >= 3:
                        rule_name = parts[1]
                        field = '.'.join(parts[2:])
                        
                        # Check if this parameter applies to this rule
                        if rule.get('name') == rule_name:
                            # Apply parameter
                            self._set_nested_field(customized_rule, field, param_value)
                
                # Check if this is a global parameter
                elif param_key.startswith('global.'):
                    field = param_key[7:]
                    self._set_nested_field(customized_rule, field, param_value)
            
            customized_rules.append(customized_rule)
        
        return customized_rules
    
    def _set_nested_field(self, obj: Dict[str, Any], field: str, value: Any):
        """
        Set a nested field in a dictionary
        
        Args:
            obj: Dictionary to modify
            field: Dot-separated field path
            value: Value to set
        """
        parts = field.split('.')
        current = obj
        
        # Navigate to the parent of the field
        for i in range(len(parts) - 1):
            part = parts[i]
            
            if part not in current:
                current[part] = {}
            
            current = current[part]
        
        # Set the field
        current[parts[-1]] = value
    
    def save_custom_template(self, template: Dict[str, Any]) -> str:
        """
        Save a custom policy template
        
        Args:
            template: Template dictionary
            
        Returns:
            Path to the saved template file
        """
        # Ensure template has an ID
        if 'id' not in template:
            template['id'] = f"template-{uuid.uuid4()}"
        
        # Generate filename
        filename = f"{template['id']}.yaml"
        file_path = os.path.join(self.template_dir, filename)
        
        # Write template to file
        with open(file_path, 'w') as f:
            yaml.dump(template, f, sort_keys=False)
        
        # Add to templates
        self.templates[template['id']] = template
        
        logger.info("Saved custom template", template_id=template['id'], file=file_path)
        
        return file_path
    
    def delete_custom_template(self, template_id: str) -> bool:
        """
        Delete a custom policy template
        
        Args:
            template_id: ID of the template
            
        Returns:
            True if successful, False otherwise
        """
        # Check if template exists
        if template_id not in self.templates:
            return False
        
        # Find template file
        filename = f"{template_id}.yaml"
        file_path = os.path.join(self.template_dir, filename)
        
        if not os.path.exists(file_path):
            # Try to find the file
            for f in os.listdir(self.template_dir):
                if f.endswith(('.yaml', '.yml')):
                    try:
                        with open(os.path.join(self.template_dir, f), 'r') as file:
                            data = yaml.safe_load(file.read())
                            if data.get('id') == template_id:
                                file_path = os.path.join(self.template_dir, f)
                                break
                    except:
                        pass
        
        # Delete template file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from templates
        if template_id in self.templates:
            del self.templates[template_id]
        
        logger.info("Deleted custom template", template_id=template_id)
        
        return True
    
    def _create_secure_container_template(self) -> Dict[str, Any]:
        """
        Create a template for secure container policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-container',
            'name': 'Secure Container Policy',
            'description': 'Policy for securing container images and runtime',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['container', 'security', 'docker', 'kubernetes'],
            'rules': [
                {
                    'name': 'no-privileged-containers',
                    'description': 'Containers should not run in privileged mode',
                    'severity': 'critical',
                    'condition': {
                        'field': 'container.privileged',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove the privileged flag from container configuration',
                        'Use more specific capabilities instead of privileged mode'
                    ]
                },
                {
                    'name': 'no-root-containers',
                    'description': 'Containers should not run as root',
                    'severity': 'high',
                    'condition': {
                        'field': 'container.user',
                        'operator': 'not_equals',
                        'value': 'root'
                    },
                    'remediation_steps': [
                        'Set a non-root user in the container configuration',
                        'Use USER directive in Dockerfile to specify a non-root user'
                    ]
                },
                {
                    'name': 'read-only-root-filesystem',
                    'description': 'Container root filesystem should be read-only',
                    'severity': 'medium',
                    'condition': {
                        'field': 'container.read_only_root_filesystem',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Set readOnlyRootFilesystem to true in container security context',
                        'Mount specific directories as writable volumes if needed'
                    ]
                },
                {
                    'name': 'no-latest-tag',
                    'description': 'Container images should not use the latest tag',
                    'severity': 'medium',
                    'condition': {
                        'field': 'container.image.tag',
                        'operator': 'not_equals',
                        'value': 'latest'
                    },
                    'remediation_steps': [
                        'Use specific version tags for container images',
                        'Implement a versioning strategy for container images'
                    ]
                },
                {
                    'name': 'drop-capabilities',
                    'description': 'Container should drop all capabilities and only add required ones',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'container.capabilities.drop',
                                'operator': 'contains',
                                'value': 'ALL'
                            },
                            {
                                'field': 'container.capabilities.add',
                                'operator': 'not_contains',
                                'value': 'NET_ADMIN'
                            },
                            {
                                'field': 'container.capabilities.add',
                                'operator': 'not_contains',
                                'value': 'SYS_ADMIN'
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Drop ALL capabilities and only add the specific ones required',
                        'Review container capabilities and remove unnecessary ones'
                    ]
                }
            ]
        }
    
    def _create_secure_kubernetes_template(self) -> Dict[str, Any]:
        """
        Create a template for secure Kubernetes policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-kubernetes',
            'name': 'Secure Kubernetes Policy',
            'description': 'Policy for securing Kubernetes deployments',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['kubernetes', 'security', 'k8s'],
            'rules': [
                {
                    'name': 'no-host-network',
                    'description': 'Pods should not use host network',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.host_network',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove hostNetwork: true from pod specification',
                        'Use Kubernetes networking instead of host networking'
                    ]
                },
                {
                    'name': 'no-host-pid',
                    'description': 'Pods should not use host PID namespace',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.host_pid',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove hostPID: true from pod specification',
                        'Use pod-level PID namespace instead of host PID namespace'
                    ]
                },
                {
                    'name': 'no-host-ipc',
                    'description': 'Pods should not use host IPC namespace',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.host_ipc',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove hostIPC: true from pod specification',
                        'Use pod-level IPC namespace instead of host IPC namespace'
                    ]
                },
                {
                    'name': 'run-as-non-root',
                    'description': 'Pods should run as non-root user',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.security_context.run_as_non_root',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Set runAsNonRoot: true in pod security context',
                        'Specify a non-root user ID in runAsUser field'
                    ]
                },
                {
                    'name': 'network-policy-defined',
                    'description': 'Namespaces should have network policies defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'kubernetes.namespace.network_policies',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define network policies for each namespace',
                        'Implement default deny policies and explicitly allow required traffic'
                    ]
                }
            ]
        }
    
    def _create_secure_cloud_template(self) -> Dict[str, Any]:
        """
        Create a template for secure cloud policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-cloud',
            'name': 'Secure Cloud Policy',
            'description': 'Policy for securing cloud resources',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['cloud', 'security', 'aws', 'azure', 'gcp'],
            'rules': [
                {
                    'name': 'encrypt-data-at-rest',
                    'description': 'Cloud storage should be encrypted at rest',
                    'severity': 'high',
                    'condition': {
                        'field': 'cloud.storage.encrypted',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable encryption at rest for cloud storage services',
                        'Use customer-managed encryption keys where possible'
                    ]
                },
                {
                    'name': 'secure-network-acls',
                    'description': 'Network ACLs should not allow unrestricted access',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'cloud.network.acl.allow_all_ingress',
                                'operator': 'equals',
                                'value': False
                            },
                            {
                                'field': 'cloud.network.acl.allow_all_egress',
                                'operator': 'equals',
                                'value': False
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Remove 0.0.0.0/0 ingress rules from security groups',
                        'Implement least privilege network access controls'
                    ]
                },
                {
                    'name': 'mfa-enabled',
                    'description': 'Multi-factor authentication should be enabled for all users',
                    'severity': 'critical',
                    'condition': {
                        'field': 'cloud.iam.users.mfa_enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable MFA for all IAM users',
                        'Implement MFA enforcement policies'
                    ]
                },
                {
                    'name': 'logging-enabled',
                    'description': 'Logging and monitoring should be enabled',
                    'severity': 'high',
                    'condition': {
                        'field': 'cloud.logging.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable CloudTrail/Activity Logs/Cloud Audit Logs',
                        'Configure log retention policies'
                    ]
                },
                {
                    'name': 'no-public-access',
                    'description': 'Cloud resources should not be publicly accessible',
                    'severity': 'critical',
                    'condition': {
                        'field': 'cloud.resource.public_access',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove public access from cloud resources',
                        'Implement private endpoints for accessing cloud services'
                    ]
                }
            ]
        }
    
    def _create_secure_web_app_template(self) -> Dict[str, Any]:
        """
        Create a template for secure web application policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-web-app',
            'name': 'Secure Web Application Policy',
            'description': 'Policy for securing web applications',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['web', 'security', 'application'],
            'rules': [
                {
                    'name': 'https-only',
                    'description': 'Web applications should use HTTPS only',
                    'severity': 'critical',
                    'condition': {
                        'field': 'webapp.protocols',
                        'operator': 'equals',
                        'value': ['https']
                    },
                    'remediation_steps': [
                        'Configure HTTPS for all web applications',
                        'Implement HSTS headers',
                        'Redirect HTTP to HTTPS'
                    ]
                },
                {
                    'name': 'secure-cookies',
                    'description': 'Cookies should have secure and httpOnly flags',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'webapp.cookies.secure',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'webapp.cookies.httpOnly',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Set secure and httpOnly flags for all cookies',
                        'Implement SameSite cookie attribute'
                    ]
                },
                {
                    'name': 'content-security-policy',
                    'description': 'Content Security Policy should be implemented',
                    'severity': 'high',
                    'condition': {
                        'field': 'webapp.headers.content_security_policy',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Implement Content Security Policy headers',
                        'Use strict CSP directives to prevent XSS attacks'
                    ]
                },
                {
                    'name': 'no-exposed-sensitive-data',
                    'description': 'Sensitive data should not be exposed in URLs or logs',
                    'severity': 'critical',
                    'condition': {
                        'field': 'webapp.exposed_sensitive_data',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove sensitive data from URLs',
                        'Implement proper data masking in logs',
                        'Use POST requests for sensitive operations'
                    ]
                },
                {
                    'name': 'input-validation',
                    'description': 'All user input should be validated',
                    'severity': 'critical',
                    'condition': {
                        'field': 'webapp.input_validation',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement server-side input validation',
                        'Use parameterized queries for database operations',
                        'Sanitize user input to prevent injection attacks'
                    ]
                }
            ]
        }
    
    def _create_secure_api_template(self) -> Dict[str, Any]:
        """
        Create a template for secure API policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-api',
            'name': 'Secure API Policy',
            'description': 'Policy for securing APIs',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['api', 'security', 'rest', 'graphql'],
            'rules': [
                {
                    'name': 'api-authentication',
                    'description': 'APIs should require authentication',
                    'severity': 'critical',
                    'condition': {
                        'field': 'api.authentication.required',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement authentication for all API endpoints',
                        'Use OAuth 2.0 or API keys for authentication'
                    ]
                },
                {
                    'name': 'api-rate-limiting',
                    'description': 'APIs should implement rate limiting',
                    'severity': 'high',
                    'condition': {
                        'field': 'api.rate_limiting.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement rate limiting for API endpoints',
                        'Configure appropriate rate limits based on endpoint sensitivity'
                    ]
                },
                {
                    'name': 'api-input-validation',
                    'description': 'APIs should validate all input parameters',
                    'severity': 'critical',
                    'condition': {
                        'field': 'api.input_validation',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement input validation for all API parameters',
                        'Use schema validation for request bodies'
                    ]
                },
                {
                    'name': 'api-https-only',
                    'description': 'APIs should use HTTPS only',
                    'severity': 'critical',
                    'condition': {
                        'field': 'api.protocols',
                        'operator': 'equals',
                        'value': ['https']
                    },
                    'remediation_steps': [
                        'Configure HTTPS for all API endpoints',
                        'Reject non-HTTPS requests'
                    ]
                },
                {
                    'name': 'api-security-headers',
                    'description': 'APIs should include security headers',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'api.headers.x_content_type_options',
                                'operator': 'exists'
                            },
                            {
                                'field': 'api.headers.x_frame_options',
                                'operator': 'exists'
                            },
                            {
                                'field': 'api.headers.x_xss_protection',
                                'operator': 'exists'
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Add security headers to API responses',
                        'Configure API gateway to add security headers'
                    ]
                }
            ]
        }
    
    def _create_pci_dss_template(self) -> Dict[str, Any]:
        """
        Create a template for PCI DSS compliance policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'pci-dss',
            'name': 'PCI DSS Compliance Policy',
            'description': 'Policy for ensuring compliance with Payment Card Industry Data Security Standard',
            'type': 'compliance',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['compliance', 'pci-dss', 'security'],
            'rules': [
                {
                    'name': 'pci-dss-req-1',
                    'description': 'Install and maintain network security controls',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'network.firewall.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'network.firewall.rules.default_deny',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement and configure firewalls between all wireless networks and the cardholder data environment',
                        'Maintain a current network diagram that documents all connections between the cardholder data environment and other networks'
                    ]
                },
                {
                    'name': 'pci-dss-req-2',
                    'description': 'Apply secure configurations to all system components',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.secure_configuration',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.default_accounts.changed',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement secure configuration standards for all system components',
                        'Change default passwords and other security parameters'
                    ]
                },
                {
                    'name': 'pci-dss-req-3',
                    'description': 'Protect stored account data',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'data.encryption.at_rest',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'data.pci.pan.masked',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Keep cardholder data storage to a minimum',
                        'Mask PAN when displayed',
                        'Render PAN unreadable anywhere it is stored'
                    ]
                },
                {
                    'name': 'pci-dss-req-4',
                    'description': 'Protect cardholder data with strong cryptography during transmission',
                    'severity': 'critical',
                    'condition': {
                        'field': 'data.encryption.in_transit',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Use strong cryptography and security protocols to safeguard sensitive cardholder data during transmission',
                        'Never send unprotected PANs by end-user messaging technologies'
                    ]
                }
            ]
        }
    
    def _create_hipaa_template(self) -> Dict[str, Any]:
        """
        Create a template for HIPAA compliance policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'hipaa',
            'name': 'HIPAA Compliance Policy',
            'description': 'Policy for ensuring compliance with Health Insurance Portability and Accountability Act',
            'type': 'compliance',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['compliance', 'hipaa', 'security', 'healthcare'],
            'rules': [
                {
                    'name': 'hipaa-access-control',
                    'description': 'Implement technical policies and procedures for electronic PHI access control',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.access_control.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.access_control.unique_user_identification',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement unique user identification mechanisms',
                        'Establish procedures for obtaining necessary ePHI during an emergency',
                        'Implement automatic logoff after a specific period of inactivity'
                    ]
                },
                {
                    'name': 'hipaa-audit-controls',
                    'description': 'Implement hardware, software, and procedural audit controls',
                    'severity': 'high',
                    'condition': {
                        'field': 'system.audit_controls.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement activity logging for all systems that contain ePHI',
                        'Regularly review audit logs for suspicious activity',
                        'Establish procedures for audit control monitoring'
                    ]
                },
                {
                    'name': 'hipaa-data-integrity',
                    'description': 'Implement policies to protect ePHI from improper alteration or destruction',
                    'severity': 'high',
                    'condition': {
                        'field': 'data.integrity_controls.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement electronic mechanisms to confirm that ePHI has not been altered or destroyed',
                        'Use digital signatures or checksums to verify data integrity',
                        'Implement access controls to prevent unauthorized modification of data'
                    ]
                },
                {
                    'name': 'hipaa-transmission-security',
                    'description': 'Implement technical security measures to guard against unauthorized access to ePHI transmitted over networks',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'data.encryption.in_transit',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'network.transmission_security.integrity_controls',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Encrypt ePHI whenever it is transmitted over networks',
                        'Implement integrity controls to ensure that transmitted ePHI is not improperly modified',
                        'Use secure protocols for all network communications containing ePHI'
                    ]
                }
            ]
        }
    
    def _create_gdpr_template(self) -> Dict[str, Any]:
        """
        Create a template for GDPR compliance policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'gdpr',
            'name': 'GDPR Compliance Policy',
            'description': 'Policy for ensuring compliance with General Data Protection Regulation',
            'type': 'compliance',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['compliance', 'gdpr', 'security', 'privacy', 'eu'],
            'rules': [
                {
                    'name': 'gdpr-data-minimization',
                    'description': 'Ensure personal data is adequate, relevant and limited to what is necessary',
                    'severity': 'high',
                    'condition': {
                        'field': 'data.gdpr.minimization',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Review data collection practices to ensure only necessary data is collected',
                        'Implement data minimization policies',
                        'Regularly audit stored personal data and remove unnecessary information'
                    ]
                },
                {
                    'name': 'gdpr-consent',
                    'description': 'Ensure valid consent is obtained for processing personal data',
                    'severity': 'critical',
                    'condition': {
                        'field': 'data.gdpr.consent.valid',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement clear consent mechanisms',
                        'Ensure consent is freely given, specific, informed and unambiguous',
                        'Maintain records of consent'
                    ]
                },
                {
                    'name': 'gdpr-right-to-access',
                    'description': 'Ensure individuals can access their personal data',
                    'severity': 'high',
                    'condition': {
                        'field': 'data.gdpr.right_to_access.implemented',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement mechanisms for individuals to request access to their data',
                        'Ensure systems can provide complete exports of personal data',
                        'Establish procedures for responding to access requests within required timeframes'
                    ]
                },
                {
                    'name': 'gdpr-right-to-erasure',
                    'description': 'Ensure individuals can request erasure of their personal data',
                    'severity': 'high',
                    'condition': {
                        'field': 'data.gdpr.right_to_erasure.implemented',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement mechanisms for individuals to request erasure of their data',
                        'Ensure systems can completely remove personal data when requested',
                        'Establish procedures for responding to erasure requests within required timeframes'
                    ]
                },
                {
                    'name': 'gdpr-data-protection',
                    'description': 'Implement appropriate technical and organizational measures to protect personal data',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'data.encryption.at_rest',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'data.encryption.in_transit',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.access_control.enabled',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Encrypt personal data at rest and in transit',
                        'Implement strong access controls',
                        'Regularly test security measures',
                        'Implement data protection by design and by default'
                    ]
                }
            ]
        }
    
    def _create_nist_template(self) -> Dict[str, Any]:
        """
        Create a template for NIST 800-53 compliance policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'nist-800-53',
            'name': 'NIST 800-53 Compliance Policy',
            'description': 'Policy for ensuring compliance with NIST Special Publication 800-53',
            'type': 'compliance',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['compliance', 'nist', 'security', 'federal'],
            'rules': [
                {
                    'name': 'nist-access-control',
                    'description': 'Implement access control policies and procedures',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.access_control.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.access_control.least_privilege',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Develop and document access control policies',
                        'Implement least privilege principles',
                        'Enforce separation of duties',
                        'Review and update access control policies regularly'
                    ]
                },
                {
                    'name': 'nist-audit-accountability',
                    'description': 'Implement audit and accountability controls',
                    'severity': 'high',
                    'condition': {
                        'field': 'system.audit.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement audit logging for all system components',
                        'Ensure audit logs capture required information',
                        'Protect audit information from unauthorized access',
                        'Establish audit review, analysis, and reporting processes'
                    ]
                },
                {
                    'name': 'nist-configuration-management',
                    'description': 'Implement configuration management controls',
                    'severity': 'medium',
                    'condition': {
                        'field': 'system.configuration_management.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Establish baseline configurations for all system components',
                        'Implement configuration change control processes',
                        'Monitor configuration changes',
                        'Use automated tools for configuration management'
                    ]
                },
                {
                    'name': 'nist-identification-authentication',
                    'description': 'Implement identification and authentication controls',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.authentication.multi_factor',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.authentication.unique_identification',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement multi-factor authentication',
                        'Ensure unique identification for all users',
                        'Implement strong password policies',
                        'Manage authenticators securely'
                    ]
                },
                {
                    'name': 'nist-system-protection',
                    'description': 'Implement system and communications protection',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.boundary_protection.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'data.encryption.in_transit',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement boundary protection mechanisms',
                        'Encrypt data in transit',
                        'Implement secure architecture principles',
                        'Protect against denial of service attacks'
                    ]
                }
            ]
        }
    
    def _create_soc2_template(self) -> Dict[str, Any]:
        """
        Create a template for SOC 2 compliance policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'soc2',
            'name': 'SOC 2 Compliance Policy',
            'description': 'Policy for ensuring compliance with SOC 2 Trust Services Criteria',
            'type': 'compliance',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['compliance', 'soc2', 'security', 'trust'],
            'rules': [
                {
                    'name': 'soc2-security',
                    'description': 'Implement controls to protect against unauthorized access',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.access_control.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.encryption.enabled',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement access controls for all system components',
                        'Encrypt sensitive data at rest and in transit',
                        'Implement security monitoring and incident response procedures',
                        'Conduct regular security assessments'
                    ]
                },
                {
                    'name': 'soc2-availability',
                    'description': 'Implement controls to ensure system availability',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.availability.monitoring',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.disaster_recovery.enabled',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement system monitoring and alerting',
                        'Develop and test disaster recovery plans',
                        'Implement redundancy for critical systems',
                        'Establish incident response procedures'
                    ]
                },
                {
                    'name': 'soc2-processing-integrity',
                    'description': 'Implement controls to ensure processing integrity',
                    'severity': 'high',
                    'condition': {
                        'field': 'system.processing_integrity.controls',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement input validation controls',
                        'Establish data processing monitoring',
                        'Implement error handling procedures',
                        'Conduct regular quality assurance testing'
                    ]
                },
                {
                    'name': 'soc2-confidentiality',
                    'description': 'Implement controls to protect confidential information',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'data.classification.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'data.retention.policies',
                                'operator': 'exists'
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement data classification policies',
                        'Establish data retention and disposal procedures',
                        'Implement confidentiality agreements',
                        'Encrypt confidential information'
                    ]
                },
                {
                    'name': 'soc2-privacy',
                    'description': 'Implement controls to protect personal information',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'data.privacy.notice',
                                'operator': 'exists'
                            },
                            {
                                'field': 'data.privacy.choice',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Develop and publish privacy notices',
                        'Implement mechanisms for user choice and consent',
                        'Establish procedures for access to personal information',
                        'Implement controls to protect personal information'
                    ]
                }
            ]
        }
    
    def _create_resource_limits_template(self) -> Dict[str, Any]:
        """
        Create a template for resource limits policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'resource-limits',
            'name': 'Resource Limits Policy',
            'description': 'Policy for ensuring proper resource limits are defined',
            'type': 'operational',
            'enforcement_mode': 'warning',
            'environments': ['all'],
            'tags': ['operational', 'resources', 'kubernetes', 'cloud'],
            'rules': [
                {
                    'name': 'cpu-limits',
                    'description': 'CPU limits should be defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'resources.limits.cpu',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define CPU limits in resource specifications',
                        'Set appropriate CPU limits based on application requirements',
                        'Monitor CPU usage to determine appropriate limits'
                    ]
                },
                {
                    'name': 'memory-limits',
                    'description': 'Memory limits should be defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'resources.limits.memory',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define memory limits in resource specifications',
                        'Set appropriate memory limits based on application requirements',
                        'Monitor memory usage to determine appropriate limits'
                    ]
                },
                {
                    'name': 'cpu-requests',
                    'description': 'CPU requests should be defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'resources.requests.cpu',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define CPU requests in resource specifications',
                        'Set appropriate CPU requests based on application requirements',
                        'Monitor CPU usage to determine appropriate requests'
                    ]
                },
                {
                    'name': 'memory-requests',
                    'description': 'Memory requests should be defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'resources.requests.memory',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define memory requests in resource specifications',
                        'Set appropriate memory requests based on application requirements',
                        'Monitor memory usage to determine appropriate requests'
                    ]
                },
                {
                    'name': 'storage-limits',
                    'description': 'Storage limits should be defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'resources.limits.storage',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define storage limits in resource specifications',
                        'Set appropriate storage limits based on application requirements',
                        'Monitor storage usage to determine appropriate limits'
                    ]
                }
            ]
        }
    
    def _create_high_availability_template(self) -> Dict[str, Any]:
        """
        Create a template for high availability policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'high-availability',
            'name': 'High Availability Policy',
            'description': 'Policy for ensuring high availability of systems',
            'type': 'operational',
            'enforcement_mode': 'warning',
            'environments': ['production', 'staging'],
            'tags': ['operational', 'availability', 'kubernetes', 'cloud'],
            'rules': [
                {
                    'name': 'multiple-replicas',
                    'description': 'Services should have multiple replicas',
                    'severity': 'high',
                    'condition': {
                        'field': 'deployment.replicas',
                        'operator': 'greater_than',
                        'value': 1
                    },
                    'remediation_steps': [
                        'Configure multiple replicas for services',
                        'Use deployment controllers that support multiple replicas',
                        'Ensure replicas are distributed across different nodes'
                    ]
                },
                {
                    'name': 'pod-anti-affinity',
                    'description': 'Pods should use anti-affinity to avoid co-location',
                    'severity': 'medium',
                    'condition': {
                        'field': 'deployment.pod_anti_affinity',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Configure pod anti-affinity rules',
                        'Ensure pods are distributed across different nodes',
                        'Use topology spread constraints for advanced distribution'
                    ]
                },
                {
                    'name': 'multi-az',
                    'description': 'Services should be deployed across multiple availability zones',
                    'severity': 'high',
                    'condition': {
                        'field': 'deployment.multi_az',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Configure deployments to span multiple availability zones',
                        'Use node selectors or affinity rules to distribute across zones',
                        'Ensure load balancers distribute traffic across all zones'
                    ]
                },
                {
                    'name': 'health-checks',
                    'description': 'Services should have health checks defined',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'deployment.liveness_probe',
                                'operator': 'exists'
                            },
                            {
                                'field': 'deployment.readiness_probe',
                                'operator': 'exists'
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Configure liveness probes to detect and restart failed containers',
                        'Configure readiness probes to determine when a container is ready to accept traffic',
                        'Set appropriate probe parameters based on application characteristics'
                    ]
                },
                {
                    'name': 'auto-scaling',
                    'description': 'Services should have auto-scaling configured',
                    'severity': 'medium',
                    'condition': {
                        'field': 'deployment.auto_scaling',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Configure horizontal pod autoscaling',
                        'Set appropriate scaling metrics and thresholds',
                        'Test autoscaling behavior under load'
                    ]
                }
            ]
        }
    
    def _create_disaster_recovery_template(self) -> Dict[str, Any]:
        """
        Create a template for disaster recovery policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'disaster-recovery',
            'name': 'Disaster Recovery Policy',
            'description': 'Policy for ensuring proper disaster recovery capabilities',
            'type': 'operational',
            'enforcement_mode': 'warning',
            'environments': ['production'],
            'tags': ['operational', 'disaster-recovery', 'backup', 'cloud'],
            'rules': [
                {
                    'name': 'regular-backups',
                    'description': 'Regular backups should be configured',
                    'severity': 'critical',
                    'condition': {
                        'field': 'backup.schedule',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Configure regular automated backups',
                        'Set appropriate backup frequency based on data criticality',
                        'Ensure backup processes are monitored and alerts are configured for failures'
                    ]
                },
                {
                    'name': 'backup-encryption',
                    'description': 'Backups should be encrypted',
                    'severity': 'high',
                    'condition': {
                        'field': 'backup.encryption',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable encryption for all backups',
                        'Use strong encryption keys and secure key management',
                        'Regularly rotate encryption keys'
                    ]
                },
                {
                    'name': 'backup-testing',
                    'description': 'Backup restoration should be regularly tested',
                    'severity': 'high',
                    'condition': {
                        'field': 'backup.testing',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Establish a regular schedule for testing backup restoration',
                        'Document backup restoration procedures',
                        'Verify data integrity after restoration'
                    ]
                },
                {
                    'name': 'multi-region-backups',
                    'description': 'Backups should be stored in multiple regions',
                    'severity': 'high',
                    'condition': {
                        'field': 'backup.multi_region',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Configure cross-region backup replication',
                        'Ensure backup storage in regions separate from primary data',
                        'Verify backup availability in secondary regions'
                    ]
                },
                {
                    'name': 'recovery-plan',
                    'description': 'Disaster recovery plan should be documented',
                    'severity': 'critical',
                    'condition': {
                        'field': 'disaster_recovery.plan',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Document comprehensive disaster recovery procedures',
                        'Define recovery time objectives (RTO) and recovery point objectives (RPO)',
                        'Regularly review and update the disaster recovery plan'
                    ]
                }
            ]
        }
    
    def _create_monitoring_template(self) -> Dict[str, Any]:
        """
        Create a template for monitoring policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'monitoring',
            'name': 'Monitoring Policy',
            'description': 'Policy for ensuring proper monitoring of systems',
            'type': 'operational',
            'enforcement_mode': 'warning',
            'environments': ['all'],
            'tags': ['operational', 'monitoring', 'observability', 'cloud'],
            'rules': [
                {
                    'name': 'metrics-collection',
                    'description': 'Metrics collection should be enabled',
                    'severity': 'high',
                    'condition': {
                        'field': 'monitoring.metrics.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Configure metrics collection for all services',
                        'Use a metrics collection system like Prometheus',
                        'Define appropriate metrics based on service characteristics'
                    ]
                },
                {
                    'name': 'alerting',
                    'description': 'Alerting should be configured',
                    'severity': 'high',
                    'condition': {
                        'field': 'monitoring.alerting.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Configure alerts for critical metrics',
                        'Define appropriate alert thresholds',
                        'Ensure alerts are routed to the right teams'
                    ]
                },
                {
                    'name': 'dashboards',
                    'description': 'Monitoring dashboards should be configured',
                    'severity': 'medium',
                    'condition': {
                        'field': 'monitoring.dashboards',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Create dashboards for visualizing system metrics',
                        'Include key performance indicators in dashboards',
                        'Make dashboards accessible to relevant teams'
                    ]
                },
                {
                    'name': 'health-checks',
                    'description': 'Health checks should be configured',
                    'severity': 'high',
                    'condition': {
                        'field': 'monitoring.health_checks.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation
import os
import yaml
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import uuid

from ..models.policy import (
    Policy,
    PolicyRule,
    PolicyType,
    PolicySeverity,
    PolicyEnforcementMode,
    PolicyStatus,
    PolicyEnvironment
)

logger = structlog.get_logger()

class PolicyTemplates:
    """
    Service for managing policy templates
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the policy templates service
        
        Args:
            template_dir: Directory containing policy templates
        """
        self.template_dir = template_dir or os.environ.get('POLICY_TEMPLATE_DIR', '/etc/security-policies/templates')
        
        # Create template directory if it doesn't exist
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Load built-in templates
        self.templates = self._load_built_in_templates()
        
        # Load custom templates
        self._load_custom_templates()
    
    def _load_built_in_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load built-in policy templates
        
        Returns:
            Dictionary of policy templates
        """
        # Define built-in templates
        return {
            # Security Templates
            'secure-container': self._create_secure_container_template(),
            'secure-kubernetes': self._create_secure_kubernetes_template(),
            'secure-cloud': self._create_secure_cloud_template(),
            'secure-web-app': self._create_secure_web_app_template(),
            'secure-api': self._create_secure_api_template(),
            
            # Compliance Templates
            'pci-dss': self._create_pci_dss_template(),
            'hipaa': self._create_hipaa_template(),
            'gdpr': self._create_gdpr_template(),
            'nist-800-53': self._create_nist_template(),
            'soc2': self._create_soc2_template(),
            
            # Operational Templates
            'resource-limits': self._create_resource_limits_template(),
            'high-availability': self._create_high_availability_template(),
            'disaster-recovery': self._create_disaster_recovery_template(),
            'monitoring': self._create_monitoring_template(),
            'logging': self._create_logging_template()
        }
    
    def _load_custom_templates(self):
        """
        Load custom policy templates from the template directory
        """
        try:
            if not os.path.exists(self.template_dir):
                return
            
            template_files = [f for f in os.listdir(self.template_dir) if f.endswith(('.yaml', '.yml'))]
            
            for filename in template_files:
                try:
                    file_path = os.path.join(self.template_dir, filename)
                    
                    with open(file_path, 'r') as f:
                        template_data = yaml.safe_load(f.read())
                        
                        # Extract template ID
                        template_id = template_data.get('id')
                        if not template_id:
                            logger.warning("Template missing ID", file=filename)
                            continue
                        
                        # Add to templates
                        self.templates[template_id] = template_data
                        logger.info("Loaded custom template", template_id=template_id, file=filename)
                
                except Exception as e:
                    logger.error("Failed to load template", file=filename, error=str(e))
        
        except Exception as e:
            logger.error("Failed to load custom templates", error=str(e))
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a policy template by ID
        
        Args:
            template_id: ID of the template
            
        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        template_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List policy templates with optional filtering
        
        Args:
            template_type: Optional template type to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            List of template dictionaries
        """
        templates = []
        
        for template_id, template in self.templates.items():
            # Apply filters
            if template_type and template.get('type') != template_type:
                continue
            
            if tags:
                template_tags = template.get('tags', [])
                if not all(tag in template_tags for tag in tags):
                    continue
            
            # Add to list
            templates.append(template)
        
        return templates
    
    def create_policy_from_template(
        self,
        template_id: str,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a policy from a template
        
        Args:
            template_id: ID of the template
            name: Name for the new policy
            description: Description for the new policy
            parameters: Optional parameters to customize the policy
            
        Returns:
            Policy dictionary
        """
        # Get template
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Create policy ID
        policy_id = f"policy-{uuid.uuid4()}"
        
        # Create policy from template
        policy = {
            'id': policy_id,
            'name': name,
            'description': description,
            'type': template.get('type', 'security'),
            'enforcement_mode': template.get('enforcement_mode', 'warning'),
            'status': 'active',
            'environments': template.get('environments', ['all']),
            'tags': template.get('tags', []),
            'version': '1.0.0',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'template_id': template_id,
            'rules': self._customize_rules(template.get('rules', []), parameters or {})
        }
        
        return policy
    
    def _customize_rules(
        self,
        rules: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Customize rules with parameters
        
        Args:
            rules: List of rule dictionaries
            parameters: Parameters to customize the rules
            
        Returns:
            List of customized rule dictionaries
        """
        customized_rules = []
        
        for rule in rules:
            # Create a copy of the rule
            customized_rule = rule.copy()
            
            # Generate a new rule ID
            customized_rule['id'] = f"rule-{uuid.uuid4()}"
            
            # Apply parameters
            for param_key, param_value in parameters.items():
                # Check if this parameter applies to this rule
                if param_key.startswith('rule.') and '.' in param_key[5:]:
                    # Extract rule name and field
                    parts = param_key.split('.')
                    if len(parts) >= 3:
                        rule_name = parts[1]
                        field = '.'.join(parts[2:])
                        
                        # Check if this parameter applies to this rule
                        if rule.get('name') == rule_name:
                            # Apply parameter
                            self._set_nested_field(customized_rule, field, param_value)
                
                # Check if this is a global parameter
                elif param_key.startswith('global.'):
                    field = param_key[7:]
                    self._set_nested_field(customized_rule, field, param_value)
            
            customized_rules.append(customized_rule)
        
        return customized_rules
    
    def _set_nested_field(self, obj: Dict[str, Any], field: str, value: Any):
        """
        Set a nested field in a dictionary
        
        Args:
            obj: Dictionary to modify
            field: Dot-separated field path
            value: Value to set
        """
        parts = field.split('.')
        current = obj
        
        # Navigate to the parent of the field
        for i in range(len(parts) - 1):
            part = parts[i]
            
            if part not in current:
                current[part] = {}
            
            current = current[part]
        
        # Set the field
        current[parts[-1]] = value
    
    def save_custom_template(self, template: Dict[str, Any]) -> str:
        """
        Save a custom policy template
        
        Args:
            template: Template dictionary
            
        Returns:
            Path to the saved template file
        """
        # Ensure template has an ID
        if 'id' not in template:
            template['id'] = f"template-{uuid.uuid4()}"
        
        # Generate filename
        filename = f"{template['id']}.yaml"
        file_path = os.path.join(self.template_dir, filename)
        
        # Write template to file
        with open(file_path, 'w') as f:
            yaml.dump(template, f, sort_keys=False)
        
        # Add to templates
        self.templates[template['id']] = template
        
        logger.info("Saved custom template", template_id=template['id'], file=file_path)
        
        return file_path
    
    def delete_custom_template(self, template_id: str) -> bool:
        """
        Delete a custom policy template
        
        Args:
            template_id: ID of the template
            
        Returns:
            True if successful, False otherwise
        """
        # Check if template exists
        if template_id not in self.templates:
            return False
        
        # Find template file
        filename = f"{template_id}.yaml"
        file_path = os.path.join(self.template_dir, filename)
        
        if not os.path.exists(file_path):
            # Try to find the file
            for f in os.listdir(self.template_dir):
                if f.endswith(('.yaml', '.yml')):
                    try:
                        with open(os.path.join(self.template_dir, f), 'r') as file:
                            data = yaml.safe_load(file.read())
                            if data.get('id') == template_id:
                                file_path = os.path.join(self.template_dir, f)
                                break
                    except:
                        pass
        
        # Delete template file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from templates
        if template_id in self.templates:
            del self.templates[template_id]
        
        logger.info("Deleted custom template", template_id=template_id)
        
        return True
    
    def _create_secure_container_template(self) -> Dict[str, Any]:
        """
        Create a template for secure container policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-container',
            'name': 'Secure Container Policy',
            'description': 'Policy for securing container images and runtime',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['container', 'security', 'docker', 'kubernetes'],
            'rules': [
                {
                    'name': 'no-privileged-containers',
                    'description': 'Containers should not run in privileged mode',
                    'severity': 'critical',
                    'condition': {
                        'field': 'container.privileged',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove the privileged flag from container configuration',
                        'Use more specific capabilities instead of privileged mode'
                    ]
                },
                {
                    'name': 'no-root-containers',
                    'description': 'Containers should not run as root',
                    'severity': 'high',
                    'condition': {
                        'field': 'container.user',
                        'operator': 'not_equals',
                        'value': 'root'
                    },
                    'remediation_steps': [
                        'Set a non-root user in the container configuration',
                        'Use USER directive in Dockerfile to specify a non-root user'
                    ]
                },
                {
                    'name': 'read-only-root-filesystem',
                    'description': 'Container root filesystem should be read-only',
                    'severity': 'medium',
                    'condition': {
                        'field': 'container.read_only_root_filesystem',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Set readOnlyRootFilesystem to true in container security context',
                        'Mount specific directories as writable volumes if needed'
                    ]
                },
                {
                    'name': 'no-latest-tag',
                    'description': 'Container images should not use the latest tag',
                    'severity': 'medium',
                    'condition': {
                        'field': 'container.image.tag',
                        'operator': 'not_equals',
                        'value': 'latest'
                    },
                    'remediation_steps': [
                        'Use specific version tags for container images',
                        'Implement a versioning strategy for container images'
                    ]
                },
                {
                    'name': 'drop-capabilities',
                    'description': 'Container should drop all capabilities and only add required ones',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'container.capabilities.drop',
                                'operator': 'contains',
                                'value': 'ALL'
                            },
                            {
                                'field': 'container.capabilities.add',
                                'operator': 'not_contains',
                                'value': 'NET_ADMIN'
                            },
                            {
                                'field': 'container.capabilities.add',
                                'operator': 'not_contains',
                                'value': 'SYS_ADMIN'
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Drop ALL capabilities and only add the specific ones required',
                        'Review container capabilities and remove unnecessary ones'
                    ]
                }
            ]
        }
    
    def _create_secure_kubernetes_template(self) -> Dict[str, Any]:
        """
        Create a template for secure Kubernetes policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-kubernetes',
            'name': 'Secure Kubernetes Policy',
            'description': 'Policy for securing Kubernetes deployments',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['kubernetes', 'security', 'k8s'],
            'rules': [
                {
                    'name': 'no-host-network',
                    'description': 'Pods should not use host network',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.host_network',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove hostNetwork: true from pod specification',
                        'Use Kubernetes networking instead of host networking'
                    ]
                },
                {
                    'name': 'no-host-pid',
                    'description': 'Pods should not use host PID namespace',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.host_pid',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove hostPID: true from pod specification',
                        'Use pod-level PID namespace instead of host PID namespace'
                    ]
                },
                {
                    'name': 'no-host-ipc',
                    'description': 'Pods should not use host IPC namespace',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.host_ipc',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove hostIPC: true from pod specification',
                        'Use pod-level IPC namespace instead of host IPC namespace'
                    ]
                },
                {
                    'name': 'run-as-non-root',
                    'description': 'Pods should run as non-root user',
                    'severity': 'high',
                    'condition': {
                        'field': 'kubernetes.pod.security_context.run_as_non_root',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Set runAsNonRoot: true in pod security context',
                        'Specify a non-root user ID in runAsUser field'
                    ]
                },
                {
                    'name': 'network-policy-defined',
                    'description': 'Namespaces should have network policies defined',
                    'severity': 'medium',
                    'condition': {
                        'field': 'kubernetes.namespace.network_policies',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Define network policies for each namespace',
                        'Implement default deny policies and explicitly allow required traffic'
                    ]
                }
            ]
        }
    
    def _create_secure_cloud_template(self) -> Dict[str, Any]:
        """
        Create a template for secure cloud policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-cloud',
            'name': 'Secure Cloud Policy',
            'description': 'Policy for securing cloud resources',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['cloud', 'security', 'aws', 'azure', 'gcp'],
            'rules': [
                {
                    'name': 'encrypt-data-at-rest',
                    'description': 'Cloud storage should be encrypted at rest',
                    'severity': 'high',
                    'condition': {
                        'field': 'cloud.storage.encrypted',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable encryption at rest for cloud storage services',
                        'Use customer-managed encryption keys where possible'
                    ]
                },
                {
                    'name': 'secure-network-acls',
                    'description': 'Network ACLs should not allow unrestricted access',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'cloud.network.acl.allow_all_ingress',
                                'operator': 'equals',
                                'value': False
                            },
                            {
                                'field': 'cloud.network.acl.allow_all_egress',
                                'operator': 'equals',
                                'value': False
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Remove 0.0.0.0/0 ingress rules from security groups',
                        'Implement least privilege network access controls'
                    ]
                },
                {
                    'name': 'mfa-enabled',
                    'description': 'Multi-factor authentication should be enabled for all users',
                    'severity': 'critical',
                    'condition': {
                        'field': 'cloud.iam.users.mfa_enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable MFA for all IAM users',
                        'Implement MFA enforcement policies'
                    ]
                },
                {
                    'name': 'logging-enabled',
                    'description': 'Logging and monitoring should be enabled',
                    'severity': 'high',
                    'condition': {
                        'field': 'cloud.logging.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Enable CloudTrail/Activity Logs/Cloud Audit Logs',
                        'Configure log retention policies'
                    ]
                },
                {
                    'name': 'no-public-access',
                    'description': 'Cloud resources should not be publicly accessible',
                    'severity': 'critical',
                    'condition': {
                        'field': 'cloud.resource.public_access',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove public access from cloud resources',
                        'Implement private endpoints for accessing cloud services'
                    ]
                }
            ]
        }
    
    def _create_secure_web_app_template(self) -> Dict[str, Any]:
        """
        Create a template for secure web application policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-web-app',
            'name': 'Secure Web Application Policy',
            'description': 'Policy for securing web applications',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['web', 'security', 'application'],
            'rules': [
                {
                    'name': 'https-only',
                    'description': 'Web applications should use HTTPS only',
                    'severity': 'critical',
                    'condition': {
                        'field': 'webapp.protocols',
                        'operator': 'equals',
                        'value': ['https']
                    },
                    'remediation_steps': [
                        'Configure HTTPS for all web applications',
                        'Implement HSTS headers',
                        'Redirect HTTP to HTTPS'
                    ]
                },
                {
                    'name': 'secure-cookies',
                    'description': 'Cookies should have secure and httpOnly flags',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'webapp.cookies.secure',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'webapp.cookies.httpOnly',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Set secure and httpOnly flags for all cookies',
                        'Implement SameSite cookie attribute'
                    ]
                },
                {
                    'name': 'content-security-policy',
                    'description': 'Content Security Policy should be implemented',
                    'severity': 'high',
                    'condition': {
                        'field': 'webapp.headers.content_security_policy',
                        'operator': 'exists'
                    },
                    'remediation_steps': [
                        'Implement Content Security Policy headers',
                        'Use strict CSP directives to prevent XSS attacks'
                    ]
                },
                {
                    'name': 'no-exposed-sensitive-data',
                    'description': 'Sensitive data should not be exposed in URLs or logs',
                    'severity': 'critical',
                    'condition': {
                        'field': 'webapp.exposed_sensitive_data',
                        'operator': 'equals',
                        'value': False
                    },
                    'remediation_steps': [
                        'Remove sensitive data from URLs',
                        'Implement proper data masking in logs',
                        'Use POST requests for sensitive operations'
                    ]
                },
                {
                    'name': 'input-validation',
                    'description': 'All user input should be validated',
                    'severity': 'critical',
                    'condition': {
                        'field': 'webapp.input_validation',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement server-side input validation',
                        'Use parameterized queries for database operations',
                        'Sanitize user input to prevent injection attacks'
                    ]
                }
            ]
        }
    
    def _create_secure_api_template(self) -> Dict[str, Any]:
        """
        Create a template for secure API policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'secure-api',
            'name': 'Secure API Policy',
            'description': 'Policy for securing APIs',
            'type': 'security',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['api', 'security', 'rest', 'graphql'],
            'rules': [
                {
                    'name': 'api-authentication',
                    'description': 'APIs should require authentication',
                    'severity': 'critical',
                    'condition': {
                        'field': 'api.authentication.required',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement authentication for all API endpoints',
                        'Use OAuth 2.0 or API keys for authentication'
                    ]
                },
                {
                    'name': 'api-rate-limiting',
                    'description': 'APIs should implement rate limiting',
                    'severity': 'high',
                    'condition': {
                        'field': 'api.rate_limiting.enabled',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement rate limiting for API endpoints',
                        'Configure appropriate rate limits based on endpoint sensitivity'
                    ]
                },
                {
                    'name': 'api-input-validation',
                    'description': 'APIs should validate all input parameters',
                    'severity': 'critical',
                    'condition': {
                        'field': 'api.input_validation',
                        'operator': 'equals',
                        'value': True
                    },
                    'remediation_steps': [
                        'Implement input validation for all API parameters',
                        'Use schema validation for request bodies'
                    ]
                },
                {
                    'name': 'api-https-only',
                    'description': 'APIs should use HTTPS only',
                    'severity': 'critical',
                    'condition': {
                        'field': 'api.protocols',
                        'operator': 'equals',
                        'value': ['https']
                    },
                    'remediation_steps': [
                        'Configure HTTPS for all API endpoints',
                        'Reject non-HTTPS requests'
                    ]
                },
                {
                    'name': 'api-security-headers',
                    'description': 'APIs should include security headers',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'api.headers.x_content_type_options',
                                'operator': 'exists'
                            },
                            {
                                'field': 'api.headers.x_frame_options',
                                'operator': 'exists'
                            },
                            {
                                'field': 'api.headers.x_xss_protection',
                                'operator': 'exists'
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Add security headers to API responses',
                        'Configure API gateway to add security headers'
                    ]
                }
            ]
        }
    
    def _create_pci_dss_template(self) -> Dict[str, Any]:
        """
        Create a template for PCI DSS compliance policies
        
        Returns:
            Template dictionary
        """
        return {
            'id': 'pci-dss',
            'name': 'PCI DSS Compliance Policy',
            'description': 'Policy for ensuring compliance with Payment Card Industry Data Security Standard',
            'type': 'compliance',
            'enforcement_mode': 'blocking',
            'environments': ['all'],
            'tags': ['compliance', 'pci-dss', 'security'],
            'rules': [
                {
                    'name': 'pci-dss-req-1',
                    'description': 'Install and maintain network security controls',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'network.firewall.enabled',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'network.firewall.rules.default_deny',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement and configure firewalls between all wireless networks and the cardholder data environment',
                        'Maintain a current network diagram that documents all connections between the cardholder data environment and other networks'
                    ]
                },
                {
                    'name': 'pci-dss-req-2',
                    'description': 'Apply secure configurations to all system components',
                    'severity': 'high',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'system.secure_configuration',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'system.default_accounts.changed',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Implement secure configuration standards for all system components',
                        'Change default passwords and other security parameters'
                    ]
                },
                {
                    'name': 'pci-dss-req-3',
                    'description': 'Protect stored account data',
                    'severity': 'critical',
                    'condition': {
                        'operator': 'and',
                        'conditions': [
                            {
                                'field': 'data.encryption.at_rest',
                                'operator': 'equals',
                                'value': True
                            },
                            {
                                'field': 'data.pci.pan.masked',
                                'operator': 'equals',
                                'value': True
                            }
                        ]
                    },
                    'remediation_steps': [
                        'Keep cardholder data storage to a minimum',
                        'Mask PAN when displayed',
                        'Render PAN unreadable anywhere it is stored'
                    ]
                },
                {
                    'name': 'pci
