from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from pomodoro import storage
from pomodoro.api import schemas
from pomodoro.api.state import shared_state

router = APIRouter()


@router.get("", response_model=List[schemas.TemplateResponse])
async def list_templates():
    with shared_state.lock:
        return [schemas.TemplateResponse.model_validate(t) for t in shared_state.app.templates]


@router.post("", response_model=schemas.TemplateResponse, status_code=201)
async def create_template(body: schemas.TemplateCreate):
    with shared_state.lock:
        template = shared_state.app.add_template(body.title, body.estimate_pomodoros)
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.TemplateResponse.model_validate(template)
    await shared_state.broadcast_snapshot()
    return response


@router.delete("/{template_id}", status_code=204)
async def remove_template(template_id: int):
    with shared_state.lock:
        template = shared_state.app.find_template(template_id)
        if template is None:
            raise HTTPException(status_code=404, detail=f"No template with id {template_id}")
        shared_state.app.templates.remove(template)
        storage.save(shared_state.app, shared_state.data_path)
    await shared_state.broadcast_snapshot()
