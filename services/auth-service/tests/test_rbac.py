import pytest
from app.models import User, UserRole
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_user(db, user_id, email, roles=None):
    """Helper: kreira korisnika sa opcionim ulogama."""
    user = User(
        id=user_id, org_unit_id=1, first_name="User", father_name="F",
        last_name=f"Prezime{user_id}", jmbg=f"{user_id}".zfill(13),
        job_title="Radnik", email=email,
        password_hash=pwd.hash("pass123"), is_active=True,
    )
    db.add(user)
    if roles:
        for role_id in roles:
            db.add(UserRole(user_id=user_id, role_id=role_id, is_permanent=True))
    db.commit()
    return user


def _get_token(client, email):
    res = client.post("/auth/login", json={"email": email, "password": "pass123"})
    return res.json()["access_token"]


def test_admin_can_list_users(client, db_session):
    """ADMIN može listati korisnike."""
    _create_user(db_session, 1, "admin@test.com", roles=[1])  # ADMIN
    token = _get_token(client, "admin@test.com")
    res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_user_without_role_cannot_list_users(client, db_session):
    """Korisnik bez uloge ne može listati korisnike (403)."""
    _create_user(db_session, 2, "nobody@test.com", roles=None)
    token = _get_token(client, "nobody@test.com")
    res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_user_cannot_read_other_user(client, db_session):
    """Korisnik ne može čitati podatke drugog korisnika (eskalacija kroz URL)."""
    _create_user(db_session, 1, "admin@test.com", roles=[1])
    _create_user(db_session, 2, "marko@test.com", roles=None)
    token = _get_token(client, "marko@test.com")
    # Marko (id=2) pokušava čitati Admina (id=1)
    res = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_user_can_read_own_data(client, db_session):
    """Korisnik može čitati sopstvene podatke."""
    _create_user(db_session, 2, "marko@test.com", roles=None)
    token = _get_token(client, "marko@test.com")
    res = client.get("/users/2", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_user_cannot_assign_admin_to_self(client, db_session):
    """Korisnik bez ADMIN uloge ne može sebi dodeliti ADMIN (403)."""
    _create_user(db_session, 2, "marko@test.com", roles=None)
    token = _get_token(client, "marko@test.com")
    res = client.post(
        "/roles/assign",
        json={"user_id": 2, "role_id": 1, "is_permanent": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_manager_role_requires_org_unit(client, db_session):
    """Dodela RUKOVODILAC uloge bez org_unit_id vraća 400."""
    _create_user(db_session, 1, "admin@test.com", roles=[1])
    token = _get_token(client, "admin@test.com")
    res = client.post(
        "/roles/assign",
        json={"user_id": 1, "role_id": 2, "is_permanent": True},  # RUKOVODILAC bez org_unit
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400


def test_roles_endpoint_requires_auth(client):
    """Roles endpoint bez tokena vraća 403."""
    res = client.get("/roles/")
    assert res.status_code == 403