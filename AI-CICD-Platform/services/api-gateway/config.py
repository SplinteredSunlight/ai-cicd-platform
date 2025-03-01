import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
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

class AuthProvider(str, Enum):
    OAUTH2 = "oauth2"
    JWT = "jwt"
    NONE = "none"

class Settings(BaseSettings):
    # Service Configuration
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: LogLevel = LogLevel.INFO
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Authentication
    auth_provider: AuthProvider = AuthProvider.JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 7
    jwt_blacklist_enabled: bool = True
    jwt_blacklist_token_checks: List[str] = ["access", "refresh"]
    
    # Token Security
    token_rotation_enabled: bool = True
    token_reuse_detection_enabled: bool = True
    token_jti_claim_enabled: bool = True
    
    # OAuth2 Configuration (if using OAuth2)
    oauth2_issuer_url: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_scopes: List[str] = ["read", "write", "admin"]
    
    # SAML Configuration
    saml_enabled: bool = False
    saml_idp_metadata_url: Optional[str] = None
    saml_sp_entity_id: Optional[str] = None
    saml_acs_url: Optional[str] = None
    
    # Social Login Configuration
    social_login_enabled: bool = False
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    
    # Authentication Rate Limiting
    auth_rate_limit_enabled: bool = True
    auth_rate_limit_max_attempts: int = 5
    auth_rate_limit_window: int = 15  # minutes
    auth_rate_limit_lockout_duration: int = 30  # minutes
    auth_rate_limit_progressive_lockout: bool = True
    auth_rate_limit_track_by_username: bool = True
    auth_rate_limit_track_by_ip: bool = True
    
    # Multi-factor Authentication
    mfa_enabled: bool = True
    mfa_required_for_roles: List[str] = ["admin"]
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 30  # seconds
    
    # Redis Configuration (for rate limiting & caching)
    redis_url: str = "redis://localhost:6379"
    redis_pool_size: int = 10
    
    # Service Discovery
    service_registry: Dict[str, str] = {
        "pipeline-generator": "http://localhost:8000",
        "security-enforcement": "http://localhost:8001",
        "self-healing-debugger": "http://localhost:8002"
    }
    
    # Monitoring & Tracing
    prometheus_enabled: bool = True
    jaeger_enabled: bool = True
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Logging Configuration
    log_format: str = "json"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Service Routes Configuration
