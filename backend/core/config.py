"""Application Configuration - Loads settings from environment variables"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Info
    APP_NAME: str = "Zava AI Portal"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/zava"

    # Azure OpenAI Configuration (v1 Responses API)
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    
    # Azure AI Foundry MCP Configuration
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    
    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5000,http://localhost:8000"        

    # GitHub Configuration (for Challenge 2)
    GH_PAT: Optional[str] = None
    GH_REPOSITORY: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Create global settings instance
settings = Settings()