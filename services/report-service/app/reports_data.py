from sqlalchemy.orm import Session
from .models import Meeting, AgendaItem, AgendaProposal, MeetingParticipant, User, ExternalPerson, MeetingCategory, OrgUnit


def _resolve_participant_name(p, db):
    """Razrešava ime učesnika (interni ili eksterni)."""
    if p.user_id:
        u = db.query(User).filter(User.id == p.user_id).first()
        return f"{u.first_name} {u.last_name}" if u else "N/A"
    else:
        e = db.query(ExternalPerson).filter(ExternalPerson.id == p.external_person_id).first()
        return f"{e.first_name} {e.last_name}" if e else "N/A"


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

    # mapiraj participant id na ime (za predloge)
    participant_name_map = {}
    for p in participants:
        participant_name_map[p.id] = _resolve_participant_name(p, db)

    # razreši imena učesnika za tabelu
    participant_rows = []
    for p in participants:
        prisustvo = "N/A"
        if p.attended is True:
            prisustvo = "Prisutan"
        elif p.attended is False:
            prisustvo = "Odsutan"

        participant_rows.append({
            "ime": participant_name_map[p.id],
            "uloga": p.role_in_meeting,
            "organizacija": "interni" if p.user_id else (
                db.query(ExternalPerson).filter(ExternalPerson.id == p.external_person_id).first().organization
                if p.external_person_id else "N/A"
            ),
            "planiran": "Da" if p.is_planned else "Ne",
            "prisustvo": prisustvo,
        })

    # predlozi po tačkama dnevnog reda
    agenda_with_proposals = []
    for item in agenda:
        proposals = db.query(AgendaProposal).filter(
            AgendaProposal.agenda_item_id == item.id
        ).all()
        proposal_rows = []
        for pr in proposals:
            name = participant_name_map.get(pr.participant_id, "N/A") if pr.participant_id else "N/A"
            proposal_rows.append({
                "ucesnik": name,
                "sadrzaj": pr.content,
            })
        agenda_with_proposals.append({
            "item": item,
            "proposals": proposal_rows,
        })

    # pronađi zapisničara
    recorder_name = "N/A"
    for p in participants:
        if p.role_in_meeting == "ZAPISNICAR":
            recorder_name = participant_name_map[p.id]
            break

    return {
        "meeting": meeting,
        "category_name": category.name if category else "N/A",
        "org_unit_name": org_unit.name if org_unit else "N/A",
        "organizer_name": f"{organizer.first_name} {organizer.last_name}" if organizer else "N/A",
        "recorder_name": recorder_name,
        "agenda": agenda_with_proposals,
        "participants": participant_rows,
    }