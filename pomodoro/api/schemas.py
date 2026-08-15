"""Pydantic request/response models. Converts to/from the plain dataclasses
in pomodoro.models — those stay untouched and I/O-free, shared with the CLI."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from pomodoro.models import AppState, Phase, TaskStatus


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    estimate_pomodoros: int
    completed_pomodoros: int
    status: TaskStatus
    created_at: str
    completed_at: Optional[str] = None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    estimate_pomodoros: int = Field(default=1, ge=1)


class TaskFromTemplateCreate(BaseModel):
    estimate_pomodoros: Optional[int] = Field(default=None, ge=1)


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    estimate_pomodoros: int


class TemplateCreate(BaseModel):
    title: str = Field(min_length=1)
    estimate_pomodoros: int = Field(default=1, ge=1)


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    focus_minutes: int
    break_minutes: int
    alarm_sound: str
    background_sound: str


class SettingsUpdate(BaseModel):
    focus_minutes: Optional[int] = Field(default=None, gt=0)
    break_minutes: Optional[int] = Field(default=None, gt=0)
    alarm_sound: Optional[Literal["bell", "silent"]] = None
    background_sound: Optional[str] = None


class TimerStatusResponse(BaseModel):
    phase: Phase
    remaining: int
    running: bool
    completed_sessions: int
    selected_task_id: Optional[int] = None
    selected_task_title: Optional[str] = None


class ReportRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label: str
    sessions: int
    minutes: int


class EtaResponse(BaseModel):
    finish_time: Optional[str] = None
    pending_pomodoros: int


class StateSnapshot(BaseModel):
    tasks: List[TaskResponse]
    templates: List[TemplateResponse]
    settings: SettingsResponse
    timer: TimerStatusResponse
    selected_task_id: Optional[int] = None
    session_count: int


def build_timer_status(app: AppState) -> TimerStatusResponse:
    task = app.selected_task()
    return TimerStatusResponse(
        phase=app.timer.phase,
        remaining=app.timer.remaining,
        running=app.timer.running,
        completed_sessions=app.timer.completed_sessions,
        selected_task_id=task.id if task else None,
        selected_task_title=task.title if task else None,
    )


def build_snapshot(app: AppState) -> StateSnapshot:
    return StateSnapshot(
        tasks=[TaskResponse.model_validate(t) for t in app.tasks],
        templates=[TemplateResponse.model_validate(t) for t in app.templates],
        settings=SettingsResponse.model_validate(app.settings),
        timer=build_timer_status(app),
        selected_task_id=app.selected_task_id,
        session_count=len(app.session_log),
    )
