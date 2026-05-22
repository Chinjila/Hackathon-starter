"""
Agent database model
Represents AI agents in the system

TODO: Use GitHub Copilot to implement the Agent model
Ask Copilot: "Create SQLAlchemy model for Agent with id, name, description, agent_type, is_active, configuration, timestamps"
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
# from backend.core.database import Base


# TODO: Create Agent model class
# Table name: "agents"
# Columns:
# - id: Integer, primary key, indexed
# - name: String(255), not null
# - description: Text, nullable
# - agent_type: String(100), not null (e.g., "mcp", "custom")
# - is_active: Boolean, default True
# - configuration: Text, nullable (for JSON config)
# - created_at: DateTime with timezone, server default now()
# - updated_at: DateTime with timezone, on update now()

# TODO: Add __repr__ method for debugging
