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
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    
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
    vuln_db_path: str = os.getenv("VULN_DB_PATH", "/tmp/artifacts/vulnerability_database.sqlite")
    vuln_db_auto_update: bool = os.getenv("VULN_DB_AUTO_UPDATE", "true").lower() == "true"
    vuln_db_sources: List[str] = os.getenv("VULN_DB_SOURCES", "NVD,GITHUB,SNYK,OSINT").split(",")
    nvd_api_key: str = os.getenv("NVD_API_KEY", "")
    vuldb_api_key: str = os.getenv("VULDB_API_KEY", "")
    mitre_cve_api_key: str = os.getenv("MITRE_CVE_API_KEY", "")
    osv_api_key: str = os.getenv("OSV_API_KEY", "")  # OSV doesn't require an API key, but added for future use
    
    # Additional Vulnerability Database Sources
    ncp_api_key: str = os.getenv("NCP_API_KEY", "")  # NIST National Checklist Program
    cert_api_key: str = os.getenv("CERT_API_KEY", "")  # CERT Coordination Center
    oval_api_key: str = os.getenv("OVAL_API_KEY", "")  # OVAL
    epss_api_key: str = os.getenv("EPSS_API_KEY", "")  # EPSS
    scap_api_key: str = os.getenv("SCAP_API_KEY", "")  # SCAP
    
    # Automated Remediation
    auto_remediation_enabled: bool = os.getenv("AUTO_REMEDIATION_ENABLED", "false").lower() == "true"
    auto_remediation_severity_threshold: str = os.getenv("AUTO_REMEDIATION_SEVERITY_THRESHOLD", "HIGH")
    auto_remediation_confidence_threshold: float = float(os.getenv("AUTO_REMEDIATION_CONFIDENCE_THRESHOLD", "0.8"))
    
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

# Remediation Configuration
REMEDIATION_CONFIG = {
    "strategies": {
        "UPGRADE": {
            "priority": 1,
            "description": "Upgrade the affected component to a fixed version",
            "confidence_threshold": 0.8
        },
        "PATCH": {
            "priority": 2,
            "description": "Apply a patch to the affected component",
            "confidence_threshold": 0.7
        },
        "REPLACE": {
            "priority": 3,
            "description": "Replace the affected component with an alternative",
            "confidence_threshold": 0.6
        },
        "MITIGATE": {
            "priority": 4,
            "description": "Apply mitigation measures without fixing the vulnerability",
            "confidence_threshold": 0.5
        },
        "WORKAROUND": {
            "priority": 5,
            "description": "Apply a workaround to avoid the vulnerability",
            "confidence_threshold": 0.4
        },
        "IGNORE": {
            "priority": 6,
            "description": "Ignore the vulnerability (with justification)",
            "confidence_threshold": 0.9
        }
    },
    "sources": {
        "NCP": {
            "priority": 1,
            "description": "NIST National Checklist Program",
            "confidence": 0.9
        },
        "CERT": {
            "priority": 2,
            "description": "CERT Coordination Center",
            "confidence": 0.85
        },
        "OVAL": {
            "priority": 3,
            "description": "Open Vulnerability and Assessment Language",
            "confidence": 0.8
        },
        "SCAP": {
            "priority": 4,
            "description": "Security Content Automation Protocol",
            "confidence": 0.75
        },
        "EPSS": {
            "priority": 5,
            "description": "Exploit Prediction Scoring System",
            "confidence": 0.7
        },
        "VENDOR": {
            "priority": 1,
            "description": "Vendor advisory",
            "confidence": 0.95
        },
        "COMMUNITY": {
            "priority": 6,
            "description": "Community-provided remediation",
            "confidence": 0.6
        },
        "INTERNAL": {
            "priority": 7,
            "description": "Internally developed remediation",
            "confidence": 0.5
        }
    }
}
