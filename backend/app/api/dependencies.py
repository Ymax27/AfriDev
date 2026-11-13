"""Authentication, authorization and pagination dependencies."""

from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import read_session_token
from app.modules.users.models import User


async def get_current_user_optional(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    user_id = read_session_token(token)
    if not user_id:
        return None
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        return None
    request.state.user_id = str(user.id)
    return user


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if user is None:
        raise UnauthorizedError("Authentication required")
    return user


async def get_optional_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User | None:
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise ForbiddenError("Administrator privileges required")
    return user


class Pagination:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> None:
        self.page = page
        self.page_size = page_size


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
AdminUser = Annotated[User, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
Paging = Annotated[Pagination, Depends()]
