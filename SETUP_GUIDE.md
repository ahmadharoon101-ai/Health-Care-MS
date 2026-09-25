# AI Laboratory Report Extraction & Patient Management System
### Development output — built on top of the existing Voice Prescription Entry app

This document describes everything added on top of the original `voice-prescription-system`
(the Whisper + fuzzy-medicine-search prescription tool). That original app's HTML/CSS/JS
and Python backend were **not rewritten** — the Whisper pipeline, the `/ws/voice` WebSocket,
`medicine_matcher.py`, and the in-progress prescription draft store in
`backend/api/prescription.py` are untouched. Everything below is additive.

---

## 1. Updated project structure

```
voice-prescription-system/
├── backend/
│   ├── main.py                      [MODIFIED] wires up DB init, seed admin, new routers
│   ├── config.py                    [MODIFIED] added DB/JWT/upload/approval settings
│   ├── requirements.txt             [MODIFIED] added sqlalchemy, bcrypt, PyJWT, pdfplumber, pytesseract, Pillow
│   ├── database.py                  [NEW] SQLAlchemy engine/session/init_db
│   ├── models_db.py                 [NEW] User, Patient, LabReport, LabResult, Prescription, AuditLog
│   ├── security.py                  [NEW] bcrypt hashing + JWT create/verify
│   ├── deps.py                      [NEW] get_current_user, require_roles(...), log_activity(...)
│   ├── schemas_system.py            [NEW] Pydantic request/response models for the new modules
│   ├── seed.py                      [NEW] creates the bootstrap Admin account on first run
│   ├── api/
│   │   ├── auth.py                  [NEW] POST /api/auth/register, /login, GET /me
│   │   ├── users.py                 [NEW] admin User Management CRUD + activate/deactivate
│   │   ├── patients.py              [NEW] Patient Record CRUD (central record)
│   │   ├── laboratory.py            [NEW] upload → extract → review → verify pipeline
│   │   ├── prescriptions.py         [NEW] persisted, patient-linked prescriptions (plural)
│   │   ├── admin.py                 [NEW] dashboard stats + activity feed
│   │   ├── prescription.py          [UNCHANGED] existing in-progress voice-draft store
│   │   └── medicine.py              [UNCHANGED] existing medicine search
│   ├── services/
│   │   ├── lab_extractor.py         [NEW] PDF/OCR text extraction + heuristic row parsing
│   │   ├── whisper_service.py       [UNCHANGED]
│   │   └── medicine_matcher.py      [UNCHANGED]
│   ├── websocket/voice.py           [UNCHANGED]
│   ├── data/                        medicine.csv (existing); app.db (SQLite, created at runtime)
│   └── uploads/lab_reports/         [NEW] uploaded lab report files (created at runtime)
│
└── frontend/
    ├── index.html, js/app.js        [MODIFIED] now requires login, is tied to a Patient
    │                                  via ?patient=<id>, and Save also persists the
    │                                  confirmed prescription to that patient's record.
    ├── js/prescription.js, js/websocket.js, css/style.css   [UNCHANGED]
    ├── css/shell.css                [NEW] sidebar/topbar/cards/badges/forms/auth-page styles
    ├── js/api.js                    [NEW] Auth (token storage/guard) + apiFetch() + toasts
    ├── js/nav.js                    [NEW] role-based sidebar navigation
    ├── login.html                   [NEW]
    ├── signup.html                  [NEW]
    ├── dashboard.html               [NEW] adaptive: Admin gets stats/activity;
    │                                  Doctor/Lab Staff/Receptionist get role quick-actions
    ├── patients.html                [NEW] search + register/edit patients (Module 2)
    ├── patient-record.html          [NEW] the central Patient Record view (Module 2)
    ├── lab-upload.html              [NEW] Module 1: upload + trigger AI/OCR extraction
    ├── lab-review.html              [NEW] Module 1: review/correct rows, then verify
    ├── lab-reports.html             [NEW] list/filter all laboratory reports
    ├── prescriptions-list.html      [NEW] list of saved, patient-linked prescriptions
    ├── users.html                   [NEW] Module 4: Admin user management
    └── activity.html                [NEW] Module 5: system activity feed
```

