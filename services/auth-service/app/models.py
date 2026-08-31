from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class OrgUnit(Base):
    __tablename__ = "org_units"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("org_units.id"), nullable=True)

    parent = relationship("OrgUnit", remote_side=[id], back_populates="children")
    children = relationship("OrgUnit", back_populates="parent")
    users = relationship("User", back_populates="org_unit")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    org_unit_id = Column(Integer, ForeignKey("org_units.id"), nullable=False)
    first_name = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    jmbg = Column(String(13), unique=True, nullable=False)
    job_title = Column(String, nullable=False)
    rank = Column(String)
    work_phone = Column(String, nullable=True)
    mobile_phone = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org_unit = relationship("OrgUnit", back_populates="users")
    roles = relationship("UserRole", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    user_roles = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    org_unit_id = Column(Integer, ForeignKey("org_units.id"), nullable=True)
    is_permanent = Column(Boolean, nullable=False, default=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    note = Column(Text, nullable=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")
    org_unit = relationship("OrgUnit")