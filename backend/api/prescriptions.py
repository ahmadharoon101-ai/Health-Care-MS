"""
Patient-linked, persisted prescriptions (plural — distinct from the
existing /api/prescription singular endpoints in backend/api/prescription.py,
which manage the in-progress voice-drafting session and are left untouched).

A Doctor builds a draft with the existing Voice Prescription flow
(mic -> speech-to-text -> search -> /api/prescription draft store), and once
they hit "Confirm", the frontend calls POST /api/prescriptions here to save
the final, doctor-approved prescription permanently against the patient's
record.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user, log_activity, require_roles
from backend.models_db import Patient, Prescription, User
from backend.schemas_system import PrescriptionCreate

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])


@router.post("", status_code=201)
def create_prescription(
    payload: PrescriptionCreate,
    db: Session = Depends(get_db),
    doctor: User = Depends(require_roles("admin", "doctor")),
):
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if not payload.items and not (payload.prescription_text or "").strip():
        raise HTTPException(
            status_code=400, detail="Cannot save an empty prescription."
        )

    record = Prescription(
        patient_id=payload.patient_id,
        doctor_id=doctor.id,
        prescription_text=payload.prescription_text,
        items_json=json.dumps(payload.items),
        source=payload.source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_activity(
        db, doctor, "prescription_created", f"Prescription saved for {patient.full_name}"
    )
    return record.to_dict()


@router.get("")
def list_prescriptions(
    patient_id: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Prescription)
    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    records = query.order_by(Prescription.created_at.desc()).all()
    return [r.to_dict() for r in records]


@router.get("/{prescription_id}")
def get_prescription(
    prescription_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    record = db.get(Prescription, prescription_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    return record.to_dict()
