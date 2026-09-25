"""
Shared FastAPI dependencies: DB session access, "who is calling", and
role-based authorization guards.

IMPORTANT (security): every protected route must depend on
`get_current_user` (or one of the `require_role(...)` wrappers below) —
the frontend hides menu items per role, but that is a UX convenience only.
The backend re-checks the role from the verified JWT on every request, per
the "never trust frontend role checks alone" requirement.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_db import AuditLog, User
from backend.security import decode_access_token

logger = logging.getLogger("deps")

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or not credentials.credentials:
        raise unauthorized

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise unauthorized

    user = db.get(User, payload.get("sub"))
    if not user:
        raise unauthorized

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active. Contact an administrator.",
        )

    return user


def require_roles(*allowed_roles: str):
    """Dependency factory: `Depends(require_roles('admin', 'doctor'))`."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _checker


def log_activity(db: Session, user: User | None, action: str, details: str = ""):
    """Best-effort audit trail entry for the Admin Dashboard's activity feed."""
    try:
        entry = AuditLog(
            user_id=user.id if user else None,
            actor_name=user.full_name if user else "system",
            action=action,
            details=details[:500],
        )
        db.add(entry)
        db.commit()
    except Exception:  # noqa: BLE001 - audit logging must never break the request
        logger.exception("Failed to write audit log entry for action=%s", action)
        db.rollback()
