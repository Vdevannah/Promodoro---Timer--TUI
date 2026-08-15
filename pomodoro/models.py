"""
Pomodoro Timer TUI — domain model
----------------------------------
Mental model: a state machine (TimerState) plus the task/settings/report
data it operates on. No I/O lives here — see storage.py and reports.py.

State:
    phase              FOCUS or BREAK
    remaining           seconds left in the current phase
    running             is the countdown currently ticking?
    completed_sessions  number of focus blocks finished

Event sources:
    user events: start, pause, reset, quit, task/template/settings commands
    time events: one tick per second

Transition rules (memorize these):
    - decrement only when running
    - on zero during FOCUS  -> completed_sessions += 1, switch to BREAK
    - on zero during BREAK  -> switch to FOCUS
    - reset restores the current phase's full duration and pauses
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional


class Phase(str, Enum):
    FOCUS = "FOCUS"
    BREAK = "BREAK"


class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"


@dataclass
class Task:
    id: int
    title: str
    estimate_pomodoros: int
    completed_pomodoros: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    completed_at: Optional[str] = None

    def remaining_pomodoros(self) -> int:
        return max(self.estimate_pomodoros - self.completed_pomodoros, 0)

    def is_done(self) -> bool:
        return self.status == TaskStatus.DONE


@dataclass
class TaskTemplate:
    id: int
    title: str
    estimate_pomodoros: int


@dataclass
class Settings:
    focus_minutes: int = 25
    break_minutes: int = 5
    alarm_sound: str = "bell"          # "bell" | "silent"
    background_sound: str = "none"     # stored only, never played

    def focus_seconds(self) -> int:
        return self.focus_minutes * 60

    def break_seconds(self) -> int:
        return self.break_minutes * 60


@dataclass
class SessionLogEntry:
    timestamp: str
    task_id: Optional[int]
    task_title: str
    duration_minutes: int


@dataclass
class TimerState:
    phase: Phase = Phase.FOCUS
    remaining: int = 1500
    running: bool = False
    completed_sessions: int = 0

    def phase_duration(self, settings: Settings) -> int:
        return settings.focus_seconds() if self.phase == Phase.FOCUS else settings.break_seconds()

    def tick(self, settings: Settings) -> Optional[Phase]:
        """Called once per second by the ticker thread.

        Returns the Phase that just finished (FOCUS or BREAK), or None if
        nothing completed on this tick.
        """
        if not self.running:
            return None

        self.remaining -= 1

        if self.remaining <= 0:
            finished = self.phase
            if self.phase == Phase.FOCUS:
                self.completed_sessions += 1
                self.phase = Phase.BREAK
            else:
                self.phase = Phase.FOCUS
            self.remaining = self.phase_duration(settings)
            return finished

        return None

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self, settings: Settings) -> None:
        self.remaining = self.phase_duration(settings)
        self.running = False

    def status_line(self) -> str:
        mins, secs = divmod(self.remaining, 60)
        state = "RUNNING" if self.running else "PAUSED"
        return (
            f"[{self.phase.name:5}] {mins:02d}:{secs:02d} "
            f"({state}) | sessions completed: {self.completed_sessions}"
        )


@dataclass
class AppState:
    tasks: List[Task] = field(default_factory=list)
    templates: List[TaskTemplate] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)
    session_log: List[SessionLogEntry] = field(default_factory=list)
    timer: TimerState = field(default_factory=TimerState)
    selected_task_id: Optional[int] = None
    next_task_id: int = 1
    next_template_id: int = 1

    def selected_task(self) -> Optional[Task]:
        return self.find_task(self.selected_task_id) if self.selected_task_id is not None else None

    def find_task(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def find_template(self, template_id: int) -> Optional[TaskTemplate]:
        return next((t for t in self.templates if t.id == template_id), None)

    def add_task(self, title: str, estimate: int) -> Task:
        task = Task(id=self.next_task_id, title=title, estimate_pomodoros=estimate)
        self.tasks.append(task)
        self.next_task_id += 1
        return task

    def add_template(self, title: str, estimate: int) -> TaskTemplate:
        template = TaskTemplate(id=self.next_template_id, title=title, estimate_pomodoros=estimate)
        self.templates.append(template)
        self.next_template_id += 1
        return template

    def add_task_from_template(self, template_id: int, estimate_override: Optional[int] = None) -> Optional[Task]:
        template = self.find_template(template_id)
        if template is None:
            return None
        estimate = estimate_override if estimate_override is not None else template.estimate_pomodoros
        return self.add_task(template.title, estimate)


def complete_focus_session(app: AppState) -> SessionLogEntry:
    """Called exactly once when tick() reports a finished FOCUS phase."""
    task = app.selected_task()
    entry = SessionLogEntry(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        task_id=task.id if task else None,
        task_title=task.title if task else "(no task selected)",
        duration_minutes=app.settings.focus_minutes,
    )
    app.session_log.append(entry)

    if task is not None:
        task.completed_pomodoros += 1
        if not task.is_done() and task.completed_pomodoros >= task.estimate_pomodoros:
            task.status = TaskStatus.DONE
            task.completed_at = entry.timestamp

    return entry


def estimate_finish_time(app: AppState, now: Optional[datetime] = None) -> Optional[datetime]:
    """Estimate the clock time today's remaining tasks will finish at.

    Simulates forward through the alternating focus/break blocks needed to
    burn down every non-done task's remaining pomodoro estimate, starting
    from wherever the timer currently is (running, paused, or fresh).
    """
    now = now or datetime.now()
    pending = sum(t.remaining_pomodoros() for t in app.tasks if not t.is_done())
    if pending <= 0:
        return None

    seconds = app.timer.remaining
    phase = app.timer.phase
    if phase == Phase.FOCUS:
        pending -= 1
        phase = Phase.BREAK
    else:
        phase = Phase.FOCUS

    while pending > 0:
        if phase == Phase.BREAK:
            seconds += app.settings.break_seconds()
            phase = Phase.FOCUS
        else:
            seconds += app.settings.focus_seconds()
            pending -= 1
            phase = Phase.BREAK

    return now + timedelta(seconds=seconds)
