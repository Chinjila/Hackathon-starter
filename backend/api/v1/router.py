"""
API Router - Main router for v1 endpoints
Registers all endpoint routers with appropriate prefixes and tags
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import expenses, health, github, security


# Create main API router for v1
api_router = APIRouter()

# Include health check endpoints
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Include expense management endpoints
api_router.include_router(
    expenses.router,
    prefix="/expenses",
    tags=["expenses"]
)

# Add GitHub routes
api_router.include_router(
    github.router,
    prefix="/github",
    tags=["github"]
)

# Add security scanning routes
api_router.include_router(
    security.router,
    prefix="/security",
    tags=["security"]
)