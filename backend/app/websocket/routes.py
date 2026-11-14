"""WebSocket endpoints with session and membership checks."""

import logging
import re
import time
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import read_session_token
from app.modules.countries.models import Country
from app.modules.messaging import service as messaging_service
from app.modules.messaging.schemas import MessageCreate
from app.modules.users.models import User
from app.websocket.manager import manager

logger = logging.getLogger("afridev.websocket")
router = APIRouter()

ROOM_MESSAGE_LIMIT = 10
ROOM_MESSAGE_WINDOW_SECONDS = 30
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _clean_room_message(payload: dict) -> str:
    return CONTROL_CHARS.sub("", str(payload.get("body", "")))[:2000]


def _throttled(timestamps: list[float]) -> bool:
    now = time.monotonic()
    timestamps[:] = [stamp for stamp in timestamps if now - stamp < ROOM_MESSAGE_WINDOW_SECONDS]
    if len(timestamps) >= ROOM_MESSAGE_LIMIT:
        return True
    timestamps.append(now)
    return False


async def _session_user(websocket: WebSocket) -> User | None:
    token = websocket.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    user_id = read_session_token(token)
    if not user_id:
        return None
    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user and user.is_active:
            return user
    return None


async def _reject(websocket: WebSocket, reason: str) -> None:
    await websocket.close(code=4401, reason=reason)


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_socket(websocket: WebSocket, conversation_id: UUID) -> None:
    user = await _session_user(websocket)
    if user is None:
        await _reject(websocket, "authentication required")
        return

    async with SessionLocal() as db:
        try:
            await messaging_service.ensure_member(db, conversation_id, user.id)
        except Exception:
            await _reject(websocket, "not a conversation member")
            return

    room = f"conversation:{conversation_id}"
    await manager.connect(room, websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") != "message.send":
                await websocket.send_json({"type": "error", "message": "unsupported event"})
                continue
            try:
                body = MessageCreate(body=str(payload.get("body", ""))).body
            except PydanticValidationError:
                await websocket.send_json({"type": "error", "message": "invalid message payload"})
                continue
            async with SessionLocal() as db:
                conversation = await messaging_service.ensure_member(db, conversation_id, user.id)
                sender = await db.get(User, user.id)
                message = await messaging_service.post_message(db, conversation, sender, body)
                await manager.broadcast(
                    room,
                    {
                        "type": "message.created",
                        "conversation_id": str(conversation_id),
                        "message": {
                            "id": str(message.id),
                            "conversation_id": str(conversation_id),
                            "sender_id": str(user.id),
                            "body": message.body,
                            "created_at": message.created_at.isoformat(),
                        },
                    },
                )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room, websocket)


@router.websocket("/ws/countries/{code}")
async def country_socket(websocket: WebSocket, code: str) -> None:
    user = await _session_user(websocket)
    if user is None:
        await _reject(websocket, "authentication required")
        return
    async with SessionLocal() as db:
        country = (
            await db.execute(select(Country).where(func.upper(Country.code) == code.upper()))
        ).scalar_one_or_none()
        if country is None:
            await _reject(websocket, "unknown country")
            return
        room_label = country.name
    room = f"country:{code.upper()}"
    await manager.connect(room, websocket)
    await manager.broadcast(
        room, {"type": "presence", "room": room_label, "members": manager.room_size(room)}
    )
    timestamps: list[float] = []
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif _throttled(timestamps):
                await websocket.send_json({"type": "error", "message": "slow down"})
            else:
                await manager.broadcast(
                    room,
                    {"type": "room.message", "author": user.username, "body": _clean_room_message(payload)},
                )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room, websocket)


@router.websocket("/ws/missions/{mission_id}")
async def mission_socket(websocket: WebSocket, mission_id: UUID) -> None:
    user = await _session_user(websocket)
    if user is None:
        await _reject(websocket, "authentication required")
        return
    room = f"mission:{mission_id}"
    await manager.connect(room, websocket)
    timestamps: list[float] = []
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif _throttled(timestamps):
                await websocket.send_json({"type": "error", "message": "slow down"})
            else:
                await manager.broadcast(
                    room,
                    {"type": "room.message", "author": user.username, "body": _clean_room_message(payload)},
                )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room, websocket)
