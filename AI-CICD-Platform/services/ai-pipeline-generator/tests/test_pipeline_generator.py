import pytest
from unittest.mock import Mock, patch, MagicMock
import yaml
from services.pipeline_generator import PipelineGeneratorService
from services.pipeline_optimizer import PipelineOptimizerService
from config import Settings
from services.platform_templates import get_supported_platforms

# Mock responses for different platforms
MOCK_RESPONSES = {
    "github-actions": """
name: Test Pipeline
on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          npm install
          npm test
""",
    "gitlab-ci": """
stages:
  - test

test_job:
  stage: test
  image: node:latest
  script:
    - npm install
    - npm test
  only:
    - main
""",
    "circle-ci": """
version: 2.1
jobs:
  test:
    docker:
      - image: cimg/node:16.13
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: npm install
      - run:
          name: Run tests
          command: npm test
workflows:
  version: 2
  test_workflow:
    jobs:
      - test
""",
    "jenkins": """
pipeline {
    agent {
        docker {
            image 'node:16-alpine'
        }
    }
    stages {
        stage('Test') {
            steps {
                sh 'npm install'
                sh 'npm test'
            }
        }
    }
}
"""
}

@pytest.fixture
def mock_openai_response(request):
    platform = getattr(request, "param", "github-actions")
    return Mock(
        choices=[
            Mock(
                message=Mock(
                    content=MOCK_RESPONSES.get(platform, MOCK_RESPONSES["github-actions"])
                )
            )
        ],
        usage=Mock(total_tokens=150)
    )

@pytest.fixture
def mock_optimizer():
    with patch('services.pipeline_generator.PipelineOptimizerService') as mock_optimizer_class:
        mock_optimizer = Mock()
        
        # Mock analyze_pipeline method
        mock_optimizer.analyze_pipeline.return_value = [
            {
                "name": "caching",
                "description": "Add Node.js dependency caching to speed up builds",
                "applies_to": "node",
                "priority": "high",
                "job_id": "build"
            },
            {
                "name": "matrix-builds",
                "description": "Use matrix builds for testing across multiple environments",
                "applies_to": "testing",
                "priority": "medium",
                "job_id": "build"
            }
        ]
        
        # Mock optimize_pipeline method
        mock_optimizer.optimize_pipeline.return_value = (
            # Optimized config
            {
                "name": "Node.js CI",
                "on": {
                    "push": {
                        "branches": ["master"]
                    },
                    "pull_request": {
                        "branches": ["master"]
                    }
                },
                "jobs": {
                    "build": {
                        "runs-on": "ubuntu-latest",
                        "strategy": {
                            "matrix": {
                                "node-version": [14, 16, 18],
                                "os": ["ubuntu-latest", "windows-latest"]
                            }
                        },
                        "steps": [
                            {"uses": "actions/checkout@v3"},
                            {
                                "name": "Cache Node.js dependencies",
                                "uses": "actions/cache@v3",
                                "with": {
                                    "path": "~/.npm",
                                    "key": "${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}",
                                    "restore-keys": "${{ runner.os }}-node-"
                                }
                            },
                            {
                                "name": "Use Node.js ${{ matrix.node-version }}",
                                "uses": "actions/setup-node@v3",
                                "with": {
                                    "node-version": "${{ matrix.node-version }}",
                                    "cache": "npm"
                                }
                            },
                            {"run": "npm ci"},
                            {"run": "npm test"}
                        ]
                    }
                }
            },
            # Applied optimizations
            [
                {
                    "name": "caching",
                    "description": "Added Node.js dependency caching to job 'build'",
                    "details": "Added caching step after checkout"
                },
                {
                    "name": "matrix-builds",
                    "description": "Added matrix build strategy to job 'build'",
                    "details": "Added matrix configuration for multiple environments"
                }
            ]
        )
        
        # Mock get_optimization_strategies method
        mock_optimizer.get_optimization_strategies.return_value = [
            {
                "name": "caching",
                "description": "Add dependency caching to speed up builds",
                "applies_to": ["node", "python", "java"],
                "priority": "high"
            },
            {
                "name": "matrix-builds",
                "description": "Use matrix builds for testing across multiple environments",
                "applies_to": ["testing"],
                "priority": "medium"
            }
        ]
        
        mock_optimizer_class.return_value = mock_optimizer
        yield mock_optimizer

