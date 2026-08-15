"""
Pomodoro Timer TUI
------------------
Mental model: a state machine.

State:
    phase              FOCUS or BREAK
    remaining           seconds left in the current phase
    running             is the countdown currently ticking?
    completed_sessions  number of focus blocks finished

Event sources:
    user events: start, pause, reset, quit
    time events: one tick per second

Transition rules (memorize these):
    - decrement only when running
    - on zero during FOCUS  -> completed_sessions += 1, switch to BREAK
    - on zero during BREAK  -> switch to FOCUS
    - reset restores the current phase's full duration and pauses
"""

from dataclasses import dataclass
from enum import Enum, auto
import threading
import time


class Phase(Enum):
    FOCUS = auto()
    BREAK = auto()


FOCUS_SECONDS = 25 * 60
BREAK_SECONDS = 5 * 60


@dataclass
class TimerState:
    phase: Phase = Phase.FOCUS
    remaining: int = FOCUS_SECONDS
    running: bool = False
    completed_sessions: int = 0

    def phase_duration(self) -> int:
        return FOCUS_SECONDS if self.phase == Phase.FOCUS else BREAK_SECONDS

    def tick(self) -> None:
        """Called once per second by the ticker thread."""
        if not self.running:
            return

        self.remaining -= 1

        if self.remaining <= 0:
            if self.phase == Phase.FOCUS:
                self.completed_sessions += 1
                self.phase = Phase.BREAK
            else:
                self.phase = Phase.FOCUS
            self.remaining = self.phase_duration()

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.remaining = self.phase_duration()
        self.running = False

    def status_line(self) -> str:
        mins, secs = divmod(self.remaining, 60)
        state = "RUNNING" if self.running else "PAUSED"
        return (
            f"[{self.phase.name:5}] {mins:02d}:{secs:02d} "
            f"({state}) | sessions completed: {self.completed_sessions}"
        )


def ticker(state: TimerState, stop_event: threading.Event) -> None:
    """Background thread: advance the state once per second."""
    while not stop_event.is_set():
        time.sleep(1)
        state.tick()


def print_help() -> None:
    print("Commands: start | pause | reset | status | help | quit")


def main() -> None:
    state = TimerState()
    stop_event = threading.Event()

    t = threading.Thread(target=ticker, args=(state, stop_event), daemon=True)
    t.start()

    print("Pomodoro Timer TUI")
    print_help()
    print(state.status_line())

    while True:
        try:
            command = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            command = "quit"

        if command == "start":
            state.start()
            print("Timer started.")
        elif command == "pause":
            state.pause()
            print("Timer paused.")
        elif command == "reset":
            state.reset()
            print("Timer reset for the current phase.")
        elif command == "status":
            print(state.status_line())
        elif command == "help":
            print_help()
        elif command == "quit":
            print("Goodbye.")
            stop_event.set()
            break
        else:
            print(f"Unknown command: {command!r}. Type 'help' for options.")


if __name__ == "__main__":
    main()