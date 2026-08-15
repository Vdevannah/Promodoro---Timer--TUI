"""WebSocket connection manager + endpoint."""

from __future__ import annotations

from typing import List

from fastapi import WebSocket, WebSocketDisconnect

from pomodoro.api import schemas
from pomodoro.api.state import shared_state


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        stale = []
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    with shared_state.lock:
        snapshot = schemas.build_snapshot(shared_state.app)
    await websocket.send_json({"type": "state", "state": snapshot.model_dump()})
    try:
        while True:
            await websocket.receive_text()  # keepalive; client sends nothing meaningful
    except WebSocketDisconnect:
        manager.disconnect(websocket)
