"""
Configuration Module

This module contains the configuration settings for the deployment automation service.
"""

import os
from pydantic import BaseSettings
from typing import List, Dict, Any, Optional

class Settings(BaseSettings):
    """
    Settings for the deployment automation service.
    """
    # Service settings
    SERVICE_NAME: str = "deployment-automation"
    VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # API settings
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/v1"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Authentication settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Deployment settings
    DEFAULT_DEPLOYMENT_TIMEOUT: int = int(os.getenv("DEFAULT_DEPLOYMENT_TIMEOUT", "3600"))  # 1 hour
    MAX_DEPLOYMENT_TIMEOUT: int = int(os.getenv("MAX_DEPLOYMENT_TIMEOUT", "86400"))  # 24 hours
    
    # Approval settings
    DEFAULT_APPROVAL_TIMEOUT: int = int(os.getenv("DEFAULT_APPROVAL_TIMEOUT", "86400"))  # 24 hours
    AUTO_APPROVE_DEVELOPMENT: bool = os.getenv("AUTO_APPROVE_DEVELOPMENT", "True").lower() in ("true", "1", "t")
    
    # Rollback settings
    AUTO_ROLLBACK_ON_FAILURE: bool = os.getenv("AUTO_ROLLBACK_ON_FAILURE", "True").lower() in ("true", "1", "t")
    
    # Monitoring settings
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "60"))  # 60 seconds
    
    # Target settings
    DEFAULT_TARGET_TYPE: str = os.getenv("DEFAULT_TARGET_TYPE", "kubernetes")
    
    # Notification settings
    NOTIFICATION_CHANNELS: List[str] = os.getenv("NOTIFICATION_CHANNELS", "email,slack").split(",")
    
    # Integration settings
    INTEGRATION_SETTINGS: Dict[str, Any] = {
        "kubernetes": {
            "in_cluster": os.getenv("KUBERNETES_IN_CLUSTER", "False").lower() in ("true", "1", "t"),
            "config_path": os.getenv("KUBERNETES_CONFIG_PATH", "~/.kube/config"),
        },
        "aws": {
            "region": os.getenv("AWS_REGION", "us-west-2"),
        },
        "azure": {
            "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID", ""),
            "resource_group": os.getenv("AZURE_RESOURCE_GROUP", ""),
        },
        "gcp": {
            "project_id": os.getenv("GCP_PROJECT_ID", ""),
            "zone": os.getenv("GCP_ZONE", "us-central1-a"),
        },
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()
