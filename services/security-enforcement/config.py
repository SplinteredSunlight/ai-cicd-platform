import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Dict, List
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Service Configuration
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security Scanner API Keys
    snyk_api_key: str = os.getenv("SNYK_API_KEY", "")
    trivy_server_url: str = os.getenv("TRIVY_SERVER_URL", "http://localhost:8080")
    zap_api_key: str = os.getenv("ZAP_API_KEY", "")
    
    # Sigstore Configuration
    sigstore_oidc_issuer: str = os.getenv("SIGSTORE_OIDC_ISSUER", "https://oauth2.sigstore.dev/auth")
    sigstore_fulcio_url: str = os.getenv("SIGSTORE_FULCIO_URL", "https://fulcio.sigstore.dev")
    sigstore_rekor_url: str = os.getenv("SIGSTORE_REKOR_URL", "https://rekor.sigstore.dev")
    
    # Scanning Configuration
    max_concurrent_scans: int = 5
    scan_timeout_seconds: int = 300
    blocking_severities: List[str] = ["CRITICAL", "HIGH"]
    
    # SBOM Configuration
    sbom_format: str = "cyclonedx"
    sbom_version: str = "1.4"
    artifact_storage_path: str = "/tmp/artifacts"
    
    # Cache Configuration
    scan_cache_ttl: int = 3600  # 1 hour
    
    # Vulnerability Database
    vuln_db_update_interval: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Scanner-specific configurations
TRIVY_CONFIG = {
    "severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    "scan_types": ["vuln", "config", "secret"],
    "timeout": 180,
    "options": {
        "skip_update": False,
        "ignore_unfixed": False,
        "vuln_type": "os,library"
    }
}

SNYK_CONFIG = {
    "org_id": os.getenv("SNYK_ORG_ID", ""),
    "scan_types": ["code", "package", "container"],
    "severity_threshold": "high",
    "additional_args": {
        "fail_on": "all",
        "json_file_output": True
    }
}

ZAP_CONFIG = {
    "scan_types": ["baseline", "full"],
    "risk_threshold": "high",
    "config_params": {
        "ajax_spider": True,
        "recursive_scan": True
    }
}

# SBOM Generation Configuration
SBOM_CONFIG = {
    "formats": ["cyclonedx-json", "cyclonedx-xml", "spdx"],
    "components": ["application", "container", "system"],
    "signing": {
        "enabled": True,
        "method": "sigstore-python"
    }
}

# Vulnerability Assessment Configuration
VULNERABILITY_THRESHOLDS = {
    Environment.DEVELOPMENT: {
        "CRITICAL": 0,
        "HIGH": 2,
        "MEDIUM": 5,
        "LOW": 10
    },
    Environment.STAGING: {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 3,
        "LOW": 5
    },
    Environment.PRODUCTION: {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 2,
        "LOW": 3
    }
}
