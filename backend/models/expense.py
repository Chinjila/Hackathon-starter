"""Expense Model - Database schema for expense tracking"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum

from backend.core.database import Base


class ExpenseClassification(str, Enum):
    """Expense classification categories"""
    NEEDS = "needs"
    WANTS = "wants"
    GOALS = "goals"


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default_user", index=True, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    category = Column(String, nullable=True)
    classification = Column(SQLEnum(ExpenseClassification), nullable=False)
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(String, nullable=True)
    amount_usd = Column(Float, nullable=False)
    expense_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)