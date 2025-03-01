import pytest
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.log_analyzer import LogAnalyzer
from models.pipeline_debug import PipelineError, ErrorCategory, ErrorSeverity, PipelineStage

def test_log_analyzer_initialization():
    """
    Test that the LogAnalyzer can be initialized correctly.
    """
    analyzer = LogAnalyzer()
    assert analyzer is not None

@pytest.mark.asyncio
async def test_log_pattern_detection():
    """
    Test the log pattern detection functionality.
    """
    analyzer = LogAnalyzer()
    
    # Example log entry for testing
    sample_log = """
    2023-01-01 12:00:00 ERROR [PipelineExecutor] ModuleNotFoundError: No module named 'requests'
    2023-01-01 12:00:01 ERROR [PipelineExecutor] Failed to import required dependency
    2023-01-01 12:00:02 ERROR [PipelineExecutor] PermissionError: [Errno 13] Permission denied: '/app/data/output.log'
    """
    
    # Call the analyzer with the sample log
    errors = await analyzer._match_error_patterns(sample_log)
    
    # Assert that the correct number of errors were detected
    assert len(errors) > 0
    
    # Check if dependency error was detected
    dependency_errors = [e for e in errors if e.category == ErrorCategory.DEPENDENCY]
    assert len(dependency_errors) > 0
    assert "No module named" in dependency_errors[0].message
    
    # Check if permission error was detected
    permission_errors = [e for e in errors if e.category == ErrorCategory.PERMISSION]
    assert len(permission_errors) > 0
    assert "Permission denied" in permission_errors[0].message

@pytest.mark.asyncio
async def test_error_severity_determination():
    """
    Test the error severity determination functionality.
    """
    analyzer = LogAnalyzer()
    
    # Test critical severity
    assert analyzer._determine_severity("CRITICAL: System crash") == ErrorSeverity.CRITICAL
    assert analyzer._determine_severity("Fatal error in main process") == ErrorSeverity.CRITICAL
    
    # Test high severity
    assert analyzer._determine_severity("ERROR: Invalid configuration") == ErrorSeverity.HIGH
    assert analyzer._determine_severity("Missing required parameter") == ErrorSeverity.HIGH
    
    # Test medium severity
    assert analyzer._determine_severity("WARNING: Deprecated function used") == ErrorSeverity.MEDIUM
    
    # Test low severity (default)
    assert analyzer._determine_severity("Info: Process completed") == ErrorSeverity.LOW

@pytest.mark.asyncio
async def test_pipeline_stage_determination():
    """
    Test the pipeline stage determination functionality.
    """
    analyzer = LogAnalyzer()
    
    # Test different pipeline stages
    assert analyzer._determine_stage("git checkout failed") == PipelineStage.CHECKOUT
    assert analyzer._determine_stage("build process error") == PipelineStage.BUILD
    assert analyzer._determine_stage("test suite failed") == PipelineStage.TEST
    assert analyzer._determine_stage("security scan detected vulnerabilities") == PipelineStage.SECURITY_SCAN
    assert analyzer._determine_stage("deployment to production failed") == PipelineStage.DEPLOY
    assert analyzer._determine_stage("health check after deployment failed") == PipelineStage.POST_DEPLOY
    
    # Test default stage
    assert analyzer._determine_stage("unknown error message") == PipelineStage.BUILD
