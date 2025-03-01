import pytest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock, call
from datetime import datetime
from rich.panel import Panel

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.cli_debugger import CLIDebugger
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

def test_cli_debugger_initialization():
    """
    Test that the CLIDebugger can be initialized correctly.
    """
    debugger = CLIDebugger()
    assert debugger is not None
    assert debugger.console is not None
    assert debugger.log_analyzer is not None
    assert debugger.auto_patcher is not None
    assert debugger.current_session is None
    assert debugger.command_history is not None
    assert debugger.auto_suggest is not None
    assert debugger.recent_commands == set()

@pytest.mark.asyncio
async def test_start_debug_session(monkeypatch):
    """
    Test starting a debug session
    """
    # Create mock objects
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
    
    mock_console = MagicMock()
    mock_handle_interactive = AsyncMock()
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.log_analyzer = mock_log_analyzer
    debugger.console = mock_console
    debugger._handle_interactive_session = mock_handle_interactive
    debugger._display_analysis_summary = AsyncMock()
    
    # Start debug session
    session = await debugger.start_debug_session("pipeline-123", "sample log content")
    
    # Verify session was created
    assert session is not None
    assert session.pipeline_id == "pipeline-123"
    assert session.status == "active"
    assert len(session.errors) == 1
    
    # Verify methods were called
    mock_log_analyzer.analyze_pipeline_logs.assert_called_once_with(
        "pipeline-123", "sample log content"
    )
    debugger._display_analysis_summary.assert_called_once()
    mock_handle_interactive.assert_called_once()

@pytest.mark.asyncio
async def test_display_errors():
    """
    Test displaying errors
    """
    # Create mock console
    mock_console = MagicMock()
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Create session with errors
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Display errors
    await debugger._display_errors()
    
    # Verify console.print was called at least twice (once for the table, once for severity distribution)
    assert mock_console.print.call_count >= 2

@pytest.mark.asyncio
async def test_analyze_specific_error(monkeypatch):
    """
    Test analyzing a specific error
    """
    # Create mock objects
    mock_log_analyzer = AsyncMock()
    mock_log_analyzer.get_error_analysis.return_value = AnalysisResult(
        error=PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        ),
        root_cause="Missing dependency",
        confidence_score=0.95,
        suggested_solutions=["Install requests package"],
        prevention_measures=["Add requests to requirements.txt"]
    )
    
    mock_console = MagicMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="test_error_1: ModuleNotFoundError")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    mock_confirm = MagicMock()
    mock_confirm.ask_async = AsyncMock(return_value=True)
    mock_questionary_confirm = MagicMock(return_value=mock_confirm)
    
    # Patch questionary
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    monkeypatch.setattr("services.cli_debugger.questionary.confirm", mock_questionary_confirm)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.log_analyzer = mock_log_analyzer
    debugger.console = mock_console
    
    # Create session with errors
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Analyze error
    await debugger._analyze_specific_error()
    
    # Verify methods were called
    mock_questionary_select.assert_called_once()
    mock_log_analyzer.get_error_analysis.assert_called_once()
    assert len(debugger.current_session.analysis_results) == 1

@pytest.mark.asyncio
async def test_handle_patch_application(monkeypatch):
    """
    Test handling patch application
    """
    # Create mock objects
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
    
    mock_console = MagicMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="test_error_1: ModuleNotFoundError")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    mock_confirm = MagicMock()
    mock_confirm.ask_async = AsyncMock(return_value=True)
    mock_questionary_confirm = MagicMock(return_value=mock_confirm)
    
    # Patch questionary
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    monkeypatch.setattr("services.cli_debugger.questionary.confirm", mock_questionary_confirm)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.auto_patcher = mock_auto_patcher
    debugger.console = mock_console
    
    # Create session with errors
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Handle patch application
    await debugger._handle_patch_application()
    
    # Verify methods were called
    mock_questionary_select.assert_called_once()
    mock_questionary_confirm.assert_called_once()
    mock_auto_patcher.generate_patch.assert_called_once()
    mock_auto_patcher.apply_patch.assert_called_once()
    assert len(debugger.current_session.applied_patches) == 1

