"""Messaging endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.core.rate_limit import rate_limit
from app.modules.messaging import service
from app.modules.messaging.schemas import (
    ConversationListOut,
    ConversationOut,
    MessageCreate,
    MessageOut,
)

router = APIRouter(tags=["messaging"])


@router.get("/conversations", response_model=ConversationListOut)
async def list_conversations(
    db: DbSession, user: CurrentUser, paging: Annotated[Pagination, Depends()]
) -> ConversationListOut:
    items, total = await service.list_conversations(
        db, user.id, page=paging.page, page_size=paging.page_size
    )
    return ConversationListOut(
        items=[ConversationOut.model_validate(item) for item in items],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: UUID, db: DbSession, user: CurrentUser
) -> list[MessageOut]:
    await service.ensure_member(db, conversation_id, user.id)
    messages, _ = await service.list_messages(db, conversation_id, page=1, page_size=100)
    return [MessageOut.model_validate(message) for message in messages]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=201,
    dependencies=[Depends(rate_limit(30, 60, scope="message-send"))],
)
async def send_message(
    conversation_id: UUID, payload: MessageCreate, db: DbSession, user: CurrentUser
) -> MessageOut:
    conversation = await service.ensure_member(db, conversation_id, user.id)
    message = await service.post_message(db, conversation, user, payload.body)
    from app.websocket.manager import manager

    await manager.broadcast(
        str(conversation_id),
        {
            "type": "message.created",
            "conversation_id": str(conversation_id),
            "message": MessageOut.model_validate(message).model_dump(mode="json"),
        },
    )
    return MessageOut.model_validate(message)
