"""Auditable reputation ledger and award rules."""

import logging
from datetime import UTC, datetime, time, timedelta
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
USEFUL_VOTE_CAP_PER_SOLUTION = 10

# Anti-cheat: an account must be a few days old before its votes and confirmations count.
ELIGIBLE_ACCOUNT_DAYS = 7
# Renderless decay when two accounts keep rewarding each other.
MUTUAL_DECAY_WINDOW_DAYS = 30
# Burst detection: one account cannot award points to dozens of people within minutes.
BURST_WINDOW_MINUTES = 10
BURST_MAX_AWARDS = 20


def _day_start() -> datetime:
    now = datetime.now(UTC)
    return datetime.combine(now.date(), time.min, tzinfo=UTC)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def is_frozen(user: User, now: datetime | None = None) -> bool:
    moment = now or datetime.now(UTC)
    if user.reputation_frozen:
        return True
    until = user.reputation_frozen_until
    return bool(until and _aware(until) > moment)


def is_eligible_account(user: User, now: datetime | None = None) -> bool:
    """Accounts need a linked history and a minimum age before their signals count."""
    moment = now or datetime.now(UTC)
    if not user.is_active or is_frozen(user, moment):
        return False
    return moment - _aware(user.created_at) >= timedelta(days=ELIGIBLE_ACCOUNT_DAYS)


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


async def _mutual_decay(db: AsyncSession, user_id: UUID, actor_id: UUID) -> int:
    """Return how many times this pair already rewarded each other in both directions."""
    since = datetime.now(UTC) - timedelta(days=MUTUAL_DECAY_WINDOW_DAYS)
    reciprocal = await db.execute(
        select(func.count(ReputationTransaction.id)).where(
            ReputationTransaction.user_id == actor_id,
            ReputationTransaction.actor_id == user_id,
            ReputationTransaction.created_at >= since,
        )
    )
    return int(reciprocal.scalar_one())


async def _actor_is_bursting(db: AsyncSession, actor_id: UUID) -> bool:
    since = datetime.now(UTC) - timedelta(minutes=BURST_WINDOW_MINUTES)
    count = await db.execute(
        select(func.count(ReputationTransaction.id)).where(
            ReputationTransaction.actor_id == actor_id,
            ReputationTransaction.created_at >= since,
        )
    )
    return int(count.scalar_one()) >= BURST_MAX_AWARDS


async def _solution_vote_points(db: AsyncSession, reference_id: str) -> int:
    solution_id = reference_id.split(":", 1)[0]
    total = await db.execute(
        select(func.coalesce(func.sum(ReputationTransaction.points), 0)).where(
            ReputationTransaction.action_type == ReputationAction.USEFUL_VOTE.value,
            ReputationTransaction.reference_id.like(f"{solution_id}:%"),
            ReputationTransaction.status == ReputationStatus.APPROVED.value,
        )
    )
    return int(total.scalar_one())


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
    if is_frozen(user) or not user.is_active:
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
        if await _solution_vote_points(db, reference_id) >= USEFUL_VOTE_CAP_PER_SOLUTION:
            logger.info("solution vote cap reached", extra={"reference_id": reference_id})
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

    if actor_id is not None:
        if await _actor_is_bursting(db, actor_id):
            logger.warning("blocked suspicious award burst", extra={"actor_id": str(actor_id)})
            return None
        mutual = await _mutual_decay(db, user_id, actor_id)
        if mutual:
            # Diminishing returns between two accounts that keep rewarding each other.
            award_points = max(1, round(award_points / (1 + mutual)))

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
