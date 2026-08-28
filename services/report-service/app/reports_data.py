from sqlalchemy.orm import Session
from .models import Meeting, AgendaItem, MeetingParticipant, User, ExternalPerson, MeetingCategory, OrgUnit


def gather_meeting_data(meeting_id: int, db: Session) -> dict:
    """Skuplja sve podatke o sastanku potrebne za izveštaj."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        return None

    category = db.query(MeetingCategory).filter(MeetingCategory.id == meeting.category_id).first()
    org_unit = db.query(OrgUnit).filter(OrgUnit.id == meeting.org_unit_id).first()
    organizer = db.query(User).filter(User.id == meeting.organizer_id).first()

    agenda = db.query(AgendaItem).filter(
        AgendaItem.meeting_id == meeting_id
    ).order_by(AgendaItem.order_no).all()

    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()

    # razreši imena učesnika (interni vs eksterni)
    participant_rows = []
    for p in participants:
        if p.user_id:
            u = db.query(User).filter(User.id == p.user_id).first()
            ime = f"{u.first_name} {u.last_name}" if u else "N/A"
            org = "interni"
        else:
            e = db.query(ExternalPerson).filter(ExternalPerson.id == p.external_person_id).first()
            ime = f"{e.first_name} {e.last_name}" if e else "N/A"
            org = e.organization if e else "N/A"

        prisustvo = "N/A"
        if p.attended is True:
            prisustvo = "Prisutan"
        elif p.attended is False:
            prisustvo = "Odsutan"

        participant_rows.append({
            "ime": ime,
            "uloga": p.role_in_meeting,
            "organizacija": org,
            "planiran": "Da" if p.is_planned else "Ne",
            "prisustvo": prisustvo,
        })

    return {
        "meeting": meeting,
        "category_name": category.name if category else "N/A",
        "org_unit_name": org_unit.name if org_unit else "N/A",
        "organizer_name": f"{organizer.first_name} {organizer.last_name}" if organizer else "N/A",
        "agenda": agenda,
        "participants": participant_rows,
    }