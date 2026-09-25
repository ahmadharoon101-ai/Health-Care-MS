# Rx Voice — Voice-Based Medicine Prescription Entry System

An internship-demo web app that lets a doctor speak a medicine name, get
fuzzy-matched suggestions from `medicine.csv`, build a prescription, and
print it — all running locally with an offline Whisper model (no cloud
speech APIs).

```
Doctor speaks → Whisper (local) → medicine.csv fuzzy search → doctor
selects/edits/adds → doctor confirms → doctor prints
```

---

## 1. Architecture overview

**Backend — FastAPI (Python)**
- `backend/main.py` — app entrypoint; loads the medicine catalog and the
  Whisper model once at startup, mounts the REST routers, the `/ws/voice`
  WebSocket, and serves the frontend as static files.
- `backend/services/medicine_matcher.py` — reads `medicine.csv` into memory
  once and answers every search from RAM using RapidFuzz. Column names are
  auto-detected (`Medicine Name`, `item_name`, etc.) so it adapts to
  whatever CSV the organization provides.
- `backend/services/whisper_service.py` — loads a local Whisper model file
  once at startup and reuses it for every transcription. It never
  downloads a model automatically.
- `backend/websocket/voice.py` — the `/ws/voice` endpoint. Receives binary
  audio chunks while the doctor is recording, and on `stop`, transcribes
  the buffered audio and sends the recognized text back.
- `backend/api/medicine.py` — `GET /api/medicines`, `GET /api/medicines/search`.
- `backend/api/prescription.py` — CRUD + confirm endpoints for the
  in-progress prescription (in-memory store, one session per server
  process — swap for a database in production).
- `backend/config.py` — every path/threshold/model name in one place.

**Frontend — plain HTML/CSS/JS (no framework), Bootstrap-free custom UI**
- `frontend/index.html` / `css/style.css` — the prescription-pad styled UI.
- `frontend/js/websocket.js` — `VoiceClient`: wraps `MediaRecorder` and the
  `/ws/voice` WebSocket (mic permission, chunk streaming, start/stop/cancel).
- `frontend/js/prescription.js` — `PrescriptionStore`: talks to
  `/api/prescription` and renders the prescription table.
- `frontend/js/app.js` — wires the mic button, search box, results table,
  manual-entry modal, confirm/print buttons, and toast notifications
  together.

**Data flow for voice entry**
```
mic button → getUserMedia → MediaRecorder (webm/opus, 250ms chunks)
  → WebSocket /ws/voice → backend buffers chunks
  → "stop" → backend writes temp file → whisper_service.transcribe()
  → {"type":"result","text":"Panadol"} → frontend fills search box
  → GET /api/medicines/search?q=Panadol → results table with Match %
  → doctor clicks "Select" → POST /api/prescription
```

The doctor always makes the final call: nothing is added to the
prescription automatically from voice or fuzzy-match results.

---

## 2. Folder structure

```
voice-prescription-system/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── api/
│   │   ├── medicine.py
│   │   └── prescription.py
│   ├── websocket/
│   │   └── voice.py
│   ├── services/
│   │   ├── whisper_service.py
│   │   └── medicine_matcher.py
│   ├── models/
│   │   └── whisper/            ← put base.pt (or your chosen model) here
│   ├── data/
│   │   └── medicine.csv        ← your organization's file goes here
│   └── utils/
│       └── text_normalizer.py
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/{app.js, websocket.js, prescription.js}
├── .env.example
└── README.md
```

---

## 3. Setup (Windows)

### 3.1 Prerequisites
- Python 3.10–3.11
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) on your `PATH` (required by
  Whisper to decode the recorded audio) — download a build, unzip it, and
  add the `bin` folder to your Windows `PATH` environment variable.
- A working microphone and a Chromium-based browser (Chrome/Edge) — voice
  capture uses `MediaRecorder`, which needs `https://` or `http://localhost`.

### 3.2 Install dependencies

```powershell
cd voice-prescription-system
python -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
```

If PyTorch fails to install automatically, install the CPU build explicitly:

```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 3.3 Add the medicine CSV

Copy the organization's file to:

```
backend\data\medicine.csv
```

(Already present in this build — the loader auto-detected an `item_name`
column, since that's the only column your file has.) If you receive a
richer CSV later with `Medicine Name / Generic Name / Strength / Form`
columns, just drop it in the same place — no code changes needed.

### 3.4 Add the local Whisper model

Whisper is never downloaded automatically. One time, on any machine with
internet access:

```powershell
python -c "import whisper; whisper.load_model('base', download_root='backend/models/whisper')"
```

Then copy the resulting `backend\models\whisper\base.pt` onto the machine
that will actually run the app (it can be fully offline after this step).

### 3.5 Configure (optional)

```powershell
copy .env.example .env
```

Edit `.env` if you want a different model size, CSV path, or match
threshold. Defaults work out of the box.

### 3.6 Run

```powershell
cd voice-prescription-system
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

---

## 4. Using the app

1. Press the microphone button and say a medicine name; press it again to
   stop. The recognized text appears and a search runs automatically.
2. Review the **Matching medicines** table — each row shows a **Match %**
   (RapidFuzz similarity, not a clinical claim). Click **Select** to add a
   medicine to the prescription.
3. Use **+ Add medicine manually** for anything not in the catalog, or to
   set dosage/frequency/duration/instructions on any entry.
4. **Edit** or **Delete** any row in the prescription table before
   confirming.
5. Click **Confirm prescription** once everything is correct.
6. Click **Print prescription** — the print view hides all controls and
   shows only the clean prescription for the printer.

---

## 5. Error handling reference

| Situation | What the doctor sees |
|---|---|
| Microphone permission denied | "Microphone permission is required to use voice input." |
| WebSocket disconnected | "Voice connection was lost. Please try again." |
| Whisper fails / model missing | "Unable to process the voice input. Please try again." (backend logs the real cause) |
| No fuzzy match found | "No closely matching medicine was found. You can add the medicine manually." |
| Empty/no speech detected | No search is run; "No speech was detected. Please try again." |
| `medicine.csv` missing | Backend logs a clear error; API returns 503 with a friendly message; header status pill turns amber. |

The header status pill (top-right) always shows whether the medicine
catalog and the voice model are ready — use it to quickly confirm setup on
a new machine.

---

## 6. Notes for the internship team

- Prescription storage is in-memory (`backend/api/prescription.py`) — fine
  for a single-doctor demo; swap in a real database for multi-user/
  production use.
- Manual additions never modify `medicine.csv`.
- Everything needed to run offline (once the model file is copied over) —
  no OpenAI/Google/Azure speech APIs are used anywhere.
- To change the fuzzy-match sensitivity, adjust `MATCH_MIN_SCORE` in `.env`
  or `backend/config.py`.