@pytest.fixture
def pipeline_generator(mock_openai_response, mock_optimizer):
    with patch('services.pipeline_generator.OpenAI') as mock_openai:
        # Create a proper async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_openai_response
        
        # Set up the mock chain
        mock_completions = Mock()
        mock_completions.create = mock_create
        
        mock_chat = Mock()
        mock_chat.completions = mock_completions
        
        mock_client = Mock()
        mock_client.chat = mock_chat
        
        mock_openai.return_value = mock_client
        
        with patch('services.pipeline_generator.get_platform_guide') as mock_guide:
            mock_guide.return_value = {
                "syntax_guide": "Test syntax guide",
                "best_practices": ["Practice 1", "Practice 2"],
                "security_recommendations": ["Security 1", "Security 2"]
            }
            
            # Mock template functions
            with patch('services.pipeline_generator.get_available_templates') as mock_templates:
                mock_templates.return_value = {
                    "basic-node": {
                        "name": "Node.js CI",
                        "description": "Basic Node.js CI workflow with testing"
                    },
                    "docker-build-push": {
                        "name": "Docker Build and Push",
                        "description": "Build and push Docker image to registry"
                    }
                }
                
                with patch('services.pipeline_generator.get_template_variables') as mock_vars:
                    mock_vars.return_value = {
                        "node_version": "16",
                        "main_branch": "main",
                        "test_command": "npm test"
                    }
                    
                    with patch('services.pipeline_generator.apply_template') as mock_apply:
                        mock_apply.return_value = """
name: Node.js CI

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18]
        
    steps:
    - uses: actions/checkout@v3
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm test
"""
                        yield PipelineGeneratorService()

@pytest.mark.asyncio
@pytest.mark.parametrize("mock_openai_response,platform", [
    ("github-actions", "github-actions"),
    ("gitlab-ci", "gitlab-ci"),
    ("circle-ci", "circle-ci"),
    ("jenkins", "jenkins")
], indirect=["mock_openai_response"])
async def test_generate_pipeline_success(pipeline_generator, platform):
    result = await pipeline_generator.generate_pipeline(
        description="Run tests on push to main branch",
        platform=platform
    )
    
    assert result["status"] == "success"
    assert result["platform"] == platform
    assert isinstance(result["pipeline_config"], dict)
    
    # For YAML-based platforms, check for expected keys
    if platform != "jenkins":
        if platform == "github-actions":
            assert "name" in result["pipeline_config"]
        elif platform == "gitlab-ci":
            assert "stages" in result["pipeline_config"]
        elif platform == "circle-ci":
            assert "version" in result["pipeline_config"]
    else:
        # For Jenkins, we store the Jenkinsfile as a string in the "jenkinsfile" key
        assert "jenkinsfile" in result["pipeline_config"]
    
    assert result["metadata"]["tokens_used"] == 150

@pytest.mark.asyncio
async def test_generate_pipeline_invalid_platform(pipeline_generator):
    with pytest.raises(ValueError) as exc_info:
        await pipeline_generator.generate_pipeline(
            description="Test pipeline",
            platform="invalid-platform"
        )
    assert "Unsupported platform" in str(exc_info.value)

def test_validate_yaml_success(pipeline_generator):
    valid_yaml = """
name: Test
on:
  push:
    branches: [ main ]
"""
    assert pipeline_generator.validate_yaml(valid_yaml) is True

