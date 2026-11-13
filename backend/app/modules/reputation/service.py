"""Auditable reputation ledger and award rules."""

import logging
from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReputationAction, ReputationStatus
from app.core.exceptions import NotFoundError
from app.core.utils import level_for_points
from app.modules.reputation.models import ReputationTransaction
from app.modules.users.models import User

logger = logging.getLogger("afridev.reputation")

POINTS: dict[str, int] = {
    ReputationAction.ACCEPTED_SOLUTION.value: 20,
    ReputationAction.USEFUL_VOTE.value: 2,
    ReputationAction.FIELD_REPORT_CONFIRMATION.value: 2,
    ReputationAction.MERGED_CONTRIBUTION.value: 15,
    ReputationAction.USEFUL_FEEDBACK.value: 3,
    ReputationAction.APPROVED_MISSION.value: 30,
    ReputationAction.VERIFIED_PROJECT_PUBLICATION.value: 5,
}

DAILY_POINT_CAP = 100
MAX_VERIFIED_PUBLICATIONS = 3
MAX_CONFIRMATION_AWARDS_PER_REPORT = 5
USEFUL_VOTE_DAILY_CAP = 10


def _day_start() -> datetime:
    now = datetime.now(UTC)
    return datetime.combine(now.date(), time.min, tzinfo=UTC)


async def _points_today(db: AsyncSession, user_id: UUID) -> int:
    total = await db.execute(
        select(func.coalesce(func.sum(ReputationTransaction.points), 0)).where(
            ReputationTransaction.user_id == user_id,
            ReputationTransaction.status == ReputationStatus.APPROVED.value,
            ReputationTransaction.created_at >= _day_start(),
        )
    )
    return int(total.scalar_one())


async def has_award(
    db: AsyncSession, *, user_id: UUID, action_type: str, reference_type: str, reference_id: str
) -> bool:
    existing = await db.execute(
        select(ReputationTransaction.id).where(
            ReputationTransaction.user_id == user_id,
            ReputationTransaction.action_type == action_type,
            ReputationTransaction.reference_type == reference_type,
            ReputationTransaction.reference_id == reference_id,
        )
    )
    return existing.scalar_one_or_none() is not None


async def award(
    db: AsyncSession,
    *,
    user_id: UUID,
    action_type: str,
    reference_type: str,
    reference_id: str,
    actor_id: UUID | None = None,
    points: int | None = None,
    is_demo: bool = False,
    note: str | None = None,
) -> ReputationTransaction | None:
    """Record a reputation transaction once, applying anti-fraud rules."""

    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("Reputation recipient not found")

    if actor_id is not None and actor_id == user_id:
        logger.info("blocked self-award", extra={"user_id": str(user_id)})
        return None
    if user.reputation_frozen or not user.is_active:
        return None
    if await has_award(
        db, user_id=user_id, action_type=action_type, reference_type=reference_type, reference_id=reference_id
    ):
        return None

    award_points = POINTS.get(action_type, 0) if points is None else points
    if award_points <= 0:
        return None

    if action_type == ReputationAction.VERIFIED_PROJECT_PUBLICATION.value:
        count = await db.execute(
            select(func.count(ReputationTransaction.id)).where(
                ReputationTransaction.user_id == user_id,
                ReputationTransaction.action_type == action_type,
            )
        )
        if int(count.scalar_one()) >= MAX_VERIFIED_PUBLICATIONS:
            return None

    if action_type == ReputationAction.USEFUL_VOTE.value:
        today_votes = await db.execute(
            select(func.coalesce(func.sum(ReputationTransaction.points), 0)).where(
                ReputationTransaction.user_id == user_id,
                ReputationTransaction.action_type == action_type,
                ReputationTransaction.created_at >= _day_start(),
            )
        )
        if int(today_votes.scalar_one()) >= USEFUL_VOTE_DAILY_CAP:
            return None

    if action_type == ReputationAction.FIELD_REPORT_CONFIRMATION.value:
        awards = await db.execute(
            select(func.count(ReputationTransaction.id)).where(
                ReputationTransaction.action_type == action_type,
                ReputationTransaction.reference_type == reference_type,
                ReputationTransaction.reference_id == reference_id,
            )
        )
        if int(awards.scalar_one()) >= MAX_CONFIRMATION_AWARDS_PER_REPORT:
            return None

    if await _points_today(db, user_id) >= DAILY_POINT_CAP:
        return None

    transaction = ReputationTransaction(
        user_id=user_id,
        actor_id=actor_id,
        points=award_points,
        action_type=action_type,
        reference_type=reference_type,
        reference_id=reference_id,
        status=ReputationStatus.APPROVED.value,
        note=note,
        approved_at=datetime.now(UTC),
        is_demo=is_demo,
    )
    db.add(transaction)
    await db.flush()

    await refresh_cached_balance(db, user)
    return transaction


async def refresh_cached_balance(db: AsyncSession, user: User) -> int:
    total = await db.execute(
        select(func.coalesce(func.sum(ReputationTransaction.points), 0)).where(
            ReputationTransaction.user_id == user.id,
            ReputationTransaction.status == ReputationStatus.APPROVED.value,
        )
    )
    user.reputation_points = int(total.scalar_one())
    user.level = level_for_points(user.reputation_points)
    await db.flush()
    return user.reputation_points


async def recalculate_all(db: AsyncSession) -> int:
    users = (await db.execute(select(User))).scalars().all()
    for user in users:
        await refresh_cached_balance(db, user)
    await db.commit()
    return len(users)


async def transactions_for(
    db: AsyncSession, user_id: UUID, *, page: int, page_size: int
) -> tuple[list[ReputationTransaction], int]:
    stmt = (
        select(ReputationTransaction)
        .where(ReputationTransaction.user_id == user_id)
        .order_by(ReputationTransaction.created_at.desc())
    )
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total
