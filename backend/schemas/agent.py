"""
Agent schemas for request/response validation

TODO: Use GitHub Copilot to implement Pydantic schemas for Agent
Ask Copilot: "Create Pydantic schemas for AgentBase, AgentCreate, AgentUpdate, AgentResponse with proper validation"
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# TODO: Create AgentBase schema
# Fields: name, description, agent_type, configuration
# Add appropriate Field validators (min/max length, etc.)


# TODO: Create AgentCreate schema
# Inherits from AgentBase
# Add: is_active (default True)


# TODO: Create AgentUpdate schema
# All fields optional
# For PATCH operations


# TODO: Create AgentResponse schema
# Inherits from AgentBase
# Add: id, is_active, created_at, updated_at
# Configure: from_attributes = True