@pytest.mark.asyncio
async def test_handle_patch_rollback(monkeypatch):
    """
    Test handling patch rollback
    """
    # Create mock objects
    mock_auto_patcher = AsyncMock()
    mock_auto_patcher.rollback_patch.return_value = True
    
    mock_console = MagicMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="patch_123: dependency")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    mock_confirm = MagicMock()
    mock_confirm.ask_async = AsyncMock(return_value=True)
    mock_questionary_confirm = MagicMock(return_value=mock_confirm)
    
    # Patch questionary
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    monkeypatch.setattr("services.cli_debugger.questionary.confirm", mock_questionary_confirm)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.auto_patcher = mock_auto_patcher
    debugger.console = mock_console
    
    # Create session with applied patches
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_patch(
        PatchSolution(
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
    )
    
    # Handle patch rollback
    await debugger._handle_patch_rollback()
    
    # Verify methods were called
    mock_questionary_select.assert_called_once()
    mock_questionary_confirm.assert_called_once()
    mock_auto_patcher.rollback_patch.assert_called_once_with("patch_123")

@pytest.mark.asyncio
async def test_display_session_summary():
    """
    Test displaying session summary
    """
    # Create mock console
    mock_console = MagicMock()
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Create session with data
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Display session summary
    await debugger._display_session_summary()
    
    # Verify console.print was called at least twice (once for summary table, once for category distribution)
    assert mock_console.print.call_count >= 2

@pytest.mark.asyncio
async def test_end_session(monkeypatch):
    """
    Test ending a debug session
    """
    # Create mock objects
    mock_console = MagicMock()
    mock_log_analyzer = AsyncMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_confirm = MagicMock()
    mock_confirm.ask_async = AsyncMock(return_value=False)  # Don't export
    mock_questionary_confirm = MagicMock(return_value=mock_confirm)
    
    # Patch questionary
    monkeypatch.setattr("services.cli_debugger.questionary.confirm", mock_questionary_confirm)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    debugger.log_analyzer = mock_log_analyzer
    debugger._export_debug_session = AsyncMock()
    
    # Create session
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    
    # End session
    await debugger._end_session()
    
    # Verify session was closed
    assert debugger.current_session.status == "completed"
    assert debugger.current_session.end_time is not None
    
    # Verify methods were called
    mock_questionary_confirm.assert_called_once()
    mock_log_analyzer.cleanup.assert_called_once()
    mock_console.print.assert_called_once()
    debugger._export_debug_session.assert_not_called()  # Should not be called since we mocked the confirm to return False

@pytest.mark.asyncio
async def test_handle_batch_patch_application(monkeypatch):
    """
    Test batch patch application
    """
    # Create mock objects
    mock_console = MagicMock()
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
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_confirm1 = MagicMock()
    mock_confirm1.ask_async = AsyncMock(return_value=True)
    mock_confirm2 = MagicMock()
    mock_confirm2.ask_async = AsyncMock(return_value=True)
    
    mock_questionary_confirm = MagicMock(side_effect=[mock_confirm1, mock_confirm2])
    
    # Patch questionary
    monkeypatch.setattr("services.cli_debugger.questionary.confirm", mock_questionary_confirm)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    debugger.auto_patcher = mock_auto_patcher
    
    # Create session with errors
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Handle batch patch application
    await debugger._handle_batch_patch_application()
    
    # Verify methods were called
    mock_questionary_confirm.assert_called()
    mock_auto_patcher.generate_patch.assert_called_once()
    mock_auto_patcher.apply_patch.assert_called()
    assert len(debugger.current_session.applied_patches) == 1

@pytest.mark.asyncio
async def test_export_debug_session(monkeypatch, tmpdir):
    """
    Test exporting debug session
    """
    # Create mock objects
    mock_console = MagicMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="JSON")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    # Patch questionary and os functions
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    monkeypatch.setattr("services.cli_debugger.os.makedirs", MagicMock())
    
    # Create a temporary directory for the test
    reports_dir = tmpdir.mkdir("debug_reports")
    monkeypatch.setattr("services.cli_debugger.os.path.join", lambda *args: str(reports_dir.join(args[-1])))
    
    # Mock open to avoid actual file writing
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Create session with data
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Export session
    await debugger._export_debug_session()
    
    # Verify methods were called
    mock_questionary_select.assert_called_once()
    mock_open.assert_called_once()
    mock_file.write.assert_called_once()
    mock_console.print.assert_called()

