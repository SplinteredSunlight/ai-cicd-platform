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
    
    # OAuth2 Configuration (if using OAuth2)
    oauth2_issuer_url: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    
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
                "cache_enabled": True
            },
            "validate": {
                "method": "POST",
                "path": "/validate",
                "rate_limit": 100,
                "cache_enabled": False
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
                "cache_enabled": True
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
        "ttl": 300,
        "max_size": 1000
    },
    "short_term": {
        "ttl": 60,
        "max_size": 500
    },
    "long_term": {
        "ttl": 3600,
        "max_size": 200
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
