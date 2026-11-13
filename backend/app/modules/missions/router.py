"""Mission endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.core.exceptions import ForbiddenError
from app.modules.missions import service
from app.modules.missions.schemas import (
    MissionCreate,
    MissionListOut,
    MissionOut,
    SubmissionCreate,
    SubmissionOut,
    SubmissionReview,
)

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=MissionListOut)
async def list_missions(
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    skill: str | None = Query(default=None, max_length=40),
) -> MissionListOut:
    missions, total = await service.list_missions(
        db, q=q, status=status, country_code=country, skill=skill, page=paging.page, page_size=paging.page_size
    )
    counts = await service.submissions_count(db, [mission.id for mission in missions])
    items = [
        MissionOut.model_validate(mission).model_copy(update={"submissions_count": counts.get(mission.id, 0)})
        for mission in missions
    ]
    return MissionListOut(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.post("", response_model=MissionOut, status_code=201)
async def create_mission(payload: MissionCreate, user: CurrentUser, db: DbSession) -> MissionOut:
    if not (user.is_admin or any(role.role in {"sponsor", "api_provider"} for role in user.roles)):
        raise ForbiddenError("Only sponsors, API providers or admins can publish missions")
    return MissionOut.model_validate(await service.create_mission(db, user, payload))


@router.get("/{mission_id}", response_model=MissionOut)
async def read_mission(mission_id: UUID, db: DbSession) -> MissionOut:
    mission = await service.get_mission(db, mission_id)
    counts = await service.submissions_count(db, [mission.id])
    return MissionOut.model_validate(mission).model_copy(update={"submissions_count": counts.get(mission.id, 0)})


@router.post("/{mission_id}/submissions", response_model=SubmissionOut, status_code=201)
async def submit_to_mission(
    mission_id: UUID, payload: SubmissionCreate, user: CurrentUser, db: DbSession
) -> SubmissionOut:
    mission = await service.get_mission(db, mission_id)
    submission = await service.create_submission(db, mission, user, payload.summary, payload.solution_url)
    return SubmissionOut.model_validate(submission)


@router.get("/{mission_id}/submissions", response_model=list[SubmissionOut])
async def list_mission_submissions(mission_id: UUID, user: CurrentUser, db: DbSession) -> list[SubmissionOut]:
    mission = await service.get_mission(db, mission_id)
    if mission.sponsor_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the mission sponsor can list submissions")
    return [SubmissionOut.model_validate(item) for item in await service.list_submissions(db, mission_id)]


@router.post("/submissions/{submission_id}/review", response_model=SubmissionOut)
async def review_submission(
    submission_id: UUID, payload: SubmissionReview, user: CurrentUser, db: DbSession
) -> SubmissionOut:
    submission = await service.get_submission(db, submission_id)
    updated = await service.review_submission(db, submission, user, payload.approve, payload.review_note)
    return SubmissionOut.model_validate(updated)