@pytest.mark.asyncio
async def test_display_help():
    """
    Test displaying help information
    """
    # Create mock console
    mock_console = MagicMock()
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Display help
    await debugger._display_help()
    
    # Verify console.print was called
    mock_console.print.assert_called_once()

@pytest.mark.asyncio
async def test_prompt_action(monkeypatch):
    """
    Test prompting for user action
    """
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="View all errors")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    # Patch questionary
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    
    # Create debugger instance
    debugger = CLIDebugger()
    
    # Prompt for action
    action = await debugger._prompt_action()
    
    # Verify action was converted to the expected format
    assert action == "view_all_errors"
    mock_questionary_select.assert_called_once()

@pytest.mark.asyncio
async def test_command_history():
    """
    Test command history functionality
    """
    # Create debugger instance
    debugger = CLIDebugger()
    
    # Add commands to history
    debugger.command_history.append_string("view_errors")
    debugger.command_history.append_string("analyze_error")
    debugger.recent_commands.add("view_errors")
    debugger.recent_commands.add("analyze_error")
    
    # Verify history
    assert "view_errors" in debugger.recent_commands
    assert "analyze_error" in debugger.recent_commands
    assert len(debugger.recent_commands) == 2
    
    # Verify history is used in auto-suggest
    assert debugger.auto_suggest is not None

@pytest.mark.asyncio
async def test_display_analysis_summary():
    """
    Test displaying analysis summary
    """
    # Create mock console
    mock_console = MagicMock()
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Create session with errors of different severities and categories
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_2",
            message="Permission denied: /var/log/app.log",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PERMISSION,
            stage=PipelineStage.DEPLOY,
            context={}
        )
    )
    
    # Display analysis summary
    await debugger._display_analysis_summary()
    
    # Verify console.print was called with a Panel
    mock_console.print.assert_called_once()
    # Verify that a Panel object was passed to print
    panel_arg = mock_console.print.call_args[0][0]
    assert isinstance(panel_arg, Panel)
    
    # Convert panel to string and check its content
    panel_str = panel_arg.renderable
    assert "Found 2 errors" in panel_str
    assert "Severity Distribution" in panel_str
    assert "Category Distribution" in panel_str

@pytest.mark.asyncio
async def test_generate_and_export_markdown_report(monkeypatch, tmpdir):
    """
    Test generating and exporting a markdown report
    """
    # Create mock objects
    mock_console = MagicMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="Markdown")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    # Patch questionary and os functions
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    monkeypatch.setattr("services.cli_debugger.os.makedirs", MagicMock())
    
    # Create a temporary directory for the test
    reports_dir = tmpdir.mkdir("debug_reports")
    monkeypatch.setattr("services.cli_debugger.os.path.join", lambda *args: str(reports_dir.join(args[-1])))
    
    # Mock open to capture the written content
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Create session with data
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    debugger.current_session.add_analysis(
        AnalysisResult(
            error=PipelineError(
                error_id="test_error_1",
                message="ModuleNotFoundError: No module named 'requests'",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DEPENDENCY,
                stage=PipelineStage.BUILD,
                context={}
            ),
            root_cause="Missing dependency",
            confidence_score=0.95,
            suggested_solutions=["Install requests package"],
            prevention_measures=["Add requests to requirements.txt"]
        )
    )
    
    # Export session
    await debugger._export_debug_session()
    
    # Verify methods were called
    mock_questionary_select.assert_called_once()
    mock_open.assert_called_once()
    
    # Verify markdown content was written
    write_content = mock_file.write.call_args[0][0]
    assert "# Debug Session Report" in write_content
    assert "## Error Analysis" in write_content
    assert "## Metrics" in write_content
    assert "## Recommendations" in write_content
    
    # Verify console preview was shown
    assert mock_console.print.call_count >= 2
    assert any("Report Preview" in str(args) for args, _ in mock_console.print.call_args_list)

