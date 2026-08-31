from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Meeting, MeetingCategory, OrgUnit, User, MeetingParticipant, Notification
from ..schemas import (
    MeetingCreate, MeetingOut, MeetingStatusUpdate,
    MeetingMinutesUpdate, MeetingCategoryCreate, MeetingCategoryOut
)
from ..dependencies import get_current_user, ManagerOrAdmin, AnyAuthenticated, RecorderOrManager

router = APIRouter()


# ── Kategorije ────────────────────────────────────────────────────────────

@router.post("/categories", response_model=MeetingCategoryOut, status_code=201)
def create_category(body: MeetingCategoryCreate, db: Session = Depends(get_db),
                    _=ManagerOrAdmin):
    if db.query(MeetingCategory).filter(MeetingCategory.name == body.name).first():
        raise HTTPException(400, "Kategorija već postoji")
    cat = MeetingCategory(name=body.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/categories", response_model=List[MeetingCategoryOut])
def list_categories(db: Session = Depends(get_db), _=AnyAuthenticated):
    return db.query(MeetingCategory).all()


# ── Sastanci CRUD ─────────────────────────────────────────────────────────

@router.post("/", response_model=MeetingOut, status_code=201)
def create_meeting(
    body: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # samo RUKOVODILAC i ADMIN mogu kreirati
    if not any(r in current_user._token_roles for r in ["RUKOVODILAC", "ADMIN"]):
        raise HTTPException(403, "Pristup zabranjen")

    # proveri da kategorija postoji
    if not db.query(MeetingCategory).filter(MeetingCategory.id == body.category_id).first():
        raise HTTPException(404, "Kategorija ne postoji")

    # proveri da org_unit postoji
    if not db.query(OrgUnit).filter(OrgUnit.id == body.org_unit_id).first():
        raise HTTPException(404, "Organizaciona celina ne postoji")

    meeting = Meeting(
        topic=body.topic,
        category_id=body.category_id,
        organizer_id=current_user.id,
        org_unit_id=body.org_unit_id,
        meeting_type=body.meeting_type.value,
        recurrence=body.recurrence.value if body.recurrence else None,
        scheduled_at=body.scheduled_at,
        location=body.location,
        room=body.room,
        act_number=body.act_number,
        act_date=body.act_date,
        act_organization=body.act_organization,
        status="PLANIRAN",
        created_at=datetime.now(),
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # automatska notifikacija kreatoru
    notif = Notification(
        user_id=current_user.id,
        meeting_id=meeting.id,
        type="USPESNO",
        message=f"Sastanak '{meeting.topic}' je uspešno zakazan za {meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')}.",
        created_at=datetime.now(),
    )
    db.add(notif)
    db.commit()

    return meeting


@router.get("/", response_model=List[MeetingOut])
def list_meetings(db: Session = Depends(get_db), _=AnyAuthenticated):
    return db.query(Meeting).order_by(Meeting.scheduled_at).all()


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db), _=AnyAuthenticated):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Sastanak ne postoji")
    return meeting


@router.patch("/{meeting_id}/status", response_model=MeetingOut)
def update_status(
    meeting_id: int,
    body: MeetingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Sastanak ne postoji")

    # samo organizator ili Admin
    if meeting.organizer_id != current_user.id and "ADMIN" not in current_user._token_roles:
        raise HTTPException(403, "Samo organizator može menjati status sastanka")

    # ne može se menjati status već održanog
    if meeting.status == "ODRZAN":
        raise HTTPException(400, "Održan sastanak ne može promeniti status")

    old_status = meeting.status
    meeting.status = body.status.value
    meeting.status_reason = body.status_reason
    db.commit()
    db.refresh(meeting)

    # notifikacija svim učesnicima
    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.user_id.isnot(None),
    ).all()
    for p in participants:
        if p.user_id != current_user.id:
            notif = Notification(
                user_id=p.user_id,
                meeting_id=meeting.id,
                type="PROMENA_OD_DRUGOG",
                message=f"Status sastanka '{meeting.topic}' promenjen: {old_status} → {body.status.value}.",
                created_at=datetime.now(),
            )
            db.add(notif)
    db.commit()

    return meeting


@router.patch("/{meeting_id}/minutes", response_model=MeetingOut)
def update_minutes(
    meeting_id: int,
    body: MeetingMinutesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unos uvodne reči i zaključka — Rukovodilac ili Zapisničar."""
    if not any(r in current_user._token_roles for r in ["RUKOVODILAC", "ZAPISNICAR", "ADMIN"]):
        raise HTTPException(403, "Pristup zabranjen")

    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Sastanak ne postoji")

    if body.intro is not None:
        meeting.intro = body.intro
    if body.conclusion is not None:
        meeting.conclusion = body.conclusion

    db.commit()
    db.refresh(meeting)
    return meeting


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Sastanak ne postoji")

    # samo organizator ili Admin
    if meeting.organizer_id != current_user.id and "ADMIN" not in current_user._token_roles:
        raise HTTPException(403, "Samo organizator može obrisati sastanak")

    # ne može se brisati već održan
    if meeting.status == "ODRZAN":
        raise HTTPException(400, "Održan sastanak ne može biti obrisan")

    db.delete(meeting)
    db.commit()