"""
AI Agents endpoints
Manages AI agents integrated via MCP

TODO: Use GitHub Copilot to implement agent CRUD endpoints
Ask Copilot: "Create FastAPI router with POST, GET, DELETE endpoints for Agent using AgentService"
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
# from backend.core.database import get_db
# from backend.schemas.agent import AgentCreate, AgentResponse
# from backend.services.agent_service import AgentService

router = APIRouter()


# TODO: Implement POST / endpoint - create_agent
# Request: AgentCreate
# Response: AgentResponse
# Use AgentService to create agent


# TODO: Implement GET / endpoint - list_agents
# Query params: skip (default 0), limit (default 100)
# Response: List[AgentResponse]
# Use AgentService to list agents


# TODO: Implement GET /{agent_id} endpoint - get_agent
# Path param: agent_id (int)
# Response: AgentResponse
# Raise 404 if not found


# TODO: Implement DELETE /{agent_id} endpoint - delete_agent
# Path param: agent_id (int)
# Response: success message
# Raise 404 if not found
