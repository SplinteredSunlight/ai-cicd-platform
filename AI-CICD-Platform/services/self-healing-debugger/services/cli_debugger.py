from typing import List, Dict, Optional, Set, Counter
import asyncio
import uuid
import os
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
from rich.markdown import Markdown
import questionary
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from config import get_settings, CLI_THEME
from models.pipeline_debug import (
    DebugSession,
    PipelineError,
    AnalysisResult,
    PatchSolution,
    DebugReport
)
from .log_analyzer import LogAnalyzer
from .auto_patcher import AutoPatcher

class CLIDebugger:
    def __init__(self):
        self.settings = get_settings()
        self.console = Console()
        self.log_analyzer = LogAnalyzer()
        self.auto_patcher = AutoPatcher()
        self.current_session: Optional[DebugSession] = None
        self.command_history = InMemoryHistory()
        self.auto_suggest = AutoSuggestFromHistory()
        self.recent_commands: Set[str] = set()
        self.command_sequence: List[str] = []  # Track command sequence for flow visualization

    async def start_debug_session(
        self,
        pipeline_id: str,
        log_content: str
    ) -> DebugSession:
        """
        Start a new interactive debug session
        """
        try:
            # Create new session
            self.current_session = DebugSession(
                session_id=str(uuid.uuid4()),
                pipeline_id=pipeline_id
            )

            # Initial analysis
            self.console.print("\n[bold blue]Starting pipeline analysis...[/]")
            with Progress() as progress:
                task = progress.add_task("[cyan]Analyzing logs...", total=100)
                
                # Analyze logs
                errors = await self.log_analyzer.analyze_pipeline_logs(
                    pipeline_id,
                    log_content
                )
                progress.update(task, advance=50)
                
                # Add errors to session
                for error in errors:
                    self.current_session.add_error(error)
                progress.update(task, advance=50)

            # Display results
            await self._display_analysis_summary()
            
            # Start interactive session
            await self._handle_interactive_session()
            
            return self.current_session

        except Exception as e:
            self.console.print(f"[bold red]Error starting debug session: {str(e)}[/]")
            raise

    async def _handle_interactive_session(self):
        """
        Handle interactive debugging session
        """
        while True:
            action = await self._prompt_action()
            
            # Add command to history
            self.command_history.append_string(action)
            self.recent_commands.add(action)
            self.command_sequence.append(action)  # Add to sequence for flow visualization
            
            if action == "view_errors":
                await self._display_errors()
            elif action == "analyze_error":
                await self._analyze_specific_error()
            elif action == "apply_patch":
                await self._handle_patch_application()
            elif action == "apply_all_patches":
                await self._handle_batch_patch_application()
            elif action == "rollback_patch":
                await self._handle_patch_rollback()
            elif action == "view_session":
                await self._display_session_summary()
            elif action == "view_history":
                await self._display_command_history()
            elif action == "export_session":
                await self._export_debug_session()
            elif action == "help":
                await self._display_help()
            elif action == "exit":
                await self._end_session()
                break

    async def _prompt_action(self) -> str:
        """
        Prompt user for next action
        """
        choices = [
            "View all errors",
            "Analyze specific error",
            "Apply patch solution",
            "Apply all patches",
            "Rollback patch",
            "View session summary",
            "View command history",
            "Export session",
            "Help",
            "Exit session"
        ]

        # Add auto-completion based on recent commands
        result = await questionary.select(
            "What would you like to do?",
            choices=choices,
            style=questionary.Style(
                [("qmark", "fg:cyan"), ("question", "bold")]
            ),
            use_arrow_keys=True,
            use_shortcuts=True
        ).ask_async()

        return result.lower().replace(" ", "_")

    async def _display_errors(self):
        """
        Display all errors in current session
        """
        if not self.current_session.errors:
            self.console.print("[yellow]No errors found in this session.[/]")
            return
            
        table = Table(title="Pipeline Errors")
        table.add_column("ID", style="cyan")
        table.add_column("Severity", style="magenta")
        table.add_column("Category", style="blue")
        table.add_column("Stage", style="green")
        table.add_column("Message", style="white")
        table.add_column("Analyzed", style="yellow")

        for error in self.current_session.errors:
            # Check if this error has been analyzed
            has_analysis = any(a.error.error_id == error.error_id for a in self.current_session.analysis_results)
            
            table.add_row(
                error.error_id,
                error.severity.value,
                error.category.value,
                error.stage.value,
                error.message[:100] + "..." if len(error.message) > 100 else error.message,
                "✓" if has_analysis else "✗"
            )

        self.console.print(table)
        
        # Show error count by severity
        severity_counts = {}
        for error in self.current_session.errors:
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
        severity_table = Table(title="Error Severity Distribution")
        severity_table.add_column("Severity", style="magenta")
        severity_table.add_column("Count", style="cyan")
        
        for severity, count in severity_counts.items():
            severity_table.add_row(severity, str(count))
            
        self.console.print(severity_table)

    async def _analyze_specific_error(self):
        """
        Analyze a specific error in detail
        """
        # Prompt for error selection
        error_choices = [
            f"{error.error_id}: {error.message[:50]}..."
            for error in self.current_session.errors
        ]

        # Call questionary.select directly
        selected = await questionary.select(
            "Select an error to analyze:",
            choices=error_choices
        ).ask_async()

        error_id = selected.split(":")[0]
        error = next(e for e in self.current_session.errors if e.error_id == error_id)

        # Generate analysis
        self.console.print("\n[bold blue]Analyzing error...[/]")
        analysis = await self.log_analyzer.get_error_analysis(error)
        self.current_session.add_analysis(analysis)

        # Display analysis
        self.console.print(Panel(
            f"[bold]Root Cause:[/]\n{analysis.root_cause}\n\n"
            f"[bold]Confidence Score:[/] {analysis.confidence_score}\n\n"
            f"[bold]Suggested Solutions:[/]\n" +
            "\n".join(f"- {solution}" for solution in analysis.suggested_solutions) +
            f"\n\n[bold]Prevention Measures:[/]\n" +
            "\n".join(f"- {measure}" for measure in analysis.prevention_measures),
            title=f"Analysis Results for {error_id}",
            border_style="blue"
        ))

    async def _handle_patch_application(self):
        """
        Handle patch solution application
        """
        # Select error to patch
        error_choices = [
            f"{error.error_id}: {error.message[:50]}..."
            for error in self.current_session.errors
        ]

        # Call questionary.select directly
        selected = await questionary.select(
            "Select an error to patch:",
            choices=error_choices
        ).ask_async()

        error_id = selected.split(":")[0]
        error = next(e for e in self.current_session.errors if e.error_id == error_id)

        # Generate patch
        self.console.print("\n[bold blue]Generating patch solution...[/]")
        patch = await self.auto_patcher.generate_patch(error, {})

        # Display patch
        self.console.print(Panel(
            Syntax(patch.patch_script, "python", theme="monokai"),
            title="Generated Patch",
            border_style="green"
        ))

        # Confirm application
        if await questionary.confirm(
            "Would you like to apply this patch?",
            default=False
        ).ask_async():
            # Apply patch
            self.console.print("\n[bold blue]Applying patch...[/]")
            success = await self.auto_patcher.apply_patch(patch, dry_run=False)

            if success:
                self.console.print("[bold green]Patch applied successfully![/]")
                self.current_session.add_patch(patch)
            else:
                self.console.print("[bold red]Patch application failed![/]")

    async def _handle_patch_rollback(self):
        """
        Handle patch rollback
        """
        if not self.current_session.applied_patches:
            self.console.print("[yellow]No patches have been applied in this session.[/]")
            return

        # Select patch to rollback
        patch_choices = [
            f"{patch.solution_id}: {patch.patch_type}"
            for patch in self.current_session.applied_patches
        ]

        # Call questionary.select directly
        selected = await questionary.select(
            "Select a patch to rollback:",
            choices=patch_choices
        ).ask_async()

        patch_id = selected.split(":")[0]

        # Confirm rollback
        if await questionary.confirm(
            "Are you sure you want to rollback this patch?",
            default=False
        ).ask_async():
            # Rollback patch
            self.console.print("\n[bold blue]Rolling back patch...[/]")
            success = await self.auto_patcher.rollback_patch(patch_id)

            if success:
                self.console.print("[bold green]Patch rolled back successfully![/]")
            else:
                self.console.print("[bold red]Patch rollback failed![/]")

    async def _display_session_summary(self):
        """
        Display debug session summary
        """
        table = Table(title="Debug Session Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        # Calculate session duration
        duration = (
            (self.current_session.end_time or datetime.utcnow()) - 
            self.current_session.start_time
        ).total_seconds()
        
        # Calculate success rate
        success_rate = 0
        if self.current_session.errors:
            resolved_errors = sum(
                1 for error in self.current_session.errors
                if any(patch.error_id == error.error_id for patch in self.current_session.applied_patches)
            )
            success_rate = (resolved_errors / len(self.current_session.errors)) * 100

        table.add_row("Session ID", self.current_session.session_id)
        table.add_row("Pipeline ID", self.current_session.pipeline_id)
        table.add_row("Start Time", self.current_session.start_time.isoformat())
        table.add_row("Duration", f"{duration:.2f} seconds")
        table.add_row("Status", self.current_session.status)
        table.add_row("Total Errors", str(len(self.current_session.errors)))
        table.add_row("Analyses Performed", str(len(self.current_session.analysis_results)))
        table.add_row("Patches Applied", str(len(self.current_session.applied_patches)))
        table.add_row("Success Rate", f"{success_rate:.1f}%")

        self.console.print(table)
        
        # Display error distribution by category
        if self.current_session.errors:
            category_counts = {}
            for error in self.current_session.errors:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                
            category_table = Table(title="Error Category Distribution")
            category_table.add_column("Category", style="blue")
            category_table.add_column("Count", style="cyan")
            category_table.add_column("Percentage", style="green")
            
            for category, count in category_counts.items():
                percentage = (count / len(self.current_session.errors)) * 100
                category_table.add_row(
                    category, 
                    str(count),
                    f"{percentage:.1f}%"
                )
                
            self.console.print(category_table)

    async def _display_analysis_summary(self):
        """
        Display initial analysis summary
        """
        error_count = len(self.current_session.errors)
        severity_counts = {}
        category_counts = {}

        for error in self.current_session.errors:
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1
            category_counts[error.category] = category_counts.get(error.category, 0) + 1

        self.console.print(Panel(
            f"[bold]Found {error_count} errors[/]\n\n"
            "[bold]Severity Distribution:[/]\n" +
            "\n".join(f"- {sev}: {count}" for sev, count in severity_counts.items()) +
            "\n\n[bold]Category Distribution:[/]\n" +
            "\n".join(f"- {cat}: {count}" for cat, count in category_counts.items()),
            title="Analysis Summary",
            border_style="blue"
        ))

    async def _display_command_history(self):
        """
        Display command history visualization
        """
        if not self.command_sequence:
            self.console.print("[yellow]No commands have been executed in this session yet.[/]")
            return
            
        # Count command frequencies
        command_counts = {}
        for cmd in self.command_sequence:
            command_counts[cmd] = command_counts.get(cmd, 0) + 1
            
        # Sort by frequency
        sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Create table
        table = Table(title="Command History")
        table.add_column("Command", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Frequency", style="green")
        
        # Calculate max count for bar scaling
        max_count = max(count for _, count in sorted_commands)
        
        for cmd, count in sorted_commands:
            # Format command name for display
            display_name = cmd.replace("_", " ").title()
            
            # Create bar visualization
            bar_width = 20  # Max width of bar
            bar_length = int((count / max_count) * bar_width)
            bar = "█" * bar_length + "░" * (bar_width - bar_length)
            
            # Add row
            table.add_row(
                display_name,
                str(count),
                bar
            )
            
        self.console.print(table)
        
        # Show command flow if there are enough commands
        if len(self.command_sequence) >= 3:
            self.console.print("\n[bold blue]Command Flow:[/]")
            
            # Get last 10 commands
            recent_flow = self.command_sequence[-10:]
            flow_text = " → ".join([cmd.replace("_", " ").title() for cmd in recent_flow])
            
            self.console.print(Panel(
                flow_text,
                title="Recent Command Sequence",
                border_style="blue"
            ))
            
            # Show command transitions
            if len(self.command_sequence) >= 5:
                self.console.print("\n[bold blue]Command Transitions:[/]")
                
                transitions = {}
                for i in range(len(self.command_sequence) - 1):
                    current = self.command_sequence[i]
                    next_cmd = self.command_sequence[i + 1]
                    
                    if current not in transitions:
                        transitions[current] = {}
                    
                    transitions[current][next_cmd] = transitions[current].get(next_cmd, 0) + 1
                
                transition_table = Table(title="Common Command Transitions")
                transition_table.add_column("From", style="cyan")
                transition_table.add_column("To", style="magenta")
                transition_table.add_column("Count", style="green")
                
                # Get top transitions
                flat_transitions = []
                for from_cmd, to_cmds in transitions.items():
                    for to_cmd, count in to_cmds.items():
                        flat_transitions.append((from_cmd, to_cmd, count))
                
                # Sort by count
                flat_transitions.sort(key=lambda x: x[2], reverse=True)
                
                # Show top 5 transitions
                for from_cmd, to_cmd, count in flat_transitions[:5]:
                    transition_table.add_row(
                        from_cmd.replace("_", " ").title(),
                        to_cmd.replace("_", " ").title(),
                        str(count)
                    )
                
                self.console.print(transition_table)

    async def _handle_batch_patch_application(self):
        """
        Handle batch application of patches for all errors
        """
        if not self.current_session.errors:
            self.console.print("[yellow]No errors to patch in this session.[/]")
            return
            
        # Get errors that don't have patches yet
        unpatched_errors = [
            error for error in self.current_session.errors
            if not any(patch.error_id == error.error_id for patch in self.current_session.applied_patches)
        ]
        
        if not unpatched_errors:
            self.console.print("[yellow]All errors already have patches applied.[/]")
            return
            
        self.console.print(f"\n[bold blue]Generating patches for {len(unpatched_errors)} errors...[/]")
        
        # Confirm batch operation
        if not await questionary.confirm(
            f"Generate and apply patches for {len(unpatched_errors)} errors?",
            default=False
        ).ask_async():
            return
            
        # Track success/failure
        successful_patches = 0
        failed_patches = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing errors...", total=len(unpatched_errors))
            
            for error in unpatched_errors:
                # Generate patch
                try:
                    patch = await self.auto_patcher.generate_patch(error, {})
                    
                    # Apply patch with dry run first
                    dry_run_success = await self.auto_patcher.apply_patch(patch, dry_run=True)
                    
                    if dry_run_success:
                        # Confirm application
                        self.console.print(Panel(
                            Syntax(patch.patch_script, "python", theme="monokai"),
                            title=f"Generated Patch for {error.error_id}",
                            border_style="green"
                        ))
                        
                        apply_patch = await questionary.confirm(
                            f"Apply patch for error {error.error_id}?",
                            default=False
                        ).ask_async()
                        
                        if apply_patch:
                            success = await self.auto_patcher.apply_patch(patch, dry_run=False)
                            
                            if success:
                                self.console.print(f"[bold green]Patch for {error.error_id} applied successfully![/]")
                                self.current_session.add_patch(patch)
                                successful_patches += 1
                            else:
                                self.console.print(f"[bold red]Patch application for {error.error_id} failed![/]")
                                failed_patches += 1
                    else:
                        self.console.print(f"[bold yellow]Dry run for {error.error_id} failed, skipping.[/]")
                        failed_patches += 1
                        
                except Exception as e:
                    self.console.print(f"[bold red]Error generating patch for {error.error_id}: {str(e)}[/]")
                    failed_patches += 1
                    
                progress.update(task, advance=1)
                
        # Summary
        self.console.print(f"\n[bold blue]Batch operation completed:[/]")
        self.console.print(f"[green]Successfully applied: {successful_patches}[/]")
        self.console.print(f"[red]Failed: {failed_patches}[/]")

    async def _export_debug_session(self):
        """
        Export debug session to a report file
        """
        if not self.current_session:
            self.console.print("[yellow]No active session to export.[/]")
            return
            
        # Generate report
        report = self._generate_debug_report()
        
        # Determine export format
        export_format = await questionary.select(
            "Select export format:",
            choices=["JSON", "Markdown", "Text"],
            style=questionary.Style([("qmark", "fg:cyan"), ("question", "bold")])
        ).ask_async()
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_report_{self.current_session.pipeline_id}_{timestamp}"
        
        if export_format == "JSON":
            filename += ".json"
            # Convert datetime objects to ISO format strings for JSON serialization
            report_dict = report.dict()
            if "start_time" in report_dict["session"]:
                report_dict["session"]["start_time"] = report_dict["session"]["start_time"].isoformat()
            if "end_time" in report_dict["session"] and report_dict["session"]["end_time"]:
                report_dict["session"]["end_time"] = report_dict["session"]["end_time"].isoformat()
            for error in report_dict.get("session", {}).get("errors", []):
                if "timestamp" in error:
                    error["timestamp"] = error["timestamp"].isoformat()
            content = json.dumps(report_dict, indent=2)
        elif export_format == "Markdown":
            filename += ".md"
            content = self._generate_markdown_report(report)
        else:  # Text
            filename += ".txt"
            content = self._generate_text_report(report)
            
        # Save to file
        reports_dir = "debug_reports"
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(content)
            
        self.console.print(f"[bold green]Debug report exported to: {filepath}[/]")
        
        # Preview report if markdown
        if export_format == "Markdown":
            self.console.print("\n[bold blue]Report Preview:[/]")
            self.console.print(Markdown(content[:500] + "...\n\n(truncated)"))

    async def _display_help(self):
        """
        Display help information
        """
        help_text = """
# Self-Healing Debugger Help

## Available Commands

- **View all errors**: Display all errors detected in the current pipeline
- **Analyze specific error**: Perform detailed analysis on a selected error
- **Apply patch solution**: Generate and apply a patch for a specific error
- **Apply all patches**: Batch generate and apply patches for all errors
- **Rollback patch**: Rollback a previously applied patch
- **View session summary**: Display summary of the current debug session
- **View command history**: Visualize command usage patterns and workflow
- **Export session**: Export debug session to a report file
- **Help**: Display this help information
- **Exit session**: End the current debug session

## Command History Visualization

The command history feature provides insights into your debugging workflow:

- **Usage frequency**: See which commands you use most often
- **Command flow**: Visualize the sequence of your recent commands
- **Command transitions**: Identify common patterns in your debugging workflow

This information can help optimize your debugging process and identify areas for automation.

## Tips

- Use arrow keys to navigate through options
- Press Tab for auto-completion
- Command history is available for quick access to previous commands
- Export your session before exiting to save your work
- Review command history to identify repetitive patterns that could be automated
        """
        
        self.console.print(Markdown(help_text))

    async def _end_session(self):
        """
        End the debug session
        """
        self.current_session.close_session()
        
        # Display command history before exiting
        if self.command_sequence:
            self.console.print("\n[bold blue]Session Command Summary:[/]")
            await self._display_command_history()
        
        # Ask if user wants to export the session
        if await questionary.confirm(
            "Would you like to export this debug session before exiting?",
            default=True
        ).ask_async():
            await self._export_debug_session()
            
        self.console.print("[bold green]Debug session ended.[/]")
        
        # Cleanup
        await self.log_analyzer.cleanup()

    def _generate_debug_report(self) -> DebugReport:
        """
        Generate a structured debug report
        """
        # Calculate metrics
        duration = (
            (self.current_session.end_time or datetime.utcnow()) - 
            self.current_session.start_time
        ).total_seconds()
        
        success_rate = 0
        if self.current_session.errors:
            resolved_errors = sum(
                1 for error in self.current_session.errors
                if any(patch.error_id == error.error_id for patch in self.current_session.applied_patches)
            )
            success_rate = (resolved_errors / len(self.current_session.errors)) * 100
            
        # Generate error analysis summary
        error_analysis = []
        for analysis in self.current_session.analysis_results:
            error_analysis.append({
                "error_id": analysis.error.error_id,
                "message": analysis.error.message,
                "root_cause": analysis.root_cause,
                "confidence": analysis.confidence_score,
                "solutions": analysis.suggested_solutions
            })
            
        # Generate solutions summary
        solutions_applied = []
        for patch in self.current_session.applied_patches:
            solutions_applied.append({
                "solution_id": patch.solution_id,
                "error_id": patch.error_id,
                "patch_type": patch.patch_type,
                "success_rate": patch.estimated_success_rate
            })
            
        # Generate recommendations
        recommendations = [
            "Add missing dependencies to requirements.txt",
            "Implement proper error handling in pipeline scripts",
            "Set up proper permissions for pipeline execution"
        ]
        
        # Include command history in report
        if self.command_sequence:
            command_counts = {}
            for cmd in self.command_sequence:
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
                
            recommendations.append(
                f"Most used command was '{max(command_counts.items(), key=lambda x: x[1])[0].replace('_', ' ')}' - consider automating this step"
            )
        
        # Create report
        return DebugReport(
            session=self.current_session,
            summary=f"Debug session for pipeline {self.current_session.pipeline_id} with {len(self.current_session.errors)} errors identified and {len(self.current_session.applied_patches)} patches applied.",
            error_analysis=error_analysis,
            solutions_applied=solutions_applied,
            recommendations=recommendations,
            metrics={
                "duration": duration,
                "success_rate": success_rate,
                "errors_resolved": len(self.current_session.applied_patches),
                "total_errors": len(self.current_session.errors),
                "analyses_performed": len(self.current_session.analysis_results),
                "commands_executed": len(self.command_sequence)
            }
        )
        
    def _generate_markdown_report(self, report: DebugReport) -> str:
        """
        Generate a markdown report from a DebugReport object
        """
        md = f"# Debug Session Report\n\n"
        md += f"## Summary\n\n{report.summary}\n\n"
        
        md += f"## Session Information\n\n"
        md += f"- **Session ID**: {report.session.session_id}\n"
        md += f"- **Pipeline ID**: {report.session.pipeline_id}\n"
        md += f"- **Start Time**: {report.session.start_time.isoformat()}\n"
        md += f"- **End Time**: {report.session.end_time.isoformat() if report.session.end_time else 'N/A'}\n"
        md += f"- **Status**: {report.session.status}\n\n"
        
        md += f"## Metrics\n\n"
        md += f"- **Duration**: {report.metrics['duration']:.2f} seconds\n"
        md += f"- **Success Rate**: {report.metrics['success_rate']:.1f}%\n"
        md += f"- **Errors Resolved**: {report.metrics['errors_resolved']} / {report.metrics['total_errors']}\n"
        md += f"- **Analyses Performed**: {report.metrics['analyses_performed']}\n"
        if "commands_executed" in report.metrics:
            md += f"- **Commands Executed**: {report.metrics['commands_executed']}\n"
        md += "\n"
        
        # Add command history section if available
        if hasattr(self, 'command_sequence') and self.command_sequence:
            md += f"## Command History\n\n"
            
            # Count command frequencies
            command_counts = {}
            for cmd in self.command_sequence:
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
                
            # Sort by frequency
            sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
            
            md += "| Command | Count | Percentage |\n"
            md += "|---------|-------|------------|\n"
            
            total_commands = len(self.command_sequence)
            for cmd, count in sorted_commands:
                display_name = cmd.replace("_", " ").title()
                percentage = (count / total_commands) * 100
                md += f"| {display_name} | {count} | {percentage:.1f}% |\n"
                
            md += "\n"
            
            # Add command flow
            if len(self.command_sequence) >= 3:
                md += "### Command Flow\n\n"
                md += "```\n"
                flow_text = " → ".join([cmd.replace("_", " ").title() for cmd in self.command_sequence[-10:]])
                md += flow_text
                md += "\n```\n\n"
        
        md += f"## Error Analysis\n\n"
        for i, analysis in enumerate(report.error_analysis):
            md += f"### Error {i+1}: {analysis['error_id']}\n\n"
            md += f"**Message**: {analysis['message']}\n\n"
            md += f"**Root Cause**: {analysis['root_cause']}\n\n"
            md += f"**Confidence**: {analysis['confidence'] * 100:.1f}%\n\n"
            md += f"**Suggested Solutions**:\n\n"
            for solution in analysis['solutions']:
                md += f"- {solution}\n"
            md += "\n"
            
        md += f"## Solutions Applied\n\n"
        if report.solutions_applied:
            for i, solution in enumerate(report.solutions_applied):
                md += f"### Solution {i+1}: {solution['solution_id']}\n\n"
                md += f"- **Error ID**: {solution['error_id']}\n"
                md += f"- **Patch Type**: {solution['patch_type']}\n"
                md += f"- **Estimated Success Rate**: {solution['success_rate'] * 100:.1f}%\n\n"
        else:
            md += "No solutions were applied during this session.\n\n"
            
        md += f"## Recommendations\n\n"
        for recommendation in report.recommendations:
            md += f"- {recommendation}\n"
            
        return md
        
    def _generate_text_report(self, report: DebugReport) -> str:
        """
        Generate a plain text report from a DebugReport object
        """
        text = f"DEBUG SESSION REPORT\n"
        text += f"{'=' * 80}\n\n"
        text += f"SUMMARY\n{'-' * 80}\n{report.summary}\n\n"
        
        text += f"SESSION INFORMATION\n{'-' * 80}\n"
        text += f"Session ID: {report.session.session_id}\n"
        text += f"Pipeline ID: {report.session.pipeline_id}\n"
        text += f"Start Time: {report.session.start_time.isoformat()}\n"
        text += f"End Time: {report.session.end_time.isoformat() if report.session.end_time else 'N/A'}\n"
        text += f"Status: {report.session.status}\n\n"
        
        text += f"METRICS\n{'-' * 80}\n"
        text += f"Duration: {report.metrics['duration']:.2f} seconds\n"
        text += f"Success Rate: {report.metrics['success_rate']:.1f}%\n"
        text += f"Errors Resolved: {report.metrics['errors_resolved']} / {report.metrics['total_errors']}\n"
        text += f"Analyses Performed: {report.metrics['analyses_performed']}\n"
        if "commands_executed" in report.metrics:
            text += f"Commands Executed: {report.metrics['commands_executed']}\n"
        text += "\n"
        
        # Add command history section if available
        if hasattr(self, 'command_sequence') and self.command_sequence:
            text += f"COMMAND HISTORY\n{'-' * 80}\n"
            
            # Count command frequencies
            command_counts = {}
            for cmd in self.command_sequence:
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
                
            # Sort by frequency
            sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
            
            for cmd, count in sorted_commands:
                display_name = cmd.replace("_", " ").title()
                percentage = (count / len(self.command_sequence)) * 100
                text += f"{display_name}: {count} ({percentage:.1f}%)\n"
                
            text += "\n"
            
            # Add command flow
            if len(self.command_sequence) >= 3:
                text += "Recent Command Sequence:\n"
                flow_text = " → ".join([cmd.replace("_", " ").title() for cmd in self.command_sequence[-10:]])
                text += f"{flow_text}\n\n"
        
        text += f"ERROR ANALYSIS\n{'-' * 80}\n"
        for i, analysis in enumerate(report.error_analysis):
            text += f"Error {i+1}: {analysis['error_id']}\n"
            text += f"Message: {analysis['message']}\n"
            text += f"Root Cause: {analysis['root_cause']}\n"
            text += f"Confidence: {analysis['confidence'] * 100:.1f}%\n"
            text += f"Suggested Solutions:\n"
            for solution in analysis['solutions']:
                text += f"  - {solution}\n"
            text += "\n"
            
        text += f"SOLUTIONS APPLIED\n{'-' * 80}\n"
        if report.solutions_applied:
            for i, solution in enumerate(report.solutions_applied):
                text += f"Solution {i+1}: {solution['solution_id']}\n"
                text += f"  Error ID: {solution['error_id']}\n"
                text += f"  Patch Type: {solution['patch_type']}\n"
                text += f"  Estimated Success Rate: {solution['success_rate'] * 100:.1f}%\n\n"
        else:
            text += "No solutions were applied during this session.\n\n"
            
        text += f"RECOMMENDATIONS\n{'-' * 80}\n"
        for recommendation in report.recommendations:
            text += f"  - {recommendation}\n"
            
        return text
