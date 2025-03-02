"""
Configuration settings for the AI Pipeline Generator service.
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Settings for the AI Pipeline Generator service."""
    
    # Service settings
    SERVICE_NAME: str = "ai-pipeline-generator"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API settings
    API_PREFIX: str = "/api/v1"
    
    # Database settings
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DB_NAME: str = Field(default="pipeline_generator", env="DB_NAME")
    
    # Optimization settings
    OPTIMIZATION_METRICS_STORAGE_PATH: str = Field(
        default="data/optimization_metrics.json",
        env="OPTIMIZATION_METRICS_STORAGE_PATH"
    )
    
    # Performance profiling settings
    PERFORMANCE_PROFILING_ENABLED: bool = Field(default=True, env="PERFORMANCE_PROFILING_ENABLED")
    PERFORMANCE_METRICS_RETENTION_DAYS: int = Field(default=30, env="PERFORMANCE_METRICS_RETENTION_DAYS")
    
    # Parallel execution settings
    MAX_PARALLEL_JOBS: int = Field(default=10, env="MAX_PARALLEL_JOBS")
    
    # Resource optimization settings
    RESOURCE_OPTIMIZATION_ENABLED: bool = Field(default=True, env="RESOURCE_OPTIMIZATION_ENABLED")
    
    # Caching settings
    CACHING_OPTIMIZATION_ENABLED: bool = Field(default=True, env="CACHING_OPTIMIZATION_ENABLED")
    
    # Supported CI/CD platforms
    SUPPORTED_PLATFORMS: List[str] = [
        "github-actions",
        "gitlab-ci",
        "circle-ci",
        "jenkins",
        "azure-pipelines",
        "travis-ci",
        "bitbucket-pipelines"
    ]
    
    # Platform-specific settings
    PLATFORM_SETTINGS: Dict[str, Dict[str, Any]] = {
        "github-actions": {
            "max_job_timeout_minutes": 360,
            "default_runner": "ubuntu-latest"
        },
        "gitlab-ci": {
            "max_job_timeout_minutes": 60,
            "default_image": "alpine:latest"
        },
        "circle-ci": {
            "max_job_timeout_minutes": 60,
            "default_executor": "docker"
        },
        "jenkins": {
            "max_job_timeout_minutes": 180,
            "default_agent": "any"
        },
        "azure-pipelines": {
            "max_job_timeout_minutes": 360,
            "default_pool": "ubuntu-latest"
        },
        "travis-ci": {
            "max_job_timeout_minutes": 50,
            "default_os": "linux"
        },
        "bitbucket-pipelines": {
            "max_job_timeout_minutes": 120,
            "default_image": "atlassian/default-image:latest"
        }
    }
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()
