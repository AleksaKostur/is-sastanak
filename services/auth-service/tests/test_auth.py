def test_login_success(client, db_session):
    """Uspešna prijava vraća access i refresh token."""
    from app.models import User
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        org_unit_id=1, first_name="Test", father_name="T",
        last_name="Testović", jmbg="2222222222222", job_title="Tester",
        email="test@test.com", password_hash=pwd.hash("test123"), is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    res = client.post("/auth/login", json={"email": "test@test.com", "password": "test123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db_session):
    """Pogrešna lozinka vraća 401."""
    from app.models import User
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        org_unit_id=1, first_name="Test", father_name="T",
        last_name="Testović", jmbg="3333333333333", job_title="Tester",
        email="test2@test.com", password_hash=pwd.hash("test123"), is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    res = client.post("/auth/login", json={"email": "test2@test.com", "password": "pogresna"})
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    """Nepostojeći korisnik vraća 401 (ista poruka kao pogrešna lozinka)."""
    res = client.post("/auth/login", json={"email": "nema@test.com", "password": "test123"})
    assert res.status_code == 401


def test_protected_endpoint_without_token(client):
    """Zaštićeni endpoint bez tokena vraća 403."""
    res = client.get("/users/")
    assert res.status_code == 403


def test_token_contains_roles(client, admin_token):
    """Access token sadrži uloge korisnika."""
    import base64, json
    payload_part = admin_token.split(".")[1]
    # dopuni padding za base64
    payload_part += "=" * (-len(payload_part) % 4)
    payload = json.loads(base64.b64decode(payload_part))
    assert "ADMIN" in payload["roles"]
    assert payload["type"] == "access"