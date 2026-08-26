from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from .config import settings
from .database import get_db
from .models import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Neispravan token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Nije access token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Korisnik ne postoji ili je deaktiviran")

    # kačimo role na user objekat da ih ne čitamo ponovo
    user._token_roles = payload.get("roles", [])
    return user


def require_roles(*roles: str):
    """
    Fabrika dependency-a — pravi funkciju koja proverava uloge.
    Primer: Depends(require_roles("ADMIN", "RUKOVODILAC"))
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not any(role in current_user._token_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Pristup zabranjen. Potrebna uloga: {', '.join(roles)}"
            )
        return current_user
    return checker


# Gotove dependency instance za česte slučajeve
AdminOnly = Depends(require_roles("ADMIN"))
AnyAuthenticated = Depends(get_current_user)
ManagerOrAdmin = Depends(require_roles("ADMIN", "RUKOVODILAC"))