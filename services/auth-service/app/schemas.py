from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime


# --- OrgUnit ---

class OrgUnitBase(BaseModel):
    name: str
    parent_id: Optional[int] = None

class OrgUnitCreate(OrgUnitBase):
    pass

class OrgUnitOut(OrgUnitBase):
    id: int

    model_config = {"from_attributes": True}


# --- User ---

class UserCreate(BaseModel):
    org_unit_id: int
    first_name: str
    father_name: str
    last_name: str
    jmbg: str
    job_title: str
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    email: EmailStr
    password: str  # plain, hešira se u servisu

    @field_validator("jmbg")
    @classmethod
    def jmbg_length(cls, v: str) -> str:
        if len(v) != 13:
            raise ValueError("JMBG mora imati 13 cifara")
        return v

class UserOut(BaseModel):
    id: int
    org_unit_id: int
    first_name: str
    father_name: str
    last_name: str
    jmbg: str
    job_title: str
    work_phone: Optional[str]
    mobile_phone: Optional[str]
    email: str
    is_active: bool
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    father_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


# --- Auth ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str


# --- UserRole ---

class UserRoleAssign(BaseModel):
    user_id: int
    role_id: int
    org_unit_id: Optional[int] = None
    is_permanent: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    note: Optional[str] = None

class UserRoleOut(BaseModel):
    id: int
    user_id: int
    role_id: int
    org_unit_id: Optional[int]
    is_permanent: bool
    valid_from: Optional[date]
    valid_to: Optional[date]
    note: Optional[str]

    model_config = {"from_attributes": True}