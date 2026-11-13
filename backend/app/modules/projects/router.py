"""Project endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DbSession, OptionalUser, Pagination
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.projects import service
from app.modules.projects.models import OwnershipVerification, ProjectFeedback
from app.modules.projects.schemas import (
    FeedbackCreate,
    FeedbackOut,
    OwnershipVerificationOut,
    OwnershipVerifyRequest,
    ProjectCreate,
    ProjectListOut,
    ProjectOut,
    ProjectUpdate,
)

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=ProjectListOut)
async def list_projects(
    db: DbSession,
    viewer: OptionalUser,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=100),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    technology: str | None = Query(default=None, max_length=40),
    mode: str | None = Query(default=None),
    category: str | None = Query(default=None, max_length=60),
    creator: str | None = Query(default=None, max_length=40),
    sort: str = Query(default="recent", pattern="^(recent|oldest|popular)$"),
) -> ProjectListOut:
    projects, total = await service.list_projects(
        db,
        viewer=viewer,
        q=q,
        country_code=country,
        technology=technology,
        mode=mode,
        category=category,
        creator_username=creator,
        sort=sort,
        page=paging.page,
        page_size=paging.page_size,
    )
    return ProjectListOut(
        items=await service.serialise_projects(db, projects, viewer),
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.get("/projects/discover", response_model=ProjectListOut)
async def discover_projects(
    db: DbSession,
    viewer: OptionalUser,
    paging: Annotated[Pagination, Depends()],
    country: str | None = Query(default=None, min_length=2, max_length=2),
    technology: str | None = Query(default=None, max_length=40),
    mode: str | None = Query(default=None),
) -> ProjectListOut:
    projects, total = await service.list_projects(
        db,
        viewer=viewer,
        q=None,
        country_code=country,
        technology=technology,
        mode=mode,
        category=None,
        creator_username=None,
        sort="recent",
        page=paging.page,
        page_size=paging.page_size,
        exclude_interacted=True,
    )
    return ProjectListOut(
        items=await service.serialise_projects(db, projects, viewer),
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(payload: ProjectCreate, user: CurrentUser, db: DbSession) -> ProjectOut:
    project = await service.create_project(db, user, payload)
    return (await service.serialise_projects(db, [project], user))[0]


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def read_project(project_id: UUID, db: DbSession, viewer: OptionalUser) -> ProjectOut:
    project = await service.get_project(db, project_id)
    project.view_count += 1
    await db.commit()
    return (await service.serialise_projects(db, [project], viewer))[0]


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: UUID, payload: ProjectUpdate, user: CurrentUser, db: DbSession
) -> ProjectOut:
    project = await service.get_project(db, project_id)
    updated = await service.update_project(db, project, user, payload)
    return (await service.serialise_projects(db, [updated], user))[0]


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: UUID, user: CurrentUser, db: DbSession) -> None:
    project = await service.get_project(db, project_id)
    if project.creator_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the project owner can delete this project")
    await db.delete(project)
    await db.commit()


@router.post("/projects/{project_id}/like", status_code=204)
async def like_project(project_id: UUID, user: CurrentUser, db: DbSession) -> None:
    project = await service.get_project(db, project_id)
    await service.like_project(db, project, user)


@router.post("/projects/{project_id}/pass", status_code=204)
async def pass_project(project_id: UUID, user: CurrentUser, db: DbSession) -> None:
    project = await service.get_project(db, project_id)
    await service.pass_project(db, project, user)


@router.get("/projects/{project_id}/feedback", response_model=list[FeedbackOut])
async def list_feedback(project_id: UUID, db: DbSession) -> list[FeedbackOut]:
    project = await service.get_project(db, project_id)
    return [FeedbackOut.model_validate(item) for item in await service.list_feedback(db, project)]


@router.post("/projects/{project_id}/feedback", response_model=FeedbackOut, status_code=201)
async def create_feedback(
    project_id: UUID, payload: FeedbackCreate, user: CurrentUser, db: DbSession
) -> FeedbackOut:
    project = await service.get_project(db, project_id)
    feedback = await service.add_feedback(
        db, project, user, payload.concept_answer, payload.improvement_answer, payload.feature_answer
    )
    return FeedbackOut.model_validate(feedback)


@router.post("/projects/{project_id}/feedback/{feedback_id}/useful", response_model=FeedbackOut)
async def mark_feedback_useful(
    project_id: UUID, feedback_id: UUID, user: CurrentUser, db: DbSession
) -> FeedbackOut:
    feedback = await db.get(ProjectFeedback, feedback_id)
    if feedback is None or feedback.project_id != project_id:
        raise NotFoundError("Feedback not found")
    return FeedbackOut.model_validate(await service.mark_feedback_useful(db, feedback, user))


@router.post(
    "/projects/{project_id}/ownership-verification",
    response_model=OwnershipVerificationOut,
    status_code=201,
)
async def start_ownership_verification(
    project_id: UUID, payload: OwnershipVerifyRequest, user: CurrentUser, db: DbSession
) -> OwnershipVerificationOut:
    project = await service.get_project(db, project_id)
    record = await service.start_ownership_verification(db, project, user, payload.method)
    return OwnershipVerificationOut.model_validate(record)


@router.post(
    "/projects/{project_id}/ownership-verification/{verification_id}/confirm",
    response_model=OwnershipVerificationOut,
)
async def confirm_ownership_verification(
    project_id: UUID, verification_id: UUID, user: CurrentUser, db: DbSession
) -> OwnershipVerificationOut:
    record = await db.get(OwnershipVerification, verification_id)
    if record is None or record.project_id != project_id:
        raise NotFoundError("Verification request not found")
    updated = await service.confirm_ownership_verification(db, record, user, record.challenge_token)
    return OwnershipVerificationOut.model_validate(updated)