@pytest.mark.asyncio
async def test_generate_and_export_text_report(monkeypatch, tmpdir):
    """
    Test generating and exporting a text report
    """
    # Create mock objects
    mock_console = MagicMock()
    
    # Create a mock for questionary that returns a mock with ask_async method
    mock_select = MagicMock()
    mock_select.ask_async = AsyncMock(return_value="Text")
    mock_questionary_select = MagicMock(return_value=mock_select)
    
    # Patch questionary and os functions
    monkeypatch.setattr("services.cli_debugger.questionary.select", mock_questionary_select)
    monkeypatch.setattr("services.cli_debugger.os.makedirs", MagicMock())
    
    # Create a temporary directory for the test
    reports_dir = tmpdir.mkdir("debug_reports")
    monkeypatch.setattr("services.cli_debugger.os.path.join", lambda *args: str(reports_dir.join(args[-1])))
    
    # Mock open to capture the written content
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    
    # Create session with data
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    
    # Export session
    await debugger._export_debug_session()
    
    # Verify methods were called
    mock_questionary_select.assert_called_once()
    mock_open.assert_called_once()
    
    # Verify text content was written
    write_content = mock_file.write.call_args[0][0]
    assert "DEBUG SESSION REPORT" in write_content
    assert "METRICS" in write_content
    assert "ERROR ANALYSIS" in write_content
    assert "RECOMMENDATIONS" in write_content

def test_generate_debug_report():
    """
    Test generating a debug report
    """
    # Create debugger instance
    debugger = CLIDebugger()
    
    # Create session with data
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    debugger.current_session.add_error(
        PipelineError(
            error_id="test_error_1",
            message="ModuleNotFoundError: No module named 'requests'",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            stage=PipelineStage.BUILD,
            context={}
        )
    )
    debugger.current_session.add_analysis(
        AnalysisResult(
            error=PipelineError(
                error_id="test_error_1",
                message="ModuleNotFoundError: No module named 'requests'",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DEPENDENCY,
                stage=PipelineStage.BUILD,
                context={}
            ),
            root_cause="Missing dependency",
            confidence_score=0.95,
            suggested_solutions=["Install requests package"],
            prevention_measures=["Add requests to requirements.txt"]
        )
    )
    
    # Generate report
    report = debugger._generate_debug_report()
    
    # Verify report
    assert isinstance(report, DebugReport)
    assert report.session == debugger.current_session
    assert len(report.error_analysis) == 1
    assert "duration" in report.metrics
    assert "success_rate" in report.metrics
    assert "errors_resolved" in report.metrics

@pytest.mark.asyncio
async def test_interactive_session_flow(monkeypatch):
    """
    Test the flow of an interactive debug session
    """
    # Create mock objects
    mock_console = MagicMock()
    mock_prompt_action = AsyncMock()
    mock_prompt_action.side_effect = [
        "view_errors",      # First action
        "analyze_error",    # Second action
        "view_session",     # Third action
        "exit"              # Exit the session
    ]
    
    mock_display_errors = AsyncMock()
    mock_analyze_error = AsyncMock()
    mock_display_session = AsyncMock()
    mock_end_session = AsyncMock()
    
    # Create debugger instance
    debugger = CLIDebugger()
    debugger.console = mock_console
    debugger._prompt_action = mock_prompt_action
    debugger._display_errors = mock_display_errors
    debugger._analyze_specific_error = mock_analyze_error
    debugger._display_session_summary = mock_display_session
    debugger._end_session = mock_end_session
    
    # Create session
    debugger.current_session = DebugSession(
        session_id="session-123",
        pipeline_id="pipeline-123"
    )
    
    # Run interactive session
    await debugger._handle_interactive_session()
    
    # Verify methods were called in the expected order
    assert mock_prompt_action.call_count == 4
    mock_display_errors.assert_called_once()
    mock_analyze_error.assert_called_once()
    mock_display_session.assert_called_once()
    mock_end_session.assert_called_once()
    
    # Verify command history was updated
    assert "view_errors" in debugger.recent_commands
    assert "analyze_error" in debugger.recent_commands
    assert "view_session" in debugger.recent_commands
    assert "exit" in debugger.recent_commands
