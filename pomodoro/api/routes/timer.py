from __future__ import annotations

from fastapi import APIRouter

from pomodoro import storage
from pomodoro.api import schemas
from pomodoro.api.state import shared_state
from pomodoro.models import estimate_finish_time

router = APIRouter()


@router.get("", response_model=schemas.TimerStatusResponse)
async def get_timer():
    with shared_state.lock:
        return schemas.build_timer_status(shared_state.app)


@router.post("/start", response_model=schemas.TimerStatusResponse)
async def start_timer():
    with shared_state.lock:
        shared_state.app.timer.start()
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.build_timer_status(shared_state.app)
    await shared_state.broadcast_snapshot()
    return response


@router.post("/pause", response_model=schemas.TimerStatusResponse)
async def pause_timer():
    with shared_state.lock:
        shared_state.app.timer.pause()
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.build_timer_status(shared_state.app)
    await shared_state.broadcast_snapshot()
    return response


@router.post("/reset", response_model=schemas.TimerStatusResponse)
async def reset_timer():
    with shared_state.lock:
        shared_state.app.timer.reset(shared_state.app.settings)
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.build_timer_status(shared_state.app)
    await shared_state.broadcast_snapshot()
    return response


@router.get("/eta", response_model=schemas.EtaResponse)
async def get_eta():
    with shared_state.lock:
        finish = estimate_finish_time(shared_state.app)
        pending = sum(
            t.remaining_pomodoros() for t in shared_state.app.tasks if not t.is_done()
        )
    return schemas.EtaResponse(
        finish_time=finish.isoformat(timespec="seconds") if finish else None,
        pending_pomodoros=pending,
    )
