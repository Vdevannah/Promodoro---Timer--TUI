"""Aggregation and ASCII rendering of the focus session log.

Pure functions only — no AppState/storage dependency, so they're easy to
reason about (and test) in isolation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List

from pomodoro.models import SessionLogEntry

GRANULARITIES = ("day", "week", "month")


@dataclass
class ReportRow:
    label: str
    sessions: int
    minutes: int


def bucket_key(ts: datetime, granularity: str) -> str:
    if granularity == "day":
        return ts.strftime("%Y-%m-%d")
    if granularity == "week":
        iso_year, iso_week, _ = ts.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if granularity == "month":
        return ts.strftime("%Y-%m")
    raise ValueError(f"Unknown granularity: {granularity!r}")


def aggregate(session_log: List[SessionLogEntry], granularity: str) -> List[ReportRow]:
    sessions_by_bucket: dict[str, int] = defaultdict(int)
    minutes_by_bucket: dict[str, int] = defaultdict(int)

    for entry in session_log:
        key = bucket_key(datetime.fromisoformat(entry.timestamp), granularity)
        sessions_by_bucket[key] += 1
        minutes_by_bucket[key] += entry.duration_minutes

    return [
        ReportRow(label=label, sessions=sessions_by_bucket[label], minutes=minutes_by_bucket[label])
        for label in sorted(sessions_by_bucket)
    ]


def render(rows: List[ReportRow], width: int = 30) -> str:
    if not rows:
        return "No focus sessions recorded yet."

    max_sessions = max(row.sessions for row in rows)
    label_width = max(len(row.label) for row in rows)

    lines = []
    for row in rows:
        bar_len = round(row.sessions / max_sessions * width) if max_sessions else 0
        bar = "#" * bar_len + "-" * (width - bar_len)
        lines.append(
            f"{row.label:<{label_width}} | {bar}  {row.sessions} sessions ({row.minutes}m)"
        )
    return "\n".join(lines)
