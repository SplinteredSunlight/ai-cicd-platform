import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.auto_patcher import AutoPatcher
from models.pipeline_debug import (
    PipelineError,
    PatchSolution,
    ErrorCategory,
    ErrorSeverity,
    PipelineStage
)

def test_auto_patcher_initialization():
    """
    Test that the AutoPatcher can be initialized correctly.
    """
    patcher = AutoPatcher()
    assert patcher is not None

@pytest.mark.asyncio
async def test_generate_dependency_patch(auto_patcher, sample_pipeline_error):
    """
    Test generating a dependency patch
    """
    # Set up a dependency error
    error = sample_pipeline_error
    error.category = ErrorCategory.DEPENDENCY
    error.message = "ModuleNotFoundError: No module named 'requests'"
    
    # Generate patch
    patch = await auto_patcher._generate_dependency_patch(error, {})
    
    # Verify patch
    assert patch is not None
    assert patch.patch_type == "dependency"
    assert "requests" in patch.patch_script
    assert patch.is_reversible
    assert "pip uninstall" in patch.rollback_script

@pytest.mark.asyncio
async def test_generate_permission_patch(auto_patcher):
    """
    Test generating a permission patch
    """
    # Set up a permission error
    error = PipelineError(
        error_id="test_error_2",
        message="PermissionError: [Errno 13] Permission denied: '/app/data/script.sh'",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.PERMISSION,
        stage=PipelineStage.BUILD,
        context={}
    )
    
    # Generate patch
    patch = await auto_patcher._generate_permission_patch(error, {})
    
    # Verify patch
    assert patch is not None
    assert patch.patch_type == "permission"
    assert "/app/data/script.sh" in patch.patch_script
    assert patch.is_reversible
    assert "chmod" in patch.rollback_script

@pytest.mark.asyncio
async def test_generate_config_patch(auto_patcher):
    """
    Test generating a configuration patch
    """
    # Set up a configuration error
    error = PipelineError(
        error_id="test_error_3",
        message="ConfigurationError: Missing environment variable: API_KEY",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.CONFIGURATION,
        stage=PipelineStage.BUILD,
        context={}
    )
    
    # Generate patch
    patch = await auto_patcher._generate_config_patch(error, {})
    
    # Verify patch
    assert patch is not None
    assert patch.patch_type == "configuration"
    assert "API_KEY" in patch.patch_script
    assert patch.is_reversible
    assert "dotenv" in patch.dependencies[0]

@pytest.mark.asyncio
async def test_simulate_patch(auto_patcher, sample_patch_solution):
    """
    Test simulating a patch
    """
    # Simulate patch
    result = await auto_patcher._simulate_patch(sample_patch_solution)
    
    # Verify result
    assert result is True

@pytest.mark.asyncio
async def test_validate_patch(auto_patcher, sample_patch_solution):
    """
    Test patch validation
    """
    # Valid patch
    assert auto_patcher._validate_patch(sample_patch_solution) is True
    
    # Invalid patch with dangerous command
    dangerous_patch = sample_patch_solution
    dangerous_patch.patch_script = "rm -rf /"
    assert auto_patcher._validate_patch(dangerous_patch) is False

@pytest.mark.asyncio
async def test_extract_code_from_solution(auto_patcher):
    """
    Test extracting code from AI solution text
    """
    solution_text = """
    Here's a solution to fix the dependency issue:
    
    ```python
    import subprocess
    subprocess.check_call(["pip", "install", "requests"])
    ```
    
    This will install the missing package.
    
    You can also try:
    
    ```bash
    pip install requests
    ```
    """
    
    code = auto_patcher._extract_code_from_solution(solution_text)
    
    assert "import subprocess" in code
    assert "pip install requests" in code

@pytest.mark.asyncio
async def test_extract_validation_steps(auto_patcher):
    """
    Test extracting validation steps from AI solution text
    """
    solution_text = """
    Here's a solution to fix the dependency issue:
    
    ```python
    import subprocess
    subprocess.check_call(["pip", "install", "requests"])
    ```
    
    ## Validation
    
    - Import the module to verify it's installed
    - Check the version using `requests.__version__`
    - Try making a simple request
    """
    
    steps = auto_patcher._extract_validation_steps(solution_text)
    
    assert len(steps) == 3
    assert "Import the module" in steps[0]
    assert "Check the version" in steps[1]
    assert "Try making a simple request" in steps[2]

@pytest.mark.asyncio
async def test_extract_package_name(auto_patcher):
    """
    Test extracting package name from error message
    """
    # Python import error
    error_message = "ModuleNotFoundError: No module named 'requests'"
    assert auto_patcher._extract_package_name(error_message) == "requests"
    
    # Node.js dependency error
    error_message = "npm ERR! missing: axios@^1.0.0"
    assert auto_patcher._extract_package_name(error_message) == "axios"
    
    # Invalid error message
    error_message = "Some other error"
    assert auto_patcher._extract_package_name(error_message) is None

@pytest.mark.asyncio
async def test_extract_path(auto_patcher):
    """
    Test extracting file path from error message
    """
    # Python permission error
    error_message = "PermissionError: [Errno 13] Permission denied: '/app/data/script.sh'"
    assert auto_patcher._extract_path(error_message) == "/app/data/script.sh"
    
    # Node.js permission error
    error_message = "EACCES: permission denied, access '/app/data/config.json'"
    assert auto_patcher._extract_path(error_message) == "/app/data/config.json"
    
    # Invalid error message
    error_message = "Some other error"
    assert auto_patcher._extract_path(error_message) is None

@pytest.mark.asyncio
async def test_generate_ai_solution(auto_patcher, sample_pipeline_error, mock_openai):
    """
    Test generating an AI solution
    """
    # Generate AI solution
    patch = await auto_patcher._generate_ai_solution(sample_pipeline_error, {})
    
    # Verify patch
    assert patch is not None
    assert patch.patch_type == "ai_generated"
    assert patch.requires_approval
    assert not patch.is_reversible
    assert patch.estimated_success_rate == 0.7
    
    # Verify OpenAI was called
    mock_openai.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_apply_patch(auto_patcher, sample_patch_solution):
    """
    Test applying a patch
    """
    # Mock the _simulate_patch method
    auto_patcher._simulate_patch = AsyncMock(return_value=True)
    
    # Apply patch in dry run mode
    result = await auto_patcher.apply_patch(sample_patch_solution, dry_run=True)
    
    # Verify result
    assert result is True
    assert sample_patch_solution.solution_id in auto_patcher.applied_patches
    
    # Verify _simulate_patch was called
    auto_patcher._simulate_patch.assert_called_once_with(sample_patch_solution)

@pytest.mark.asyncio
async def test_rollback_patch(auto_patcher, sample_patch_solution):
    """
    Test rolling back a patch
    """
    # Add patch to applied patches
    auto_patcher.applied_patches[sample_patch_solution.solution_id] = sample_patch_solution
    
    # Mock the _execute_script method
    auto_patcher._execute_script = AsyncMock(return_value=True)
    
    # Rollback patch
    result = await auto_patcher.rollback_patch(sample_patch_solution.solution_id)
    
    # Verify result
    assert result is True
    assert sample_patch_solution.solution_id not in auto_patcher.applied_patches
    
    # Verify _execute_script was called
    auto_patcher._execute_script.assert_called_once_with(sample_patch_solution.rollback_script)
