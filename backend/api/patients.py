"""Patient Record Management (Module 2) — the central record every other
module links back to."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user, log_activity, require_roles
from backend.models_db import LabReport, Patient, Prescription, User
from backend.schemas_system import PatientCreate, PatientUpdate

router = APIRouter(prefix="/api/patients", tags=["patients"])

# Every role can at least search/view patients; only these roles can
# register/edit them (Receptionist front-desk intake, Admin oversight).
_CAN_WRITE = ("admin", "receptionist")


def _next_patient_code(db: Session) -> str:
    count = db.query(func.count(Patient.id)).scalar() or 0
    return f"P-{count + 1:05d}"


@router.get("")
def list_patients(
    q: str | None = Query(None, description="Search by name, patient code, or phone"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Patient)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Patient.full_name.ilike(like))
            | (Patient.patient_code.ilike(like))
            | (Patient.phone.ilike(like))
        )
    patients = query.order_by(Patient.created_at.desc()).all()
    return [p.to_dict() for p in patients]


@router.post("", status_code=201)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_CAN_WRITE)),
):
    patient = Patient(
        patient_code=_next_patient_code(db),
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
        registered_by=user.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    log_activity(db, user, "patient_created", f"Registered patient {patient.full_name}")
    return patient.to_dict()


@router.get("/{patient_id}")
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Full patient record: personal info + lab history + prescription history,
    used to render the central Patient Record view for any role."""
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    reports = (
        db.query(LabReport)
        .filter(LabReport.patient_id == patient_id)
        .order_by(LabReport.created_at.desc())
        .all()
    )
    prescriptions = (
        db.query(Prescription)
        .filter(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
        .all()
    )

    data = patient.to_dict()
    data["lab_reports"] = [r.to_dict() for r in reports]
    data["prescriptions"] = [p.to_dict() for p in prescriptions]
    return data


@router.put("/{patient_id}")
def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_CAN_WRITE)),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    log_activity(db, user, "patient_updated", f"Updated patient {patient.full_name}")
    return patient.to_dict()
