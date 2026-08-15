from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from pomodoro import storage
from pomodoro.api import schemas
from pomodoro.api.state import shared_state
from pomodoro.models import TaskStatus

router = APIRouter()


@router.get("", response_model=List[schemas.TaskResponse])
async def list_tasks():
    with shared_state.lock:
        return [schemas.TaskResponse.model_validate(t) for t in shared_state.app.tasks]


@router.post("", response_model=schemas.TaskResponse, status_code=201)
async def create_task(body: schemas.TaskCreate):
    with shared_state.lock:
        task = shared_state.app.add_task(body.title, body.estimate_pomodoros)
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.TaskResponse.model_validate(task)
    await shared_state.broadcast_snapshot()
    return response


@router.post("/from-template/{template_id}", response_model=schemas.TaskResponse, status_code=201)
async def create_task_from_template(
    template_id: int,
    body: schemas.TaskFromTemplateCreate = schemas.TaskFromTemplateCreate(),
):
    with shared_state.lock:
        task = shared_state.app.add_task_from_template(template_id, body.estimate_pomodoros)
        if task is None:
            raise HTTPException(status_code=404, detail=f"No template with id {template_id}")
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.TaskResponse.model_validate(task)
    await shared_state.broadcast_snapshot()
    return response


@router.post("/{task_id}/select", response_model=schemas.TaskResponse)
async def select_task(task_id: int):
    with shared_state.lock:
        task = shared_state.app.find_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"No task with id {task_id}")
        shared_state.app.selected_task_id = task.id
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.TaskResponse.model_validate(task)
    await shared_state.broadcast_snapshot()
    return response


@router.post("/{task_id}/done", response_model=schemas.TaskResponse)
async def complete_task(task_id: int):
    with shared_state.lock:
        task = shared_state.app.find_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"No task with id {task_id}")
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now().isoformat(timespec="seconds")
        storage.save(shared_state.app, shared_state.data_path)
        response = schemas.TaskResponse.model_validate(task)
    await shared_state.broadcast_snapshot()
    return response


@router.delete("/{task_id}", status_code=204)
async def remove_task(task_id: int):
    with shared_state.lock:
        task = shared_state.app.find_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"No task with id {task_id}")
        shared_state.app.tasks.remove(task)
        if shared_state.app.selected_task_id == task_id:
            shared_state.app.selected_task_id = None
        storage.save(shared_state.app, shared_state.data_path)
    await shared_state.broadcast_snapshot()
