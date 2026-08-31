from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..dependencies import get_current_user, require_roles, AdminOnly, AnyAuthenticated, ManagerOrAdmin
from ..database import get_db
from ..models import User, OrgUnit
from ..schemas import UserCreate, UserOut, UserUpdate
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db),
                _: User = AdminOnly):
    # provera da li email ili JMBG već postoji
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email već postoji")
    if db.query(User).filter(User.jmbg == user_in.jmbg).first():
        raise HTTPException(status_code=400, detail="JMBG već postoji")

    # provera da org_unit postoji
    org_unit = db.query(OrgUnit).filter(OrgUnit.id == user_in.org_unit_id).first()
    if not org_unit:
        raise HTTPException(status_code=404, detail="Organizaciona celina ne postoji")

    user = User(
        org_unit_id=user_in.org_unit_id,
        first_name=user_in.first_name,
        father_name=user_in.father_name,
        last_name=user_in.last_name,
        jmbg=user_in.jmbg,
        job_title=user_in.job_title,
        rank=user_in.rank,
        work_phone=user_in.work_phone,
        mobile_phone=user_in.mobile_phone,
        email=user_in.email,
        password_hash=pwd_context.hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db),
               _: User = ManagerOrAdmin):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = AnyAuthenticated,
):
    # Korisnik može videti samo sopstvene podatke
    # Admin i Rukovodilac mogu videti sve
    is_privileged = any(r in current_user._token_roles for r in ["ADMIN", "RUKOVODILAC"])
    if not is_privileged and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemate pravo pristupa podacima drugog korisnika"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik ne postoji")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = AnyAuthenticated,
):
    # Samo Admin može menjati tuđe podatke
    if "ADMIN" not in current_user._token_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemate pravo izmene podataka drugog korisnika"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik ne postoji")

    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db),
                    _: User = AdminOnly):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik ne postoji")
    user.is_active = False
    db.commit()