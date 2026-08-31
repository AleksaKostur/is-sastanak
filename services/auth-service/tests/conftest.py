import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret")
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import OrgUnit, Role

# in-memory SQLite za testove — brz i izolovan
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
    # seed: org celina + uloge
    session.add(OrgUnit(id=1, name="Test celina"))
    session.add_all([
        Role(id=1, name="ADMIN"),
        Role(id=2, name="RUKOVODILAC"),
        Role(id=3, name="ZAPISNICAR"),
        Role(id=4, name="UCESNIK"),
    ])
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    # override get_db da koristi test bazu
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client, db_session):
    """Kreira admin korisnika i vraća njegov access token."""
    from app.models import User, UserRole
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        id=1, org_unit_id=1, first_name="Admin", father_name="Test",
        last_name="Adminović", jmbg="1111111111111", job_title="Admin",
        email="admin@test.com", password_hash=pwd.hash("admin123"), is_active=True,
    )
    db_session.add(user)
    db_session.add(UserRole(user_id=1, role_id=1, is_permanent=True))
    db_session.commit()

    res = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["access_token"]