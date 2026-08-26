from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..dependencies import AdminOnly, AnyAuthenticated
from ..models import Role, UserRole, User, OrgUnit
from ..schemas import UserRoleAssign, UserRoleOut

router = APIRouter()


@router.get("/", response_model=List[dict])
def list_roles(db: Session = Depends(get_db),
               _: User = AnyAuthenticated):
    roles = db.query(Role).all()
    return [{"id": r.id, "name": r.name} for r in roles]


@router.post("/assign", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED)
def assign_role(body: UserRoleAssign, db: Session = Depends(get_db),
                _: User = AdminOnly):
    # proveri da korisnik postoji
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik ne postoji")

    # proveri da uloga postoji
    role = db.query(Role).filter(Role.id == body.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Uloga ne postoji")

    # ako je rukovodilac, org_unit_id je obavezan
    if role.name == "RUKOVODILAC" and body.org_unit_id is None:
        raise HTTPException(
            status_code=400,
            detail="Za ulogu RUKOVODILAC obavezno je navesti organizacionu celinu"
        )

    # proveri da ista uloga nije već dodeljena u istoj celini
    existing = db.query(UserRole).filter(
        UserRole.user_id == body.user_id,
        UserRole.role_id == body.role_id,
        UserRole.org_unit_id == body.org_unit_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Uloga je već dodeljena")

    user_role = UserRole(
        user_id=body.user_id,
        role_id=body.role_id,
        org_unit_id=body.org_unit_id,
        is_permanent=body.is_permanent,
        valid_from=body.valid_from,
        valid_to=body.valid_to,
        note=body.note,
    )
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    return user_role


@router.delete("/assign/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_role(user_role_id: int, db: Session = Depends(get_db),
                _: User = AdminOnly):
    user_role = db.query(UserRole).filter(UserRole.id == user_role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="Dodela uloge ne postoji")
    db.delete(user_role)
    db.commit()


@router.get("/user/{user_id}", response_model=List[UserRoleOut])
def get_user_roles(user_id: int, db: Session = Depends(get_db),
                   _: User = AnyAuthenticated):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik ne postoji")
    return user.roles