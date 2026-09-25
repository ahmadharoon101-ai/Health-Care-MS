"""
AI Laboratory Report Extraction (Module 1).

Enforced workflow: Upload -> Extract -> Review (edit) -> Verify -> visible
on the Patient Record. A report's `status` field tracks this so the
frontend can never skip a step, and AI output is never treated as final
until a human (Lab Staff / Doctor) verifies it.
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend import config
from backend.database import get_db
from backend.deps import get_current_user, log_activity, require_roles
from backend.models_db import LabReport, LabResult, Patient, User
from backend.schemas_system import LabReportReviewUpdate
from backend.services.lab_extractor import ExtractionUnavailableError, run_extraction

logger = logging.getLogger("api.laboratory")
router = APIRouter(prefix="/api/laboratory", tags=["laboratory"])

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"}


@router.post("/upload", status_code=201)
async def upload_report(
    patient_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "lab_staff")),
):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: "
            f"{', '.join(sorted(config.ALLOWED_UPLOAD_EXTENSIONS))}.",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Max is {config.MAX_UPLOAD_SIZE_MB} MB.",
        )

    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = config.UPLOAD_DIR / safe_name
    dest_path.write_bytes(contents)

    file_type = "pdf" if ext == ".pdf" else "image"

    report = LabReport(
        patient_id=patient_id,
        uploaded_by=user.id,
        original_filename=file.filename,
        stored_path=str(dest_path),
        file_type=file_type,
        status="uploaded",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    log_activity(
        db, user, "lab_report_uploaded", f"Uploaded '{file.filename}' for {patient.full_name}"
    )
    return report.to_dict()


@router.post("/extract/{report_id}")
def extract_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "lab_staff")),
):
    report = db.get(LabReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laboratory report not found.")

    try:
        raw_text, rows = run_extraction(report.stored_path, report.file_type)
    except ExtractionUnavailableError as exc:
        # Still let the report proceed to manual review rather than blocking
        # the whole workflow on a missing OCR dependency.
        report.raw_text = f"[Automatic extraction unavailable: {exc}]"
        report.status = "extracted"
        db.commit()
        return {
            "report": report.to_dict(),
            "warning": str(exc),
        }

    # Replace any previous (re-run) extraction results.
    db.query(LabResult).filter(LabResult.report_id == report.id).delete()

    for row in rows:
        db.add(
            LabResult(
                report_id=report.id,
                test_name=row.test_name,
                result_value=row.result_value,
                unit=row.unit,
                reference_range=row.reference_range,
                flag=row.flag,
                verified=False,
            )
        )

    report.raw_text = raw_text
    report.status = "extracted"
    db.commit()
    db.refresh(report)

    log_activity(
        db, user, "lab_report_extracted", f"Extracted {len(rows)} result(s) from report"
    )

    warning = None
    if not rows:
        warning = (
            "No structured results could be detected automatically. Add rows "
            "manually during review."
        )
    return {"report": report.to_dict(), "warning": warning}


@router.get("/reports")
def list_reports(
    patient_id: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(LabReport)
    if patient_id:
        query = query.filter(LabReport.patient_id == patient_id)
    if status_filter:
        query = query.filter(LabReport.status == status_filter)
    reports = query.order_by(LabReport.created_at.desc()).all()
    return [r.to_dict() for r in reports]


@router.get("/reports/{report_id}")
def get_report(
    report_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
):
    report = db.get(LabReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laboratory report not found.")
    return report.to_dict()


@router.put("/reports/{report_id}")
def review_report(
    report_id: str,
    payload: LabReportReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "lab_staff")),
):
    """Lab Staff reviews/corrects extracted rows before verification. Rows
    without an id are new (manually added during review); existing ids are
    updated; any existing row not present in the payload is removed."""
    report = db.get(LabReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laboratory report not found.")

    if payload.report_date is not None:
        report.report_date = payload.report_date

    kept_ids = set()
    for item in payload.results:
        if item.id:
            existing = db.get(LabResult, item.id)
            if existing and existing.report_id == report.id:
                existing.test_name = item.test_name
                existing.result_value = item.result_value
                existing.unit = item.unit
                existing.reference_range = item.reference_range
                existing.flag = item.flag
                kept_ids.add(existing.id)
                continue
        new_row = LabResult(
            report_id=report.id,
            test_name=item.test_name,
            result_value=item.result_value,
            unit=item.unit,
            reference_range=item.reference_range,
            flag=item.flag,
        )
        db.add(new_row)
        db.flush()
        kept_ids.add(new_row.id)

    for existing in list(report.results):
        if existing.id not in kept_ids:
            db.delete(existing)

    db.commit()
    db.refresh(report)
    log_activity(db, user, "lab_report_reviewed", f"Reviewed report {report.id}")
    return report.to_dict()


@router.post("/reports/{report_id}/verify")
def verify_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "lab_staff")),
):
    report = db.get(LabReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laboratory report not found.")
    if not report.results:
        raise HTTPException(
            status_code=400,
            detail="Cannot verify a report with no results. Add or review results first.",
        )

    for r in report.results:
        r.verified = True
    report.status = "verified"
    db.commit()
    db.refresh(report)

    log_activity(db, user, "lab_report_verified", f"Verified report for patient {report.patient_id}")
    return report.to_dict()
