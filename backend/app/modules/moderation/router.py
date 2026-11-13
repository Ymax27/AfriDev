"""Moderation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, DbSession
from app.core.rate_limit import rate_limit
from app.modules.moderation import service
from app.modules.moderation.schemas import BlockCreate, BlockOut, ReportCreate, ReportOut

router = APIRouter(tags=["moderation"])


@router.post(
    "/reports",
    response_model=ReportOut,
    status_code=201,
    dependencies=[Depends(rate_limit(10, 3600, scope="report-create"))],
)
async def create_report(payload: ReportCreate, user: CurrentUser, db: DbSession) -> ReportOut:
    report = await service.create_report(
        db, user, payload.target_type, payload.target_id, payload.reason, payload.details
    )
    return ReportOut.model_validate(report)


@router.get("/blocks", response_model=list[BlockOut])
async def list_blocks(user: CurrentUser, db: DbSession) -> list[BlockOut]:
    return [
        BlockOut(
            id=block.id,
            blocked_id=blocked.id,
            blocked_username=blocked.username,
            reason=block.reason,
            created_at=block.created_at,
        )
        for block, blocked in await service.list_blocks(db, user)
    ]


@router.post("/blocks", response_model=BlockOut, status_code=201)
async def block_user(payload: BlockCreate, user: CurrentUser, db: DbSession) -> BlockOut:
    block = await service.block_user(db, user, payload.username, payload.reason)
    return BlockOut(
        id=block.id,
        blocked_id=block.blocked_id,
        blocked_username=payload.username,
        reason=block.reason,
        created_at=block.created_at,
    )


@router.delete("/blocks/{block_id}", status_code=204)
async def unblock_user(block_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await service.unblock_user(db, user, block_id)
