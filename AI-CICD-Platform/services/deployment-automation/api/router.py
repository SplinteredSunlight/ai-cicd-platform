"""
API Router

This module sets up the API router for the deployment automation service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from config import settings
from services.deployment_pipeline_generator import DeploymentPipelineGenerator
from services.approval_workflow import ApprovalWorkflow
from services.rollback_manager import RollbackManager
from services.deployment_monitor import DeploymentMonitor
from services.target_integrator import TargetIntegrator

from api.routes import pipelines, approvals, rollbacks, monitoring, targets

# Create API router
api_router = APIRouter()

# Include route modules
api_router.include_router(
    pipelines.router,
    prefix="/v1/pipelines",
    tags=["pipelines"],
)

api_router.include_router(
    approvals.router,
    prefix="/v1/approvals",
    tags=["approvals"],
)

api_router.include_router(
    rollbacks.router,
    prefix="/v1/rollbacks",
    tags=["rollbacks"],
)

api_router.include_router(
    monitoring.router,
    prefix="/v1/monitoring",
    tags=["monitoring"],
)

api_router.include_router(
    targets.router,
    prefix="/v1/targets",
    tags=["targets"],
)

# Add version endpoint
@api_router.get("/version", tags=["system"])
async def get_version():
    """
    Get the API version.
    """
    return {
        "version": settings.VERSION,
        "api_version": "v1",
    }

# Add status endpoint
@api_router.get("/status", tags=["system"])
async def get_status():
    """
    Get the API status.
    """
    return {
        "status": "operational",
        "services": {
            "deployment_pipeline_generator": "up",
            "approval_workflow": "up",
            "rollback_manager": "up",
            "deployment_monitor": "up",
            "target_integrator": "up",
        },
    }
