"""Live event broadcast for the dashboard.

The orchestrator (Day 3) will push agent messages, status changes, and task
updates into the broadcaster; connected clients receive them in real time.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class Broadcaster:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)

    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._connections:
            return
        message = json.dumps({"type": event_type, "data": payload})
        async with self._lock:
            stale: list[WebSocket] = []
            for ws in self._connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    stale.append(ws)
            for ws in stale:
                self._connections.discard(ws)


broadcaster = Broadcaster()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        # Greet the client so it can confirm the connection is live.
        await ws.send_text(json.dumps({"type": "connected", "data": {"ok": True}}))
        while True:
            # We don't expect client messages yet; just keep the socket alive.
            await ws.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect(ws)
    except Exception:
        await broadcaster.disconnect(ws)
