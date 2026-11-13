"""Contribution request endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.core.rate_limit import rate_limit
from app.modules.contributions import service
from app.modules.contributions.schemas import ContributionCreate, ContributionListOut, ContributionOut
from app.modules.projects.service import get_project

router = APIRouter(tags=["contributions"])


class RejectPayload(BaseModel):
    reason: str | None = None


@router.post(
    "/projects/{project_id}/contributions",
    response_model=ContributionOut,
    status_code=201,
    dependencies=[Depends(rate_limit(10, 3600, scope="contribution-create"))],
)
async def create_contribution(
    project_id: UUID, payload: ContributionCreate, user: CurrentUser, db: DbSession
) -> ContributionOut:
    project = await get_project(db, project_id)
    request = await service.create_request(db, project, user, payload)
    return ContributionOut.model_validate(request)


@router.get("/contributions/me", response_model=ContributionListOut)
async def my_contributions(
    db: DbSession, user: CurrentUser, paging: Annotated[Pagination, Depends()]
) -> ContributionListOut:
    items, total = await service.list_for_requester(
        db, user.id, page=paging.page, page_size=paging.page_size
    )
    return ContributionListOut(
        items=[ContributionOut.model_validate(item) for item in items],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.get("/projects/{project_id}/contributions", response_model=ContributionListOut)
async def project_contributions(
    project_id: UUID,
    db: DbSession,
    user: CurrentUser,
    paging: Annotated[Pagination, Depends()],
    status: str | None = Query(default=None),
) -> ContributionListOut:
    project = await get_project(db, project_id)
    from app.core.exceptions import ForbiddenError

    if project.creator_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the project maintainer can list contribution requests")
    items, total = await service.list_for_project(
        db, project_id, status=status, page=paging.page, page_size=paging.page_size
    )
    return ContributionListOut(
        items=[ContributionOut.model_validate(item) for item in items],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.post("/contributions/{request_id}/accept", response_model=ContributionOut)
async def accept_contribution(request_id: UUID, user: CurrentUser, db: DbSession) -> ContributionOut:
    request = await service.get_request(db, request_id)
    return ContributionOut.model_validate(await service.accept_request(db, request, user))


@router.post("/contributions/{request_id}/reject", response_model=ContributionOut)
async def reject_contribution(
    request_id: UUID, payload: RejectPayload, user: CurrentUser, db: DbSession
) -> ContributionOut:
    request = await service.get_request(db, request_id)
    return ContributionOut.model_validate(await service.reject_request(db, request, user, payload.reason))


@router.post("/contributions/{request_id}/merged", response_model=ContributionOut)
async def mark_contribution_merged(
    request_id: UUID, user: CurrentUser, db: DbSession
) -> ContributionOut:
    request = await service.get_request(db, request_id)
    return ContributionOut.model_validate(await service.mark_merged(db, request, user))
