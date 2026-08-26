from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import secrets

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, TokenResponse, TokenRefreshRequest
from ..config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory blacklist za invalidisane refresh tokene
# U produkciji bi ovo bilo u Redisu
token_blacklist: set[str] = set()


def create_access_token(user_id: int, role_names: list[str]) -> str:
    payload = {
        "sub": str(user_id),
        "roles": role_names,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": secrets.token_hex(16),  # jedinstveni ID tokena
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pogrešan email ili lozinka",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Nalog je deaktiviran")

    role_names = [ur.role.name for ur in user.roles]
    access_token = create_access_token(user.id, role_names)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Neispravan refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Nije refresh token")

    jti = payload.get("jti")
    if jti in token_blacklist:
        raise HTTPException(status_code=401, detail="Token je poništen")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Korisnik ne postoji")

    role_names = [ur.role.name for ur in user.roles]
    new_access = create_access_token(user.id, role_names)
    new_refresh = create_refresh_token(user.id)

    token_blacklist.add(jti)  # stari refresh token invalidisati

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: TokenRefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        jti = payload.get("jti")
        if jti:
            token_blacklist.add(jti)
    except JWTError:
        pass  # token već neispravan, nije problem