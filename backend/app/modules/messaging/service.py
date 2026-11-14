"""Private and contextual conversations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.messaging.models import Conversation, ConversationMember, Message
from app.modules.moderation.service import blocked_between
from app.modules.users.models import User


async def list_conversations(
    db: AsyncSession, user_id: UUID, *, page: int, page_size: int
) -> tuple[list[Conversation], int]:
    stmt = (
        select(Conversation)
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .where(ConversationMember.user_id == user_id)
        .order_by(func.coalesce(Conversation.last_message_at, Conversation.created_at).desc())
    )
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def get_conversation(db: AsyncSession, conversation_id: UUID) -> Conversation:
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise NotFoundError("Conversation not found")
    return conversation


async def ensure_member(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> Conversation:
    conversation = await get_conversation(db, conversation_id)
    member = next((item for item in conversation.members if item.user_id == user_id), None)
    if member is None:
        raise ForbiddenError("You are not a member of this conversation")
    return conversation


async def list_messages(
    db: AsyncSession, conversation_id: UUID, *, page: int, page_size: int
) -> tuple[list[Message], int]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def post_message(
    db: AsyncSession, conversation: Conversation, sender: User, body: str
) -> Message:
    for member in conversation.members:
        if member.user_id != sender.id and await blocked_between(db, sender.id, member.user_id):
            raise ForbiddenError("Messaging is blocked between these accounts")
    message = Message(conversation_id=conversation.id, sender_id=sender.id, body=body.strip())
    db.add(message)
    conversation.last_message_at = datetime.now(UTC)
    member = next((item for item in conversation.members if item.user_id == sender.id), None)
    if member:
        member.last_read_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(message)
    return message
