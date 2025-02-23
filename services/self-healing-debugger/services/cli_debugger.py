from typing import List, Dict, Optional
import asyncio
import uuid
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
import questionary

from ..config import get_settings, CLI_THEME
from ..models.pipeline_debug import (
    DebugSession,
    PipelineError,
    AnalysisResult,
    PatchSolution
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
            
            if action == "view_errors":
                await self._display_errors()
            elif action == "analyze_error":
                await self._analyze_specific_error()
            elif action == "apply_patch":
                await self._handle_patch_application()
            elif action == "rollback_patch":
                await self._handle_patch_rollback()
            elif action == "view_session":
                await self._display_session_summary()
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
            "Rollback patch",
            "View session summary",
            "Exit session"
        ]

        result = await questionary.select(
            "What would you like to do?",
            choices=choices,
            style=questionary.Style(
                [("qmark", "fg:cyan"), ("question", "bold")]
            )
        ).ask_async()

        return result.lower().replace(" ", "_")

    async def _display_errors(self):
        """
        Display all errors in current session
        """
        table = Table(title="Pipeline Errors")
        table.add_column("ID", style="cyan")
        table.add_column("Severity", style="magenta")
        table.add_column("Category", style="blue")
        table.add_column("Message", style="white")

        for error in self.current_session.errors:
            table.add_row(
                error.error_id,
                error.severity.value,
                error.category.value,
                error.message[:100] + "..." if len(error.message) > 100 else error.message
            )

        self.console.print(table)

    async def _analyze_specific_error(self):
        """
        Analyze a specific error in detail
        """
        # Prompt for error selection
        error_choices = [
            f"{error.error_id}: {error.message[:50]}..."
            for error in self.current_session.errors
        ]

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

        table.add_row("Session ID", self.current_session.session_id)
        table.add_row("Pipeline ID", self.current_session.pipeline_id)
        table.add_row("Start Time", self.current_session.start_time.isoformat())
        table.add_row("Total Errors", str(len(self.current_session.errors)))
        table.add_row("Analyses Performed", str(len(self.current_session.analysis_results)))
        table.add_row("Patches Applied", str(len(self.current_session.applied_patches)))

        self.console.print(table)

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

    async def _end_session(self):
        """
        End the debug session
        """
        self.current_session.close_session()
        self.console.print("[bold green]Debug session ended.[/]")
        
        # Cleanup
        await self.log_analyzer.cleanup()
