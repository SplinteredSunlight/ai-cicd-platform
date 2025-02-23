import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Dict, List, Optional
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):
    # Service Configuration
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: LogLevel = LogLevel.INFO
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Elasticsearch Configuration
    elasticsearch_hosts: List[str] = ["http://localhost:9200"]
    elasticsearch_username: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    elasticsearch_index_prefix: str = "pipeline-logs-"
    
    # Auto-patching Configuration
    auto_patch_enabled: bool = True
    confidence_threshold: float = 0.85
    max_auto_patches_per_run: int = 3
    patch_approval_required: bool = True
    
    # Pattern Matching Configuration
    similarity_threshold: float = 0.8
    max_pattern_matches: int = 5
    context_lines: int = 3
    
    # CLI Configuration
    enable_rich_formatting: bool = True
    max_history_items: int = 100
    auto_suggest_enabled: bool = True
    
    # Cache Configuration
    pattern_cache_ttl: int = 3600  # 1 hour
    solution_cache_ttl: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Common error patterns and their solutions
ERROR_PATTERNS = {
    "dependency": {
        "patterns": [
            r"ModuleNotFoundError: No module named '(.+)'",
            r"ImportError: No module named (.+)",
            r"npm ERR! missing: (.+)@",
            r"Unable to resolve dependency: (.+)"
        ],
        "solutions": {
            "python": "pip install {package}",
            "node": "npm install {package}",
            "general": "Install missing dependency: {package}"
        }
    },
    "permission": {
        "patterns": [
            r"PermissionError: (.+)",
            r"EACCES: permission denied",
            r"AccessDenied: (.+)"
        ],
        "solutions": {
            "file": "chmod {mode} {path}",
            "directory": "sudo chown -R {user}:{group} {path}",
            "general": "Check and fix permissions for: {resource}"
        }
    },
    "configuration": {
        "patterns": [
            r"ConfigurationError: (.+)",
            r"InvalidConfiguration: (.+)",
            r"Missing configuration for: (.+)"
        ],
        "solutions": {
            "env": "Set environment variable: {variable}",
            "file": "Create/update config file: {file}",
            "general": "Fix configuration: {detail}"
        }
    }
}

# Auto-patching templates
PATCH_TEMPLATES = {
    "python_dependency": """
try:
    import subprocess
    subprocess.check_call(["pip", "install", "{package}"])
    print("Successfully installed {package}")
except Exception as e:
    print(f"Failed to install {package}: {str(e)}")
""",
    "node_dependency": """
try {
    const { execSync } = require('child_process');
    execSync('npm install {package}');
    console.log('Successfully installed {package}');
} catch (error) {
    console.error(`Failed to install {package}: ${error.message}`);
}
""",
    "permission_fix": """
import os
import stat

try:
    os.chmod("{path}", {mode})
    print(f"Successfully updated permissions for {path}")
except Exception as e:
    print(f"Failed to update permissions: {str(e)}")
"""
}

# AI prompt templates
PROMPT_TEMPLATES = {
    "error_analysis": """Analyze the following pipeline error and suggest solutions:

Error Context:
{error_context}

Pipeline Configuration:
{pipeline_config}

Previous Solutions Attempted:
{previous_solutions}

Provide:
1. Root cause analysis
2. Suggested solutions
3. Prevention measures
""",
    
    "solution_generation": """Generate a solution for the following pipeline error:

Error:
{error_message}

Context:
{context}

Requirements:
1. The solution should be automated
2. Include error handling
3. Be reversible if needed
4. Follow security best practices

Generate solution in {language} format.
""",
    
    "pattern_extraction": """Extract common patterns from these pipeline failures:

Failures:
{failures}

Extract:
1. Common error patterns
2. Correlation between failures
3. Environmental factors
4. Potential preventive measures
"""
}

# CLI Theme Configuration
CLI_THEME = {
    "info": "blue",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "debug": "grey",
    "prompt": "cyan",
    "input": "white"
}
