"""Admin Dashboard (Module 5) — statistics and system activity feed."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import require_roles
from backend.models_db import AuditLog, LabReport, Patient, Prescription, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    def count_role(role):
        return db.query(func.count(User.id)).filter(User.role == role).scalar() or 0

    stats = {
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "total_doctors": count_role("doctor"),
        "total_lab_staff": count_role("lab_staff"),
        "total_receptionists": count_role("receptionist"),
        "total_patients": db.query(func.count(Patient.id)).scalar() or 0,
        "total_lab_reports": db.query(func.count(LabReport.id)).scalar() or 0,
        "total_prescriptions": db.query(func.count(Prescription.id)).scalar() or 0,
        "pending_approvals": db.query(func.count(User.id))
        .filter(User.status == "pending")
        .scalar()
        or 0,
    }

    recent_users = (
        db.query(User).order_by(User.created_at.desc()).limit(5).all()
    )
    recent_patients = (
        db.query(Patient).order_by(Patient.created_at.desc()).limit(5).all()
    )
    recent_reports = (
        db.query(LabReport).order_by(LabReport.created_at.desc()).limit(5).all()
    )
    recent_prescriptions = (
        db.query(Prescription).order_by(Prescription.created_at.desc()).limit(5).all()
    )

    return {
        "stats": stats,
        "recent_users": [u.to_public_dict() for u in recent_users],
        "recent_patients": [p.to_dict() for p in recent_patients],
        "recent_lab_reports": [r.to_dict(include_results=False) for r in recent_reports],
        "recent_prescriptions": [p.to_dict() for p in recent_prescriptions],
    }


@router.get("/activity")
def activity(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    logs = (
        db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    )
    return [log.to_dict() for log in logs]
