"""
Central configuration for the Voice-Based Medicine Prescription Entry System.

Every environment-specific value (file paths, model name, CORS origins, etc.)
lives here so the rest of the codebase never hard-codes it. Values can be
overridden with environment variables (see .env.example).
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Medicine CSV configuration
# ---------------------------------------------------------------------------
# Change this path (or set MEDICINE_CSV_PATH env var) once the organization
# provides the real medicine.csv file.
MEDICINE_CSV_PATH = Path(
    os.getenv("MEDICINE_CSV_PATH", str(BACKEND_DIR / "data" / "medicine.csv"))
)

# Candidate column names the loader will look for (case-insensitive).
# The first match found in the CSV is used for each field. This lets the
# same code work whether the CSV has "Medicine Name", "item_name",
# "MedicineName", etc.
MEDICINE_NAME_COLUMNS = ["medicine name", "medicine_name", "item_name", "name", "medicine"]
GENERIC_NAME_COLUMNS = ["generic name", "generic_name", "generic"]
STRENGTH_COLUMNS = ["strength", "dosage", "power"]
FORM_COLUMNS = ["form", "dosage form", "type"]

# ---------------------------------------------------------------------------
# Whisper (local, offline) configuration
# ---------------------------------------------------------------------------
# Name of the whisper model to load (tiny, base, small, medium, large, ...)
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "base")

# Local directory that must contain the pre-downloaded model weights
# (e.g. backend/models/whisper/base.pt). The backend NEVER downloads the
# model automatically — it must already exist here.
WHISPER_MODEL_PATH = Path(
    os.getenv("WHISPER_MODEL_PATH", str(BACKEND_DIR / "models" / "whisper"))
)

# Force CPU inference (no GPU required).
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

# Language hint for transcription. Set to None to let Whisper auto-detect.
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

# ---------------------------------------------------------------------------
# Fuzzy matching configuration
# ---------------------------------------------------------------------------
# Minimum similarity score (0-100) for a medicine to be shown as a match.
MATCH_MIN_SCORE = int(os.getenv("MATCH_MIN_SCORE", "60"))

# Maximum number of matches returned per search.
MATCH_MAX_RESULTS = int(os.getenv("MATCH_MAX_RESULTS", "10"))

# ---------------------------------------------------------------------------
# CORS / server configuration
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ---------------------------------------------------------------------------
# Audio handling
# ---------------------------------------------------------------------------
TEMP_AUDIO_DIR = Path(os.getenv("TEMP_AUDIO_DIR", str(BACKEND_DIR / "temp_audio")))
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_PATH = Path(os.getenv("DB_PATH", str(BACKEND_DIR / "data" / "app.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# ---------------------------------------------------------------------------
# Auth / JWT
# ---------------------------------------------------------------------------
# IMPORTANT: override JWT_SECRET_KEY in your real .env — this default is only
# for local development.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-in-.env")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 hours

# ---------------------------------------------------------------------------
# Registration / approval workflow
# ---------------------------------------------------------------------------
# When true, users who self-register (doctor/lab_staff/receptionist) start
# with status "pending" and an Admin must Activate them from User Management
# before they can log in. When false, new accounts are active immediately.
REQUIRE_ADMIN_APPROVAL = os.getenv("REQUIRE_ADMIN_APPROVAL", "true").lower() == "true"

# Roles allowed to self-register from the public Signup page. Admin accounts
# are never exposed on the public signup form.
PUBLIC_SIGNUP_ROLES = ["doctor", "lab_staff", "receptionist"]
ALL_ROLES = ["admin", "doctor", "lab_staff", "receptionist"]

# Seed admin account, created automatically on first startup if no admin
# exists yet. CHANGE THIS PASSWORD after first login.
SEED_ADMIN_USERNAME = os.getenv("SEED_ADMIN_USERNAME", "admin")
SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@clinic.local")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")

# ---------------------------------------------------------------------------
# File uploads (laboratory reports)
# ---------------------------------------------------------------------------
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads" / "lab_reports")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"}
