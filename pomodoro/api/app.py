"""FastAPI app factory."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pomodoro.api import schemas, ws
from pomodoro.api.routes import reports, settings, tasks, templates, timer
from pomodoro.api.state import shared_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    shared_state.start(loop=loop, broadcast=ws.manager.broadcast)
    yield
    shared_state.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="Pomodoro Timer API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(timer.router, prefix="/api/timer", tags=["timer"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

    @app.get("/api/state", response_model=schemas.StateSnapshot)
    async def get_state():
        with shared_state.lock:
            return schemas.build_snapshot(shared_state.app)

    app.websocket("/api/ws")(ws.websocket_endpoint)

    return app


app = create_app()
