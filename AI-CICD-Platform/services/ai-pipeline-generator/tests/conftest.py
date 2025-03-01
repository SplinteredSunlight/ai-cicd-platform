import pytest
import os
import sys
from typing import Generator
from fastapi.testclient import TestClient

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    yield
    # Cleanup
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("DEBUG", None)

@pytest.fixture
def test_client() -> Generator:
    """Create a test client for FastAPI app"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_pipeline_request():
    """Sample pipeline generation request data"""
    return {
        "description": "Build and test a Python application, run pytest, and deploy to AWS Lambda",
        "platform": "github-actions",
        "template_vars": {
            "python_version": "3.11",
            "aws_region": "us-west-2"
        }
    }

@pytest.fixture
def sample_pipeline_response():
    """Sample pipeline generation response data"""
    return {
        "status": "success",
        "platform": "github-actions",
        "pipeline_config": {
            "name": "Python CI/CD",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v2"},
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v2",
                            "with": {"python-version": "3.11"}
                        }
                    ]
                }
            }
        },
        "metadata": {
            "model": "gpt-4",
            "tokens_used": 150
        }
    }
