from fastapi import APIRouter

from .remediation_api import create_remediation_router

# Create the main API router
api_router = APIRouter()

# Include the remediation router
api_router.include_router(create_remediation_router())
