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
    
    # ML Classification Configuration
    use_ml_classification: bool = True
    ml_confidence_threshold: float = 0.7
    ml_model_dir: str = "models/trained"
    
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
            # Python dependency errors
            r"ModuleNotFoundError: No module named '(.+)'",
            r"ImportError: No module named (.+)",
            r"ImportError: cannot import name '(.+)' from '(.+)'",
            r"ImportError: cannot import name '(.+)'",
            r"ImportError: (.+) requires (.+)",
            r"pkg_resources\.DistributionNotFound: The '(.+)' distribution was not found",
            r"pkg_resources\.VersionConflict: \((.+) (.+), Requirement\.parse\('(.+)'\)\)",
            
            # Node.js dependency errors
            r"npm ERR! missing: (.+)@",
            r"npm ERR! 404 Not Found: (.+)@",
            r"npm ERR! code E404",
            r"Cannot find module '(.+)'",
            r"Error: Cannot find module '(.+)'",
            r"Module not found: Error: Can't resolve '(.+)'",
            r"Failed to resolve entry for package \"(.+)\"",
            r"Unable to resolve dependency: (.+)",
            
            # Java/Maven dependency errors
            r"Could not resolve dependencies for project (.+): Could not find artifact (.+)",
            r"Could not transfer artifact (.+) from/to (.+)",
            r"Failed to collect dependencies at (.+)",
            
            # Docker dependency errors
            r"pull access denied for (.+), repository does not exist",
            r"failed to solve: (.+): pull access denied",
            r"failed to register layer: (.+)",
            
            # Go dependency errors
            r"go: (.+): no matching versions for query",
            r"go: missing go.sum entry for module providing package (.+)",
            
            # Ruby dependency errors
            r"Gem::LoadError: Could not find (.+) in any of the sources",
            r"Bundler::GemNotFound: Could not find gem '(.+)'",
            
            # General dependency errors
            r"Failed to find (.+) in registry",
            r"Unable to locate package (.+)",
            r"Package '(.+)' has no installation candidate"
        ],
        "solutions": {
            "python": "pip install {package}",
            "node": "npm install {package}",
            "java": "mvn dependency:get -Dartifact={package}",
            "docker": "docker pull {package}",
            "go": "go get {package}",
            "ruby": "gem install {package}",
            "general": "Install missing dependency: {package}"
        }
    },
    "permission": {
        "patterns": [
            # File system permission errors
            r"PermissionError: (.+)",
            r"EACCES: permission denied",
            r"AccessDenied: (.+)",
            r"chmod: cannot access '(.+)': No such file or directory",
            r"chown: cannot access '(.+)': No such file or directory",
            r"mkdir: cannot create directory '(.+)': Permission denied",
            r"touch: cannot touch '(.+)': Permission denied",
            r"cp: cannot create regular file '(.+)': Permission denied",
            r"mv: cannot move '(.+)': Permission denied",
            r"rm: cannot remove '(.+)': Permission denied",
            
            # Docker permission errors
            r"permission denied while trying to connect to the Docker daemon socket",
            r"Got permission denied while trying to connect to the Docker daemon",
            r"docker: Got permission denied (.+)",
            
            # Git permission errors
            r"Permission denied \(publickey\)",
            r"fatal: could not create work tree dir '(.+)'(.+)Permission denied",
            r"fatal: Unable to create '(.+)/\.git/(.+)': Permission denied",
            
            # CI/CD platform permission errors
            r"Error: EACCES: permission denied, access '(.+)'",
            r"Error: EACCES: permission denied, mkdir '(.+)'",
            r"Error: EACCES: permission denied, open '(.+)'",
            r"Error: EACCES: permission denied, unlink '(.+)'",
            r"Error: EACCES: permission denied, rmdir '(.+)'",
            r"Error: EACCES: permission denied, copyfile '(.+)'",
            r"Error: EACCES: permission denied, chmod '(.+)'",
            
            # Kubernetes/Cloud permission errors
            r"Error from server \(Forbidden\): (.+) is forbidden: (.+)",
            r"AccessDeniedException: (.+)",
            r"User (.+) cannot (.+) resource (.+) in API group (.+)",
            r"Error: configmaps (.+) is forbidden: (.+)"
        ],
        "solutions": {
            "file": "chmod {mode} {path}",
            "directory": "sudo chown -R {user}:{group} {path}",
            "docker": "sudo usermod -aG docker $USER && newgrp docker",
            "git": "chmod 600 ~/.ssh/id_rsa && ssh-add ~/.ssh/id_rsa",
            "kubernetes": "kubectl create rolebinding {name} --clusterrole={role} --user={user}",
            "general": "Check and fix permissions for: {resource}"
        }
    },
    "configuration": {
        "patterns": [
            # General configuration errors
            r"ConfigurationError: (.+)",
            r"InvalidConfiguration: (.+)",
            r"Missing configuration for: (.+)",
            r"Configuration file '(.+)' not found",
            r"Failed to load configuration from '(.+)'",
            r"Invalid configuration: (.+)",
            r"No configuration file found at: (.+)",
            
            # Environment variable errors
            r"Environment variable (.+) is not set",
            r"Required environment variable (.+) is not defined",
            r"Missing required environment variable: (.+)",
            r"Could not find environment variable: (.+)",
            
            # CI/CD platform configuration errors
            r"\.github/workflows/(.+)\.yml: (.+)",
            r"\.gitlab-ci\.yml: (.+)",
            r"Error: Workflow file (.+) not found",
            r"Error: Workflow file (.+) is not valid YAML",
            r"Error: Workflow file (.+) has invalid syntax",
            
            # Docker configuration errors
            r"Error response from daemon: (.+)",
            r"The Compose file '(.+)' is invalid",
            r"Dockerfile parse error line (.+): (.+)",
            r"invalid reference format: repository name must be lowercase",
            
            # Kubernetes configuration errors
            r"error validating \"(.+)\": (.+)",
            r"error: error validating \"(.+)\": (.+)",
            r"The (.+) \"(.+)\" is invalid: (.+)",
            
            # Cloud provider configuration errors
            r"InvalidClientTokenId: The security token included in the request is invalid",
            r"AuthFailure: AWS was not able to validate the provided access credentials",
            r"InvalidAuthenticationTokenTenant: The access token is from the wrong tenant",
            r"Request had insufficient authentication scopes"
        ],
        "solutions": {
            "env": "Set environment variable: {variable}",
            "file": "Create/update config file: {file}",
            "docker": "Check Docker configuration: {detail}",
            "kubernetes": "Validate Kubernetes manifest: {detail}",
            "cloud": "Verify cloud provider credentials: {detail}",
            "general": "Fix configuration: {detail}"
        }
    },
    "network": {
        "patterns": [
            # General network errors
            r"ConnectionError: (.+)",
            r"Connection refused: (.+)",
            r"Failed to connect to (.+)",
            r"Network error: (.+)",
            r"Network unreachable: (.+)",
            r"Could not resolve host: (.+)",
            r"Name or service not known",
            r"Connection timed out",
            
            # HTTP errors
            r"HTTPError: (.+)",
            r"HTTP Error 4\d\d: (.+)",
            r"HTTP Error 5\d\d: (.+)",
            r"Status code (.+) for url: (.+)",
            
            # API errors
            r"API rate limit exceeded",
            r"API Error: (.+)",
            r"API request failed: (.+)",
            
            # DNS errors
            r"getaddrinfo ENOTFOUND (.+)",
            r"getaddrinfo EAI_AGAIN (.+)",
            r"Could not resolve DNS for (.+)",
            
            # Proxy errors
            r"ProxyError: (.+)",
            r"Proxy Authentication Required",
            r"407 Proxy Authentication Required",
            
            # SSL/TLS errors
            r"SSLError: (.+)",
            r"SSL Certificate Error: (.+)",
            r"SSL: CERTIFICATE_VERIFY_FAILED",
            r"SSL handshake failed"
        ],
        "solutions": {
            "connection": "Check network connectivity to {host}",
            "dns": "Verify DNS resolution for {host}",
            "proxy": "Configure proxy settings: {detail}",
            "ssl": "Fix SSL certificate issues: {detail}",
            "api": "Handle API rate limiting or authentication: {detail}",
            "general": "Resolve network issue: {detail}"
        }
    },
    "resource": {
        "patterns": [
            # Memory errors
            r"MemoryError: (.+)",
            r"java\.lang\.OutOfMemoryError: (.+)",
            r"JavaScript heap out of memory",
            r"Killed: 9",  # OOM killer
            r"fatal error: runtime: out of memory",
            r"Cannot allocate memory",
            
            # Disk space errors
            r"No space left on device",
            r"Disk quota exceeded",
            r"IOException: No space left on device",
            r"Not enough free disk space",
            
            # CPU errors
            r"CPU usage exceeded (.+)",
            r"Process timed out after (.+)",
            
            # Resource limit errors
            r"Resource temporarily unavailable",
            r"Too many open files",
            r"Error: EMFILE, too many open files",
            r"Error: ENFILE, file table overflow",
            
            # Container resource errors
            r"OOMKilled: true",
            r"Container killed due to memory usage",
            r"Container exited with code 137",  # OOM kill
            r"Container exited with code 143"   # SIGTERM
        ],
        "solutions": {
            "memory": "Increase memory allocation: {detail}",
            "disk": "Free up disk space or increase disk quota: {detail}",
            "cpu": "Optimize CPU usage or increase CPU allocation: {detail}",
            "files": "Increase file descriptor limits: {detail}",
            "container": "Adjust container resource limits: {detail}",
            "general": "Resolve resource constraint: {detail}"
        }
    },
    "build": {
        "patterns": [
            # Compilation errors
            r"Compilation failed: (.+)",
            r"Compilation error: (.+)",
            r"Build failed: (.+)",
            r"Failed to compile (.+)",
            r"error: (.+)",
            r"ERROR in (.+)",
            
            # Syntax errors
            r"SyntaxError: (.+)",
            r"ParseError: (.+)",
            r"Syntax error: (.+)",
            
            # Type errors
            r"TypeError: (.+)",
            r"Type error: (.+)",
            r"Type mismatch: (.+)",
            
            # Linker errors
            r"Linker error: (.+)",
            r"Undefined reference to (.+)",
            r"Undefined symbol: (.+)",
            
            # Package manager build errors
            r"npm ERR! code EBUILD",
            r"npm ERR! Failed at the (.+) script",
            r"ERROR: Could not build wheels for (.+)",
            
            # Docker build errors
            r"failed to build: (.+)",
            r"error building image: (.+)",
            r"Step \d+/\d+ : (.+) returned a non-zero code: (.+)"
        ],
        "solutions": {
            "compilation": "Fix compilation error: {detail}",
            "syntax": "Fix syntax error: {detail}",
            "type": "Fix type error: {detail}",
            "linker": "Resolve linker error: {detail}",
            "package": "Fix package build error: {detail}",
            "docker": "Fix Docker build error: {detail}",
            "general": "Resolve build error: {detail}"
        }
    },
    "test": {
        "patterns": [
            # Test failure patterns
            r"Test failed: (.+)",
            r"FAIL: (.+)",
            r"AssertionError: (.+)",
            r"Expected (.+) but got (.+)",
            r"Expected value to be (.+), but got (.+)",
            r"Expected to be (.+), but was (.+)",
            
            # Test framework errors
            r"pytest\.(.+)Error: (.+)",
            r"jest\.(.+)Error: (.+)",
            r"mocha\.(.+)Error: (.+)",
            r"junit\.(.+)Error: (.+)",
            
            # Test timeout errors
            r"Test timed out after (.+)",
            r"Timeout - Async callback was not invoked within (.+)",
            r"Error: Timeout of (.+) exceeded",
            
            # Test setup errors
            r"SetupError: (.+)",
            r"BeforeAll hook failed: (.+)",
            r"BeforeEach hook failed: (.+)",
            r"Error in setup: (.+)",
            
            # Test coverage errors
            r"Coverage failed: (.+)",
            r"Coverage threshold not met: (.+)",
            r"Expected coverage to be at least (.+)%, but was (.+)%"
        ],
        "solutions": {
            "assertion": "Fix test assertion: {detail}",
            "framework": "Resolve test framework error: {detail}",
            "timeout": "Increase test timeout or optimize test: {detail}",
            "setup": "Fix test setup error: {detail}",
            "coverage": "Improve test coverage: {detail}",
            "general": "Fix test failure: {detail}"
        }
    },
    "deployment": {
        "patterns": [
            # Deployment errors
            r"Deployment failed: (.+)",
            r"Failed to deploy: (.+)",
            r"Error deploying to (.+): (.+)",
            
            # Kubernetes deployment errors
            r"Error creating: (.+): (.+) already exists",
            r"Error creating: (.+): (.+) is invalid",
            r"Error from server \((.+)\): (.+)",
            r"pods \"(.+)\" is forbidden: (.+)",
            
            # Cloud provider deployment errors
            r"OperationError: (.+)",
            r"ResourceNotFound: (.+)",
            r"ResourceExistsError: (.+)",
            r"QuotaExceeded: (.+)",
            
            # Container registry errors
            r"denied: requested access to the resource is denied",
            r"unauthorized: authentication required",
            r"toomanyrequests: You have reached your pull rate limit",
            
            # Serverless deployment errors
            r"Function (.+) failed to deploy: (.+)",
            r"Lambda function (.+) failed to deploy: (.+)",
            r"CloudFormation stack (.+) failed to create/update: (.+)"
        ],
        "solutions": {
            "kubernetes": "Fix Kubernetes deployment: {detail}",
            "cloud": "Resolve cloud provider deployment issue: {detail}",
            "registry": "Fix container registry access: {detail}",
            "serverless": "Fix serverless deployment: {detail}",
            "general": "Resolve deployment error: {detail}"
        }
    },
    "security": {
        "patterns": [
            # Security scan errors
            r"Security vulnerability found: (.+)",
            r"CVE-\d+-\d+: (.+)",
            r"Critical vulnerability detected: (.+)",
            r"High severity vulnerability: (.+)",
            
            # Authentication errors
            r"Authentication failed: (.+)",
            r"Unauthorized: (.+)",
            r"Invalid credentials: (.+)",
            r"Access token expired",
            
            # Authorization errors
            r"Forbidden: (.+)",
            r"Access denied: (.+)",
            r"Insufficient permissions: (.+)",
            
            # Secret management errors
            r"Secret (.+) not found",
            r"Failed to retrieve secret: (.+)",
            r"Error accessing secret: (.+)",
            
            # Certificate errors
            r"Certificate validation failed: (.+)",
            r"Certificate expired: (.+)",
            r"Certificate not trusted: (.+)",
            r"Certificate verification failed: (.+)"
        ],
        "solutions": {
            "vulnerability": "Fix security vulnerability: {detail}",
            "authentication": "Fix authentication issue: {detail}",
            "authorization": "Fix authorization issue: {detail}",
            "secret": "Fix secret management issue: {detail}",
            "certificate": "Fix certificate issue: {detail}",
            "general": "Resolve security issue: {detail}"
        }
    }
}

