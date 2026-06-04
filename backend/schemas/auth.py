"""
Pydantic schemas for authentication endpoints.

SECURITY: the public RegisterRequest never accepts a privileged role. Whatever a
client sends is ignored — registration always produces a `patient`. Privileged
accounts (doctor / admin) are created exclusively through the admin path.
"""

import re
from datetime import datetime, date
from typing import Literal, Optional
from pydantic import BaseModel, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: str) -> str:
    if not _EMAIL_RE.match(v):
        raise ValueError("Enter a valid email address")
    return v.lower()


def _validate_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one number")
    return v


class RegisterRequest(BaseModel):
    """Public self-registration. Role is intentionally NOT accepted here.

    Any `role` key in the request body is ignored (extra fields permitted but
    dropped) so a client can never self-provision a doctor or admin account.
    """

    email: str
    password: str
    full_name: str

    # Optional patient profile fields persisted onto the User record.
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None

    # Allow (and ignore) any extra client-supplied fields such as `role`.
    model_config = {"extra": "ignore"}

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Full name is required")
        return v.strip()


class UserCreate(RegisterRequest):
    """Alias retained for the spine contract."""


class AdminUserCreate(BaseModel):
    """Privileged account creation (admin-only path).

    Admins may set any role and, for doctors, the specialty + license number.
    """

    email: str
    password: str
    full_name: str
    role: Literal["doctor", "patient", "admin"] = "patient"

    # Patient profile
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None

    # Doctor profile
    specialty: Optional[str] = None
    license_number: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Full name is required")
        return v.strip()


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        return _validate_email(v)


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
