"""
Deployment Automation Service

This is the main entry point for the deployment automation service.
"""

import logging
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.router import api_router
from api.websocket import websocket_router
from services.deployment_pipeline_generator import DeploymentPipelineGenerator
from services.approval_workflow import ApprovalWorkflow
from services.rollback_manager import RollbackManager
from services.deployment_monitor import DeploymentMonitor
from services.target_integrator import TargetIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Deployment Automation Service",
    description="Service for automating deployments to various environments",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
deployment_pipeline_generator = DeploymentPipelineGenerator()
approval_workflow = ApprovalWorkflow()
rollback_manager = RollbackManager()
deployment_monitor = DeploymentMonitor()
target_integrator = TargetIntegrator()

# Add service dependencies
def get_deployment_pipeline_generator():
    return deployment_pipeline_generator

def get_approval_workflow():
    return approval_workflow

def get_rollback_manager():
    return rollback_manager

def get_deployment_monitor():
    return deployment_monitor

def get_target_integrator():
    return target_integrator

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)

@app.get("/")
async def root():
    """
    Root endpoint for the deployment automation service.
    """
    return {
        "service": "Deployment Automation",
        "status": "running",
        "version": "0.1.0",
    }

@app.get("/health")
async def health():
    """
    Health check endpoint for the deployment automation service.
    """
    return {
        "status": "healthy",
        "services": {
            "deployment_pipeline_generator": "up",
            "approval_workflow": "up",
            "rollback_manager": "up",
            "deployment_monitor": "up",
            "target_integrator": "up",
        },
    }

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
