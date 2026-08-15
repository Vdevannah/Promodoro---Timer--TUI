"""JSON persistence for AppState — the only place that touches the disk."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from pomodoro.models import (
    AppState,
    Phase,
    Settings,
    SessionLogEntry,
    Task,
    TaskStatus,
    TaskTemplate,
    TimerState,
)

SCHEMA_VERSION = 1
DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "pomodoro_data.json"


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "estimate_pomodoros": task.estimate_pomodoros,
        "completed_pomodoros": task.completed_pomodoros,
        "status": task.status.value,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
    }


def _task_from_dict(data: dict) -> Task:
    return Task(
        id=data["id"],
        title=data["title"],
        estimate_pomodoros=data["estimate_pomodoros"],
        completed_pomodoros=data.get("completed_pomodoros", 0),
        status=TaskStatus(data.get("status", "pending")),
        created_at=data.get("created_at", ""),
        completed_at=data.get("completed_at"),
    )


def _template_to_dict(template: TaskTemplate) -> dict:
    return {
        "id": template.id,
        "title": template.title,
        "estimate_pomodoros": template.estimate_pomodoros,
    }


def _template_from_dict(data: dict) -> TaskTemplate:
    return TaskTemplate(
        id=data["id"],
        title=data["title"],
        estimate_pomodoros=data["estimate_pomodoros"],
    )


def _session_entry_to_dict(entry: SessionLogEntry) -> dict:
    return {
        "timestamp": entry.timestamp,
        "task_id": entry.task_id,
        "task_title": entry.task_title,
        "duration_minutes": entry.duration_minutes,
    }


def _session_entry_from_dict(data: dict) -> SessionLogEntry:
    return SessionLogEntry(
        timestamp=data["timestamp"],
        task_id=data.get("task_id"),
        task_title=data.get("task_title", ""),
        duration_minutes=data["duration_minutes"],
    )


def _settings_to_dict(settings: Settings) -> dict:
    return {
        "focus_minutes": settings.focus_minutes,
        "break_minutes": settings.break_minutes,
        "alarm_sound": settings.alarm_sound,
        "background_sound": settings.background_sound,
    }


def _settings_from_dict(data: dict) -> Settings:
    return Settings(
        focus_minutes=data.get("focus_minutes", 25),
        break_minutes=data.get("break_minutes", 5),
        alarm_sound=data.get("alarm_sound", "bell"),
        background_sound=data.get("background_sound", "none"),
    )


def _timer_to_dict(timer: TimerState) -> dict:
    return {
        "phase": timer.phase.value,
        "remaining": timer.remaining,
        "running": timer.running,
        "completed_sessions": timer.completed_sessions,
    }


def _timer_from_dict(data: dict) -> TimerState:
    return TimerState(
        phase=Phase(data.get("phase", "FOCUS")),
        remaining=data.get("remaining", 1500),
        running=data.get("running", False),
        completed_sessions=data.get("completed_sessions", 0),
    )


def _app_to_dict(app: AppState) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "settings": _settings_to_dict(app.settings),
        "timer": _timer_to_dict(app.timer),
        "selected_task_id": app.selected_task_id,
        "next_task_id": app.next_task_id,
        "next_template_id": app.next_template_id,
        "tasks": [_task_to_dict(t) for t in app.tasks],
        "templates": [_template_to_dict(t) for t in app.templates],
        "session_log": [_session_entry_to_dict(e) for e in app.session_log],
    }


def _app_from_dict(data: dict) -> AppState:
    return AppState(
        tasks=[_task_from_dict(t) for t in data.get("tasks", [])],
        templates=[_template_from_dict(t) for t in data.get("templates", [])],
        settings=_settings_from_dict(data.get("settings", {})),
        session_log=[_session_entry_from_dict(e) for e in data.get("session_log", [])],
        timer=_timer_from_dict(data.get("timer", {})),
        selected_task_id=data.get("selected_task_id"),
        next_task_id=data.get("next_task_id", 1),
        next_template_id=data.get("next_template_id", 1),
    )


def load(path: Path = DEFAULT_DATA_PATH) -> AppState:
    if not path.exists():
        return AppState()

    try:
        with path.open("r") as f:
            data = json.load(f)
        return _app_from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError, OSError) as exc:
        print(f"Warning: could not read {path} ({exc}); starting with fresh data.")
        return AppState()


def save(app: AppState, path: Path = DEFAULT_DATA_PATH) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w") as f:
        json.dump(_app_to_dict(app), f, indent=2)
    os.replace(tmp_path, path)
