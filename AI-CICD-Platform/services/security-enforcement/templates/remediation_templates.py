import os
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set

from ..models.remediation import (
    RemediationAction,
    RemediationStrategy,
    RemediationSource
)

class TemplateType(str, Enum):
    """
    Types of remediation templates
    """
    DEPENDENCY_UPDATE = "DEPENDENCY_UPDATE"  # Update a dependency to a fixed version
    CODE_FIX = "CODE_FIX"  # Fix code vulnerability
    CONFIG_UPDATE = "CONFIG_UPDATE"  # Update configuration
    PERMISSION_FIX = "PERMISSION_FIX"  # Fix permission issues
    CUSTOM = "CUSTOM"  # Custom template

class RemediationTemplate:
    """
    A template for remediation actions
    """
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        template_type: TemplateType,
        vulnerability_types: List[str],
        steps: List[Dict[str, Any]],
        variables: Dict[str, Dict[str, Any]],
        strategy: RemediationStrategy = RemediationStrategy.AUTOMATED,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.template_type = template_type
        self.vulnerability_types = vulnerability_types
        self.steps = steps
        self.variables = variables
        self.strategy = strategy
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "vulnerability_types": self.vulnerability_types,
            "steps": self.steps,
            "variables": self.variables,
            "strategy": self.strategy,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemediationTemplate':
        """
        Create from dictionary
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            template_type=TemplateType(data["template_type"]),
            vulnerability_types=data["vulnerability_types"],
            steps=data["steps"],
            variables=data["variables"],
            strategy=RemediationStrategy(data["strategy"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )

class RemediationTemplateService:
    """
    Service for managing remediation templates
    """
    def __init__(self):
        """
        Initialize the template service
        """
        self.templates_dir = os.path.join(os.path.dirname(__file__), "..", "data", "templates")
        
        # Create directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Load built-in templates
        self._load_built_in_templates()
    
    def _load_built_in_templates(self) -> None:
        """
        Load built-in templates
        """
        # Create dependency update template
        dependency_update_template = RemediationTemplate(
            id="TEMPLATE-DEPENDENCY-UPDATE",
            name="Dependency Update",
            description="Update a dependency to a fixed version",
            template_type=TemplateType.DEPENDENCY_UPDATE,
            vulnerability_types=["CVE", "DEPENDENCY"],
            steps=[
                {
                    "name": "Identify dependency file",
                    "description": "Identify the file containing the dependency",
                    "action": "IDENTIFY",
                    "parameters": {
                        "file_path": "${file_path}"
                    }
                },
                {
                    "name": "Update dependency version",
                    "description": "Update the dependency to the fixed version",
                    "action": "UPDATE",
                    "parameters": {
                        "file_path": "${file_path}",
                        "dependency_name": "${dependency_name}",
                        "current_version": "${current_version}",
                        "fixed_version": "${fixed_version}"
                    }
                },
                {
                    "name": "Verify update",
                    "description": "Verify the dependency was updated correctly",
                    "action": "VERIFY",
                    "parameters": {
                        "file_path": "${file_path}",
                        "dependency_name": "${dependency_name}",
                        "fixed_version": "${fixed_version}"
                    }
                }
            ],
            variables={
                "file_path": {
                    "description": "Path to the dependency file",
                    "type": "string",
                    "required": True
                },
                "dependency_name": {
                    "description": "Name of the dependency",
                    "type": "string",
                    "required": True
                },
                "current_version": {
                    "description": "Current version of the dependency",
                    "type": "string",
                    "required": True
                },
                "fixed_version": {
                    "description": "Fixed version of the dependency",
                    "type": "string",
                    "required": True
                }
            },
            strategy=RemediationStrategy.AUTOMATED,
            created_at=datetime.utcnow(),
            metadata={
                "built_in": True,
                "supported_package_managers": ["npm", "pip", "maven", "gradle"]
            }
        )
        
        # Create code fix template
        code_fix_template = RemediationTemplate(
            id="TEMPLATE-CODE-FIX",
            name="Code Fix",
            description="Fix code vulnerability",
            template_type=TemplateType.CODE_FIX,
            vulnerability_types=["XSS", "SQL_INJECTION", "COMMAND_INJECTION"],
            steps=[
                {
                    "name": "Identify vulnerable code",
                    "description": "Identify the vulnerable code",
                    "action": "IDENTIFY",
                    "parameters": {
                        "file_path": "${file_path}",
                        "line_number": "${line_number}"
                    }
                },
                {
                    "name": "Apply fix",
                    "description": "Apply the fix to the vulnerable code",
                    "action": "REPLACE",
                    "parameters": {
                        "file_path": "${file_path}",
                        "line_number": "${line_number}",
                        "original_code": "${original_code}",
                        "fixed_code": "${fixed_code}"
                    }
                },
                {
                    "name": "Verify fix",
                    "description": "Verify the fix was applied correctly",
                    "action": "VERIFY",
                    "parameters": {
                        "file_path": "${file_path}",
                        "line_number": "${line_number}",
                        "fixed_code": "${fixed_code}"
                    }
                }
            ],
            variables={
                "file_path": {
                    "description": "Path to the file containing the vulnerable code",
                    "type": "string",
                    "required": True
                },
                "line_number": {
                    "description": "Line number of the vulnerable code",
                    "type": "integer",
                    "required": True
                },
                "original_code": {
                    "description": "Original vulnerable code",
                    "type": "string",
                    "required": True
                },
                "fixed_code": {
                    "description": "Fixed code",
                    "type": "string",
                    "required": True
                }
            },
            strategy=RemediationStrategy.ASSISTED,
            created_at=datetime.utcnow(),
            metadata={
                "built_in": True,
                "supported_languages": ["javascript", "python", "java", "go"]
            }
        )
        
        # Create config update template
        config_update_template = RemediationTemplate(
            id="TEMPLATE-CONFIG-UPDATE",
            name="Configuration Update",
            description="Update configuration to fix security issues",
            template_type=TemplateType.CONFIG_UPDATE,
            vulnerability_types=["MISCONFIGURATION", "SECURITY_CONFIG"],
            steps=[
                {
                    "name": "Identify configuration file",
                    "description": "Identify the configuration file",
                    "action": "IDENTIFY",
                    "parameters": {
                        "file_path": "${file_path}"
                    }
                },
                {
                    "name": "Update configuration",
                    "description": "Update the configuration",
                    "action": "UPDATE",
                    "parameters": {
                        "file_path": "${file_path}",
                        "config_key": "${config_key}",
                        "current_value": "${current_value}",
                        "fixed_value": "${fixed_value}"
                    }
                },
                {
                    "name": "Verify update",
                    "description": "Verify the configuration was updated correctly",
                    "action": "VERIFY",
                    "parameters": {
                        "file_path": "${file_path}",
                        "config_key": "${config_key}",
                        "fixed_value": "${fixed_value}"
                    }
                }
            ],
            variables={
                "file_path": {
                    "description": "Path to the configuration file",
                    "type": "string",
                    "required": True
                },
                "config_key": {
                    "description": "Configuration key to update",
                    "type": "string",
                    "required": True
                },
                "current_value": {
                    "description": "Current value of the configuration",
                    "type": "string",
                    "required": True
                },
                "fixed_value": {
                    "description": "Fixed value for the configuration",
                    "type": "string",
                    "required": True
                }
            },
            strategy=RemediationStrategy.AUTOMATED,
            created_at=datetime.utcnow(),
            metadata={
                "built_in": True,
                "supported_formats": ["json", "yaml", "ini", "xml"]
            }
        )
        
        # Save built-in templates
        self._save_template(dependency_update_template)
        self._save_template(code_fix_template)
        self._save_template(config_update_template)
    
    async def create_template(
        self,
        name: str,
        description: str,
        template_type: TemplateType,
        vulnerability_types: List[str],
        steps: List[Dict[str, Any]],
        variables: Dict[str, Dict[str, Any]],
        strategy: RemediationStrategy = RemediationStrategy.AUTOMATED,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RemediationTemplate:
        """
        Create a new template
        """
        # Generate a unique ID for the template
        template_id = f"TEMPLATE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create the template
        template = RemediationTemplate(
            id=template_id,
            name=name,
            description=description,
            template_type=template_type,
            vulnerability_types=vulnerability_types,
            steps=steps,
            variables=variables,
            strategy=strategy,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Save the template
        self._save_template(template)
        
        return template
    
    def get_template(self, template_id: str) -> Optional[RemediationTemplate]:
        """
        Get a template by ID
        """
        template_path = os.path.join(self.templates_dir, f"{template_id}.json")
        
        if not os.path.exists(template_path):
            return None
        
        try:
            with open(template_path, "r") as f:
                template_data = json.load(f)
            
            return RemediationTemplate.from_dict(template_data)
        except Exception as e:
            print(f"Error loading template {template_id}: {str(e)}")
            return None
    
    def get_all_templates(self) -> List[RemediationTemplate]:
        """
        Get all templates
        """
        templates = []
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                template_id = filename[:-5]  # Remove .json extension
                template = self.get_template(template_id)
                
                if template:
                    templates.append(template)
        
        return templates
    
    def find_templates_for_vulnerability(
        self,
        vulnerability_id: str,
        vulnerability_description: Optional[str] = None
    ) -> List[RemediationTemplate]:
        """
        Find templates for a vulnerability
        """
        # TODO: Implement more sophisticated matching logic
        # For now, we'll just return all templates
        
        return self.get_all_templates()
    
    def create_action_from_template(
        self,
        template_id: str,
        vulnerability_id: str,
        variables: Dict[str, Any]
    ) -> RemediationAction:
        """
        Create a remediation action from a template
        """
        # Get the template
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Validate variables
        for var_name, var_info in template.variables.items():
            if var_info.get("required", False) and var_name not in variables:
                raise ValueError(f"Missing required variable: {var_name}")
        
        # Generate a unique ID for the action
        action_id = f"ACTION-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create the action
        action = RemediationAction(
            id=action_id,
            vulnerability_id=vulnerability_id,
            name=f"Remediate {vulnerability_id}",
            description=f"Remediation for {vulnerability_id} using template {template.name}",
            strategy=template.strategy,
            source=RemediationSource.TEMPLATE,
            steps=self._substitute_variables(template.steps, variables),
            status="PENDING",
            created_at=datetime.utcnow(),
            metadata={
                "template_id": template_id,
                "template_name": template.name,
                "template_type": template.template_type,
                "variables": variables
            }
        )
        
        return action
    
    def _substitute_variables(
        self,
        steps: List[Dict[str, Any]],
        variables: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Substitute variables in steps
        """
        substituted_steps = []
        
        for step in steps:
            substituted_step = step.copy()
            
            # Substitute variables in parameters
            if "parameters" in substituted_step:
                substituted_parameters = {}
                
                for param_name, param_value in substituted_step["parameters"].items():
                    if isinstance(param_value, str) and param_value.startswith("${") and param_value.endswith("}"):
                        var_name = param_value[2:-1]
                        if var_name in variables:
                            substituted_parameters[param_name] = variables[var_name]
                        else:
                            substituted_parameters[param_name] = param_value
                    else:
                        substituted_parameters[param_name] = param_value
                
                substituted_step["parameters"] = substituted_parameters
            
            substituted_steps.append(substituted_step)
        
        return substituted_steps
    
    def _save_template(self, template: RemediationTemplate) -> None:
        """
        Save a template to disk
        """
        template_path = os.path.join(self.templates_dir, f"{template.id}.json")
        
        with open(template_path, "w") as f:
            json.dump(template.to_dict(), f, indent=2)
