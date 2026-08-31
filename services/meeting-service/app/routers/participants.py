from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Meeting, MeetingParticipant, ExternalPerson, User, Notification
from ..schemas import (
    ParticipantAdd, ParticipantOut,
    AttendanceUpdate,
    ExternalPersonCreate, ExternalPersonOut,
)
from ..dependencies import get_current_user, AnyAuthenticated, ManagerOrAdmin

router = APIRouter()


def _get_meeting_or_404(meeting_id: int, db: Session) -> Meeting:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Sastanak ne postoji")
    return meeting


# ── Eksterna lica ─────────────────────────────────────────────────────────

@router.post("/external-persons", response_model=ExternalPersonOut, status_code=201)
def create_external_person(
    body: ExternalPersonCreate,
    db: Session = Depends(get_db),
    _=ManagerOrAdmin,
):
    person = ExternalPerson(**body.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/external-persons", response_model=List[ExternalPersonOut])
def list_external_persons(db: Session = Depends(get_db), _=AnyAuthenticated):
    return db.query(ExternalPerson).all()


# ── Učesnici sastanka ─────────────────────────────────────────────────────

@router.post("/{meeting_id}/participants", response_model=ParticipantOut, status_code=201)
def add_participant(
    meeting_id: int,
    body: ParticipantAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _get_meeting_or_404(meeting_id, db)

    # samo organizator ili Admin
    if meeting.organizer_id != current_user.id and "ADMIN" not in current_user._token_roles:
        raise HTTPException(403, "Samo organizator može dodavati učesnike")

    if meeting.status != "PLANIRAN":
        raise HTTPException(400, "Učesnici se mogu dodavati samo za planirane sastanke")

    # proveri da li user postoji (ako je interni)
    if body.user_id is not None:
        user = db.query(User).filter(User.id == body.user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(404, "Korisnik ne postoji ili je deaktiviran")

    # proveri da li external_person postoji
    if body.external_person_id is not None:
        ext = db.query(ExternalPerson).filter(
            ExternalPerson.id == body.external_person_id
        ).first()
        if not ext:
            raise HTTPException(404, "Eksterno lice ne postoji")

    # proveri da nije već dodat isti učesnik
    existing = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.user_id == body.user_id if body.user_id else
        MeetingParticipant.external_person_id == body.external_person_id,
    ).first()
    if existing:
        raise HTTPException(400, "Učesnik je već dodat na ovaj sastanak")

    # proveri substitute_for_id ako je naveden
    if body.substitute_for_id is not None:
        original = db.query(MeetingParticipant).filter(
            MeetingParticipant.id == body.substitute_for_id,
            MeetingParticipant.meeting_id == meeting_id,
        ).first()
        if not original:
            raise HTTPException(404, "Učesnik kojeg zamenjuje ne postoji na ovom sastanku")

    participant = MeetingParticipant(
        meeting_id=meeting_id,
        user_id=body.user_id,
        external_person_id=body.external_person_id,
        role_in_meeting=body.role_in_meeting.value,
        is_planned=True,
        substitute_for_id=body.substitute_for_id,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    # notifikacija internom učesniku
    if body.user_id and body.user_id != current_user.id:
        notif = Notification(
            user_id=body.user_id,
            meeting_id=meeting_id,
            type="USPESNO",
            message=f"Dodati ste kao učesnik na sastanak '{meeting.topic}' "
                    f"zakazan za {meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')}.",
            created_at=datetime.now(),
        )
        db.add(notif)
        db.commit()

    return participant


@router.get("/{meeting_id}/participants", response_model=List[ParticipantOut])
def list_participants(
    meeting_id: int,
    db: Session = Depends(get_db),
    _=AnyAuthenticated,
):
    _get_meeting_or_404(meeting_id, db)
    return db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()


@router.delete("/{meeting_id}/participants/{participant_id}", status_code=204)
def remove_participant(
    meeting_id: int,
    participant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _get_meeting_or_404(meeting_id, db)

    if meeting.organizer_id != current_user.id and "ADMIN" not in current_user._token_roles:
        raise HTTPException(403, "Samo organizator može uklanjati učesnike")

    if meeting.status != "PLANIRAN":
        raise HTTPException(400, "Učesnici se mogu uklanjati samo za planirane sastanke")

    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting_id,
    ).first()
    if not participant:
        raise HTTPException(404, "Učesnik ne postoji na ovom sastanku")

    db.delete(participant)
    db.commit()


# ── Evidencija prisustva ──────────────────────────────────────────────────

@router.patch("/{meeting_id}/participants/{participant_id}/attendance",
              response_model=ParticipantOut)
def record_attendance(
    meeting_id: int,
    participant_id: int,
    body: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evidencija prisustva — Rukovodilac ili Zapisničar.
    72h pravilo: može se evidentirati najkasnije 72 sata posle sastanka.
    """
    if not any(r in current_user._token_roles for r in ["RUKOVODILAC", "ZAPISNICAR", "ADMIN"]):
        raise HTTPException(403, "Pristup zabranjen")

    meeting = _get_meeting_or_404(meeting_id, db)

    # evidencija ima smisla samo kad je sastanak planiran ili održan
    if meeting.status == "OTKAZAN":
        raise HTTPException(400, "Ne može se evidentirati prisustvo na otkazanom sastanku")

    # ne može se evidentirati prisustvo pre početka sastanka
    if datetime.now() < meeting.scheduled_at:
        raise HTTPException(
            400,
            "Ne može se evidentirati prisustvo pre početka sastanka"
        )

    # 72h pravilo
    deadline = meeting.scheduled_at + timedelta(hours=72)
    if datetime.now() > deadline:
        raise HTTPException(
            400,
            f"Rok za evidenciju prisustva je istekao "
            f"(72h od {meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')}, "
            f"rok bio: {deadline.strftime('%d.%m.%Y %H:%M')})"
        )

    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting_id,
    ).first()
    if not participant:
        raise HTTPException(404, "Učesnik ne postoji na ovom sastanku")

    participant.attended = body.attended
    participant.recorded_at = datetime.now()
    db.commit()
    db.refresh(participant)

    # ako su svi učesnici evidentirani, automatski postavi status na ODRZAN
    all_participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.is_planned == True,
    ).all()

    if all_participants and all(p.attended is not None for p in all_participants):
        meeting.status = "ODRZAN"
        db.commit()

    return participant