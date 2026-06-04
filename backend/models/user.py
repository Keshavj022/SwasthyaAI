"""
User model for authentication and role-based access control.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="patient")  # doctor | patient | admin
    is_active = Column(Boolean, default=True, nullable=False)

    # Patient profile fields (collected at registration; nullable for other roles)
    date_of_birth = Column(Date, nullable=True)
    blood_group = Column(String, nullable=True)

    # Doctor profile fields (set via the admin-created doctor path; nullable otherwise)
    specialty = Column(String, nullable=True)
    license_number = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
