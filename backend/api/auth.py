"""
Authentication endpoints: register, login, current-user info.

Workflow implemented (matches the required auth flowchart):
  Signup -> "Account created, please login" -> Login -> validate credentials
  -> check role -> frontend redirects to that role's dashboard.

Self-registered accounts start "pending" when REQUIRE_ADMIN_APPROVAL is on
(default) and cannot log in until an Admin activates them from User
Management. Admin accounts are never created through this public endpoint.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import config
from backend.database import get_db
from backend.deps import get_current_user, log_activity
from backend.models_db import User
from backend.schemas_system import LoginRequest, SignupRequest, TokenResponse
from backend.security import create_access_token, hash_password, verify_password

logger = logging.getLogger("api.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter((User.email == payload.email) | (User.username == payload.username))
        .first()
    )
    if existing:
        field = "email" if existing.email == payload.email else "username"
        raise HTTPException(status_code=409, detail=f"That {field} is already registered.")

    initial_status = "pending" if config.REQUIRE_ADMIN_APPROVAL else "active"

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        status=initial_status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_activity(db, user, "user_registered", f"{user.full_name} registered as {user.role}")

    return {
        "message": (
            "Account created successfully. An administrator must approve your "
            "account before you can log in."
            if initial_status == "pending"
            else "Account created successfully. Please login to continue."
        ),
        "status": initial_status,
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip().lower()
    user = (
        db.query(User)
        .filter((User.email == identifier) | (User.username == payload.identifier.strip()))
        .first()
    )

    invalid = HTTPException(status_code=401, detail="Invalid email/username or password.")
    if not user or not verify_password(payload.password, user.password_hash):
        raise invalid

    if user.status == "pending":
        raise HTTPException(
            status_code=403,
            detail="Your account is awaiting administrator approval.",
        )
    if user.status == "inactive":
        raise HTTPException(
            status_code=403,
            detail="This account has been deactivated. Contact an administrator.",
        )

    token = create_access_token(user.id, user.role, user.username)
    log_activity(db, user, "user_login", f"{user.full_name} logged in")

    return TokenResponse(access_token=token, user=user.to_public_dict())


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user.to_public_dict()
