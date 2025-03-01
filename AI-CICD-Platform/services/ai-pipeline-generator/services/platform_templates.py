"""
Platform-specific templates and configurations for CI/CD pipeline generation.
This module provides specialized templates and guidance for each supported CI/CD platform.
It also includes customizable templates for common CI/CD workflows.
"""

from typing import Dict, List, Optional, Any
import copy

# Platform-specific syntax guides
PLATFORM_SYNTAX_GUIDES = {
    "github-actions": """
GitHub Actions YAML structure:
```yaml
name: workflow_name
on: [trigger_events]
jobs:
  job_id:
    runs-on: runner_type
    steps:
      - name: step_name
        uses: action_name
        with:
          param: value
```
    """,
    
    "gitlab-ci": """
GitLab CI YAML structure:
```yaml
stages:
  - stage_name

job_name:
  stage: stage_name
  image: image_name
  script:
    - command
  only:
    - branch_name
```
    """,
    
    "azure-pipelines": """
Azure Pipelines YAML structure:
```yaml
trigger:
  - branch_name

pool:
  vmImage: 'image_name'

steps:
  - task: task_name@version
    inputs:
      param: value
```
    """,
    
    "circle-ci": """
CircleCI YAML structure:
```yaml
version: 2.1
jobs:
  job_name:
    docker:
      - image: image_name
    steps:
      - checkout
      - run:
          name: step_name
          command: command
workflows:
  workflow_name:
    jobs:
      - job_name
```
    """,
    
    "jenkins": """
Jenkinsfile (Declarative Pipeline) structure:
```groovy
pipeline {
    agent any
    stages {
        stage('Stage Name') {
            steps {
                sh 'command'
            }
        }
    }
}
```
    """,
    
    "travis-ci": """
Travis CI YAML structure:
```yaml
language: language_name
os: os_name
dist: distribution_name
branches:
  only:
    - branch_name
script:
  - command
```
    """,
    
    "bitbucket-pipelines": """
Bitbucket Pipelines YAML structure:
```yaml
pipelines:
  branches:
    branch_name:
      - step:
          name: step_name
          script:
            - command
```
    """,
    
    "aws-codebuild": """
AWS CodeBuild buildspec.yml structure:
```yaml
version: 0.2
phases:
  install:
    commands:
      - command
  build:
    commands:
      - command
artifacts:
  files:
    - file_path
```
    """,
}

# Platform-specific best practices
PLATFORM_BEST_PRACTICES = {
    "github-actions": [
        "Use actions/checkout@v3 to check out your repository",
        "Use caching for dependencies to speed up workflows",
        "Set up matrix builds for testing across multiple environments",
        "Use environment secrets for sensitive information",
        "Set up concurrency groups to avoid redundant workflow runs"
    ],
    
    "gitlab-ci": [
        "Use stages to organize jobs in a pipeline",
        "Use cache to speed up subsequent pipeline runs",
        "Use GitLab CI/CD variables for configuration",
        "Use 'only' and 'except' to control when jobs run",
        "Use artifacts to pass data between jobs"
    ],
    
    "azure-pipelines": [
        "Use pipeline variables for configuration",
        "Use templates to reuse pipeline configurations",
        "Use service connections for external services",
        "Use deployment jobs for releases",
        "Use environments for deployment targets"
    ],
    
    "circle-ci": [
        "Use orbs to simplify configuration",
        "Use workflows to organize jobs",
        "Use contexts for managing environment variables",
        "Use resource classes to specify compute resources",
        "Use caching to speed up builds"
    ],
    
    "jenkins": [
        "Use declarative pipelines for better readability",
        "Use shared libraries for reusable code",
        "Use parameters for configurable pipelines",
        "Use agents to specify execution environments",
        "Use stages and steps to organize pipeline execution"
    ],
    
    "travis-ci": [
        "Use build stages to organize jobs",
        "Use build matrix for testing across environments",
        "Use caching to speed up builds",
        "Use environment variables for configuration",
        "Use conditional builds to control when jobs run"
    ],
    
    "bitbucket-pipelines": [
        "Use custom pipelines for different branches",
        "Use caching to speed up builds",
        "Use services for external dependencies",
        "Use artifacts to pass data between steps",
        "Use deployment environments for releases"
    ],
    
    "aws-codebuild": [
        "Use buildspec phases to organize build steps",
        "Use environment variables for configuration",
        "Use artifacts to store build outputs",
        "Use cache to speed up builds",
        "Use reports to publish test results"
    ],
}

