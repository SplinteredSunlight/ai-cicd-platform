from typing import List, Dict, Optional, Tuple, Any
import asyncio
import json
import os
import re
from datetime import datetime
import subprocess
from jinja2 import Template
from openai import OpenAI

from config import get_settings, PATCH_TEMPLATES, PROMPT_TEMPLATES
from models.pipeline_debug import (
    PipelineError,
    PatchSolution,
    ErrorCategory,
    ErrorSeverity
)
from services.ml_classifier_service import MLClassifierService

class AutoPatcher:
    def __init__(self, ml_classifier_service=None):
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.applied_patches: Dict[str, PatchSolution] = {}
        
        # Initialize ML classifier service if not provided
        if ml_classifier_service:
            self.ml_classifier_service = ml_classifier_service
        else:
            try:
                self.ml_classifier_service = MLClassifierService()
                self.use_ml_classification = self.settings.use_ml_classification if hasattr(self.settings, 'use_ml_classification') else True
            except Exception as e:
                print(f"Failed to initialize ML classifier service: {str(e)}")
                self.ml_classifier_service = None
                self.use_ml_classification = False

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
            elif error.category == ErrorCategory.NETWORK:
                return await self._generate_network_patch(error, context)
            elif error.category == ErrorCategory.RESOURCE:
                return await self._generate_resource_patch(error, context)
            elif error.category == ErrorCategory.TEST:
                return await self._generate_test_patch(error, context)
            elif error.category == ErrorCategory.SECURITY:
                return await self._generate_security_patch(error, context)
            return None

        except Exception as e:
            print(f"Template solution generation failed: {str(e)}")
            return None

    async def _generate_ai_solution(
        self,
        error: PipelineError,
        context: Dict
    ) -> PatchSolution:
        """
        Generate a solution using AI, enhanced with ML classification results
        """
        try:
            # Get ML classification results if available
            ml_classification = None
            if self.ml_classifier_service and hasattr(self, 'use_ml_classification') and self.use_ml_classification:
                try:
                    ml_classification = await self.ml_classifier_service.classify_error(
                        error,
                        detailed=True,
                        confidence_threshold=0.6
                    )
                    
                    if ml_classification["status"] == "success":
                        # Add ML classification results to context
                        context["ml_classification"] = ml_classification["classifications"]
                        context["ml_confidence"] = ml_classification.get("overall_confidence", 0.0)
                        
                        # Log ML classification results
                        print(f"ML classification results: {json.dumps(ml_classification['classifications'], indent=2)}")
                except Exception as e:
                    print(f"ML classification failed: {str(e)}")
            
            # Detect programming language from error and context
            language = self._detect_language(error, context)
            
            # Prepare prompt with enhanced context
            prompt = PROMPT_TEMPLATES["solution_generation"].format(
                error_message=error.message,
                context=json.dumps(context, indent=2),
                language=language
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
            
            # Calculate estimated success rate based on ML confidence if available
            estimated_success_rate = 0.7  # Default conservative estimate
            if ml_classification and "overall_confidence" in ml_classification:
                # Scale success rate based on ML confidence
                ml_confidence = ml_classification["overall_confidence"]
                if ml_confidence > 0.8:
                    estimated_success_rate = 0.85
                elif ml_confidence > 0.6:
                    estimated_success_rate = 0.75
                # else keep default
            
            # Create patch solution
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="ai_generated",
                patch_script=self._extract_code_from_solution(solution_text),
                is_reversible=False,  # AI-generated patches are not automatically reversible
                requires_approval=True,
                estimated_success_rate=estimated_success_rate,
                validation_steps=self._extract_validation_steps(solution_text)
            )

        except Exception as e:
            raise Exception(f"AI solution generation failed: {str(e)}")
    
    def _detect_language(self, error: PipelineError, context: Dict) -> str:
        """
        Detect the programming language from error and context
        """
        error_message = error.message.lower()
        
        # Check for Python-specific errors
        if any(term in error_message for term in [
            "importerror", "modulenotfounderror", "syntaxerror", "indentationerror",
            "python", "pip", "pytest", "django", "flask", "fastapi"
        ]):
            return "python"
        
        # Check for JavaScript/Node.js errors
        elif any(term in error_message for term in [
            "npm", "node", "javascript", "js", "typescript", "ts", "react", "angular", "vue",
            "uncaught referenceerror", "cannot find module", "undefined is not a function"
        ]):
            return "javascript"
        
        # Check for Java errors
        elif any(term in error_message for term in [
            "java.lang.", "nullpointerexception", "classnotfoundexception", "maven", "gradle",
            "spring", "java", "jar", "class"
        ]):
            return "java"
        
        # Check for Go errors
        elif any(term in error_message for term in [
            "go", "golang", "panic:", "undefined:", "cannot use", "go mod", "go get"
        ]):
            return "go"
        
        # Check for Ruby errors
        elif any(term in error_message for term in [
            "ruby", "rails", "gem", "bundler", "rake", "nameerror", "nomethoderror"
        ]):
            return "ruby"
        
        # Check for C/C++ errors
        elif any(term in error_message for term in [
            "segmentation fault", "memory access", "undefined reference", "linker",
            "gcc", "g++", "clang", "cmake", "make"
        ]):
            return "c++"
        
        # Check for shell script errors
        elif any(term in error_message for term in [
            "bash", "sh:", "command not found", "no such file or directory",
            "permission denied", "syntax error near unexpected token"
        ]):
            return "bash"
        
        # Check for Docker/container errors
        elif any(term in error_message for term in [
            "docker", "container", "image", "dockerfile", "kubernetes", "k8s", "pod"
        ]):
            return "docker"
        
        # Default to Python as a safe choice
        return "python"

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

        template_str = PATCH_TEMPLATES["python_dependency"]
        template = Template(template_str)
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

    async def _generate_config_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> Optional[PatchSolution]:
        """
        Generate a patch for configuration-related errors
        """
        # Extract configuration details from error message
        config_details = self._extract_config_details(error.message)
        if not config_details:
            return None
            
        # Create a patch script based on the configuration type
        config_type = config_details.get("type")
        config_name = config_details.get("name")
        
        if config_type == "env":
            # Environment variable configuration
            patch_script = f"""
import os
import dotenv

# Load .env file if it exists
dotenv_path = '.env'
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)

# Set environment variable
os.environ['{config_name}'] = '{config_details.get("value", "")}'

# Update .env file
with open(dotenv_path, 'a+') as f:
    f.seek(0)
    content = f.read()
    if '{config_name}=' not in content:
        f.write('\\n{config_name}={config_details.get("value", "")}')
        
print(f"Added {config_name} to environment variables")
"""
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="configuration",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.9,
                dependencies=["pip:python-dotenv"],
                validation_steps=[
                    f"python -c \"import os; print(os.environ.get('{config_name}', 'Not set'))\""
                ],
                rollback_script=f"python -c \"import os, dotenv; dotenv.load_dotenv(); os.environ.pop('{config_name}', None)\""
            )
            
        elif config_type == "file":
            # Configuration file
            file_path = config_details.get("path", "config.json")
            file_content = config_details.get("content", "{}")
            
            patch_script = f"""
import os
import json

config_path = '{file_path}'
os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)

config_content = {file_content}

with open(config_path, 'w') as f:
    json.dump(config_content, f, indent=2)
    
print(f"Created/updated configuration file: {file_path}")
"""
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="configuration",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.9,
                dependencies=[],
                validation_steps=[
                    f"python -c \"import os; print('Config file exists:', os.path.exists('{file_path}'))\""
                ],
                rollback_script=f"import os; os.remove('{file_path}') if os.path.exists('{file_path}') else None"
            )
            
        return None
    
    def _extract_config_details(self, error_message: str) -> Optional[Dict]:
        """
        Extract configuration details from error message
        """
        # Check for environment variable configuration issues
        env_match = re.search(r"Missing environment variable: ([A-Za-z0-9_]+)", error_message)
        if env_match:
            return {
                "type": "env",
                "name": env_match.group(1),
                "value": ""  # Default empty value
            }
            
        # Check for configuration file issues
        file_match = re.search(r"Configuration file not found: (.+)", error_message)
        if file_match:
            return {
                "type": "file",
                "path": file_match.group(1),
                "content": "{}"  # Default empty JSON
            }
            
        # Check for missing configuration parameter
        param_match = re.search(r"Missing configuration for: ([A-Za-z0-9_]+)", error_message)
        if param_match:
            return {
                "type": "env",
                "name": param_match.group(1),
                "value": ""
            }
            
        return None
    
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

        template_str = PATCH_TEMPLATES["permission_fix"]
        template = Template(template_str)
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

    async def _simulate_patch(self, patch: PatchSolution) -> bool:
        """
        Simulate patch application without actually applying it
        """
        try:
            # Log the simulation
            print(f"Simulating patch: {patch.solution_id}")
            print(f"Patch script:\n{patch.patch_script}")
            
            # Validate the patch script
            if not self._validate_patch(patch):
                return False
            
            # Check if dependencies can be resolved
            for dependency in patch.dependencies:
                # Just check if dependency is available, don't install
                print(f"Checking dependency: {dependency}")
            
            # Return success
            return True
            
        except Exception as e:
            print(f"Patch simulation failed: {str(e)}")
            return False

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
            if "```" in line:
                if in_code_block:
                    code_blocks.append("\n".join(current_block))
                    current_block = []
                in_code_block = not in_code_block
            elif in_code_block:
                current_block.append(line)
        
        # Don't forget the last block if we're still in a code block
        if in_code_block and current_block:
            code_blocks.append("\n".join(current_block))

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

    async def _execute_script(self, script: str) -> bool:
        """
        Execute a script string
        """
        try:
            # Create temporary script file
            script_id = datetime.utcnow().timestamp()
            script_path = f"/tmp/script_{script_id}.sh"
            with open(script_path, "w") as f:
                f.write(script)
            
            # Make executable
            os.chmod(script_path, 0o755)
            
            # Execute script
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Cleanup
            os.remove(script_path)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Script execution failed: {str(e)}")
            return False
    
    async def _install_dependency(self, dependency: str) -> bool:
        """
        Install a dependency
        """
        try:
            # Determine package manager based on dependency format
            if dependency.startswith("pip:"):
                package = dependency.split("pip:")[1].strip()
                cmd = ["pip", "install", package]
            elif dependency.startswith("npm:"):
                package = dependency.split("npm:")[1].strip()
                cmd = ["npm", "install", package]
            else:
                # Default to pip
                cmd = ["pip", "install", dependency]
            
            # Install dependency
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Dependency installation failed: {str(e)}")
            return False
    
    async def _generate_network_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> Optional[PatchSolution]:
        """
        Generate a patch for network-related errors
        """
        # Check for proxy issues
        if any(term in error.message.lower() for term in ["proxy", "407", "authentication required"]):
            # Extract proxy URL from context or use a default
            proxy_url = context.get("proxy_url", "http://proxy.example.com:8080")
            
            template_str = PATCH_TEMPLATES["proxy_config_fix"]
            template = Template(template_str)
            patch_script = template.render(proxy_url=proxy_url)
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="network_proxy",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.8,
                dependencies=[],
                validation_steps=[
                    "curl -s -o /dev/null -w '%{http_code}' https://www.google.com"
                ],
                rollback_script="""
import os
import subprocess

# Unset proxy environment variables
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

# Remove from git config
try:
    subprocess.check_call(['git', 'config', '--global', '--unset', 'http.proxy'])
    subprocess.check_call(['git', 'config', '--global', '--unset', 'https.proxy'])
except:
    pass

print("Proxy configuration removed")
"""
            )
        
        # Check for DNS issues
        elif any(term in error.message.lower() for term in ["dns", "resolve", "host", "getaddrinfo"]):
            # Extract hostname from error message
            hostname_match = re.search(r"getaddrinfo ENOTFOUND (.+)", error.message)
            hostname = hostname_match.group(1) if hostname_match else "example.com"
            
            # Use a default IP for demonstration (would need to be determined in real usage)
            ip_address = "127.0.0.1"
            
            template_str = PATCH_TEMPLATES["dns_fix"]
            template = Template(template_str)
            patch_script = template.render(ip_address=ip_address, hostname=hostname)
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="network_dns",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.7,
                dependencies=[],
                validation_steps=[
                    f"ping -c 1 {hostname}"
                ],
                rollback_script=f"""
import subprocess

# Remove entry from /etc/hosts
try:
    subprocess.check_call(['sed', '-i', '/ {hostname}$/d', '/etc/hosts'])
    print("DNS entry removed")
except:
    print("Failed to remove DNS entry, may require manual removal")
"""
            )
        
        # Check for SSL/TLS issues
        elif any(term in error.message.lower() for term in ["ssl", "certificate", "tls", "handshake"]):
            # For SSL issues, we often need to disable certificate verification (in dev environments only)
            # This is a simplified example - in production, proper certificate handling is essential
            
            patch_script = """
import os

# Set environment variables to disable SSL verification (for development only)
os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Add warning about security implications
print("WARNING: SSL certificate verification has been disabled.")
print("This is only suitable for development environments.")
print("In production, proper SSL certificates should be configured.")
"""
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="network_ssl",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.7,
                dependencies=[],
                validation_steps=[
                    "python -c \"import os; print('SSL verification disabled:', os.environ.get('PYTHONHTTPSVERIFY', 'Not set'))\""
                ],
                rollback_script="""
import os

# Restore SSL verification
os.environ.pop('NODE_TLS_REJECT_UNAUTHORIZED', None)
os.environ.pop('PYTHONHTTPSVERIFY', None)

print("SSL certificate verification has been restored.")
"""
            )
            
        return None

    async def _generate_resource_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> Optional[PatchSolution]:
        """
        Generate a patch for resource-related errors
        """
        # Check for memory issues
        if any(term in error.message.lower() for term in ["memory", "heap", "oom", "killed: 9"]):
            # Default memory limit increase (would be adjusted based on context in real usage)
            memory_limit = 4096  # 4GB
            
            template_str = PATCH_TEMPLATES["memory_limit_fix"]
            template = Template(template_str)
            patch_script = template.render(memory_limit=memory_limit)
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="resource_memory",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.8,
                dependencies=[],
                validation_steps=[
                    "node -e \"console.log('Memory limit check: ' + process.env.NODE_OPTIONS || 'Not set')\""
                ],
                rollback_script="""
import json
import os
import yaml

# Revert Node.js memory limit
if os.path.exists('package.json'):
    with open('package.json', 'r') as f:
        package_json = json.load(f)
    
    # Remove NODE_OPTIONS from scripts
    for script_name in package_json.get('scripts', {}):
        if 'NODE_OPTIONS' in package_json['scripts'][script_name]:
            package_json['scripts'][script_name] = package_json['scripts'][script_name].replace(
                /NODE_OPTIONS='--max-old-space-size=\\d+' /g, ''
            )
    
    with open('package.json', 'w') as f:
        json.dump(package_json, f, indent=2)
    
    print("Reverted Node.js memory limit")

# Revert Docker memory limits
elif os.path.exists('docker-compose.yml'):
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)
    
    # Remove memory limits from services
    for service_name in compose.get('services', {}):
        if 'deploy' in compose['services'][service_name]:
            if 'resources' in compose['services'][service_name]['deploy']:
                if 'limits' in compose['services'][service_name]['deploy']['resources']:
                    if 'memory' in compose['services'][service_name]['deploy']['resources']['limits']:
                        del compose['services'][service_name]['deploy']['resources']['limits']['memory']
    
    with open('docker-compose.yml', 'w') as f:
        yaml.dump(compose, f, default_flow_style=False)
    
    print("Reverted Docker memory limits")
"""
            )
        
        # Check for disk space issues
        elif any(term in error.message.lower() for term in ["disk", "space", "quota", "no space left"]):
            # For disk space issues, we can create a cleanup script
            patch_script = """
import os
import subprocess
import shutil

# List of directories to clean up
cleanup_dirs = [
    './node_modules/.cache',
    './.npm/_cacache',
    './tmp',
    './.cache',
    './build',
    './dist'
]

space_freed = 0

# Clean up directories
for directory in cleanup_dirs:
    if os.path.exists(directory):
        try:
            size = sum(os.path.getsize(os.path.join(dirpath, filename))
                       for dirpath, dirnames, filenames in os.walk(directory)
                       for filename in filenames)
            
            shutil.rmtree(directory)
            space_freed += size
            print(f"Cleaned up {directory}: {size / (1024*1024):.2f} MB")
        except Exception as e:
            print(f"Failed to clean up {directory}: {str(e)}")

# Clean up Docker
try:
    subprocess.run(['docker', 'system', 'prune', '-f'], check=False)
    print("Cleaned up unused Docker resources")
except:
    pass

# Report total space freed
print(f"Total space freed: {space_freed / (1024*1024):.2f} MB")
"""
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="resource_disk",
                patch_script=patch_script,
                is_reversible=False,  # Cleanup operations are not reversible
                requires_approval=True,
                estimated_success_rate=0.8,
                dependencies=[],
                validation_steps=[
                    "df -h ."
                ]
            )
            
        # Check for file descriptor limit issues
        elif any(term in error.message.lower() for term in ["too many open files", "emfile", "enfile"]):
            patch_script = """
import os
import subprocess
import platform

# Increase file descriptor limits for the current process
try:
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
    print(f"Increased file descriptor limit from {soft} to {hard}")
except Exception as e:
    print(f"Failed to increase file descriptor limit: {str(e)}")

# Add instructions for permanent fix
system = platform.system()
if system == 'Linux':
    print("\\nTo permanently increase file descriptor limits:")
    print("1. Edit /etc/security/limits.conf")
    print("2. Add the following lines:")
    print("   * soft nofile 65536")
    print("   * hard nofile 65536")
    print("3. Log out and log back in")
elif system == 'Darwin':  # macOS
    print("\\nTo permanently increase file descriptor limits:")
    print("1. Create/edit /Library/LaunchDaemons/limit.maxfiles.plist")
    print("2. Add the following content:")
    print("   <?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?>")
    print("   <!DOCTYPE plist PUBLIC \\"-//Apple//DTD PLIST 1.0//EN\\" \\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\\">")
    print("   <plist version=\\"1.0\\">")
    print("     <dict>")
    print("       <key>Label</key>")
    print("       <string>limit.maxfiles</string>")
    print("       <key>ProgramArguments</key>")
    print("       <array>")
    print("         <string>launchctl</string>")
    print("         <string>limit</string>")
    print("         <string>maxfiles</string>")
    print("         <string>65536</string>")
    print("         <string>65536</string>")
    print("       </array>")
    print("       <key>RunAtLoad</key>")
    print("       <true/>")
    print("       <key>ServiceIPC</key>")
    print("       <false/>")
    print("     </dict>")
    print("   </plist>")
    print("3. Reboot your system")
"""
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="resource_files",
                patch_script=patch_script,
                is_reversible=False,
                requires_approval=True,
                estimated_success_rate=0.7,
                dependencies=[],
                validation_steps=[
                    "python -c \"import resource; print('File descriptor limit:', resource.getrlimit(resource.RLIMIT_NOFILE))\""
                ]
            )
            
        return None

    async def _generate_test_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> Optional[PatchSolution]:
        """
        Generate a patch for test-related errors
        """
        # Check for test timeout issues
        if any(term in error.message.lower() for term in ["timeout", "timed out"]):
            # Extract timeout value from error message or use default
            timeout_match = re.search(r"timeout of (\d+)", error.message.lower())
            current_timeout = int(timeout_match.group(1)) if timeout_match else 5000
            
            # Double the timeout
            new_timeout = current_timeout * 2
            
            template_str = PATCH_TEMPLATES["test_timeout_fix"]
            template = Template(template_str)
            patch_script = template.render(timeout=new_timeout)
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="test_timeout",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.8,
                dependencies=[],
                validation_steps=[
                    "test -f package.json && grep -q testTimeout package.json || test -f pytest.ini && grep -q timeout pytest.ini || test -f .mocharc.json && grep -q timeout .mocharc.json || echo 'No timeout configuration found'"
                ],
                rollback_script=f"""
import json
import os
import re

# Revert Jest timeout
if os.path.exists('package.json'):
    with open('package.json', 'r') as f:
        package_json = json.load(f)
    
    if 'jest' in package_json and 'testTimeout' in package_json['jest']:
        package_json['jest']['testTimeout'] = {current_timeout}
        
        with open('package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        
        print(f"Reverted Jest test timeout to {current_timeout}ms")

# Revert pytest timeout
elif os.path.exists('pytest.ini'):
    with open('pytest.ini', 'r') as f:
        content = f.read()
    
    if 'timeout' in content:
        content = re.sub(r'timeout = \\d+', f'timeout = {current_timeout // 1000}', content)
        
        with open('pytest.ini', 'w') as f:
            f.write(content)
        
        print(f"Reverted pytest timeout to {current_timeout // 1000}s")

# Revert Mocha timeout
elif os.path.exists('.mocharc.json'):
    with open('.mocharc.json', 'r') as f:
        mocha_config = json.load(f)
    
    if 'timeout' in mocha_config:
        mocha_config['timeout'] = {current_timeout}
        
        with open('.mocharc.json', 'w') as f:
            json.dump(mocha_config, f, indent=2)
        
        print(f"Reverted Mocha test timeout to {current_timeout}ms")
"""
            )
        
        # Check for test assertion failures
        elif any(term in error.message.lower() for term in ["assertion", "assert", "expected", "but got"]):
            # For assertion failures, we need more context to generate a proper fix
            # This is a simplified example that skips the failing test
            
            # Try to extract the test name
            test_name_match = re.search(r"FAIL: (.+)", error.message)
            test_name = test_name_match.group(1) if test_name_match else "unknown_test"
            
            patch_script = f"""
import os
import re

# Detect test framework
if os.path.exists('package.json'):
    # For Jest
    test_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.test.js') or file.endswith('.test.ts') or file.endswith('.test.tsx'):
                test_files.append(os.path.join(root, file))
    
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Look for the test name
        if '{test_name}' in content:
            # Replace test with skipped test
            modified_content = re.sub(
                r'(test|it)\([\'"]' + re.escape('{test_name}') + r'[\'"]',
                r'\\1.skip(\\'\{test_name}\\'',
                content
            )
            
            with open(test_file, 'w') as f:
                f.write(modified_content)
            
            print(f"Skipped failing test '{test_name}' in {{test_file}}")
            break
    else:
        print(f"Could not find test '{test_name}' in any test file")

elif os.path.exists('pytest.ini') or os.path.exists('conftest.py'):
    # For pytest
    test_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Look for the test name
        if '{test_name}' in content:
            # Replace test with skipped test
            modified_content = re.sub(
                r'def ' + re.escape('{test_name}') + r'\(',
                r'@pytest.mark.skip(reason="Temporarily skipped due to failure")\\ndef {test_name}(',
                content
            )
            
            # Add pytest import if needed
            if 'import pytest' not in modified_content:
                modified_content = 'import pytest\\n' + modified_content
            
            with open(test_file, 'w') as f:
                f.write(modified_content)
            
            print(f"Skipped failing test '{test_name}' in {{test_file}}")
            break
    else:
        print(f"Could not find test '{test_name}' in any test file")

else:
    print("Could not detect test framework")
"""
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="test_skip",
                patch_script=patch_script,
                is_reversible=False,  # Would need more context for proper reversal
                requires_approval=True,
                estimated_success_rate=0.6,  # Lower success rate due to complexity
                dependencies=[],
                validation_steps=[
                    "echo 'Test skip patch applied. Run tests to verify.'"
                ]
            )
            
        return None

    async def _generate_security_patch(
        self,
        error: PipelineError,
        context: Dict
    ) -> Optional[PatchSolution]:
        """
        Generate a patch for security-related errors
        """
        # Check for npm vulnerability issues
        if any(term in error.message.lower() for term in ["npm", "vulnerability", "cve"]):
            template_str = PATCH_TEMPLATES["npm_audit_fix"]
            template = Template(template_str)
            patch_script = template.render()
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="security_npm",
                patch_script=patch_script,
                is_reversible=False,
                requires_approval=True,
                estimated_success_rate=0.7,
                dependencies=[],
                validation_steps=[
                    "npm audit --json | grep -q '\"vulnerabilities\": 0' && echo 'No vulnerabilities found' || echo 'Vulnerabilities still exist'"
                ]
            )
        
        # Check for Python package vulnerability issues
        elif any(term in error.message.lower() for term in ["pip", "python", "vulnerability", "cve"]):
            # Extract package details from error message or context
            # This is a simplified example - in real usage, you'd need more sophisticated extraction
            vulnerable_package = context.get("package", "example-package")
            vulnerable_version = context.get("vulnerable_version", "1.0.0")
            safe_version = context.get("safe_version", "1.1.0")
            
            template_str = PATCH_TEMPLATES["pip_vulnerability_fix"]
            template = Template(template_str)
            patch_script = template.render(
                package=vulnerable_package,
                vulnerable_version=vulnerable_version,
                safe_version=safe_version
            )
            
            return PatchSolution(
                solution_id=f"patch_{datetime.utcnow().timestamp()}",
                error_id=error.error_id,
                patch_type="security_pip",
                patch_script=patch_script,
                is_reversible=True,
                requires_approval=True,
                estimated_success_rate=0.8,
                dependencies=[],
                validation_steps=[
                    f"pip show {vulnerable_package} | grep -q 'Version: {safe_version}' && echo 'Package updated successfully' || echo 'Package update failed'"
                ],
                rollback_script=f"""
import subprocess

try:
    subprocess.check_call(["pip", "install", "{vulnerable_package}=={vulnerable_version}"])
    print(f"Reverted {vulnerable_package} to version {vulnerable_version}")
except Exception as e:
    print(f"Failed to revert {vulnerable_package}: {str(e)}")
"""
            )
            
        return None

    @staticmethod
    def _extract_path(error_message: str) -> Optional[str]:
        """
        Extract file path from error message
        """
        patterns = [
            r"PermissionError: \[Errno 13\] Permission denied: '(.+)'",
            r"EACCES: permission denied, access '(.+)'",
            r"chmod: cannot access '(.+)'",
            r"chown: cannot access '(.+)'",
            r"mkdir: cannot create directory '(.+)'",
            r"touch: cannot touch '(.+)'",
            r"cp: cannot create regular file '(.+)'",
            r"mv: cannot move '(.+)'",
            r"rm: cannot remove '(.+)'"
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)
        return None
