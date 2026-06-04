"""
Authentication router: register, login, me.

Security posture:
- Public /register ALWAYS creates a `patient`. A client cannot self-assign a
  privileged role — the role is hard-coded server side, never read from the body.
- Login returns a single generic message for both "no such email" and "wrong
  password" so the endpoint does not reveal whether an email is registered.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserPublic
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Single generic credential error — identical for unknown email, wrong password,
# and (deliberately) does not distinguish a disabled account at this layer beyond
# a dedicated 403 for accounts that authenticated successfully but are disabled.
_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new PATIENT and return a JWT token.

    The role is forced to "patient" regardless of any client input. Doctor/admin
    accounts are provisioned only through the admin panel.
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="patient",  # SECURITY: never trust client-supplied role on public register
        date_of_birth=payload.date_of_birth,
        blood_group=payload.blood_group,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/password and return a JWT token."""
    user = db.query(User).filter(User.email == payload.email).first()

    # Same generic error whether the email is unknown or the password is wrong —
    # prevents user enumeration. Run verify_password against a dummy hash when the
    # user is missing so timing does not leak account existence.
    if not user:
        # Constant-time-ish guard: still perform a hash comparison.
        verify_password(payload.password, "$2b$12$" + "0" * 53)
        raise _INVALID_CREDENTIALS

    if not verify_password(payload.password, user.hashed_password):
        raise _INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserPublic.model_validate(current_user)