def test_validate_yaml_invalid(pipeline_generator):
    invalid_yaml = """
name: Test
  invalid:
    indentation
"""
    with pytest.raises(ValueError) as exc_info:
        pipeline_generator.validate_yaml(invalid_yaml)
    assert "Invalid YAML syntax" in str(exc_info.value)

def test_extract_yaml_or_code_block(pipeline_generator):
    # Test with markdown code block with language identifier
    content_with_markdown = """
Here's the pipeline configuration:

```yaml
name: Test
on:
  push:
    branches: [ main ]
```
    """
    extracted = pipeline_generator._extract_yaml_or_code_block(content_with_markdown)
    assert "name: Test" in extracted
    assert "```" not in extracted
    
    # Test with markdown code block without language identifier
    content_without_lang = """
Here's the pipeline:

```
name: Test
on:
  push:
    branches: [ main ]
```
    """
    extracted = pipeline_generator._extract_yaml_or_code_block(content_without_lang)
    assert "name: Test" in extracted
    assert "```" not in extracted
    
    # Test with no code blocks
    content_no_blocks = """
name: Test
on:
  push:
    branches: [ main ]
    """
    extracted = pipeline_generator._extract_yaml_or_code_block(content_no_blocks)
    assert "name: Test" in extracted

def test_get_supported_platforms(pipeline_generator):
    platforms = pipeline_generator.get_supported_platforms()
    assert isinstance(platforms, list)
    assert len(platforms) > 0
    assert "github-actions" in platforms
    assert "gitlab-ci" in platforms
    assert "circle-ci" in platforms

@pytest.mark.asyncio
async def test_generate_from_template(pipeline_generator):
    # Test generating a pipeline from a predefined template
    result = await pipeline_generator.generate_pipeline(
        description="Basic Node.js CI workflow",
        platform="github-actions",
        template_name="basic-node",
        template_vars={
            "node_version": "18",
            "main_branch": "master"
        }
    )
    
    assert result["status"] == "success"
    assert result["platform"] == "github-actions"
    assert result["template_used"] == "basic-node"
    assert isinstance(result["pipeline_config"], dict)
    assert result["metadata"]["source"] == "template"
    assert result["metadata"]["template_name"] == "basic-node"
    
    # Check that template variables were applied
    assert "master" in result["raw_content"]
    assert "18" in result["raw_content"]

def test_get_available_templates(pipeline_generator):
    templates = pipeline_generator.get_available_templates("github-actions")
    assert isinstance(templates, dict)
    assert len(templates) > 0
    assert "basic-node" in templates
    assert "docker-build-push" in templates
    
    # Check template info structure
    template_info = templates["basic-node"]
    assert "name" in template_info
    assert "description" in template_info

def test_get_template_variables(pipeline_generator):
    variables = pipeline_generator.get_template_variables("github-actions", "basic-node")
    assert isinstance(variables, dict)
    assert "node_version" in variables
    assert "main_branch" in variables
    assert "test_command" in variables

@pytest.mark.asyncio
async def test_generate_pipeline_with_optimization(pipeline_generator):
    """Test generating a pipeline with optimization."""
    result = await pipeline_generator.generate_pipeline(
        description="Run tests on push to main branch",
        platform="github-actions",
        optimize=True
    )
    
    assert result["status"] == "success"
    assert result["platform"] == "github-actions"
    assert "optimizations" in result
    assert "metadata" in result
    assert result["metadata"]["optimized"] is True

@pytest.mark.asyncio
async def test_generate_pipeline_with_specific_optimizations(pipeline_generator):
    """Test generating a pipeline with specific optimizations."""
    result = await pipeline_generator.generate_pipeline(
        description="Run tests on push to main branch",
        platform="github-actions",
        optimize=True,
        optimizations=["caching"]
    )
    
    assert result["status"] == "success"
    assert result["platform"] == "github-actions"
    assert "optimizations" in result
    assert "metadata" in result
    assert result["metadata"]["optimized"] is True

