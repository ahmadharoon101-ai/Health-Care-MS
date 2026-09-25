"""
SQLAlchemy ORM models for the AI Laboratory Report Extraction & Patient
Management System.

Relationships:

    User (admin / doctor / lab_staff / receptionist)

    Patient
      +-- LabReport (uploaded document)
      |     +-- LabResult (one row per extracted test)
      +-- Prescription

    AuditLog — append-only system activity feed (Admin Dashboard).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_uuid)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True, index=True)
    phone = Column(String(40), nullable=True)
    username = Column(String(60), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin | doctor | lab_staff | receptionist
    # pending  -> awaiting admin approval (self-registered, approval required)
    # active   -> can log in
    # inactive -> deactivated by admin, cannot log in
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    patients_registered = relationship("Patient", back_populates="registered_by_user")
    lab_reports_uploaded = relationship("LabReport", back_populates="uploaded_by_user")
    prescriptions = relationship("Prescription", back_populates="doctor")

    def to_public_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "username": self.username,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(32), primary_key=True, default=_uuid)
    patient_code = Column(String(20), nullable=False, unique=True, index=True)
    full_name = Column(String(120), nullable=False)
    date_of_birth = Column(String(10), nullable=True)  # YYYY-MM-DD
    gender = Column(String(20), nullable=True)
    phone = Column(String(40), nullable=True)
    address = Column(Text, nullable=True)
    registered_by = Column(String(32), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    registered_by_user = relationship("User", back_populates="patients_registered")
    lab_reports = relationship(
        "LabReport", back_populates="patient", cascade="all, delete-orphan"
    )
    prescriptions = relationship(
        "Prescription", back_populates="patient", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_code": self.patient_code,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "phone": self.phone,
            "address": self.address,
            "registered_by": self.registered_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LabReport(Base):
    __tablename__ = "laboratory_reports"

    id = Column(String(32), primary_key=True, default=_uuid)
    patient_id = Column(String(32), ForeignKey("patients.id"), nullable=False)
    uploaded_by = Column(String(32), ForeignKey("users.id"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf | image
    report_date = Column(String(10), nullable=True)  # YYYY-MM-DD, editable during review
    # uploaded  -> file saved, not yet processed
    # extracted -> AI/OCR ran, awaiting human review
    # verified  -> lab staff confirmed the results are correct
    status = Column(String(20), nullable=False, default="uploaded")
    raw_text = Column(Text, nullable=True)  # full OCR/text-extraction dump, for audit/debug
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="lab_reports")
    uploaded_by_user = relationship("User", back_populates="lab_reports_uploaded")
    results = relationship(
        "LabResult", back_populates="report", cascade="all, delete-orphan"
    )

    def to_dict(self, include_results=True):
        data = {
            "id": self.id,
            "patient_id": self.patient_id,
            "uploaded_by": self.uploaded_by,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "report_date": self.report_date,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_results:
            data["results"] = [r.to_dict() for r in self.results]
        return data


class LabResult(Base):
    __tablename__ = "laboratory_results"

    id = Column(String(32), primary_key=True, default=_uuid)
    report_id = Column(String(32), ForeignKey("laboratory_reports.id"), nullable=False)
    test_name = Column(String(200), nullable=False)
    result_value = Column(String(100), nullable=True)
    unit = Column(String(40), nullable=True)
    reference_range = Column(String(100), nullable=True)
    flag = Column(String(20), nullable=True)  # normal | abnormal | unknown
    # Was this row auto-extracted (false) or has a human already confirmed/
    # edited it (true)? Separate from the parent report's overall status.
    verified = Column(Boolean, default=False)

    report = relationship("LabReport", back_populates="results")

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "flag": self.flag,
            "verified": self.verified,
        }


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(String(32), primary_key=True, default=_uuid)
    patient_id = Column(String(32), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String(32), ForeignKey("users.id"), nullable=True)
    prescription_text = Column(Text, nullable=True)  # free-text summary (e.g. from voice draft)
    items_json = Column(Text, nullable=True)  # JSON list of {medicine, strength, frequency, ...}
    source = Column(String(20), default="voice")  # voice | manual
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("User", back_populates="prescriptions")

    def to_dict(self):
        import json

        try:
            items = json.loads(self.items_json) if self.items_json else []
        except (TypeError, ValueError):
            items = []
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor.full_name if self.doctor else None,
            "prescription_text": self.prescription_text,
            "items": items,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=True)
    actor_name = Column(String(120), nullable=True)
    action = Column(String(60), nullable=False)
    details = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "actor_name": self.actor_name,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
