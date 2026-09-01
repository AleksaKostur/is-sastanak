import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from jose import jwt

from app.main import app
from app.database import Base, get_db
from app.models import OrgUnit, User, MeetingCategory
from app.config import settings

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    # seed: dve org celine, rukovodilac (celina 1), kategorija
    session.add(OrgUnit(id=1, name="Matična celina"))
    session.add(OrgUnit(id=2, name="Druga celina"))
    session.add(User(
        id=1, org_unit_id=1, first_name="Petar", father_name="J",
        last_name="Petrović", jmbg="1111111111111", job_title="Rukovodilac",
        email="petar@test.com", password_hash="x", is_active=True,
    ))
    session.add(MeetingCategory(id=1, name="Kolegijum"))
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_token(user_id: int, roles: list[str]) -> str:
    """Pravi validan access token za testove (isti jwt_secret kao servis)."""
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.fixture
def manager_headers():
    """Authorization header za rukovodioca (user 1, RUKOVODILAC)."""
    token = make_token(1, ["RUKOVODILAC"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    token = make_token(1, ["ADMIN"])
    return {"Authorization": f"Bearer {token}"}