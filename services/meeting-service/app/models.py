from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    Text, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# ── tabele u vlasništvu auth servisa ──────────────────────────────────────
# Definišemo ih ovde samo da bi SQLAlchemy razrešio FK i relationships.
# Meeting servis ih NE kreira i NE menja — schema.sql je jedini vlasnik.

class OrgUnit(Base):
    __tablename__ = "org_units"

    id        = Column(Integer, primary_key=True)
    name      = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("org_units.id"), nullable=True)


class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True)
    org_unit_id  = Column(Integer, ForeignKey("org_units.id"), nullable=False)
    first_name   = Column(String, nullable=False)
    father_name  = Column(String, nullable=False)
    last_name    = Column(String, nullable=False)
    jmbg         = Column(String(13), unique=True, nullable=False)
    job_title    = Column(String, nullable=False)
    work_phone   = Column(String)
    mobile_phone = Column(String)
    email        = Column(String, unique=True, nullable=False)
    password_hash= Column(String, nullable=False)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime)


# ── tabele u vlasništvu meeting servisa ──────────────────────────────────

class MeetingCategory(Base):
    __tablename__ = "meeting_categories"

    id   = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    meetings = relationship("Meeting", back_populates="category")


class Meeting(Base):
    __tablename__ = "meetings"

    id               = Column(Integer, primary_key=True)
    topic            = Column(String, nullable=False)
    category_id      = Column(Integer, ForeignKey("meeting_categories.id"), nullable=False)
    organizer_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_unit_id      = Column(Integer, ForeignKey("org_units.id"), nullable=False)
    meeting_type     = Column(String, nullable=False)   # STALNI / VANREDNI
    recurrence       = Column(String)                   # NULL za vanredne
    scheduled_at     = Column(DateTime, nullable=False)
    location         = Column(String, nullable=False)
    room             = Column(String, nullable=False)
    status           = Column(String, nullable=False, default="PLANIRAN")
    status_reason    = Column(Text)
    act_number       = Column(String)
    act_date         = Column(Date)
    act_organization = Column(String)
    intro            = Column(Text)
    conclusion       = Column(Text)
    created_at       = Column(DateTime, server_default=func.now())

    category     = relationship("MeetingCategory", back_populates="meetings")
    organizer    = relationship("User", foreign_keys=[organizer_id])
    org_unit     = relationship("OrgUnit", foreign_keys=[org_unit_id])
    agenda_items = relationship("AgendaItem", back_populates="meeting",
                                order_by="AgendaItem.order_no",
                                cascade="all, delete-orphan")
    participants = relationship("MeetingParticipant", back_populates="meeting",
                                cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="meeting")


class AgendaItem(Base):
    __tablename__ = "agenda_items"

    id         = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    order_no   = Column(Integer, nullable=False)
    title      = Column(String, nullable=False)
    discussion = Column(Text)

    meeting   = relationship("Meeting", back_populates="agenda_items")
    proposals = relationship("AgendaProposal", back_populates="agenda_item",
                             cascade="all, delete-orphan")


class AgendaProposal(Base):
    __tablename__ = "agenda_proposals"

    id             = Column(Integer, primary_key=True)
    agenda_item_id = Column(Integer, ForeignKey("agenda_items.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("meeting_participants.id"), nullable=True)
    content        = Column(Text, nullable=False)

    agenda_item = relationship("AgendaItem", back_populates="proposals")
    participant = relationship("MeetingParticipant", foreign_keys=[participant_id])


class ExternalPerson(Base):
    __tablename__ = "external_persons"

    id           = Column(Integer, primary_key=True)
    organization = Column(String, nullable=False)
    first_name   = Column(String, nullable=False)
    last_name    = Column(String, nullable=False)
    job_title    = Column(String)
    country      = Column(String)
    rank         = Column(String)  # čin


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id                 = Column(Integer, primary_key=True)
    meeting_id         = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id            = Column(Integer, ForeignKey("users.id"), nullable=True)
    external_person_id = Column(Integer, ForeignKey("external_persons.id"), nullable=True)
    role_in_meeting    = Column(String, nullable=False)  # RUKOVODILAC/ZAPISNICAR/UCESNIK
    is_planned         = Column(Boolean, nullable=False, default=True)
    attended           = Column(Boolean, nullable=True)   # NULL dok se ne evidentira
    substitute_for_id  = Column(Integer, ForeignKey("meeting_participants.id"), nullable=True)
    recorded_at        = Column(DateTime, nullable=True)  # 72h pravilo

    meeting         = relationship("Meeting", back_populates="participants")
    user            = relationship("User", foreign_keys=[user_id])
    external_person = relationship("ExternalPerson", foreign_keys=[external_person_id])
    substitute_for  = relationship("MeetingParticipant",
                                   remote_side="MeetingParticipant.id",
                                   foreign_keys=[substitute_for_id])


class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    type       = Column(String, nullable=False)  # USPESNO/NEUSPESNO/PROMENA_OD_DRUGOG
    message    = Column(Text, nullable=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user    = relationship("User", foreign_keys=[user_id])
    meeting = relationship("Meeting", back_populates="notifications")