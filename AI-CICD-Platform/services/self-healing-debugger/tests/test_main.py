import pytest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, debug_service
from models.pipeline_debug import (
    DebugSession,
    PipelineError,
    AnalysisResult,
    PatchSolution,
    DebugReport,
    ErrorCategory,
    ErrorSeverity,
    PipelineStage
)

# Create test client
client = TestClient(app)

def test_root_endpoint():
    """
    Test the root endpoint
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "self-healing-debugger"
    assert "version" in response.json()

@pytest.mark.asyncio
async def test_analyze_pipeline_endpoint(monkeypatch):
    """
    Test the analyze pipeline endpoint
    """
    # Create mock log analyzer
    mock_log_analyzer = AsyncMock()
    mock_log_analyzer.analyze_pipeline_logs.return_value = [
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    ]
    
    # Patch the debug_service
    original_get_log_analyzer = debug_service.get_log_analyzer
    debug_service.get_log_analyzer = lambda: mock_log_analyzer
    
    try:
        # Make request
        response = client.post(
            "/api/v1/debug/analyze",
            params={
                "pipeline_id": "pipeline-123",
                "log_content": "sample log content"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["pipeline_id"] == "pipeline-123"
        assert len(response.json()["errors"]) == 1
        
        # Verify mock was called
        mock_log_analyzer.analyze_pipeline_logs.assert_called_once_with(
            "pipeline-123", "sample log content"
        )
    
    finally:
        # Restore original method
        debug_service.get_log_analyzer = original_get_log_analyzer

@pytest.mark.asyncio
async def test_generate_patch_endpoint(monkeypatch):
    """
    Test the generate patch endpoint
    """
    # Create mock auto patcher
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.generate_patch.return_value = PatchSolution(
        solution_id="patch_123",
        error_id="test_error_1",
        patch_type="dependency",
        patch_script="pip install requests",
        is_reversible=True,
        requires_approval=True,
        estimated_success_rate=0.9,
        dependencies=[],
        validation_steps=["import requests"],
        rollback_script="pip uninstall -y requests"
    )
    
    # Patch the debug_service
    original_get_auto_patcher = debug_service.get_auto_patcher
    debug_service.get_auto_patcher = lambda: mock_auto_patcher
    
    try:
        # Create test error
        error = PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
        
        # Make request
        response = client.post(
            "/api/v1/debug/patch",
            json=error.dict(),
            params={"context": {}}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["solution_id"] == "patch_123"
        assert response.json()["error_id"] == "test_error_1"
        assert response.json()["patch_type"] == "dependency"
        
        # Verify mock was called
        mock_auto_patcher.generate_patch.assert_called_once()
    
    finally:
        # Restore original method
        debug_service.get_auto_patcher = original_get_auto_patcher

@pytest.mark.asyncio
async def test_apply_patch_endpoint(monkeypatch):
    """
    Test the apply patch endpoint
    """
    # Create mock auto patcher
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.apply_patch.return_value = True
    
    # Patch the debug_service
    original_get_auto_patcher = debug_service.get_auto_patcher
    debug_service.get_auto_patcher = lambda: mock_auto_patcher
    
    try:
        # Create test patch
        patch = PatchSolution(
            solution_id="patch_123",
            error_id="test_error_1",
            patch_type="dependency",
            patch_script="pip install requests",
            is_reversible=True,
            requires_approval=True,
            estimated_success_rate=0.9,
            dependencies=[],
            validation_steps=["import requests"],
            rollback_script="pip uninstall -y requests"
        )
        
        # Make request
        response = client.post(
            "/api/v1/debug/apply-patch",
            json=patch.dict(),
            params={"dry_run": True}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["dry_run"] is True
        assert response.json()["patch_id"] == "patch_123"
        
        # Verify mock was called
        mock_auto_patcher.apply_patch.assert_called_once()
    
    finally:
        # Restore original method
        debug_service.get_auto_patcher = original_get_auto_patcher

@pytest.mark.asyncio
async def test_rollback_patch_endpoint(monkeypatch):
    """
    Test the rollback patch endpoint
    """
    # Create mock auto patcher
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.rollback_patch.return_value = True
    
    # Patch the debug_service
    original_get_auto_patcher = debug_service.get_auto_patcher
    debug_service.get_auto_patcher = lambda: mock_auto_patcher
    
    try:
        # Make request
        response = client.post(
            "/api/v1/debug/rollback",
            params={"patch_id": "patch_123"}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["patch_id"] == "patch_123"
        
        # Verify mock was called
        mock_auto_patcher.rollback_patch.assert_called_once_with("patch_123")
    
    finally:
        # Restore original method
        debug_service.get_auto_patcher = original_get_auto_patcher

@pytest.mark.asyncio
async def test_batch_apply_patches_endpoint(monkeypatch):
    """
    Test the batch apply patches endpoint
    """
    # Create mock auto patcher
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.generate_patch.return_value = PatchSolution(
        solution_id="patch_123",
        error_id="test_error_1",
        patch_type="dependency",
        patch_script="pip install requests",
        is_reversible=True,
        requires_approval=True,
        estimated_success_rate=0.9,
        dependencies=[],
        validation_steps=["import requests"],
        rollback_script="pip uninstall -y requests"
    )
    mock_auto_patcher.apply_patch.return_value = True
    
    # Create mock session
    mock_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    mock_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    mock_session.add_error(
        PipelineError(
            error_id="test_error_2",
            message="PermissionError: Permission denied",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PERMISSION,
            stage=PipelineStage.DEPLOY,
            context={}
        )
    )
    
    # Patch the debug_service
    original_get_auto_patcher = debug_service.get_auto_patcher
    debug_service.get_auto_patcher = lambda: mock_auto_patcher
    debug_service.active_sessions = {"pipeline-123": mock_session}
    
    try:
        # Make request
        response = client.post(
            "/api/v1/debug/batch-apply-patches",
            json=["test_error_1", "test_error_2"],
            params={
                "pipeline_id": "pipeline-123",
                "dry_run": True
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["dry_run"] is True
        assert len(response.json()["results"]) == 2
        assert response.json()["success_count"] == 2
        assert response.json()["failure_count"] == 0
        
        # Verify mock was called
        assert mock_auto_patcher.generate_patch.call_count == 2
        assert mock_auto_patcher.apply_patch.call_count == 2
    
    finally:
        # Restore original method
        debug_service.get_auto_patcher = original_get_auto_patcher
        debug_service.active_sessions = {}

@pytest.mark.asyncio
async def test_export_session_endpoint(monkeypatch, tmpdir):
    """
    Test the export session endpoint
    """
    # Create mock CLI debugger
    mock_cli_debugger = MagicMock()
    mock_cli_debugger._generate_debug_report.return_value = DebugReport(
        session=DebugSession(
            session_id="session-123",
            pipeline_id="pipeline-123"
        ),
        summary="Test debug session",
        error_analysis=[],
        solutions_applied=[],
        recommendations=["Fix dependencies"],
        metrics={
            "duration": 60.0,
            "success_rate": 0.0,
            "errors_resolved": 0
        }
    )
    mock_cli_debugger._generate_markdown_report.return_value = "# Debug Report"
    mock_cli_debugger._generate_text_report.return_value = "DEBUG REPORT"
    
    # Create mock session
    mock_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    
    # Patch the debug_service and file operations
    original_get_cli_debugger = debug_service.get_cli_debugger
    debug_service.get_cli_debugger = lambda: mock_cli_debugger
    debug_service.active_sessions = {"pipeline-123": mock_session}
    
    # Create a temporary directory for the test
    reports_dir = tmpdir.mkdir("debug_reports")
    
    # Mock os.path.join and open
    original_join = os.path.join
    os.path.join = lambda *args: str(reports_dir.join(args[-1]))
    
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    original_open = open
    
    try:
        with patch("builtins.open", mock_open):
            # Test JSON format
            response = client.post(
                "/api/v1/debug/export-session",
                params={
                    "pipeline_id": "pipeline-123",
                    "format": "json"
                }
            )
            
            # Verify response
            assert response.status_code == 200
            assert mock_cli_debugger._generate_debug_report.call_count == 1
            assert mock_open.call_count == 1
            assert mock_file.write.call_count == 1
            
            # Reset mocks
            mock_cli_debugger.reset_mock()
            mock_open.reset_mock()
            mock_file.reset_mock()
            
            # Test Markdown format
            response = client.post(
                "/api/v1/debug/export-session",
                params={
                    "pipeline_id": "pipeline-123",
                    "format": "markdown"
                }
            )
            
            # Verify response
            assert response.status_code == 200
            assert mock_cli_debugger._generate_debug_report.call_count == 1
            assert mock_cli_debugger._generate_markdown_report.call_count == 1
            assert mock_open.call_count == 1
            assert mock_file.write.call_count == 1
    
    finally:
        # Restore original methods
        debug_service.get_cli_debugger = original_get_cli_debugger
        debug_service.active_sessions = {}
        os.path.join = original_join

@pytest.mark.asyncio
async def test_error_handling(monkeypatch):
    """
    Test error handling in endpoints
    """
    # Create mock auto patcher that raises an exception
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.rollback_patch.side_effect = ValueError("Patch not found")
    
    # Patch the debug_service
    original_get_auto_patcher = debug_service.get_auto_patcher
    debug_service.get_auto_patcher = lambda: mock_auto_patcher
    
    try:
        # Make request
        response = client.post(
            "/api/v1/debug/rollback",
            params={"patch_id": "nonexistent_patch"}
        )
        
        # Verify response
        assert response.status_code == 400
        assert "Patch not found" in response.json()["detail"]
        
        # Verify mock was called
        mock_auto_patcher.rollback_patch.assert_called_once_with("nonexistent_patch")
    
    finally:
        # Restore original method
        debug_service.get_auto_patcher = original_get_auto_patcher

@pytest.mark.asyncio
async def test_session_not_found_error(monkeypatch):
    """
    Test error handling when session is not found
    """
    # Create mock CLI debugger
    mock_cli_debugger = MagicMock()
    
    # Patch the debug_service
    original_get_cli_debugger = debug_service.get_cli_debugger
    debug_service.get_cli_debugger = lambda: mock_cli_debugger
    debug_service.active_sessions = {}  # Empty sessions
    
    try:
        # Make request to export session
        response = client.post(
            "/api/v1/debug/export-session",
            params={
                "pipeline_id": "nonexistent_pipeline",
                "format": "json"
            }
        )
        
        # Verify response
        assert response.status_code == 404
        assert "No active session found" in response.json()["detail"]
        
    finally:
        # Restore original method
        debug_service.get_cli_debugger = original_get_cli_debugger

@pytest.mark.asyncio
async def test_websocket_debug_session(monkeypatch):
    """
    Test the WebSocket debug session endpoint
    """
    # Create mock log analyzer
    mock_log_analyzer = AsyncMock()
    mock_log_analyzer.analyze_pipeline_logs.return_value = [
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    ]
    
    # Create mock auto patcher
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.generate_patch.return_value = PatchSolution(
        solution_id="patch_123",
        error_id="test_error_1",
        patch_type="dependency",
        patch_script="pip install requests",
        is_reversible=True,
        requires_approval=True,
        estimated_success_rate=0.9,
        dependencies=[],
        validation_steps=["import requests"],
        rollback_script="pip uninstall -y requests"
    )
    mock_auto_patcher.apply_patch.return_value = True
    mock_auto_patcher.rollback_patch.return_value = True
    
    # Create mock CLI debugger
    mock_cli_debugger = MagicMock()
    mock_cli_debugger.log_analyzer = mock_log_analyzer
    mock_cli_debugger.auto_patcher = mock_auto_patcher
    mock_cli_debugger.start_debug_session = AsyncMock()
    mock_cli_debugger.start_debug_session.return_value = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    mock_cli_debugger._generate_debug_report.return_value = DebugReport(
        session=DebugSession(
            session_id="session-123",
            pipeline_id="pipeline-123"
        ),
        summary="Test debug session",
        error_analysis=[],
        solutions_applied=[],
        recommendations=["Fix dependencies"],
        metrics={
            "duration": 60.0,
            "success_rate": 0.0,
            "errors_resolved": 0
        }
    )
    mock_cli_debugger._generate_markdown_report.return_value = "# Debug Report"
    mock_cli_debugger._generate_text_report.return_value = "DEBUG REPORT"
    
    # Patch the debug_service
    original_get_cli_debugger = debug_service.get_cli_debugger
    debug_service.get_cli_debugger = lambda: mock_cli_debugger
    
    try:
        # Test WebSocket connection
        with client.websocket_connect("/ws/debug-session") as websocket:
            # Send initial parameters
            websocket.send_json({
                "pipeline_id": "pipeline-123",
                "log_content": "sample log content"
            })
            
            # Receive session update
            response = websocket.receive_json()
            assert response["type"] == "session_update"
            assert "data" in response
            
            # Test analyze_error command
            websocket.send_json({
                "command": "analyze_error",
                "error_id": "test_error_1"
            })
            
            # Receive analysis result
            response = websocket.receive_json()
            assert response["type"] == "analysis_result" or response["type"] == "error"
            
            # Test generate_patch command
            websocket.send_json({
                "command": "generate_patch",
                "error_id": "test_error_1"
            })
            
            # Receive patch solution
            response = websocket.receive_json()
            assert response["type"] == "patch_solution" or response["type"] == "error"
            
            # Test apply_patch command
            websocket.send_json({
                "command": "apply_patch",
                "patch": {
                    "solution_id": "patch_123",
                    "error_id": "test_error_1",
                    "patch_type": "dependency",
                    "patch_script": "pip install requests",
                    "is_reversible": True,
                    "requires_approval": True,
                    "estimated_success_rate": 0.9,
                    "dependencies": [],
                    "validation_steps": ["import requests"],
                    "rollback_script": "pip uninstall -y requests"
                },
                "dry_run": True
            })
            
            # Receive patch applied result
            response = websocket.receive_json()
            assert response["type"] == "patch_applied" or response["type"] == "error"
            
            # Test get_session_summary command
            websocket.send_json({
                "command": "get_session_summary"
            })
            
            # Receive session summary
            response = websocket.receive_json()
            assert response["type"] == "session_summary" or response["type"] == "error"
            
            # Test export_session command
            websocket.send_json({
                "command": "export_session",
                "format": "json"
            })
            
            # Receive exported session
            response = websocket.receive_json()
            assert response["type"] == "session_exported" or response["type"] == "error"
            
            # Test exit command
            websocket.send_json({
                "command": "exit"
            })
            
            # WebSocket should close
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
    
    finally:
        # Restore original method
        debug_service.get_cli_debugger = original_get_cli_debugger

@pytest.mark.asyncio
async def test_websocket_error_handling(monkeypatch):
    """
    Test error handling in WebSocket endpoint
    """
    # Create mock CLI debugger that raises an exception
    mock_cli_debugger = MagicMock()
    mock_cli_debugger.start_debug_session = AsyncMock()
    mock_cli_debugger.start_debug_session.side_effect = Exception("Failed to start session")
    
    # Patch the debug_service
    original_get_cli_debugger = debug_service.get_cli_debugger
    debug_service.get_cli_debugger = lambda: mock_cli_debugger
    
    try:
        # Test WebSocket connection
        with client.websocket_connect("/ws/debug-session") as websocket:
            # Send initial parameters
            websocket.send_json({
                "pipeline_id": "pipeline-123",
                "log_content": "sample log content"
            })
            
            # Receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Failed to start session" in response["message"]
            
            # WebSocket should close
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()
    
    finally:
        # Restore original method
        debug_service.get_cli_debugger = original_get_cli_debugger
