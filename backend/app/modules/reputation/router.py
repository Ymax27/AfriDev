"""Reputation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.core.utils import level_for_points
from app.modules.reputation import service
from app.modules.reputation.schemas import ReputationSummary, TransactionListOut, TransactionOut
from app.modules.users.service import get_by_id

router = APIRouter(tags=["reputation"])

LEVEL_THRESHOLDS = [("newcomer", 0), ("contributor", 50), ("confirmed", 200), ("expert", 500)]


def _next_level(points: int) -> tuple[str | None, int]:
    for name, threshold in LEVEL_THRESHOLDS:
        if points < threshold:
            return name, threshold - points
    return None, 0


@router.get("/reputation/me", response_model=ReputationSummary)
async def my_reputation(user: CurrentUser, db: DbSession) -> ReputationSummary:
    transactions, _ = await service.transactions_for(db, user.id, page=1, page_size=5)
    next_level, remaining = _next_level(user.reputation_points)
    return ReputationSummary(
        user_id=user.id,
        username=user.username,
        reputation_points=user.reputation_points,
        level=level_for_points(user.reputation_points),
        next_level=next_level,
        points_to_next_level=remaining,
        recent_transactions=[TransactionOut.model_validate(tx) for tx in transactions],
    )


@router.get("/reputation/transactions", response_model=TransactionListOut)
async def my_transactions(
    db: DbSession, user: CurrentUser, paging: Annotated[Pagination, Depends()]
) -> TransactionListOut:
    transactions, total = await service.transactions_for(
        db, user.id, page=paging.page, page_size=paging.page_size
    )
    return TransactionListOut(
        items=[TransactionOut.model_validate(tx) for tx in transactions],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.get("/reputation/transactions/{user_id}", response_model=TransactionListOut)
async def user_transactions(
    user_id: UUID, db: DbSession, paging: Annotated[Pagination, Depends()]
) -> TransactionListOut:
    await get_by_id(db, user_id)
    transactions, total = await service.transactions_for(
        db, user_id, page=paging.page, page_size=paging.page_size
    )
    return TransactionListOut(
        items=[TransactionOut.model_validate(tx) for tx in transactions],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )
