"""In-process WebSocket room manager."""

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("afridev.websocket")


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, room: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms[room].add(websocket)
        logger.info("websocket joined room", extra={"path": room})

    async def disconnect(self, room: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._rooms[room].discard(websocket)
            if not self._rooms[room]:
                self._rooms.pop(room, None)

    async def broadcast(self, room: str, payload: dict[str, Any]) -> None:
        for connection in list(self._rooms.get(room, set())):
            try:
                await connection.send_json(payload)
            except Exception:  # pragma: no cover - client disconnect races
                await self.disconnect(room, connection)

    def room_size(self, room: str) -> int:
        return len(self._rooms.get(room, set()))


manager = ConnectionManager()
