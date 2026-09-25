"""
REST endpoints for managing the in-progress prescription.

Storage is a simple in-memory dict, which is appropriate for a single-doctor
demo/internship workflow (one active prescription session per server
process). Swap this for a real database in production.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException

from backend.schemas import PrescriptionItemIn, PrescriptionItemOut, PrescriptionItemUpdate

logger = logging.getLogger("api.prescription")
router = APIRouter(prefix="/api/prescription", tags=["prescription"])

# id -> PrescriptionItemOut (as dict)
_prescription_store: dict[str, dict] = {}
_confirmed = {"status": False}


@router.get("", response_model=list[PrescriptionItemOut])
def get_prescription():
    return list(_prescription_store.values())


@router.post("", response_model=PrescriptionItemOut)
def add_medicine(item: PrescriptionItemIn):
    if not item.medicine_name or not item.medicine_name.strip():
        raise HTTPException(status_code=400, detail="Medicine name is required.")

    new_id = str(uuid.uuid4())
    record = {"id": new_id, **item.model_dump()}
    _prescription_store[new_id] = record
    _confirmed["status"] = False  # any edit invalidates a prior confirmation
    return record


@router.put("/{item_id}", response_model=PrescriptionItemOut)
def update_medicine(item_id: str, update: PrescriptionItemUpdate):
    if item_id not in _prescription_store:
        raise HTTPException(status_code=404, detail="Prescription item not found.")

    record = _prescription_store[item_id]
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    record.update(updates)
    _prescription_store[item_id] = record
    _confirmed["status"] = False
    return record


@router.delete("/{item_id}")
def delete_medicine(item_id: str):
    if item_id not in _prescription_store:
        raise HTTPException(status_code=404, detail="Prescription item not found.")
    del _prescription_store[item_id]
    _confirmed["status"] = False
    return {"deleted": item_id}


@router.delete("")
def clear_prescription():
    """Remove every medicine from the in-progress prescription (Clear All / New Prescription)."""
    _prescription_store.clear()
    _confirmed["status"] = False
    return {"cleared": True}


@router.post("/confirm")
def confirm_prescription():
    if not _prescription_store:
        raise HTTPException(
            status_code=400,
            detail="Cannot confirm an empty prescription. Add at least one medicine first.",
        )
    _confirmed["status"] = True
    return {"confirmed": True, "items": list(_prescription_store.values())}


@router.get("/status")
def prescription_status():
    return {"confirmed": _confirmed["status"], "item_count": len(_prescription_store)}
