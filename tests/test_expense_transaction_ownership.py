from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.api.v1.endpoints.expenses import delete_expense
from backend.core import database
from backend.services.ai_classification_service import AIClassificationService
from backend.services.expense_service import ExpenseService


class MockSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_get_db_commits_once_after_success(monkeypatch):
    session = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    monkeypatch.setattr(
        database,
        "async_session_maker",
        lambda: MockSessionContext(session),
    )

    generator = database.get_db()
    yielded_session = await generator.__anext__()

    assert yielded_session is session

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()

    session.commit.assert_awaited_once()
    session.rollback.assert_not_called()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_exception(monkeypatch):
    session = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()

    monkeypatch.setattr(
        database,
        "async_session_maker",
        lambda: MockSessionContext(session),
    )

    generator = database.get_db()
    await generator.__anext__()

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    session.commit.assert_not_called()
    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_expense_flushes_without_committing(monkeypatch):
    classification_mock = AsyncMock(
        return_value={
            "classification": "needs",
            "confidence": 0.95,
            "reasoning": "essential expense",
        }
    )
    monkeypatch.setattr(
        AIClassificationService,
        "classify_expense_ai",
        classification_mock,
    )

    db = Mock()
    db.add = Mock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.commit = AsyncMock()

    expense = await ExpenseService.create_expense(
        db=db,
        description="Groceries",
        amount=42.5,
        currency="USD",
        category="food",
        user_id="user-123",
    )

    assert expense.description == "Groceries"
    db.add.assert_called_once()
    db.flush.assert_awaited_once()
    db.refresh.assert_awaited_once_with(expense)
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_expense_does_not_commit_directly():
    expense = object()
    result = Mock()
    result.scalar_one_or_none.return_value = expense

    db = Mock()
    db.execute = AsyncMock(return_value=result)
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    deleted = await ExpenseService.delete_expense(db=db, expense_id=7)

    assert deleted is True
    db.delete.assert_awaited_once_with(expense)
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_endpoint_delegates_write_without_committing(monkeypatch):
    delete_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(ExpenseService, "delete_expense", delete_mock)

    db = Mock()
    db.commit = AsyncMock()

    response = await delete_expense(expense_id=9, db=db)

    assert response == {"message": "Expense deleted successfully"}
    delete_mock.assert_awaited_once_with(db=db, expense_id=9)
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_endpoint_returns_404_when_service_finds_nothing(monkeypatch):
    monkeypatch.setattr(ExpenseService, "delete_expense", AsyncMock(return_value=False))

    with pytest.raises(HTTPException) as exc_info:
        await delete_expense(expense_id=99, db=Mock())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Expense not found"
