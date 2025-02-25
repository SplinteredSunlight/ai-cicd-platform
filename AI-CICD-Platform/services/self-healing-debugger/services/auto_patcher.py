from typing import List, Dict, Optional, Tuple
import asyncio
import json
import os
from datetime import datetime
import subprocess
from jinja2 import Template

from ..config import get_settings, PATCH_TEMPLATES, PROMPT_TEMPLATES
from ..models.pipeline_debug import (
    PipelineError,
    PatchSolution,
    ErrorCategory,
    ErrorSeverity
)

class AutoPatcher:
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.applied_patches: Dict[str, PatchSolution] = {}

    async def generate_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> PatchSolution:
        """
        Generate a patch solution for the given error
        """
        try:
            # Try template-based solution first
            template_solution = await self._generate_template_solution(error, context)
            if template_solution:
                return template_solution

            # Fall back to AI-generated solution
            ai_solution = await self._generate_ai_solution(error, context)
            return ai_solution

        except Exception as e:
            raise Exception(f"Patch generation failed: {str(e)}")

    async def apply_patch(
        self,
        patch: PatchSolution,
        dry_run: bool = True
    ) -> bool:
        """
        Apply a patch solution and verify its effectiveness
        """
        try:
            if not self._validate_patch(patch):
                raise ValueError("Patch validation failed")

            if patch.requires_approval and not dry_run:
                raise ValueError("Patch requires approval but dry_run is False")

            # Apply dependencies first
            for dependency in patch.dependencies:
                await self._install_dependency(dependency)

            # Execute the patch
            if dry_run:
                success = await self._simulate_patch(patch)
            else:
                success = await self._execute_patch(patch)

            if success:
                self.applied_patches[patch.solution_id] = patch

            return success

        except Exception as e:
            raise Exception(f"Patch application failed: {str(e)}")

    async def rollback_patch(
        self,
        patch_id: str
    ) -> bool:
        """
        Rollback a previously applied patch
        """
        try:
            patch = self.applied_patches.get(patch_id)
            if not patch:
                raise ValueError(f"No patch found with ID: {patch_id}")

            if not patch.is_reversible:
                raise ValueError("Patch is not reversible")

            if not patch.rollback_script:
                raise ValueError("No rollback script available")

            success = await self._execute_script(patch.rollback_script)
            if success:
                del self.applied_patches[patch_id]

            return success

        except Exception as e:
            raise Exception(f"Patch rollback failed: {str(e)}")

    async def _generate_template_solution(
        self,
        error: PipelineError,
        context: Dict
    ) -> Optional[PatchSolution]:
        """
        Generate a solution using predefined templates
        """
        try:
            if error.category == ErrorCategory.DEPENDENCY:
                return await self._generate_dependency_patch(error, context)
            elif error.category == ErrorCategory.PERMISSION:
                return await self._generate_permission_patch(error, context)
            elif error.category == ErrorCategory.CONFIGURATION:
                return await self._generate_config_patch(error, context)
            return None

        except Exception:
            return None

    async def _generate_ai_solution(
        self,
        error: PipelineError,
        context: Dict
    ) -> PatchSolution:
        """
        Generate a solution using AI
        """
        try:
            # Prepare prompt
            prompt = PROMPT_TEMPLATES["solution_generation"].format(
                error_message=error.message,
                context=json.dumps(context, indent=2),
                language="python"  # TODO: Detect appropriate language
            )

            # Get AI response
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert at generating solutions for CI/CD pipeline errors."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=self.settings.max_tokens
            )

            solution_text = response.choices[0].message.content
            
            # Create patch solution
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="ai_generated",
                patch_script=self._extract_code_from_solution(solution_text),
                is_reversible=False,  # AI-generated patches are not automatically reversible
                requires_approval=True,
                estimated_success_rate=0.7,  # Conservative estimate for AI solutions
                validation_steps=self._extract_validation_steps(solution_text)
            )

        except Exception as e:
            raise Exception(f"AI solution generation failed: {str(e)}")

    async def _generate_dependency_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> PatchSolution:
        """
        Generate a patch for dependency-related errors
        """
        package_name = self._extract_package_name(error.message)
        if not package_name:
            return None

        template = Template(PATCH_TEMPLATES["python_dependency"])
        patch_script = template.render(package=package_name)

        return PatchSolution(
            solution_id=f"patch_{datetime.utcnow().timestamp()}",
            error_id=error.error_id,
            patch_type="dependency",
            patch_script=patch_script,
            is_reversible=True,
            requires_approval=True,
            estimated_success_rate=0.9,
            dependencies=[],
            validation_steps=[
                f"import {package_name}",
                f"print({package_name}.__version__)"
            ],
            rollback_script=f"pip uninstall -y {package_name}"
        )

    async def _generate_permission_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> PatchSolution:
        """
        Generate a patch for permission-related errors
        """
        path = self._extract_path(error.message)
        if not path:
            return None

        template = Template(PATCH_TEMPLATES["permission_fix"])
        patch_script = template.render(
            path=path,
            mode=0o755  # Default to executable permission
        )

        return PatchSolution(
            solution_id=f"patch_{datetime.utcnow().timestamp()}",
            error_id=error.error_id,
            patch_type="permission",
            patch_script=patch_script,
            is_reversible=True,
            requires_approval=True,
            estimated_success_rate=0.95,
            dependencies=[],
            validation_steps=[
                f"test -x {path}"
            ],
            rollback_script=f"chmod 644 {path}"
        )

    async def _execute_patch(self, patch: PatchSolution) -> bool:
        """
        Execute a patch script
        """
        try:
            # Create temporary script file
            script_path = f"/tmp/patch_{patch.solution_id}.py"
            with open(script_path, "w") as f:
                f.write(patch.patch_script)

            # Execute script
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Cleanup
            os.remove(script_path)

            # Validate patch
            if result.returncode == 0:
                return await self._validate_patch_result(patch)
            return False

        except Exception as e:
            print(f"Patch execution failed: {str(e)}")
            return False

    async def _validate_patch_result(self, patch: PatchSolution) -> bool:
        """
        Validate patch application
        """
        try:
            for step in patch.validation_steps:
                result = subprocess.run(
                    step,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0:
                    return False
            return True

        except Exception:
            return False

    def _validate_patch(self, patch: PatchSolution) -> bool:
        """
        Validate patch before application
        """
        if not patch.patch_script:
            return False

        # Check for dangerous commands
        dangerous_commands = [
            "rm -rf",
            "sudo",
            "chmod 777",
            "eval",
            "exec"
        ]

        return not any(cmd in patch.patch_script.lower() for cmd in dangerous_commands)

    def _extract_code_from_solution(self, solution_text: str) -> str:
        """
        Extract code blocks from AI solution text
        """
        code_blocks = []
        in_code_block = False
        current_block = []

        for line in solution_text.split("\n"):
            if line.startswith("```"):
                if in_code_block:
                    code_blocks.append("\n".join(current_block))
                    current_block = []
                in_code_block = not in_code_block
            elif in_code_block:
                current_block.append(line)

        return "\n\n".join(code_blocks)

    def _extract_validation_steps(self, solution_text: str) -> List[str]:
        """
        Extract validation steps from AI solution text
        """
        steps = []
        validation_section = False

        for line in solution_text.split("\n"):
            if "validation" in line.lower():
                validation_section = True
            elif validation_section and line.strip().startswith("-"):
                step = line.strip("- ").strip()
                if step:
                    steps.append(step)

        return steps or ["python -c 'print(\"Validation not specified\")'"]

    @staticmethod
    def _extract_package_name(error_message: str) -> Optional[str]:
        """
        Extract package name from error message
        """
        patterns = [
            r"No module named '(.+)'",
            r"ImportError: (.+) not found",
            r"npm ERR! missing: (.+)@"
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _extract_path(error_message: str) -> Optional[str]:
        """
        Extract file path from error message
        """
        patterns = [
            r"PermissionError: \[Errno 13\] Permission denied: '(.+)'",
            r"EACCES: permission denied, access '(.+)'"
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)
        return None
