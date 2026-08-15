from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from pomodoro import reports
from pomodoro.api import schemas
from pomodoro.api.state import shared_state

router = APIRouter()


@router.get("", response_model=List[schemas.ReportRowResponse])
async def get_report(granularity: str = Query(default="day")):
    if granularity not in reports.GRANULARITIES:
        raise HTTPException(
            status_code=400,
            detail=f"granularity must be one of {reports.GRANULARITIES}",
        )
    with shared_state.lock:
        rows = reports.aggregate(shared_state.app.session_log, granularity)
    return [schemas.ReportRowResponse.model_validate(r) for r in rows]
