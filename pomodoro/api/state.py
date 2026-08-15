"""Shared AppState singleton + the ticker thread that drives it.

Mirrors pomodoro.cli's ticker() but broadcasts over WebSocket instead of
printing to stdout, bridging from a plain threading.Thread into the FastAPI
process's asyncio event loop via asyncio.run_coroutine_threadsafe.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Awaitable, Callable, Optional

from pomodoro import storage
from pomodoro.models import AppState, Phase, complete_focus_session

Broadcast = Callable[[dict], Awaitable[None]]


class SharedState:
    def __init__(self, data_path: Path = storage.DEFAULT_DATA_PATH) -> None:
        self.data_path = data_path
        self.app: AppState = storage.load(data_path)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._broadcast: Optional[Broadcast] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, loop: asyncio.AbstractEventLoop, broadcast: Broadcast) -> None:
        self.loop = loop
        self._broadcast = broadcast
        self.stop_event.clear()
        self._thread = threading.Thread(target=self._run_ticker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    async def broadcast_snapshot(self) -> None:
        """Called from REST route handlers, already running on the loop."""
        if self._broadcast is None:
            return
        from pomodoro.api import schemas

        with self.lock:
            snapshot = schemas.build_snapshot(self.app)
        await self._broadcast({"type": "state", "state": snapshot.model_dump()})

    def _run_ticker(self) -> None:
        """Runs on a plain threading.Thread, not the asyncio loop."""
        from pomodoro.api import schemas

        while not self.stop_event.is_set():
            self.stop_event.wait(1)
            if self.stop_event.is_set():
                break

            finished: Optional[Phase] = None
            should_broadcast = False
            snapshot = None
            with self.lock:
                finished = self.app.timer.tick(self.app.settings)
                if finished is not None:
                    if finished == Phase.FOCUS:
                        complete_focus_session(self.app)
                    storage.save(self.app, self.data_path)
                should_broadcast = self.app.timer.running or finished is not None
                if should_broadcast:
                    snapshot = schemas.build_snapshot(self.app)

            if should_broadcast and self.loop is not None and self._broadcast is not None:
                message = {
                    "type": "phase_change" if finished is not None else "tick",
                    "state": snapshot.model_dump(),
                }
                if finished is not None:
                    message["finished_phase"] = finished.value
                asyncio.run_coroutine_threadsafe(self._broadcast(message), self.loop)


shared_state = SharedState()