# Platform-specific security recommendations
PLATFORM_SECURITY_RECOMMENDATIONS = {
    "github-actions": [
        "Use GITHUB_TOKEN with minimum required permissions",
        "Pin actions to specific SHA commits instead of tags",
        "Use OpenID Connect for cloud provider authentication",
        "Set up required reviewers for workflow files",
        "Use dependabot to keep actions up to date"
    ],
    
    "gitlab-ci": [
        "Use masked variables for secrets",
        "Use protected branches and tags",
        "Use dependency scanning",
        "Use container scanning",
        "Use SAST (Static Application Security Testing)"
    ],
    
    "azure-pipelines": [
        "Use secure files for certificates and keys",
        "Use service connections with minimum permissions",
        "Use environment protection rules",
        "Use approvals for sensitive deployments",
        "Use secret variables for sensitive information"
    ],
    
    "circle-ci": [
        "Use contexts for managing secrets",
        "Use restricted contexts with limited access",
        "Use environment variables for sensitive information",
        "Use approval jobs for sensitive operations",
        "Use resource classes with appropriate permissions"
    ],
    
    "jenkins": [
        "Use credentials binding for secrets",
        "Use role-based access control",
        "Use script security sandbox",
        "Use pipeline shared libraries with security reviews",
        "Use secure agent configurations"
    ],
    
    "travis-ci": [
        "Use encrypted environment variables",
        "Use secure environment variables for secrets",
        "Limit access to sensitive repositories",
        "Use minimal build environments",
        "Avoid logging sensitive information"
    ],
    
    "bitbucket-pipelines": [
        "Use secured variables for secrets",
        "Use deployment permissions",
        "Use IP restrictions for access",
        "Use branch restrictions",
        "Use deployment environments with approvals"
    ],
    
    "aws-codebuild": [
        "Use parameter store for secrets",
        "Use IAM roles with least privilege",
        "Use VPC for network isolation",
        "Use build logs with minimal detail level",
        "Use encrypted artifacts"
    ],
}

# Customizable templates for common CI/CD workflows
# These templates can be customized with variables
PIPELINE_TEMPLATES = {
    # GitHub Actions templates
    "github-actions": {
        "basic-node": {
            "name": "Node.js CI",
            "description": "Basic Node.js CI workflow with testing",
            "variables": {
                "node_version": "16",
                "main_branch": "main",
                "test_command": "npm test",
                "install_command": "npm ci"
            },
            "template": """
name: Node.js CI

on:
  push:
    branches: [ {{main_branch}} ]
  pull_request:
    branches: [ {{main_branch}} ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [{{node_version}}]
        
    steps:
    - uses: actions/checkout@v3
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: {{install_command}}
    - run: {{test_command}}
"""
        },
        "docker-build-push": {
            "name": "Docker Build and Push",
            "description": "Build and push Docker image to registry",
            "variables": {
                "registry": "ghcr.io",
                "image_name": "username/repo",
                "main_branch": "main",
                "dockerfile_path": "Dockerfile"
            },
            "template": """
name: Docker Build and Push

on:
  push:
    branches: [ {{main_branch}} ]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Log in to the Container registry
        uses: docker/login-action@v2
        with:
          registry: {{registry}}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: {{dockerfile_path}}
          push: true
          tags: {{registry}}/{{image_name}}:latest
"""
        }
    },
    
    # GitLab CI templates
    "gitlab-ci": {
        "basic-node": {
            "name": "Node.js CI",
            "description": "Basic Node.js CI pipeline with testing",
            "variables": {
                "node_version": "16-alpine",
                "main_branch": "main",
                "test_command": "npm test",
                "install_command": "npm ci"
            },
            "template": """
stages:
  - test

test:
  stage: test
  image: node:{{node_version}}
  script:
    - {{install_command}}
    - {{test_command}}
  only:
    - {{main_branch}}
    - merge_requests
"""
        },
        "docker-build-push": {
            "name": "Docker Build and Push",
            "description": "Build and push Docker image to registry",
            "variables": {
                "registry": "registry.gitlab.com",
                "main_branch": "main"
            },
            "template": """
stages:
  - build
  - deploy

build:
  stage: build
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t {{registry}}/$CI_PROJECT_PATH:latest .
    - docker push {{registry}}/$CI_PROJECT_PATH:latest
  only:
    - {{main_branch}}
"""
        }
    },
    
    # CircleCI templates
    "circle-ci": {
        "basic-node": {
            "name": "Node.js CI",
            "description": "Basic Node.js CI workflow with testing",
            "variables": {
                "node_version": "16.14",
                "test_command": "npm test",
                "install_command": "npm ci"
            },
            "template": """
version: 2.1
jobs:
  build-and-test:
    docker:
      - image: cimg/node:{{node_version}}
    steps:
      - checkout
      - restore_cache:
          keys:
            - v1-dependencies-{{ checksum "package.json" }}
            - v1-dependencies-
      - run:
          name: Install Dependencies
          command: {{install_command}}
      - save_cache:
          paths:
            - node_modules
          key: v1-dependencies-{{ checksum "package.json" }}
      - run:
          name: Run tests
          command: {{test_command}}

workflows:
  version: 2
  build-and-test:
    jobs:
      - build-and-test
"""
        }
    },
    
    # Jenkins templates
    "jenkins": {
        "basic-node": {
            "name": "Node.js CI",
            "description": "Basic Node.js CI pipeline with testing",
            "variables": {
                "node_version": "16",
                "test_command": "npm test",
                "install_command": "npm ci"
            },
            "template": """
pipeline {
    agent {
        docker {
            image 'node:{{node_version}}-alpine'
        }
    }
    stages {
        stage('Install') {
            steps {
                sh '{{install_command}}'
            }
        }
        stage('Test') {
            steps {
                sh '{{test_command}}'
            }
        }
    }
}
"""
        }
    },
    
    # Azure Pipelines templates
    "azure-pipelines": {
        "basic-node": {
            "name": "Node.js CI",
            "description": "Basic Node.js CI pipeline with testing",
            "variables": {
                "node_version": "16.x",
                "vm_image": "ubuntu-latest",
                "test_command": "npm test",
                "install_command": "npm ci"
            },
            "template": """
trigger:
- main

pool:
  vmImage: '{{vm_image}}'

steps:
- task: NodeTool@0
  inputs:
    versionSpec: '{{node_version}}'
  displayName: 'Install Node.js'

- script: |
    {{install_command}}
  displayName: 'Install dependencies'

- script: |
    {{test_command}}
  displayName: 'Run tests'
"""
        }
    }
}

