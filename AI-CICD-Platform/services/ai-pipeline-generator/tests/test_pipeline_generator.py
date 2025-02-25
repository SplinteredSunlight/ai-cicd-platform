import pytest
from unittest.mock import Mock, patch
import yaml
from services.pipeline_generator import PipelineGeneratorService
from config import Settings

@pytest.fixture
def mock_openai_response():
    return Mock(
        choices=[
            Mock(
                message=Mock(
                    content="""
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
"""
                )
            )
        ],
        usage=Mock(total_tokens=150)
    )

@pytest.fixture
def pipeline_generator():
    with patch('services.pipeline_generator.OpenAI') as mock_openai:
        mock_openai.return_value = Mock(
            chat=Mock(
                completions=Mock(
                    create=Mock(return_value=mock_openai_response())
                )
            )
        )
        yield PipelineGeneratorService()

@pytest.mark.asyncio
async def test_generate_pipeline_success(pipeline_generator):
    result = await pipeline_generator.generate_pipeline(
        description="Run tests on push to main branch",
        platform="github-actions"
    )
    
    assert result["status"] == "success"
    assert result["platform"] == "github-actions"
    assert isinstance(result["pipeline_config"], dict)
    assert "name" in result["pipeline_config"]
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
