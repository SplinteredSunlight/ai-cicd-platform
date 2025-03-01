import pytest
import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.log_analyzer import LogAnalyzer
from services.auto_patcher import AutoPatcher
from models.pipeline_debug import (
    PipelineError,
    AnalysisResult,
    PatchSolution,
    ErrorCategory,
    ErrorSeverity,
    PipelineStage
)

@pytest.fixture
def mock_elasticsearch():
    """
    Mock Elasticsearch client for testing
    """
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "error_id": "test_error_1",
                        "message": "ModuleNotFoundError: No module named 'requests'",
                        "severity": "HIGH",
                        "category": "DEPENDENCY",
                        "stage": "BUILD",
                        "context": {}
                    }
                }
            ]
        }
    }
    mock_es.index.return_value = {"result": "created"}
    return mock_es

@pytest.fixture
def mock_openai():
    """
    Mock OpenAI client for testing
    """
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    mock_message.content = """
    ## Analysis
    
    The error is caused by a missing dependency.
    
    ## Solution
    
    ```python
    import subprocess
    subprocess.check_call(["pip", "install", "requests"])
    ```
    
    ## Validation
    
    - Import the module to verify it's installed
    - Check the version
    """
    
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    
    mock_chat = AsyncMock()
    mock_chat.completions.create.return_value = mock_completion
    
    mock_client.chat = mock_chat
    return mock_client

@pytest.fixture
def sample_pipeline_error():
    """
    Sample pipeline error for testing
    """
    return PipelineError(
        error_id="test_error_1",
        message="ModuleNotFoundError: No module named 'requests'",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.DEPENDENCY,
        stage=PipelineStage.BUILD,
        context={
            "line_number": 10,
            "file": "app/main.py"
        }
    )

@pytest.fixture
def sample_patch_solution():
    """
    Sample patch solution for testing
    """
    return PatchSolution(
        solution_id="patch_123456789",
        error_id="test_error_1",
        patch_type="dependency",
        patch_script="import subprocess\nsubprocess.check_call(['pip', 'install', 'requests'])",
        is_reversible=True,
        requires_approval=True,
        estimated_success_rate=0.9,
        dependencies=[],
        validation_steps=["import requests", "print(requests.__version__)"],
        rollback_script="pip uninstall -y requests"
    )

@pytest.fixture
def log_analyzer(mock_elasticsearch, mock_openai):
    """
    LogAnalyzer instance with mocked dependencies
    """
    analyzer = LogAnalyzer()
    analyzer.es_client = mock_elasticsearch
    analyzer.openai_client = mock_openai
    return analyzer

@pytest.fixture
def auto_patcher(mock_openai):
    """
    AutoPatcher instance with mocked dependencies
    """
    patcher = AutoPatcher()
    patcher.openai_client = mock_openai
    return patcher
