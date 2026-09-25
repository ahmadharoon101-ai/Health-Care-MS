"""Pydantic models shared across the API layer."""

from typing import Optional
from pydantic import BaseModel, Field


class MedicineMatch(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    match_score: float = Field(..., description="Similarity percentage, 0-100")


class SearchResponse(BaseModel):
    query: str
    results: list[MedicineMatch]
    message: Optional[str] = None


class PrescriptionItemIn(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    source: str = Field("manual", description="'voice' or 'manual'")
    match_score: Optional[float] = None


class PrescriptionItemOut(PrescriptionItemIn):
    id: str


class PrescriptionItemUpdate(BaseModel):
    medicine_name: Optional[str] = None
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
