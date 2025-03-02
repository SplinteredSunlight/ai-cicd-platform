import pytest
import os
import json
from datetime import datetime

from ..templates.remediation_templates import (
    TemplateType,
    RemediationTemplate,
    RemediationTemplateService
)
from ..models.remediation import (
    RemediationAction,
    RemediationStrategy,
    RemediationSource
)

@pytest.fixture
def template_service():
    """
    Create a template service for testing
    """
    return RemediationTemplateService()

def test_template_creation():
    """
    Test creating a template
    """
    template = RemediationTemplate(
        id="test-template",
        name="Test Template",
        description="A test template",
        template_type=TemplateType.DEPENDENCY_UPDATE,
        vulnerability_types=["CVE", "DEPENDENCY"],
        steps=[
            {
                "name": "Test Step",
                "description": "A test step",
                "action": "TEST",
                "parameters": {
                    "param1": "value1",
                    "param2": "value2"
                }
            }
        ],
        variables={
            "var1": {
                "description": "Variable 1",
                "type": "string",
                "required": True
            },
            "var2": {
                "description": "Variable 2",
                "type": "integer",
                "required": False
            }
        },
        strategy=RemediationStrategy.AUTOMATED,
        created_at=datetime.utcnow(),
        metadata={
            "test": True
        }
    )
    
    assert template.id == "test-template"
    assert template.name == "Test Template"
    assert template.description == "A test template"
    assert template.template_type == TemplateType.DEPENDENCY_UPDATE
    assert "CVE" in template.vulnerability_types
    assert "DEPENDENCY" in template.vulnerability_types
    assert len(template.steps) == 1
    assert template.steps[0]["name"] == "Test Step"
    assert template.steps[0]["action"] == "TEST"
    assert template.steps[0]["parameters"]["param1"] == "value1"
    assert template.variables["var1"]["required"] == True
    assert template.variables["var2"]["required"] == False
    assert template.strategy == RemediationStrategy.AUTOMATED
    assert template.metadata["test"] == True

def test_template_to_dict():
    """
    Test converting a template to a dictionary
    """
    template = RemediationTemplate(
        id="test-template",
        name="Test Template",
        description="A test template",
        template_type=TemplateType.DEPENDENCY_UPDATE,
        vulnerability_types=["CVE", "DEPENDENCY"],
        steps=[
            {
                "name": "Test Step",
                "description": "A test step",
                "action": "TEST",
                "parameters": {
                    "param1": "value1",
                    "param2": "value2"
                }
            }
        ],
        variables={
            "var1": {
                "description": "Variable 1",
                "type": "string",
                "required": True
            },
            "var2": {
                "description": "Variable 2",
                "type": "integer",
                "required": False
            }
        },
        strategy=RemediationStrategy.AUTOMATED,
        created_at=datetime.utcnow(),
        metadata={
            "test": True
        }
    )
    
    template_dict = template.to_dict()
    
    assert template_dict["id"] == "test-template"
    assert template_dict["name"] == "Test Template"
    assert template_dict["description"] == "A test template"
    assert template_dict["template_type"] == TemplateType.DEPENDENCY_UPDATE
    assert "CVE" in template_dict["vulnerability_types"]
    assert "DEPENDENCY" in template_dict["vulnerability_types"]
    assert len(template_dict["steps"]) == 1
    assert template_dict["steps"][0]["name"] == "Test Step"
    assert template_dict["steps"][0]["action"] == "TEST"
    assert template_dict["steps"][0]["parameters"]["param1"] == "value1"
    assert template_dict["variables"]["var1"]["required"] == True
    assert template_dict["variables"]["var2"]["required"] == False
    assert template_dict["strategy"] == RemediationStrategy.AUTOMATED
    assert template_dict["metadata"]["test"] == True

