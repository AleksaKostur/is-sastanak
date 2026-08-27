from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Meeting, AgendaItem, AgendaProposal, MeetingParticipant, User
from ..schemas import (
    AgendaItemCreate, AgendaItemOut,
    AgendaItemDiscussionUpdate,
    AgendaProposalCreate, AgendaProposalOut,
)
from ..dependencies import get_current_user, AnyAuthenticated

router = APIRouter()


def _get_meeting_or_404(meeting_id: int, db: Session) -> Meeting:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Sastanak ne postoji")
    return meeting


def _assert_organizer_or_admin(meeting: Meeting, current_user: User):
    if meeting.organizer_id != current_user.id and "ADMIN" not in current_user._token_roles:
        raise HTTPException(403, "Samo organizator može menjati dnevni red")


# ── Stavke dnevnog reda ───────────────────────────────────────────────────

@router.post("/{meeting_id}/agenda", response_model=AgendaItemOut, status_code=201)
def add_agenda_item(
    meeting_id: int,
    body: AgendaItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _get_meeting_or_404(meeting_id, db)
    _assert_organizer_or_admin(meeting, current_user)

    if meeting.status != "PLANIRAN":
        raise HTTPException(400, "Dnevni red može se menjati samo za planirane sastanke")

    # pravilo: dnevni red mora biti zatvoren min 3 dana pre sastanka
    deadline = meeting.scheduled_at - timedelta(days=3)
    if datetime.now() > deadline:
        raise HTTPException(
            400,
            f"Dnevni red mora biti dostavljen najkasnije 3 dana pre sastanka "
            f"(rok bio: {deadline.strftime('%d.%m.%Y %H:%M')})"
        )

    # proveri duplikat rednog broja
    if db.query(AgendaItem).filter(
        AgendaItem.meeting_id == meeting_id,
        AgendaItem.order_no == body.order_no,
    ).first():
        raise HTTPException(400, f"Stavka sa rednim brojem {body.order_no} već postoji")

    item = AgendaItem(
        meeting_id=meeting_id,
        order_no=body.order_no,
        title=body.title,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{meeting_id}/agenda", response_model=List[AgendaItemOut])
def list_agenda_items(
    meeting_id: int,
    db: Session = Depends(get_db),
    _=AnyAuthenticated,
):
    _get_meeting_or_404(meeting_id, db)
    return db.query(AgendaItem).filter(
        AgendaItem.meeting_id == meeting_id
    ).order_by(AgendaItem.order_no).all()


@router.delete("/{meeting_id}/agenda/{item_id}", status_code=204)
def delete_agenda_item(
    meeting_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _get_meeting_or_404(meeting_id, db)
    _assert_organizer_or_admin(meeting, current_user)

    if meeting.status != "PLANIRAN":
        raise HTTPException(400, "Dnevni red može se menjati samo za planirane sastanke")

    deadline = meeting.scheduled_at - timedelta(days=3)
    if datetime.now() > deadline:
        raise HTTPException(400, "Rok za izmenu dnevnog reda je istekao (3 dana pre sastanka)")

    item = db.query(AgendaItem).filter(
        AgendaItem.id == item_id,
        AgendaItem.meeting_id == meeting_id,
    ).first()
    if not item:
        raise HTTPException(404, "Stavka dnevnog reda ne postoji")

    db.delete(item)
    db.commit()


# ── Diskusija po tački (vođenje sastanka) ─────────────────────────────────

@router.patch("/{meeting_id}/agenda/{item_id}/discussion", response_model=AgendaItemOut)
def update_discussion(
    meeting_id: int,
    item_id: int,
    body: AgendaItemDiscussionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unos diskusije po tački — Rukovodilac ili Zapisničar."""
    if not any(r in current_user._token_roles for r in ["RUKOVODILAC", "ZAPISNICAR", "ADMIN"]):
        raise HTTPException(403, "Pristup zabranjen")

    meeting = _get_meeting_or_404(meeting_id, db)

    if meeting.status not in ("PLANIRAN", "ODRZAN"):
        raise HTTPException(400, "Diskusija se može uneti samo za planirane ili održane sastanke")

    item = db.query(AgendaItem).filter(
        AgendaItem.id == item_id,
        AgendaItem.meeting_id == meeting_id,
    ).first()
    if not item:
        raise HTTPException(404, "Stavka dnevnog reda ne postoji")

    item.discussion = body.discussion
    db.commit()
    db.refresh(item)
    return item


# ── Predlozi učesnika ─────────────────────────────────────────────────────

@router.post("/{meeting_id}/agenda/{item_id}/proposals",
             response_model=AgendaProposalOut, status_code=201)
def add_proposal(
    meeting_id: int,
    item_id: int,
    body: AgendaProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Učesnik iznosi predlog po tački dnevnog reda."""
    _get_meeting_or_404(meeting_id, db)

    item = db.query(AgendaItem).filter(
        AgendaItem.id == item_id,
        AgendaItem.meeting_id == meeting_id,
    ).first()
    if not item:
        raise HTTPException(404, "Stavka dnevnog reda ne postoji")

    # pronađi participant zapis za current_user u ovom sastanku
    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.user_id == current_user.id,
    ).first()
    # participant_id može biti None ako korisnik nije formalno na listi
    participant_id = participant.id if participant else None

    proposal = AgendaProposal(
        agenda_item_id=item_id,
        participant_id=participant_id,
        content=body.content,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("/{meeting_id}/agenda/{item_id}/proposals",
            response_model=List[AgendaProposalOut])
def list_proposals(
    meeting_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _=AnyAuthenticated,
):
    _get_meeting_or_404(meeting_id, db)
    return db.query(AgendaProposal).filter(
        AgendaProposal.agenda_item_id == item_id
    ).all()