SERVICE_ROUTES = {
    "pipeline-generator": {
        "prefix": "/api/v1/pipeline",
        "endpoints": {
            "generate": {
                "method": "POST",
                "path": "/generate",
                "rate_limit": 50,
                "cache_enabled": True,
                "cache_config": "medium_term",
                "cache_vary_by_user": False,
                "cache_vary_by_role": True
            },
            "validate": {
                "method": "POST",
                "path": "/validate",
                "rate_limit": 100,
                "cache_enabled": False
            },
            "status": {
                "method": "GET",
                "path": "/status",
                "rate_limit": 200,
                "cache_enabled": True,
                "cache_config": "short_term"
            },
            "list": {
                "method": "GET",
                "path": "/list",
                "rate_limit": 100,
                "cache_enabled": True,
                "cache_config": "user_specific",
                "cache_vary_by_user": True
            }
        }
    },
    "security-enforcement": {
        "prefix": "/api/v1/security",
        "endpoints": {
            "scan": {
                "method": "POST",
                "path": "/scan",
                "rate_limit": 30,
                "cache_enabled": False
            },
            "sbom": {
                "method": "POST",
                "path": "/sbom",
                "rate_limit": 30,
                "cache_enabled": True,
                "cache_config": "medium_term"
            },
            "vulnerabilities": {
                "method": "GET",
                "path": "/vulnerabilities",
                "rate_limit": 100,
                "cache_enabled": True,
                "cache_config": "short_term"
            },
            "compliance": {
                "method": "GET",
                "path": "/compliance",
                "rate_limit": 50,
                "cache_enabled": True,
                "cache_config": "role_specific",
                "cache_vary_by_role": True
            }
        }
    },
    "self-healing-debugger": {
        "prefix": "/api/v1/debug",
        "endpoints": {
            "analyze": {
                "method": "POST",
                "path": "/analyze",
                "rate_limit": 50,
                "cache_enabled": False
            },
            "patch": {
                "method": "POST",
                "path": "/patch",
                "rate_limit": 30,
                "cache_enabled": False
            },
            "history": {
                "method": "GET",
                "path": "/history",
                "rate_limit": 100,
                "cache_enabled": True,
                "cache_config": "user_specific",
                "cache_vary_by_user": True
            },
            "status": {
                "method": "GET",
                "path": "/status",
                "rate_limit": 200,
                "cache_enabled": True,
                "cache_config": "short_term"
            }
        }
    }
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIGS = {
    "default": {
        "requests": 100,
        "window": 60
    },
    "auth": {
        "requests": 20,
        "window": 60
    },
    "auth_login": {
        "requests": 10,
        "window": 60,
        "lockout_threshold": 5,
        "lockout_duration": 15  # minutes
    },
    "auth_mfa": {
        "requests": 5,
        "window": 60,
        "lockout_threshold": 3,
        "lockout_duration": 10  # minutes
    },
    "auth_refresh": {
        "requests": 30,
        "window": 60,
        "lockout_threshold": 10,
        "lockout_duration": 5  # minutes
    },
    "high_priority": {
        "requests": 200,
        "window": 60
    }
}

# Circuit Breaker Configuration
CIRCUIT_BREAKER_CONFIGS = {
    "default": {
        "failure_threshold": 5,
        "recovery_timeout": 30,
        "max_failures": 3
    },
    "critical": {
        "failure_threshold": 3,
        "recovery_timeout": 60,
        "max_failures": 2
    }
}

# Cache Configuration
CACHE_CONFIGS = {
    "default": {
        "ttl": 300,  # 5 minutes
        "max_size": 1000,  # KB
        "vary_by_user": False,
        "vary_by_role": False
    },
    "short_term": {
        "ttl": 60,  # 1 minute
        "max_size": 500,
        "vary_by_user": False,
        "vary_by_role": False
    },
    "medium_term": {
        "ttl": 600,  # 10 minutes
        "max_size": 800,
        "vary_by_user": False,
        "vary_by_role": True
    },
    "long_term": {
        "ttl": 3600,  # 1 hour
        "max_size": 200,
        "vary_by_user": False,
        "vary_by_role": False
    },
    "user_specific": {
        "ttl": 300,  # 5 minutes
        "max_size": 500,
        "vary_by_user": True,
        "vary_by_role": False
    },
    "role_specific": {
        "ttl": 600,  # 10 minutes
        "max_size": 800,
        "vary_by_user": False,
        "vary_by_role": True
    },
    "no_cache": {
        "ttl": 0,
        "max_size": 0,
        "vary_by_user": False,
        "vary_by_role": False
    }
}

# Error Response Templates
ERROR_TEMPLATES = {
    "rate_limit_exceeded": {
        "status_code": 429,
        "detail": "Rate limit exceeded. Please try again in {retry_after} seconds.",
        "headers": {
            "Retry-After": "{retry_after}"
        }
    },
    "auth_lockout": {
        "status_code": 429,
        "detail": "Too many failed authentication attempts. Your account has been temporarily locked. Please try again in {lockout_time} minutes.",
        "headers": {
            "Retry-After": "{retry_after}"
        }
    },
    "progressive_lockout": {
        "status_code": 429,
        "detail": "Too many failed authentication attempts. Your account has been locked for {lockout_time} minutes.",
        "headers": {
            "Retry-After": "{retry_after}"
        }
    },
    "circuit_open": {
        "status_code": 503,
        "detail": "Service temporarily unavailable. Please try again in {recovery_time} seconds.",
        "headers": {
            "Retry-After": "{recovery_time}"
        }
    },
    "service_unavailable": {
        "status_code": 503,
        "detail": "Service {service_name} is currently unavailable.",
        "headers": {}
    },
    "unauthorized": {
        "status_code": 401,
        "detail": "Authentication required.",
        "headers": {
            "WWW-Authenticate": "Bearer"
        }
    }
}
