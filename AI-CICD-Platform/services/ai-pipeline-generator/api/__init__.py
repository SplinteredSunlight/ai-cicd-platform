"""
API package for the AI Pipeline Generator service.
"""

from fastapi import APIRouter

from .optimization_api import router as optimization_router
from .dependency_api import router as dependency_router

# Create a main router
router = APIRouter()

# Include all sub-routers
router.include_router(optimization_router)
router.include_router(dependency_router)
