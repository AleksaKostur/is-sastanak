from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


# ── Enum validatori ───────────────────────────────────────────────────────

class MeetingType(str, Enum):
    STALNI   = "STALNI"
    VANREDNI = "VANREDNI"

class MeetingStatus(str, Enum):
    PLANIRAN = "PLANIRAN"
    ODRZAN   = "ODRZAN"
    ODLOZEN  = "ODLOZEN"
    OTKAZAN  = "OTKAZAN"

class Recurrence(str, Enum):
    DNEVNI       = "DNEVNI"
    NEDELJNI     = "NEDELJNI"
    MESECNI      = "MESECNI"
    TROMESECNI   = "TROMESECNI"
    SESTOMESECNI = "SESTOMESECNI"
    GODISNJI     = "GODISNJI"

class RoleInMeeting(str, Enum):
    RUKOVODILAC = "RUKOVODILAC"
    ZAPISNICAR  = "ZAPISNICAR"
    UCESNIK     = "UCESNIK"

class NotificationType(str, Enum):
    USPESNO           = "USPESNO"
    NEUSPESNO         = "NEUSPESNO"
    PROMENA_OD_DRUGOG = "PROMENA_OD_DRUGOG"


# ── MeetingCategory ───────────────────────────────────────────────────────

class MeetingCategoryCreate(BaseModel):
    name: str

class MeetingCategoryOut(BaseModel):
    id:   int
    name: str

    model_config = {"from_attributes": True}


# ── Meeting ───────────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    topic:            str
    category_id:      int
    org_unit_id:      int
    meeting_type:     MeetingType
    recurrence:       Optional[Recurrence] = None
    scheduled_at:     datetime
    location:         str
    room:             str
    act_number:       Optional[str] = None
    act_date:         Optional[date] = None
    act_organization: Optional[str] = None

    @model_validator(mode="after")
    def recurrence_required_for_stalni(self):
        if self.meeting_type == MeetingType.STALNI and self.recurrence is None:
            raise ValueError("Za stalni sastanak obavezno je navesti periodičnost (recurrence)")
        if self.meeting_type == MeetingType.VANREDNI and self.recurrence is not None:
            raise ValueError("Vanredni sastanak ne može imati periodičnost")
        return self


class MeetingStatusUpdate(BaseModel):
    status:        MeetingStatus
    status_reason: Optional[str] = None

    @model_validator(mode="after")
    def reason_required_when_not_held(self):
        if self.status in (MeetingStatus.ODLOZEN, MeetingStatus.OTKAZAN):
            if not self.status_reason:
                raise ValueError("Obrazloženje je obavezno pri odlaganju ili otkazivanju")
        return self


class MeetingMinutesUpdate(BaseModel):
    """Zapisnik — unosi Rukovodilac ili Zapisničar tokom/posle sastanka."""
    intro:      Optional[str] = None
    conclusion: Optional[str] = None


class MeetingOut(BaseModel):
    id:               int
    topic:            str
    category_id:      int
    organizer_id:     int
    org_unit_id:      int
    meeting_type:     str
    recurrence:       Optional[str]
    scheduled_at:     datetime
    location:         str
    room:             str
    status:           str
    status_reason:    Optional[str]
    act_number:       Optional[str]
    act_date:         Optional[date]
    act_organization: Optional[str]
    intro:            Optional[str]
    conclusion:       Optional[str]
    created_at:       Optional[datetime]

    model_config = {"from_attributes": True}


# ── AgendaItem ────────────────────────────────────────────────────────────

class AgendaItemCreate(BaseModel):
    order_no: int
    title:    str

class AgendaItemDiscussionUpdate(BaseModel):
    """Diskusija po tački — unosi se tokom vođenja sastanka."""
    discussion: Optional[str] = None

class AgendaItemOut(BaseModel):
    id:         int
    meeting_id: int
    order_no:   int
    title:      str
    discussion: Optional[str]

    model_config = {"from_attributes": True}


# ── AgendaProposal ────────────────────────────────────────────────────────

class AgendaProposalCreate(BaseModel):
    agenda_item_id: int
    content:        str

class AgendaProposalOut(BaseModel):
    id:             int
    agenda_item_id: int
    participant_id: Optional[int]
    content:        str

    model_config = {"from_attributes": True}


# ── ExternalPerson ────────────────────────────────────────────────────────

class ExternalPersonCreate(BaseModel):
    organization: str
    first_name:   str
    last_name:    str
    job_title:    Optional[str] = None
    country:      Optional[str] = None
    rank:         Optional[str] = None

class ExternalPersonOut(BaseModel):
    id:           int
    organization: str
    first_name:   str
    last_name:    str
    job_title:    Optional[str]
    country:      Optional[str]
    rank:         Optional[str]

    model_config = {"from_attributes": True}


# ── MeetingParticipant ────────────────────────────────────────────────────

class ParticipantAdd(BaseModel):
    """Dodavanje učesnika — ili user_id ili external_person_id, ne oba."""
    user_id:            Optional[int] = None
    external_person_id: Optional[int] = None
    role_in_meeting:    RoleInMeeting
    substitute_for_id:  Optional[int] = None

    @model_validator(mode="after")
    def exactly_one_person(self):
        if self.user_id is None and self.external_person_id is None:
            raise ValueError("Mora biti naveden user_id ili external_person_id")
        if self.user_id is not None and self.external_person_id is not None:
            raise ValueError("Ne mogu biti navedeni i user_id i external_person_id istovremeno")
        return self


class AttendanceUpdate(BaseModel):
    """Evidencija prisustva — 72h pravilo se primenjuje na serveru."""
    attended: bool


class ParticipantOut(BaseModel):
    id:                 int
    meeting_id:         int
    user_id:            Optional[int]
    external_person_id: Optional[int]
    role_in_meeting:    str
    is_planned:         bool
    attended:           Optional[bool]
    substitute_for_id:  Optional[int]
    recorded_at:        Optional[datetime]

    model_config = {"from_attributes": True}


# ── Notification ──────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id:         int
    user_id:    int
    meeting_id: Optional[int]
    type:       str
    message:    str
    is_read:    bool
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}