**Design note on the Admin/Doctor/Lab/Reception "5 dashboards" requirement:** rather than
four near-duplicate dashboard pages, `dashboard.html` is one adaptive page that renders
Admin's stat cards + activity feed, or each other role's quick-action cards, based on the
logged-in user — same requirement, less duplicate code to maintain. Likewise `patients.html`
and `patient-record.html` are shared across roles, with the backend (not just the UI) gating
which actions each role can actually perform.

---

## 2. Database changes

SQLite by default (`backend/data/app.db`, auto-created), swappable via `DATABASE_URL` in
`.env` for Postgres/MySQL. Tables (see `backend/models_db.py`):

- **users** — id, full_name, email, phone, username, password_hash (bcrypt), role
  (`admin`/`doctor`/`lab_staff`/`receptionist`), status (`pending`/`active`/`inactive`), created_at
- **patients** — id, patient_code (auto `P-00001`, ...), full_name, date_of_birth, gender,
  phone, address, registered_by (→ users), created_at
- **laboratory_reports** — id, patient_id (→ patients), uploaded_by (→ users),
  original_filename, stored_path, file_type, report_date, status
  (`uploaded`/`extracted`/`verified`), raw_text, created_at
- **laboratory_results** — id, report_id (→ laboratory_reports), test_name, result_value,
  unit, reference_range, flag (`normal`/`abnormal`), verified
- **prescriptions** — id, patient_id (→ patients), doctor_id (→ users), prescription_text,
  items_json, source (`voice`/`manual`), created_at
- **audit_logs** — id, user_id, actor_name, action, details, created_at (Admin activity feed)

---

## 3. API endpoints (new)

```
POST   /api/auth/register            signup (doctor/lab_staff/receptionist only)
POST   /api/auth/login               returns JWT + user info
GET    /api/auth/me                  current user

GET    /api/users                    admin — list/search/filter
POST   /api/users                    admin — create (skips approval queue)
GET    /api/users/{id}               admin
PUT    /api/users/{id}                admin — edit
PATCH  /api/users/{id}/status        admin — activate/deactivate/pending

GET    /api/patients                 search (?q=)
POST   /api/patients                 admin/receptionist — register
GET    /api/patients/{id}            full record: info + lab history + prescriptions
PUT    /api/patients/{id}            admin/receptionist — update

POST   /api/laboratory/upload?patient_id=   admin/lab_staff — upload file
POST   /api/laboratory/extract/{report_id}  admin/lab_staff — run AI/OCR extraction
GET    /api/laboratory/reports              list/filter (?patient_id=, ?status_filter=)
GET    /api/laboratory/reports/{id}
PUT    /api/laboratory/reports/{id}         admin/lab_staff — save reviewed/corrected rows
POST   /api/laboratory/reports/{id}/verify  admin/lab_staff — finalize, saved to patient record

POST   /api/prescriptions            admin/doctor — save a confirmed prescription
GET    /api/prescriptions            list (?patient_id=)
GET    /api/prescriptions/{id}

GET    /api/admin/dashboard          admin — stats + recent lists
GET    /api/admin/activity           admin — activity feed
```

Existing, untouched: `GET/POST /api/prescription` (singular — in-progress voice draft),
`GET /api/medicines`, `GET /api/medicines/search`, `WS /ws/voice`, `GET /api/health`.

Every endpoint above depends on `get_current_user` and, where relevant,
`require_roles(...)` — **the backend re-checks the role from the verified JWT on every
request**; the sidebar hiding menu items is a UX convenience only, not the real
authorization boundary.

---

## 4. Authentication workflow (implemented as specified)

```
Signup (doctor/lab_staff/receptionist only — no public Admin signup)
  → "Account created successfully" → status = pending (if REQUIRE_ADMIN_APPROVAL=true)
  → Admin activates the account in User Management
  → Login → validate credentials → check role
  → redirect to the role's dashboard (single adaptive dashboard.html)
```

A bootstrap **Admin** account is auto-created on first startup (see `backend/seed.py`):
`username=admin`, `password=ChangeMe123!` unless overridden in `.env`. **Change this
password immediately** — it's a placeholder for first login, not a production credential.

### Role permissions (enforced server-side)

| Action | Admin | Doctor | Lab Staff | Receptionist |
|---|---|---|---|---|
| View dashboard/stats | ✅ (full) | quick actions | quick actions | quick actions |
| Manage users | ✅ | ❌ | ❌ | ❌ |
| Register/edit patients | ✅ | ❌ (view/search only) | ❌ (view/search only) | ✅ |
| Upload/extract lab reports | ✅ | ❌ (view only) | ✅ | ❌ |
| Review/verify lab results | ✅ | ❌ | ✅ | ❌ |
| Voice Prescription / save prescriptions | ✅ | ✅ | ❌ | ❌ |
| View system activity | ✅ | ❌ | ❌ | ❌ |

