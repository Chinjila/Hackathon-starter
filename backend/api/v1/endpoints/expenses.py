"""Expense API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.core.database import get_db
from backend.models.expense import ExpenseClassification
from backend.services.expense_service import ExpenseService
from pydantic import BaseModel

router = APIRouter()


class ExpenseCreate(BaseModel):
    description: str
    amount: float
    currency: str = "USD"
    category: Optional[str] = None
    user_id: str = "default_user"


@router.post("/", response_model=dict)
async def create_expense(
    expense: ExpenseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new expense with AI classification"""
    result = await ExpenseService.create_expense(
        db=db,
        description=expense.description,
        amount=expense.amount,
        currency=expense.currency,
        category=expense.category,
        user_id=expense.user_id
    )
    return {
        "id": result.id,
        "user_id": result.user_id,
        "description": result.description,
        "amount": result.amount,
        "currency": result.currency,
        "category": result.category,
        "classification": result.classification.value if result.classification else None,
        "ai_confidence": result.ai_confidence,
        "ai_reasoning": result.ai_reasoning,
        "amount_usd": result.amount_usd,
        "expense_date": result.expense_date.isoformat() if result.expense_date else None,
        "created_at": result.created_at.isoformat() if result.created_at else None,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None
    }


@router.get("/")
async def get_expenses(
    classification: Optional[str] = Query(None),
    user_id: str = Query("default_user"),
    db: AsyncSession = Depends(get_db)
):
    """Get all expenses with optional filtering"""
    classification_enum = None
    if classification:
        classification_enum = ExpenseClassification(classification)
    
    expenses = await ExpenseService.get_expenses(
        db=db,
        user_id=user_id,
        classification=classification_enum
    )
    
    return {
        "expenses": [
            {
                "id": exp.id,
                "user_id": exp.user_id,
                "description": exp.description,
                "amount": exp.amount,
                "currency": exp.currency,
                "category": exp.category,
                "classification": exp.classification.value if exp.classification else None,
                "ai_confidence": exp.ai_confidence,
                "ai_reasoning": exp.ai_reasoning,
                "amount_usd": exp.amount_usd,
                "expense_date": exp.expense_date.isoformat() if exp.expense_date else None,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "updated_at": exp.updated_at.isoformat() if exp.updated_at else None
            }
            for exp in expenses
        ],
        "count": len(expenses)
    }


@router.get("/summary")
async def get_summary(
    user_id: str = Query("default_user"),
    db: AsyncSession = Depends(get_db)
):
    """Get spending summary by category"""
    return await ExpenseService.get_expense_summary(db=db, user_id=user_id)


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an expense"""
    deleted = await ExpenseService.delete_expense(db=db, expense_id=expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense deleted successfully"}