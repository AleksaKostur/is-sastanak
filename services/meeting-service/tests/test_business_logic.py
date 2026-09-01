from datetime import datetime, timedelta


def _create_meeting(client, headers, **overrides):
    """Helper: kreira sastanak sa default vrednostima, override po potrebi."""
    payload = {
        "topic": "Test sastanak",
        "category_id": 1,
        "org_unit_id": 1,
        "meeting_type": "VANREDNI",
        "scheduled_at": (datetime.now() + timedelta(days=10)).isoformat(),
        "location": "Zgrada A",
        "room": "Sala 1",
    }
    payload.update(overrides)
    return client.post("/meetings/", json=payload, headers=headers)


# ── Recurrence validacija ─────────────────────────────────────────────────

def test_stalni_meeting_requires_recurrence(client, manager_headers):
    """Stalni sastanak bez periodičnosti vraća 422."""
    res = _create_meeting(client, manager_headers, meeting_type="STALNI")
    assert res.status_code == 422


def test_stalni_meeting_with_recurrence_ok(client, manager_headers):
    """Stalni sastanak sa periodičnošću prolazi."""
    res = _create_meeting(client, manager_headers, meeting_type="STALNI", recurrence="NEDELJNI")
    assert res.status_code == 201


def test_vanredni_meeting_with_recurrence_rejected(client, manager_headers):
    """Vanredni sastanak sa periodičnošću vraća 422."""
    res = _create_meeting(client, manager_headers, meeting_type="VANREDNI", recurrence="NEDELJNI")
    assert res.status_code == 422


# ── RBAC na kreiranju ─────────────────────────────────────────────────────

def test_participant_cannot_create_meeting(client):
    """Korisnik sa ulogom UCESNIK ne može kreirati sastanak (403)."""
    from tests.conftest import make_token
    token = make_token(1, ["UCESNIK"])
    headers = {"Authorization": f"Bearer {token}"}
    res = _create_meeting(client, headers)
    assert res.status_code == 403


# ── 3-dana pravilo za dnevni red ──────────────────────────────────────────

def test_agenda_within_3_days_rejected(client, manager_headers):
    """Dodavanje stavke dnevnog reda manje od 3 dana pre sastanka vraća 400."""
    # sastanak za 2 dana
    res = _create_meeting(
        client, manager_headers,
        scheduled_at=(datetime.now() + timedelta(days=2)).isoformat(),
    )
    meeting_id = res.json()["id"]

    res = client.post(
        f"/meetings/{meeting_id}/agenda",
        json={"order_no": 1, "title": "Tačka"},
        headers=manager_headers,
    )
    assert res.status_code == 400


def test_agenda_more_than_3_days_ok(client, manager_headers):
    """Dodavanje stavke više od 3 dana pre sastanka prolazi."""
    # sastanak za 10 dana (default)
    res = _create_meeting(client, manager_headers)
    meeting_id = res.json()["id"]

    res = client.post(
        f"/meetings/{meeting_id}/agenda",
        json={"order_no": 1, "title": "Tačka"},
        headers=manager_headers,
    )
    assert res.status_code == 201


# ── 72h pravilo za evidenciju prisustva ───────────────────────────────────

def test_attendance_before_meeting_rejected(client, manager_headers, db_session):
    """Evidencija prisustva pre početka sastanka vraća 400."""
    res = _create_meeting(client, manager_headers)  # sastanak za 10 dana
    meeting_id = res.json()["id"]

    # dodaj učesnika
    res = client.post(
        f"/meetings/{meeting_id}/participants",
        json={"user_id": 1, "role_in_meeting": "UCESNIK"},
        headers=manager_headers,
    )
    participant_id = res.json()["id"]

    # pokušaj evidencije (sastanak još nije počeo)
    res = client.patch(
        f"/meetings/{meeting_id}/participants/{participant_id}/attendance",
        json={"attended": True},
        headers=manager_headers,
    )
    assert res.status_code == 400


def test_attendance_after_72h_rejected(client, manager_headers, db_session):
    """Evidencija više od 72h posle sastanka vraća 400."""
    from app.models import Meeting, MeetingParticipant
    # ručno kreiraj sastanak u prošlosti (pre 5 dana)
    meeting = Meeting(
        topic="Stari", category_id=1, organizer_id=1, org_unit_id=1,
        meeting_type="VANREDNI", scheduled_at=datetime.now() - timedelta(days=5),
        location="A", room="1", status="PLANIRAN",
    )
    db_session.add(meeting)
    db_session.commit()
    participant = MeetingParticipant(
        meeting_id=meeting.id, user_id=1, role_in_meeting="UCESNIK", is_planned=True,
    )
    db_session.add(participant)
    db_session.commit()

    res = client.patch(
        f"/meetings/{meeting.id}/participants/{participant.id}/attendance",
        json={"attended": True},
        headers=manager_headers,
    )
    assert res.status_code == 400


# ── Klasifikacija matična/druga ───────────────────────────────────────────

def test_classification_maticna(client, manager_headers):
    """Sastanak u org. celini rukovodioca je MATICNA."""
    res = _create_meeting(client, manager_headers, org_unit_id=1)  # rukovodilac je u celini 1
    assert res.status_code == 201
    # proveri kroz kalendar
    res = client.get("/calendar/?classification=MATICNA", headers=manager_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1
    assert all(m["classification"] == "MATICNA" for m in res.json())


def test_classification_druga(client, manager_headers):
    """Sastanak van org. celine rukovodioca je DRUGA."""
    res = _create_meeting(client, manager_headers, org_unit_id=2)  # celina 2, rukovodilac u 1
    assert res.status_code == 201
    res = client.get("/calendar/?classification=DRUGA", headers=manager_headers)
    assert res.status_code == 200
    assert all(m["classification"] == "DRUGA" for m in res.json())


# ── XOR učesnik (interni ili eksterni, ne oba) ────────────────────────────

def test_participant_requires_user_or_external(client, manager_headers):
    """Učesnik bez user_id i bez external_person_id vraća 422."""
    res = _create_meeting(client, manager_headers)
    meeting_id = res.json()["id"]

    res = client.post(
        f"/meetings/{meeting_id}/participants",
        json={"role_in_meeting": "UCESNIK"},  # ni user_id ni external_person_id
        headers=manager_headers,
    )
    assert res.status_code == 422