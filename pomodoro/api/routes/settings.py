from __future__ import annotations

from fastapi import APIRouter

from pomodoro import storage
from pomodoro.api import schemas
from pomodoro.api.state import shared_state

router = APIRouter()


@router.get("", response_model=schemas.SettingsResponse)
async def get_settings():
    with shared_state.lock:
        return schemas.SettingsResponse.model_validate(shared_state.app.settings)


@router.patch("", response_model=schemas.SettingsResponse)
async def update_settings(body: schemas.SettingsUpdate):
    with shared_state.lock:
        settings = shared_state.app.settings
        updates = body.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(settings, field, value)
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.SettingsResponse.model_validate(settings)
    await shared_state.broadcast_snapshot()
    return response
