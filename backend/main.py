"""
FastAPI application entrypoint for the Voice-Based Medicine Prescription
Entry System.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

The Whisper model and the medicine CSV are both loaded once here, at
startup, and reused for every request (see backend/services/).
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.api import admin, auth, laboratory, medicine, patients, prescription, prescriptions, users
from backend.database import SessionLocal, init_db
from backend.seed import seed_admin
from backend.websocket import voice
from backend.services.medicine_matcher import medicine_matcher
from backend.services.whisper_service import whisper_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

app = FastAPI(
    title="Voice-Based Medicine Prescription Entry System",
    description="Internship demo: speech-to-text medicine search and prescription builder.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("Starting up: initializing database...")
    init_db()
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()

    logger.info("Starting up: loading medicine catalog...")
    medicine_matcher.load()
    if not medicine_matcher.is_loaded:
        logger.error(
            "medicine.csv could not be loaded from %s. Search will be unavailable "
            "until this is fixed.",
            config.MEDICINE_CSV_PATH,
        )

    logger.info("Starting up: loading Whisper model (this may take a moment)...")
    whisper_service.load()
    if not whisper_service.is_ready:
        logger.warning(
            "Whisper model is not ready: %s. Voice transcription will be "
            "unavailable until this is fixed.",
            whisper_service.load_error,
        )


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------
app.include_router(medicine.router)
app.include_router(prescription.router)  # existing in-progress voice draft store
app.include_router(voice.router)

# New system modules (auth, RBAC, patients, laboratory, admin dashboard).
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(laboratory.router)
app.include_router(prescriptions.router)  # persisted, patient-linked prescriptions
app.include_router(admin.router)


@app.get("/api/health")
def health_check():
    """Simple health/status endpoint the frontend can use to show setup issues."""
    return {
        "status": "ok",
        "medicine_catalog_loaded": medicine_matcher.is_loaded,
        "medicine_count": medicine_matcher.count() if medicine_matcher.is_loaded else 0,
        "whisper_ready": whisper_service.is_ready,
        "whisper_error": whisper_service.load_error,
    }


# ---------------------------------------------------------------------------
# Serve the static frontend (so the whole app can run from a single server)
# ---------------------------------------------------------------------------
# Resolved as an absolute path (relative to this file, not the process's
# current working directory) so the app serves the UI correctly no matter
# where `uvicorn backend.main:app` is launched from (a script, a Windows
# service, a different shell, etc.).
FRONTEND_DIR = config.BACKEND_DIR.parent / "frontend"
if not FRONTEND_DIR.exists():
    logger.error(
        "Frontend directory not found at %s — the UI will not be served.",
        FRONTEND_DIR,
    )
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