@pytest.mark.asyncio
async def test_generate_from_template_with_optimization(pipeline_generator):
    """Test generating a pipeline from a template with optimization."""
    result = await pipeline_generator.generate_pipeline(
        description="Basic Node.js CI workflow",
        platform="github-actions",
        template_name="basic-node",
        template_vars={
            "node_version": "18",
            "main_branch": "master"
        },
        optimize=True
    )
    
    assert result["status"] == "success"
    assert result["platform"] == "github-actions"
    assert result["template_used"] == "basic-node"
    assert "optimizations" in result
    assert "metadata" in result
    assert result["metadata"]["optimized"] is True

@pytest.mark.asyncio
async def test_optimize_pipeline(pipeline_generator):
    """Test optimizing an existing pipeline."""
    # Create a pipeline result to optimize
    pipeline_result = {
        "status": "success",
        "platform": "github-actions",
        "pipeline_config": {
            "name": "Test Pipeline",
            "on": {
                "push": {
                    "branches": ["main"]
                }
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v3"},
                        {"name": "Set up Node.js", "uses": "actions/setup-node@v3", "with": {"node-version": "16"}},
                        {"name": "Install dependencies", "run": "npm ci"},
                        {"name": "Run tests", "run": "npm test"}
                    ]
                }
            }
        },
        "raw_content": "name: Test Pipeline\non:\n  push:\n    branches: [main]\n...",
        "metadata": {
            "source": "ai",
            "model": "gpt-4",
            "tokens_used": 150
        }
    }
    
    result = await pipeline_generator.optimize_pipeline(pipeline_result)
    
    assert "optimizations" in result
    assert "metadata" in result
    assert result["metadata"]["optimized"] is True

@pytest.mark.asyncio
async def test_optimize_pipeline_with_specific_optimizations(pipeline_generator):
    """Test optimizing an existing pipeline with specific optimizations."""
    # Create a pipeline result to optimize
    pipeline_result = {
        "status": "success",
        "platform": "github-actions",
        "pipeline_config": {
            "name": "Test Pipeline",
            "on": {
                "push": {
                    "branches": ["main"]
                }
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v3"},
                        {"name": "Set up Node.js", "uses": "actions/setup-node@v3", "with": {"node-version": "16"}},
                        {"name": "Install dependencies", "run": "npm ci"},
                        {"name": "Run tests", "run": "npm test"}
                    ]
                }
            }
        },
        "raw_content": "name: Test Pipeline\non:\n  push:\n    branches: [main]\n...",
        "metadata": {
            "source": "ai",
            "model": "gpt-4",
            "tokens_used": 150
        }
    }
    
    result = await pipeline_generator.optimize_pipeline(pipeline_result, optimizations=["caching"])
    
    assert "optimizations" in result
    assert "metadata" in result
    assert result["metadata"]["optimized"] is True

def test_get_optimization_strategies(pipeline_generator):
    """Test getting optimization strategies."""
    strategies = pipeline_generator.get_optimization_strategies("github-actions")
    
    assert isinstance(strategies, list)
    assert len(strategies) > 0
    assert strategies[0]["name"] == "caching"

@pytest.mark.asyncio
async def test_analyze_pipeline(pipeline_generator):
    """Test analyzing a pipeline for optimization opportunities."""
    pipeline_config = {
        "name": "Test Pipeline",
        "on": {
            "push": {
                "branches": ["main"]
            }
        },
        "jobs": {
            "test": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v3"},
                    {"name": "Set up Node.js", "uses": "actions/setup-node@v3", "with": {"node-version": "16"}},
                    {"name": "Install dependencies", "run": "npm ci"},
                    {"name": "Run tests", "run": "npm test"}
                ]
            }
        }
    }
    
    recommendations = await pipeline_generator.analyze_pipeline("github-actions", pipeline_config)
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert recommendations[0]["name"] == "caching"
