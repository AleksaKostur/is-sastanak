from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Meeting, User
from ..schemas import MeetingOut
from ..dependencies import AnyAuthenticated

router = APIRouter()


@router.get("/", response_model=List[MeetingOut])
def get_calendar(
    date_from:    Optional[datetime] = Query(None, description="Filter od datuma (ISO 8601)"),
    date_to:      Optional[datetime] = Query(None, description="Filter do datuma (ISO 8601)"),
    status:       Optional[str]      = Query(None, description="PLANIRAN / ODRZAN / ODLOZEN / OTKAZAN"),
    meeting_type: Optional[str]      = Query(None, description="STALNI / VANREDNI"),
    org_unit_id:  Optional[int]      = Query(None, description="Filter po organizacionoj celini"),
    classification: Optional[str]      = Query(None, description="MATICNA / DRUGA — u odnosu na org. celinu rukovodioca"),
    db: Session = Depends(get_db),
    _=AnyAuthenticated,
):
    query = db.query(Meeting)

    if date_from:
        query = query.filter(Meeting.scheduled_at >= date_from)
    if date_to:
        query = query.filter(Meeting.scheduled_at <= date_to)
    if status:
        query = query.filter(Meeting.status == status.upper())
    if meeting_type:
        query = query.filter(Meeting.meeting_type == meeting_type.upper())
    if org_unit_id:
        query = query.filter(Meeting.org_unit_id == org_unit_id)

    # klasifikacija: MATICNA = sastanak u org. celini rukovodioca, DRUGA = van nje
    if classification:
        query = query.join(User, Meeting.organizer_id == User.id)
        if classification.upper() == "MATICNA":
            query = query.filter(Meeting.org_unit_id == User.org_unit_id)
        elif classification.upper() == "DRUGA":
            query = query.filter(Meeting.org_unit_id != User.org_unit_id)

    return query.order_by(Meeting.scheduled_at).all()