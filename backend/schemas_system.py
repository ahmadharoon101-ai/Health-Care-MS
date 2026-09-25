"""
Pydantic request/response models for the new system modules (auth, users,
patients, laboratory, persisted prescriptions, admin). Kept separate from
the original backend/schemas.py (voice-prescription draft models) so neither
module has to be reshuffled.
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend import config

# A deliberately lenient email pattern (not pydantic's EmailStr / email-validator)
# because that library rejects reserved-looking TLDs such as .local/.internal/
# .test/.lan, which are common and legitimate on hospital intranets that have
# no public DNS at all. We just want "looks like an email", not "is publicly
# deliverable".
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    value = value.strip()
    if not _EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address.")
    return value.lower()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str
    phone: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=60)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    role: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        return _validate_email(v)

    @field_validator("role")
    @classmethod
    def role_must_be_public(cls, v):
        if v not in config.PUBLIC_SIGNUP_ROLES:
            raise ValueError(
                f"role must be one of {config.PUBLIC_SIGNUP_ROLES}"
            )
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match.")
        return v


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or username")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ---------------------------------------------------------------------------
# Users (admin-only management)
# ---------------------------------------------------------------------------
class UserCreateByAdmin(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str
    phone: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=60)
    password: str = Field(..., min_length=8, max_length=128)
    role: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        return _validate_email(v)

    @field_validator("role")
    @classmethod
    def role_valid(cls, v):
        if v not in config.ALL_ROLES:
            raise ValueError(f"role must be one of {config.ALL_ROLES}")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        return _validate_email(v) if v else v


class UserStatusUpdate(BaseModel):
    status: str  # active | inactive | pending

    @field_validator("status")
    @classmethod
    def status_valid(cls, v):
        if v not in ("active", "inactive", "pending"):
            raise ValueError("status must be active, inactive, or pending")
        return v


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------
class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


# ---------------------------------------------------------------------------
# Laboratory
# ---------------------------------------------------------------------------
class LabResultUpdateItem(BaseModel):
    id: Optional[str] = None  # omit/empty for a newly added row during review
    test_name: str
    result_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None


class LabReportReviewUpdate(BaseModel):
    report_date: Optional[str] = None
    results: list[LabResultUpdateItem]


# ---------------------------------------------------------------------------
# Persisted (patient-linked) prescriptions
# ---------------------------------------------------------------------------
class PrescriptionCreate(BaseModel):
    patient_id: str
    prescription_text: Optional[str] = None
    items: list[dict] = Field(default_factory=list)
    source: str = "voice"
