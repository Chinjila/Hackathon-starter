"""
Health check endpoint
"""

from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check endpoint that returns service status and metadata.
    
    Returns:
        dict: Service health information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service": "zava-ai-portal"
    }
