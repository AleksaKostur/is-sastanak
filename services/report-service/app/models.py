from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    Text, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# ── mirror tabele (vlasništvo drugih servisa) ─────────────────────────────

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
    rank         = Column(String)
    work_phone   = Column(String)
    mobile_phone = Column(String)
    email        = Column(String, unique=True, nullable=False)
    password_hash= Column(String, nullable=False)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime)


class MeetingCategory(Base):
    __tablename__ = "meeting_categories"
    id   = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Meeting(Base):
    __tablename__ = "meetings"
    id               = Column(Integer, primary_key=True)
    topic            = Column(String, nullable=False)
    category_id      = Column(Integer, ForeignKey("meeting_categories.id"), nullable=False)
    organizer_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_unit_id      = Column(Integer, ForeignKey("org_units.id"), nullable=False)
    meeting_type     = Column(String, nullable=False)
    recurrence       = Column(String)
    scheduled_at     = Column(DateTime, nullable=False)
    location         = Column(String, nullable=False)
    room             = Column(String, nullable=False)
    status           = Column(String, nullable=False)
    status_reason    = Column(Text)
    act_number       = Column(String)
    act_date         = Column(Date)
    act_organization = Column(String)
    intro            = Column(Text)
    conclusion       = Column(Text)
    created_at       = Column(DateTime)

    category     = relationship("MeetingCategory", foreign_keys=[category_id])
    organizer    = relationship("User", foreign_keys=[organizer_id])
    org_unit     = relationship("OrgUnit", foreign_keys=[org_unit_id])
    agenda_items = relationship("AgendaItem", order_by="AgendaItem.order_no")
    participants = relationship("MeetingParticipant")


class AgendaItem(Base):
    __tablename__ = "agenda_items"
    id         = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    order_no   = Column(Integer, nullable=False)
    title      = Column(String, nullable=False)
    discussion = Column(Text)


class ExternalPerson(Base):
    __tablename__ = "external_persons"
    id           = Column(Integer, primary_key=True)
    organization = Column(String, nullable=False)
    first_name   = Column(String, nullable=False)
    last_name    = Column(String, nullable=False)
    job_title    = Column(String)
    country      = Column(String)
    rank         = Column(String)


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    id                 = Column(Integer, primary_key=True)
    meeting_id         = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id            = Column(Integer, ForeignKey("users.id"), nullable=True)
    external_person_id = Column(Integer, ForeignKey("external_persons.id"), nullable=True)
    role_in_meeting    = Column(String, nullable=False)
    is_planned         = Column(Boolean, nullable=False, default=True)
    attended           = Column(Boolean, nullable=True)
    substitute_for_id  = Column(Integer, ForeignKey("meeting_participants.id"), nullable=True)
    recorded_at        = Column(DateTime, nullable=True)

    user            = relationship("User", foreign_keys=[user_id])
    external_person = relationship("ExternalPerson", foreign_keys=[external_person_id])


# ── tabela u vlasništvu report servisa ────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"
    id           = Column(Integer, primary_key=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type  = Column(String, nullable=False)
    period       = Column(String, nullable=True)
    meeting_id   = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    generated_at = Column(DateTime, server_default=func.now())

    meeting   = relationship("Meeting", foreign_keys=[meeting_id])
    requester = relationship("User", foreign_keys=[requested_by])