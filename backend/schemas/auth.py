"""
Pydantic schemas for authentication endpoints.
"""

import re
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: str) -> str:
    if not _EMAIL_RE.match(v):
        raise ValueError("Enter a valid email address")
    return v.lower()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: Literal["doctor", "patient", "admin"] = "patient"

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserCreate(RegisterRequest):
    pass


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
