"""User Management — Admin only (Module 4)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user, log_activity, require_roles
from backend.models_db import User
from backend.schemas_system import UserCreateByAdmin, UserStatusUpdate, UserUpdate
from backend.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(
    role: str | None = Query(None),
    q: str | None = Query(None, description="Search by name, email, or username"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (User.full_name.ilike(like))
            | (User.email.ilike(like))
            | (User.username.ilike(like))
        )
    users = query.order_by(User.created_at.desc()).all()
    return [u.to_public_dict() for u in users]


@router.post("", status_code=201)
def create_user(
    payload: UserCreateByAdmin,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    existing = (
        db.query(User)
        .filter((User.email == payload.email) | (User.username == payload.username))
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already exists.")

    user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        phone=payload.phone,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        status="active",  # admin-created accounts skip the approval queue
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_activity(db, admin, "user_created", f"Admin created {user.role} account {user.username}")
    return user.to_public_dict()


@router.get("/{user_id}")
def get_user(
    user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_roles("admin"))
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user.to_public_dict()


@router.put("/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    log_activity(db, admin, "user_updated", f"Admin updated user {user.username}")
    return user.to_public_dict()


@router.patch("/{user_id}/status")
def set_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id and payload.status != "active":
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")

    user.status = payload.status
    db.commit()
    db.refresh(user)
    log_activity(
        db, admin, "user_status_changed", f"{user.username} set to {payload.status}"
    )
    return user.to_public_dict()
