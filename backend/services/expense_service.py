"""
Expense Service - Business Logic Layer

This service handles expense creation with AI classification,
retrieval with filters, and summary calculations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict
from datetime import datetime
import logging

from backend.models.expense import Expense, ExpenseClassification
from backend.services.ai_classification_service import AIClassificationService

logger = logging.getLogger(__name__)


class ExpenseService:
    """Service for managing expenses with AI classification"""
    
    @staticmethod
    async def create_expense(
        db: AsyncSession,
        description: str,
        amount: float,
        currency: str = "USD",
        category: Optional[str] = None,
        user_id: str = "default_user"
    ) -> Expense:
        """
        Create a new expense with AI classification.

        The database dependency owns commit/rollback. This method only stages
        changes in the current transaction and refreshes the pending model so
        callers can use generated fields before the request completes.
        
        Args:
            db: Database session
            description: Expense description
            amount: Expense amount
            currency: Currency code (default: USD)
            category: Optional category hint
            user_id: User identifier (default: default_user)
            
        Returns:
            Created Expense object with AI classification
        """
        # Step 1: Classify expense via Azure AI Foundry Responses API
        classification_result = await AIClassificationService.classify_expense_ai(
            description=description,
            amount=amount,
            category=category
        )
        
        # Step 2: Create expense in database
        expense = Expense(
            user_id=user_id,
            description=description,
            amount=amount,
            currency=currency,
            category=category,
            classification=ExpenseClassification(classification_result["classification"]),
            ai_confidence=classification_result["confidence"],
            ai_reasoning=classification_result["reasoning"],
            amount_usd=amount,  # TODO: Add currency conversion if needed
            expense_date=datetime.utcnow()
        )
        
        db.add(expense)
        await db.flush()
        await db.refresh(expense)
        
        logger.info(f"Created expense: {expense.id} - {expense.description} ({expense.classification})")
        
        return expense
    
    @staticmethod
    async def get_expenses(
        db: AsyncSession,
        user_id: str = "default_user",
        classification: Optional[ExpenseClassification] = None,
        limit: int = 100
    ) -> List[Expense]:
        """
        Retrieve expenses with optional filtering.
        
        Args:
            db: Database session
            user_id: User identifier to filter by
            classification: Optional classification filter (needs/wants/goals)
            limit: Maximum number of expenses to return
            
        Returns:
            List of Expense objects
        """
        query = select(Expense).where(Expense.user_id == user_id)
        
        if classification:
            query = query.where(Expense.classification == classification)
        
        query = query.order_by(Expense.expense_date.desc()).limit(limit)
        
        result = await db.execute(query)
        expenses = result.scalars().all()
        
        logger.info(f"Retrieved {len(expenses)} expenses for user {user_id}")
        
        return list(expenses)
    
    @staticmethod
    async def get_expense_summary(
        db: AsyncSession,
        user_id: str = "default_user"
    ) -> Dict[str, float]:
        """
        Calculate spending summary by classification.
        
        Args:
            db: Database session
            user_id: User identifier
            
        Returns:
            Dict with totals for needs, wants, goals, and overall total
        """
        query = select(
            Expense.classification,
            func.sum(Expense.amount_usd).label("total"),
            func.count(Expense.id).label("count")
        ).where(
            Expense.user_id == user_id
        ).group_by(Expense.classification)
        
        result = await db.execute(query)
        rows = result.all()
        
        summary = {
            "needs": 0.0,
            "wants": 0.0,
            "goals": 0.0,
            "total": 0.0
        }
        
        for row in rows:
            classification = row.classification.value if row.classification else "wants"
            amount = float(row.total) if row.total else 0.0
            summary[classification] = amount
            summary["total"] += amount
        
        logger.info(f"Calculated summary for user {user_id}: Total ${summary['total']:.2f}")
        
        return summary
    
    @staticmethod
    async def delete_expense(
        db: AsyncSession,
        expense_id: int,
        user_id: str = "default_user"
    ) -> bool:
        """
        Delete an expense by ID.
        
        Args:
            db: Database session
            expense_id: ID of expense to delete
            user_id: User identifier (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        query = select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == user_id
        )
        result = await db.execute(query)
        expense = result.scalar_one_or_none()
        
        if not expense:
            logger.warning(f"Expense {expense_id} not found for user {user_id}")
            return False
        
        await db.delete(expense)
        
        logger.info(f"Deleted expense: {expense_id}")
        
        return True