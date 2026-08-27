from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Notification, User
from ..schemas import NotificationOut
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[NotificationOut])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vraća sve notifikacije prijavljenog korisnika, od najnovije."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(404, "Notifikacija ne postoji")
    if notif.user_id != current_user.id:
        raise HTTPException(403, "Nije vaša notifikacija")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.patch("/read-all", response_model=List[NotificationOut])
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .all()
    )
    for n in notifs:
        n.is_read = True
    db.commit()
    return notifs