---

## 5. Setup instructions

```bash
cd voice-prescription-system/backend
python3 -m venv venv && source venv/bin/activate      # optional but recommended
pip install -r requirements.txt --break-system-packages   # or drop the flag in a venv

cp ../.env.example ../.env
# then edit .env — at minimum set a real JWT_SECRET_KEY and SEED_ADMIN_PASSWORD
```

### Environment variables (new, in addition to the existing Whisper/CSV ones)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | sqlite file at `DB_PATH` | swap for Postgres/MySQL in production |
| `JWT_SECRET_KEY` | dev placeholder | **change this** — signs all login sessions |
| `JWT_EXPIRE_MINUTES` | 480 | session length |
| `REQUIRE_ADMIN_APPROVAL` | true | self-registered accounts need Admin activation |
| `SEED_ADMIN_USERNAME/EMAIL/PASSWORD` | admin / admin@clinic.local / ChangeMe123! | bootstrap Admin — **change the password** |
| `UPLOAD_DIR` | `backend/uploads/lab_reports` | where lab report files are stored |
| `MAX_UPLOAD_SIZE_MB` | 15 | upload size limit |

### Optional: OCR for scanned/image lab reports

PDF text-layer extraction (pdfplumber) works out of the box. For scanned PDFs or image
uploads, install the Tesseract OCR binary separately (not pip-installable):

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
```

Without it, image/scanned-PDF uploads still go through Upload → Review, just with an empty
extraction — Lab Staff can add rows manually on the review screen.

### Running

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open `http://localhost:8000` — the frontend is served from the same FastAPI app
(`StaticFiles` mount, unchanged from the original project). Start at `/login.html`.

---

## 6. Testing instructions

1. **Log in as Admin** (`admin` / your `SEED_ADMIN_PASSWORD`) → Dashboard.
2. **Sign up** a Doctor, a Lab Staff, and a Receptionist account from `/signup.html`.
3. Back in Admin → **Users** → Activate each pending account.
4. **Log in as Receptionist** → Patients → Register a patient.
5. **Log in as Lab Staff** → Upload Laboratory Report → pick the patient → upload a PDF/image
   → extraction runs automatically → Review page → correct/add rows → Verify.
6. **Log in as Doctor** → Patients → open the patient → confirm the verified lab results show
   up → New Voice Prescription → (mic requires a local Whisper model file per the original
   project's setup — manual search/add still works without it) → add medicine(s) → Save →
   confirms it now appears on the patient's record and in Prescriptions.
7. **Log in as Admin** → Dashboard stats and System Activity should reflect all of the above.

I ran this exact flow via the API directly (`curl`) end-to-end during development —
registration → approval → RBAC checks (403s where expected) → patient creation → PDF
upload → extraction (heuristic parser correctly read a real generated PDF's Hemoglobin/
WBC/Glucose rows with units, reference ranges, and High/Normal flags) → review → verify →
persisted prescription → full patient record aggregation → admin dashboard/activity feed —
and it worked end-to-end. What I have **not** been able to test in this environment is the
actual browser UI (clicking through the HTML pages) or the mic-based voice flow (no Whisper
model file present here) — please click through those yourself and report anything odd.

---

## 7. Known limitations / next steps

- **Lab extraction is heuristic, not ML-based** — regex parsing over PDF text-layer/OCR
  output. It worked well on a clean synthetic report; real-world scanned reports with
  unusual layouts will need more manual correction. `services/lab_extractor.py` has a
  clearly marked swap-in point if you later want to plug in a real OCR/LLM extraction API.
- **Patient edit** currently reuses the register modal on `patients.html` (search there and
  click a row's edit affordance) rather than a dedicated edit page — functional but minimal.
- **No password-reset flow** yet (out of scope of the original prompt's modules).
- **No automated test suite** — everything above was verified manually via `curl` against a
  running server plus Node/Python syntax checks on every new file; no pytest/Jest tests were
  written.
- Rate limiting, HTTPS/TLS termination, and production-grade file-storage (e.g. S3 instead of
  local disk) are left to your deployment setup, as with the original project.
