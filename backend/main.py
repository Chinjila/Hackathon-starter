"""
Zava AI Portal - Main Application Entry Point
FastAPI backend server with AI agent integration via MCP
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: Database and router imports are commented until those modules are fully implemented
from backend.core.database import engine, Base
from backend.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for application startup and shutdown.
    
    Startup:
    - Creates database tables if they don't exist
    
    Shutdown:
    - Disposes database engine and cleans up resources
    """
    # Startup: Create database tables
    logger.info("Starting up Zava AI Portal...")
    
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("Shutting down Zava AI Portal...")
    
    try:
        # Cleanup database engine
        await engine.dispose()
        logger.info("Database engine disposed")

        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application instance
app = FastAPI(
    title="Zava AI Portal",
    version="1.0.0",
    description="AI-powered personal finance management with expense classification and insights",
    lifespan=lifespan
)


# Configure CORS middleware
# Load allowed origins from environment variable (comma-separated)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS enabled for origins: {cors_origins}")


# Mount static files (frontend)
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    logger.info("Static files mounted at /static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Include API router
# Uncomment when router module is fully implemented:
app.include_router(api_router, prefix="/api/v1")
logger.info("API router included at /api/v1")


# Root endpoint - redirect to static frontend
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to the frontend application"""
    return RedirectResponse(url="/static/index.html")


# Health check endpoint at root level
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "Zava AI Portal",
        "version": "1.0.0"
    }


# Application info endpoint
@app.get("/info")
async def app_info():
    """Application information and configuration"""
    return {
        "name": "Zava AI Portal",
        "version": "1.0.0",
        "description": "AI-powered personal finance management",
        "mcp_server": os.getenv("MCP_SERVER_URL", "http://localhost:8000"),
        "mcp_enabled": os.getenv("MCP_ENABLED", "true").lower() == "true",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
