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