def get_platform_guide(platform: str) -> Dict[str, any]:
    """
    Get platform-specific guidance for generating CI/CD pipelines.
    
    Args:
        platform (str): The CI/CD platform name
        
    Returns:
        Dict containing syntax guide, best practices, and security recommendations
    """
    return {
        "syntax_guide": PLATFORM_SYNTAX_GUIDES.get(platform, ""),
        "best_practices": PLATFORM_BEST_PRACTICES.get(platform, []),
        "security_recommendations": PLATFORM_SECURITY_RECOMMENDATIONS.get(platform, [])
    }

def get_supported_platforms() -> List[str]:
    """
    Get a list of all supported CI/CD platforms.
    
    Returns:
        List of platform names
    """
    return list(PLATFORM_SYNTAX_GUIDES.keys())

def get_available_templates(platform: str) -> Dict[str, Dict[str, str]]:
    """
    Get available templates for a specific platform.
    
    Args:
        platform (str): The CI/CD platform name
        
    Returns:
        Dict of template names and their descriptions
    """
    platform_templates = PIPELINE_TEMPLATES.get(platform, {})
    return {
        name: {
            "name": template["name"],
            "description": template["description"]
        }
        for name, template in platform_templates.items()
    }

def get_template_variables(platform: str, template_name: str) -> Dict[str, str]:
    """
    Get the customizable variables for a specific template.
    
    Args:
        platform (str): The CI/CD platform name
        template_name (str): The template name
        
    Returns:
        Dict of variable names and their default values
    """
    platform_templates = PIPELINE_TEMPLATES.get(platform, {})
    template = platform_templates.get(template_name, {})
    return template.get("variables", {})

def apply_template(platform: str, template_name: str, variables: Dict[str, Any]) -> Optional[str]:
    """
    Apply variables to a template and return the customized pipeline configuration.
    
    Args:
        platform (str): The CI/CD platform name
        template_name (str): The template name
        variables (Dict[str, Any]): The variables to apply to the template
        
    Returns:
        String containing the customized pipeline configuration, or None if template not found
    """
    platform_templates = PIPELINE_TEMPLATES.get(platform, {})
    template = platform_templates.get(template_name, {})
    
    if not template:
        return None
    
    # Get template content
    template_content = template.get("template", "")
    
    # Get default variables
    default_vars = template.get("variables", {})
    
    # Merge provided variables with defaults
    merged_vars = {**default_vars, **variables}
    
    # Apply variables to template
    for var_name, var_value in merged_vars.items():
        placeholder = f"{{{{{var_name}}}}}"
        template_content = template_content.replace(placeholder, str(var_value))
    
    return template_content