def test_template_from_dict():
    """
    Test creating a template from a dictionary
    """
    template_dict = {
        "id": "test-template",
        "name": "Test Template",
        "description": "A test template",
        "template_type": TemplateType.DEPENDENCY_UPDATE,
        "vulnerability_types": ["CVE", "DEPENDENCY"],
        "steps": [
            {
                "name": "Test Step",
                "description": "A test step",
                "action": "TEST",
                "parameters": {
                    "param1": "value1",
                    "param2": "value2"
                }
            }
        ],
        "variables": {
            "var1": {
                "description": "Variable 1",
                "type": "string",
                "required": True
            },
            "var2": {
                "description": "Variable 2",
                "type": "integer",
                "required": False
            }
        },
        "strategy": RemediationStrategy.AUTOMATED,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {
            "test": True
        }
    }
    
    template = RemediationTemplate.from_dict(template_dict)
    
    assert template.id == "test-template"
    assert template.name == "Test Template"
    assert template.description == "A test template"
    assert template.template_type == TemplateType.DEPENDENCY_UPDATE
    assert "CVE" in template.vulnerability_types
    assert "DEPENDENCY" in template.vulnerability_types
    assert len(template.steps) == 1
    assert template.steps[0]["name"] == "Test Step"
    assert template.steps[0]["action"] == "TEST"
    assert template.steps[0]["parameters"]["param1"] == "value1"
    assert template.variables["var1"]["required"] == True
    assert template.variables["var2"]["required"] == False
    assert template.strategy == RemediationStrategy.AUTOMATED
    assert template.metadata["test"] == True

def test_template_service_initialization(template_service):
    """
    Test initializing the template service
    """
    assert template_service is not None
    assert template_service.templates_dir is not None
    assert os.path.exists(template_service.templates_dir)

def test_template_service_get_all_templates(template_service):
    """
    Test getting all templates
    """
    templates = template_service.get_all_templates()
    
    assert templates is not None
    assert len(templates) > 0
    
    # Check that the built-in templates are loaded
    template_ids = [t.id for t in templates]
    assert "TEMPLATE-DEPENDENCY-UPDATE" in template_ids
    assert "TEMPLATE-CODE-FIX" in template_ids
    assert "TEMPLATE-CONFIG-UPDATE" in template_ids

def test_template_service_get_template(template_service):
    """
    Test getting a template by ID
    """
    template = template_service.get_template("TEMPLATE-DEPENDENCY-UPDATE")
    
    assert template is not None
    assert template.id == "TEMPLATE-DEPENDENCY-UPDATE"
    assert template.name == "Dependency Update"
    assert template.template_type == TemplateType.DEPENDENCY_UPDATE
    assert "CVE" in template.vulnerability_types
    assert "DEPENDENCY" in template.vulnerability_types

def test_template_service_find_templates_for_vulnerability(template_service):
    """
    Test finding templates for a vulnerability
    """
    templates = template_service.find_templates_for_vulnerability(
        "CVE-2023-1234",
        "A dependency vulnerability"
    )
    
    assert templates is not None
    assert len(templates) > 0

def test_template_service_create_action_from_template(template_service):
    """
    Test creating an action from a template
    """
    action = template_service.create_action_from_template(
        "TEMPLATE-DEPENDENCY-UPDATE",
        "CVE-2023-1234",
        {
            "file_path": "package.json",
            "dependency_name": "example-dependency",
            "current_version": "1.0.0",
            "fixed_version": "1.1.0"
        }
    )
    
    assert action is not None
    assert action.vulnerability_id == "CVE-2023-1234"
    assert action.strategy == RemediationStrategy.AUTOMATED
    assert action.source == RemediationSource.TEMPLATE
    assert len(action.steps) == 3
    
    # Check that variables were substituted
    assert action.steps[0]["parameters"]["file_path"] == "package.json"
    assert action.steps[1]["parameters"]["dependency_name"] == "example-dependency"
    assert action.steps[1]["parameters"]["current_version"] == "1.0.0"
    assert action.steps[1]["parameters"]["fixed_version"] == "1.1.0"
    assert action.steps[2]["parameters"]["dependency_name"] == "example-dependency"
    assert action.steps[2]["parameters"]["fixed_version"] == "1.1.0"

def test_template_service_substitute_variables(template_service):
    """
    Test substituting variables in steps
    """
    steps = [
        {
            "name": "Test Step 1",
            "description": "A test step",
            "action": "TEST",
            "parameters": {
                "param1": "${var1}",
                "param2": "${var2}"
            }
        },
        {
            "name": "Test Step 2",
            "description": "Another test step",
            "action": "TEST",
            "parameters": {
                "param3": "${var3}",
                "param4": "static value"
            }
        }
    ]
    
    variables = {
        "var1": "value1",
        "var2": "value2",
        "var3": "value3"
    }
    
    substituted_steps = template_service._substitute_variables(steps, variables)
    
    assert substituted_steps is not None
    assert len(substituted_steps) == 2
    assert substituted_steps[0]["parameters"]["param1"] == "value1"
    assert substituted_steps[0]["parameters"]["param2"] == "value2"
    assert substituted_steps[1]["parameters"]["param3"] == "value3"
    assert substituted_steps[1]["parameters"]["param4"] == "static value"