# Auto-patching templates
PATCH_TEMPLATES = {
    # Dependency patches
    "python_dependency": """
try:
    import subprocess
    subprocess.check_call(["pip", "install", "{{ package }}"])
    print("Successfully installed {{ package }}")
except Exception as e:
    print(f"Failed to install {{ package }}: {str(e)}")
""",
    "node_dependency": """
try {
    const { execSync } = require('child_process');
    execSync('npm install {{ package }}');
    console.log('Successfully installed {{ package }}');
} catch (error) {
    console.error(`Failed to install {{ package }}: ${error.message}`);
}
""",
    "java_dependency": """
try {
    import subprocess
    subprocess.check_call(["mvn", "dependency:get", "-Dartifact={{ package }}"])
    print("Successfully installed {{ package }}")
except Exception as e:
    print(f"Failed to install {{ package }}: {str(e)}")
""",
    "go_dependency": """
try {
    import subprocess
    subprocess.check_call(["go", "get", "{{ package }}"])
    print("Successfully installed {{ package }}")
except Exception as e:
    print(f"Failed to install {{ package }}: {str(e)}")
""",
    "ruby_dependency": """
try:
    import subprocess
    subprocess.check_call(["gem", "install", "{{ package }}"])
    print("Successfully installed {{ package }}")
except Exception as e:
    print(f"Failed to install {{ package }}: {str(e)}")
""",
    
    # Permission patches
    "permission_fix": """
import os
import stat

try:
    os.chmod("{{ path }}", {{ mode }})
    print(f"Successfully updated permissions for {{ path }}")
except Exception as e:
    print(f"Failed to update permissions: {str(e)}")
""",
    "recursive_permission_fix": """
import os
import stat
import subprocess

try:
    # For directories, apply recursively
    subprocess.check_call(["chmod", "-R", "{{ mode }}", "{{ path }}"])
    print(f"Successfully updated permissions recursively for {{ path }}")
except Exception as e:
    print(f"Failed to update permissions: {str(e)}")
""",
    "docker_permission_fix": """
import subprocess

try:
    # Add current user to docker group
    subprocess.check_call(["sudo", "usermod", "-aG", "docker", "$USER"])
    print("Added current user to docker group. You may need to log out and back in for changes to take effect.")
except Exception as e:
    print(f"Failed to update docker permissions: {str(e)}")
""",
    
    # Configuration patches
    "env_var_fix": """
import os
import dotenv

try:
    # Create or update .env file
    env_path = '.env'
    
    # Load existing .env if it exists
    env_vars = {}
    if os.path.exists(env_path):
        dotenv.load_dotenv(env_path)
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Add or update the variable
    env_vars['{{ variable }}'] = '{{ value }}'
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\\n")
    
    # Set in current environment
    os.environ['{{ variable }}'] = '{{ value }}'
    
    print(f"Successfully set environment variable {{ variable }}={{ value }}")
except Exception as e:
    print(f"Failed to set environment variable: {str(e)}")
""",
    "json_config_fix": """
import json
import os

try:
    config_path = '{{ path }}'
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    
    # Load existing config if it exists
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Update with new values
    new_config = {{ config_values }}
    
    # Merge configs
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                deep_update(d[k], v)
            else:
                d[k] = v
    
    deep_update(config, new_config)
    
    # Write back to file
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Successfully updated configuration file: {config_path}")
except Exception as e:
    print(f"Failed to update configuration: {str(e)}")
""",
    "yaml_config_fix": """
import yaml
import os

try:
    config_path = '{{ path }}'
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    
    # Load existing config if it exists
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    
    # Update with new values
    new_config = {{ config_values }}
    
    # Merge configs
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                deep_update(d[k], v)
            else:
                d[k] = v
    
    deep_update(config, new_config)
    
    # Write back to file
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Successfully updated configuration file: {config_path}")
except Exception as e:
    print(f"Failed to update configuration: {str(e)}")
""",
    
    # Network patches
    "proxy_config_fix": """
import os
import subprocess

try:
    # Set proxy environment variables
    os.environ['HTTP_PROXY'] = '{{ proxy_url }}'
    os.environ['HTTPS_PROXY'] = '{{ proxy_url }}'
    
    # Add to .bashrc or .zshrc for persistence
    shell_config = os.path.expanduser('~/.bashrc')
    if os.path.exists(os.path.expanduser('~/.zshrc')):
        shell_config = os.path.expanduser('~/.zshrc')
    
    with open(shell_config, 'a') as f:
        f.write(f"\\n# Added by Self-Healing Debugger\\n")
        f.write(f"export HTTP_PROXY='{{ proxy_url }}'\\n")
        f.write(f"export HTTPS_PROXY='{{ proxy_url }}'\\n")
    
    # Configure git to use proxy
    subprocess.check_call(['git', 'config', '--global', 'http.proxy', '{{ proxy_url }}'])
    subprocess.check_call(['git', 'config', '--global', 'https.proxy', '{{ proxy_url }}'])
    
    print(f"Successfully configured proxy settings")
except Exception as e:
    print(f"Failed to configure proxy: {str(e)}")
""",
    "dns_fix": """
import subprocess

try:
    # Add entry to /etc/hosts
    with open('/etc/hosts', 'a') as f:
        f.write(f"{{ ip_address }} {{ hostname }}\\n")
    
    print(f"Successfully added DNS entry for {{ hostname }}")
except Exception as e:
    print(f"Failed to update DNS configuration: {str(e)}")
    print("Try running with sudo or manually add the entry to /etc/hosts")
""",
    
    # Resource patches
    "memory_limit_fix": """
import json
import os

try:
    # For Node.js applications
    if os.path.exists('package.json'):
        with open('package.json', 'r') as f:
            package_json = json.load(f)
        
        # Add or update NODE_OPTIONS in scripts
        for script_name in package_json.get('scripts', {}):
            if 'NODE_OPTIONS' not in package_json['scripts'][script_name]:
                package_json['scripts'][script_name] = f"NODE_OPTIONS='--max-old-space-size={{ memory_limit }}' {package_json['scripts'][script_name]}"
        
        with open('package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        
        print(f"Successfully updated Node.js memory limit to {{ memory_limit }}MB")
    
    # For Docker applications
    elif os.path.exists('docker-compose.yml'):
        import yaml
        with open('docker-compose.yml', 'r') as f:
            compose = yaml.safe_load(f)
        
        # Update memory limits for services
        for service_name in compose.get('services', {}):
            if 'deploy' not in compose['services'][service_name]:
                compose['services'][service_name]['deploy'] = {}
            if 'resources' not in compose['services'][service_name]['deploy']:
                compose['services'][service_name]['deploy']['resources'] = {}
            if 'limits' not in compose['services'][service_name]['deploy']['resources']:
                compose['services'][service_name]['deploy']['resources']['limits'] = {}
            
            compose['services'][service_name]['deploy']['resources']['limits']['memory'] = '{{ memory_limit }}m'
        
        with open('docker-compose.yml', 'w') as f:
            yaml.dump(compose, f, default_flow_style=False)
        
        print(f"Successfully updated Docker memory limits to {{ memory_limit }}MB")
    
    else:
        print("No supported configuration files found for memory limit adjustment")
except Exception as e:
    print(f"Failed to update memory limits: {str(e)}")
""",
    
    # Test patches
    "test_timeout_fix": """
import json
import os
import re

try:
    # For Jest (JavaScript/TypeScript)
    if os.path.exists('package.json'):
        with open('package.json', 'r') as f:
            package_json = json.load(f)
        
        # Add or update Jest timeout in package.json
        if 'jest' not in package_json:
            package_json['jest'] = {}
        
        package_json['jest']['testTimeout'] = {{ timeout }}
        
        with open('package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        
        print(f"Successfully updated Jest test timeout to {{ timeout }}ms")
    
    # For pytest (Python)
    elif os.path.exists('pytest.ini'):
        with open('pytest.ini', 'r') as f:
            content = f.read()
        
        if 'timeout' in content:
            content = re.sub(r'timeout = \\d+', f'timeout = {{ timeout // 1000 }}', content)
        else:
            if '[pytest]' not in content:
                content = '[pytest]\\n' + content
            content += f"\\ntimeout = {{ timeout // 1000 }}\\n"
        
        with open('pytest.ini', 'w') as f:
            f.write(content)
        
        print(f"Successfully updated pytest timeout to {{ timeout // 1000 }}s")
    
    # For Mocha (JavaScript)
    elif os.path.exists('.mocharc.json') or os.path.exists('.mocharc.js'):
        config_file = '.mocharc.json' if os.path.exists('.mocharc.json') else '.mocharc.js'
        
        if config_file.endswith('.json'):
            with open(config_file, 'r') as f:
                mocha_config = json.load(f)
            
            mocha_config['timeout'] = {{ timeout }}
            
            with open(config_file, 'w') as f:
                json.dump(mocha_config, f, indent=2)
        else:
            # For .js config, we'll append to it
            with open(config_file, 'a') as f:
                f.write(f"\\n// Updated by Self-Healing Debugger\\nmodule.exports.timeout = {{ timeout }};\\n")
        
        print(f"Successfully updated Mocha test timeout to {{ timeout }}ms")
    
    else:
        print("No supported test configuration files found for timeout adjustment")
except Exception as e:
    print(f"Failed to update test timeout: {str(e)}")
""",
    
    # Security patches
    "npm_audit_fix": """
try {
    const { execSync } = require('child_process');
    console.log('Running npm audit fix...');
    const output = execSync('npm audit fix', { encoding: 'utf8' });
    console.log(output);
    console.log('Successfully ran npm audit fix');
} catch (error) {
    console.error(`Failed to run npm audit fix: ${error.message}`);
    console.error('You may need to run npm audit fix --force for breaking changes');
}
""",
    "pip_vulnerability_fix": """
import subprocess
import re

try:
    # Get list of vulnerable packages
    print("Checking for vulnerable packages...")
    pip_list = subprocess.check_output(["pip", "list", "--format=freeze"], text=True)
    
    # Extract package names and versions
    packages = []
    for line in pip_list.splitlines():
        if '==' in line:
            package, version = line.split('==', 1)
            packages.append((package, version))
    
    # Check for known vulnerable package: {{ package }}
    vulnerable_package = "{{ package }}"
    vulnerable_version = "{{ vulnerable_version }}"
    safe_version = "{{ safe_version }}"
    
    for package, version in packages:
        if package.lower() == vulnerable_package.lower() and version == vulnerable_version:
            print(f"Found vulnerable package {package}=={version}")
            print(f"Upgrading to {safe_version}...")
            subprocess.check_call(["pip", "install", "--upgrade", f"{package}=={safe_version}"])
            print(f"Successfully upgraded {package} to {safe_version}")
            break
    else:
        print(f"Vulnerable package {vulnerable_package}=={vulnerable_version} not found")
    
except Exception as e:
    print(f"Failed to fix vulnerability: {str(e)}")
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
