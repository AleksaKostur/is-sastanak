from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReportOut(BaseModel):
    id:           int
    requested_by: int
    report_type:  str
    period:       Optional[str]
    meeting_id:   Optional[int]
    generated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    user_id: int
    user_name: str
    weekly: int
    monthly: int
    yearly: int


class AttendanceReportItem(BaseModel):
    meeting_id: int
    topic: str
    scheduled_at: datetime
    status: str
    agenda_items: list[str]

    model_config = {"from_attributes": True}