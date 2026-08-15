"""Command dispatch loop, ticker thread, and process entry point."""

from __future__ import annotations

import shlex
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pomodoro import reports, storage
from pomodoro.models import (
    AppState,
    Phase,
    TaskStatus,
    complete_focus_session,
    estimate_finish_time,
)


def ticker(app: AppState, lock: threading.Lock, stop_event: threading.Event, data_path: Path) -> None:
    """Background thread: advance the state once per second."""
    while not stop_event.is_set():
        stop_event.wait(1)
        if stop_event.is_set():
            break

        finished: Optional[Phase] = None
        next_phase: Optional[Phase] = None
        with lock:
            finished = app.timer.tick(app.settings)
            if finished is not None:
                if finished == Phase.FOCUS:
                    complete_focus_session(app)
                next_phase = app.timer.phase
                storage.save(app, data_path)

        if finished is not None:
            _announce_phase_change(finished, next_phase, app.settings)


def _announce_phase_change(finished: Phase, next_phase: Phase, settings) -> None:
    bell = "\a" if settings.alarm_sound == "bell" else ""
    if finished == Phase.FOCUS:
        msg = f"Focus session complete! Time for a {settings.break_minutes}-minute break."
    else:
        msg = f"Break's over! Back to focus for {settings.focus_minutes} minutes."
    print(f"\n{bell}{msg}")
    print("> ", end="", flush=True)


def print_help() -> None:
    print("Timer:     start | pause | reset | status | quit")
    print("Tasks:     task add <title> [estimate] | task list | task select <id>")
    print("           task done <id> | task remove <id> | task from-template <id> [estimate]")
    print("Templates: template add <title> [estimate] | template list | template remove <id>")
    print("Planning:  eta | report [day|week|month]")
    print("Settings:  settings show | settings set <focus|break|alarm|background> <value>")
    print("Other:     help")


def handle_task(args: List[str], app: AppState) -> None:
    if not args:
        print("Usage: task <add|list|select|done|remove|from-template> ...")
        return

    sub, rest = args[0], args[1:]

    if sub == "add":
        if not rest:
            print("Usage: task add <title> [estimate=1]")
            return
        estimate = 1
        title_parts = rest
        if len(rest) > 1 and rest[-1].isdigit():
            estimate = int(rest[-1])
            title_parts = rest[:-1]
        title = " ".join(title_parts)
        task = app.add_task(title, estimate)
        print(f"Added task #{task.id}: {task.title} (0/{task.estimate_pomodoros} pomodoros)")

    elif sub == "list":
        if not app.tasks:
            print("No tasks yet. Add one with: task add <title> [estimate]")
            return
        for task in app.tasks:
            marker = "*" if task.id == app.selected_task_id else " "
            done_box = "[x]" if task.is_done() else "[ ]"
            print(f"{marker}{done_box} #{task.id} {task.title} "
                  f"({task.completed_pomodoros}/{task.estimate_pomodoros} pomodoros)")

    elif sub == "select":
        if not rest or not rest[0].isdigit():
            print("Usage: task select <id>")
            return
        task = app.find_task(int(rest[0]))
        if task is None:
            print(f"No task with id {rest[0]}.")
            return
        app.selected_task_id = task.id
        print(f"Selected task #{task.id}: {task.title}")

    elif sub == "done":
        if not rest or not rest[0].isdigit():
            print("Usage: task done <id>")
            return
        task = app.find_task(int(rest[0]))
        if task is None:
            print(f"No task with id {rest[0]}.")
            return
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now().isoformat(timespec="seconds")
        print(f"Marked task #{task.id} done.")

    elif sub == "remove":
        if not rest or not rest[0].isdigit():
            print("Usage: task remove <id>")
            return
        task_id = int(rest[0])
        task = app.find_task(task_id)
        if task is None:
            print(f"No task with id {task_id}.")
            return
        app.tasks.remove(task)
        if app.selected_task_id == task_id:
            app.selected_task_id = None
        print(f"Removed task #{task_id}.")

    elif sub == "from-template":
        if not rest or not rest[0].isdigit():
            print("Usage: task from-template <template_id> [estimate]")
            return
        template_id = int(rest[0])
        estimate_override = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else None
        task = app.add_task_from_template(template_id, estimate_override)
        if task is None:
            print(f"No template with id {template_id}.")
            return
        print(f"Added task #{task.id} from template: {task.title} (0/{task.estimate_pomodoros} pomodoros)")

    else:
        print(f"Unknown task command: {sub!r}")


