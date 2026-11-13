"""User and profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.modules.users import service
from app.modules.users.schemas import ProfileUpdate, UserListResponse, UserOut, UserProfileOut

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=80),
    country: str | None = Query(default=None, min_length=2, max_length=2),
) -> UserListResponse:
    users, total = await service.list_users(
        db, query=q, country_code=country, page=paging.page, page_size=paging.page_size
    )
    return UserListResponse(
        items=[UserOut.model_validate(user) for user in users],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.get("/users/me", response_model=UserProfileOut)
async def read_my_profile(user: CurrentUser, db: DbSession) -> UserProfileOut:
    return await service.build_profile(db, user)


@router.patch("/users/me", response_model=UserProfileOut)
async def update_my_profile(payload: ProfileUpdate, user: CurrentUser, db: DbSession) -> UserProfileOut:
    updated = await service.update_profile(db, user, payload)
    return await service.build_profile(db, updated)


@router.get("/users/{username}", response_model=UserProfileOut)
async def read_profile(username: str, db: DbSession) -> UserProfileOut:
    target = await service.get_by_username(db, username)
    return await service.build_profile(db, target)