def handle_template(args: List[str], app: AppState) -> None:
    if not args:
        print("Usage: template <add|list|remove> ...")
        return

    sub, rest = args[0], args[1:]

    if sub == "add":
        if not rest:
            print("Usage: template add <title> [estimate=1]")
            return
        estimate = 1
        title_parts = rest
        if len(rest) > 1 and rest[-1].isdigit():
            estimate = int(rest[-1])
            title_parts = rest[:-1]
        title = " ".join(title_parts)
        template = app.add_template(title, estimate)
        print(f"Saved template #{template.id}: {template.title} ({template.estimate_pomodoros} pomodoros)")

    elif sub == "list":
        if not app.templates:
            print("No templates yet. Add one with: template add <title> [estimate]")
            return
        for template in app.templates:
            print(f"#{template.id} {template.title} ({template.estimate_pomodoros} pomodoros)")

    elif sub == "remove":
        if not rest or not rest[0].isdigit():
            print("Usage: template remove <id>")
            return
        template_id = int(rest[0])
        template = app.find_template(template_id)
        if template is None:
            print(f"No template with id {template_id}.")
            return
        app.templates.remove(template)
        print(f"Removed template #{template_id}.")

    else:
        print(f"Unknown template command: {sub!r}")


def handle_settings(args: List[str], app: AppState) -> None:
    if not args:
        print("Usage: settings <show|set> ...")
        return

    sub, rest = args[0], args[1:]

    if sub == "show":
        s = app.settings
        print(f"focus_minutes: {s.focus_minutes}")
        print(f"break_minutes: {s.break_minutes}")
        print(f"alarm_sound: {s.alarm_sound}")
        print(f"background_sound: {s.background_sound}")

    elif sub == "set":
        if len(rest) < 2:
            print("Usage: settings set <focus|break|alarm|background> <value>")
            return
        field, value = rest[0], rest[1]
        if field == "focus":
            if not value.isdigit() or int(value) <= 0:
                print("focus minutes must be a positive integer.")
                return
            app.settings.focus_minutes = int(value)
            print(f"focus_minutes set to {value}.")
        elif field == "break":
            if not value.isdigit() or int(value) <= 0:
                print("break minutes must be a positive integer.")
                return
            app.settings.break_minutes = int(value)
            print(f"break_minutes set to {value}.")
        elif field == "alarm":
            if value not in ("bell", "silent"):
                print("alarm must be 'bell' or 'silent'.")
                return
            app.settings.alarm_sound = value
            print(f"alarm_sound set to {value}.")
        elif field == "background":
            app.settings.background_sound = value
            print(f"background_sound set to {value}.")
        else:
            print(f"Unknown setting: {field!r}")

    else:
        print(f"Unknown settings command: {sub!r}")


def handle_eta(app: AppState) -> None:
    finish = estimate_finish_time(app)
    if finish is None:
        print("No pending tasks.")
        return
    pending = sum(t.remaining_pomodoros() for t in app.tasks if not t.is_done())
    print(f"Estimated finish: {finish.strftime('%I:%M %p')} ({pending} pomodoros remaining)")


def handle_report(args: List[str], app: AppState) -> None:
    granularity = args[0] if args else "day"
    if granularity not in reports.GRANULARITIES:
        print(f"Usage: report [{'|'.join(reports.GRANULARITIES)}]")
        return
    print(reports.render(reports.aggregate(app.session_log, granularity)))


def main() -> None:
    data_path = storage.DEFAULT_DATA_PATH
    app = storage.load(data_path)

    lock = threading.Lock()
    stop_event = threading.Event()

    t = threading.Thread(target=ticker, args=(app, lock, stop_event, data_path), daemon=True)
    t.start()

    print("Pomodoro Timer TUI")
    print_help()
    print(app.timer.status_line())

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            line = "quit"

        if not line:
            continue

        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            print(f"Could not parse command: {exc}")
            continue

        command, args = tokens[0].lower(), tokens[1:]

        with lock:
            if command == "start":
                app.timer.start()
                print("Timer started.")
            elif command == "pause":
                app.timer.pause()
                print("Timer paused.")
            elif command == "reset":
                app.timer.reset(app.settings)
                print("Timer reset for the current phase.")
            elif command == "status":
                task = app.selected_task()
                task_note = f"task: {task.title} ({task.completed_pomodoros}/{task.estimate_pomodoros})" if task else "task: none selected"
                print(f"{app.timer.status_line()} | {task_note}")
            elif command == "help":
                print_help()
            elif command == "task":
                handle_task(args, app)
            elif command == "template":
                handle_template(args, app)
            elif command == "settings":
                handle_settings(args, app)
            elif command == "eta":
                handle_eta(app)
            elif command == "report":
                handle_report(args, app)
            elif command == "quit":
                print("Goodbye.")
                storage.save(app, data_path)
                stop_event.set()
                break
            else:
                print(f"Unknown command: {command!r}. Type 'help' for options.")
                continue

            if command != "quit":
                storage.save(app, data_path)


if __name__ == "__main__":
    main()
