# 🏥 Health Care Management System

A full-stack **Health Care Management System** designed to streamline patient record management, laboratory report processing, medicine prescription, authentication, and administrative operations through a centralized web-based platform.

The system combines **AI-powered laboratory report extraction**, **voice-based prescription entry**, **medicine searching**, **patient management**, and **role-based access control** into a single healthcare workflow.

---

## 📌 Project Overview

The Health Care Management System provides healthcare staff with a centralized platform for managing patient information and healthcare-related operations.

### Main Modules

* 👤 User Management
* 🔐 Authentication & Role-Based Access Control
* 🧑‍⚕️ Patient Record Management
* 🧪 AI Laboratory Report Extraction
* 🎙️ Voice Prescription
* 💊 Medicine Search & Prescription Management
* 📊 Admin Dashboard

The frontend communicates with a **Python/FastAPI backend** through REST APIs. The backend manages application logic, authentication, AI processing, medicine searching, database operations, and prescription functionality.

---

# ✨ Main Features

## 🔐 Authentication & User Management

* User registration
* Secure login
* Logout
* Role-based access control
* User account management
* Protected application routes
* Authentication validation

---

## 🧑‍⚕️ Patient Record Management

The patient management module allows authorized users to manage patient information.

Features include:

* Create patient records
* View patient information
* Update patient records
* Search patient records
* Manage patient details
* Retrieve healthcare information
* Maintain centralized patient records

---

## 🧪 AI Laboratory Report Extraction

The system can process laboratory reports and extract relevant patient and report information.

### Workflow

```text
Upload Laboratory Report
          ↓
Backend Processing
          ↓
AI Report Extraction
          ↓
Extract Patient Information
          ↓
Review Extracted Information
          ↓
Save Patient Record
```

The module is designed to reduce manual data entry and make laboratory information easier to manage.

---

# 🎙️ Voice Prescription

The Voice Prescription module allows healthcare professionals to enter medicine information using voice input.

### Workflow

```text
Doctor Voice Input
        ↓
Audio Recording
        ↓
Whisper Model
        ↓
Speech-to-Text
        ↓
Recognized Text
        ↓
Medicine Search
        ↓
Fuzzy Medicine Matching
        ↓
Medicine Selection
        ↓
Prescription Management
        ↓
Prescription Generation
```

The voice module uses **OpenAI Whisper** for speech-to-text processing.

---

# 💊 Medicine Search & Prescription Management

The medicine module provides medicine searching and prescription management functionality.

Features include:

* Medicine search
* Medicine name matching
* Fuzzy medicine matching
* Matching percentage
* Medicine selection
* Manual medicine entry
* Prescription item management
* Prescription generation
* Prescription printing/PDF workflow

The medicine catalog is loaded from the project's medicine dataset.

---

# 📊 Admin Dashboard

The Admin Dashboard provides administrative functionality for managing the healthcare system.

Administrative functionality may include:

* User management
* Patient management
* System records
* Healthcare modules
* Administrative information
* Application activity

Access to administrative functions is controlled through user roles and permissions.

---

# 🏗️ System Architecture

```text
┌───────────────────────────────────────────┐
│                 FRONTEND                  │
│                                           │
│           HTML / CSS / JavaScript         │
│                                           │
│          User Interface & Pages           │
└─────────────────────┬─────────────────────┘
                      │
                      │ REST API / HTTP
                      ▼
┌───────────────────────────────────────────┐
│                 BACKEND                   │
│                                           │
│              Python + FastAPI             │
│                                           │
│ Authentication                            │
│ Patient Management                        │
│ Laboratory Processing                     │
│ Voice / Speech Processing                 │
│ Medicine Search                           │
│ Prescription Management                   │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│                 DATABASE                  │
│                                           │
│ Users                                     │
│ Patients                                  │
│ Prescriptions                             │
│ Laboratory Records                        │
│ System Data                               │
└───────────────────────────────────────────┘
```

---

# 🛠️ Technologies Used

## Frontend

* HTML5
* CSS3
* JavaScript
* Responsive Web Design
* REST API integration

## Backend

* **Python**
* **FastAPI**
* **Uvicorn**
* **Pydantic**
* **SQLAlchemy**
* REST APIs

## AI & Speech Processing

* OpenAI Whisper
* Speech-to-Text
* AI-based laboratory report extraction
* Fuzzy medicine matching

## Database

* SQL Database
* SQLAlchemy ORM

## Development Tools

* Visual Studio Code
* Git
* GitHub
* Python Virtual Environment

---

# 📁 Project Structure

```text
Health-Care-MS/
│
├── backend/
│   ├── data/
│   │   └── medicine.csv
│   │
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   │
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── requirements.txt
│
├── frontend/
│   ├── assets/
│   ├── css/
│   ├── js/
│   ├── pages/
│   └── index.html
│
├── .env.example
├── .gitignore
├── README.md
└── SETUP_GUIDE.md
```

> The exact folders may vary depending on the current implementation.

---

# 🚀 How to Run the Project

Follow the steps below to run the **Python backend and HTML/CSS/JavaScript frontend locally**.

---

# 1. Clone the Repository

Clone the project:

```bash
git clone https://github.com/ahmadharoon101-ai/Health-Care-MS.git
```

Enter the project directory:

```bash
cd Health-Care-MS
```

---

# 🐍 2. Backend — Python + FastAPI

The backend is developed using **Python and FastAPI**.

## Step 1 — Create Virtual Environment

From the project root:

```powershell
python -m venv venv
```

---

## Step 2 — Activate Virtual Environment

On Windows PowerShell:

```powershell
venv\Scripts\activate
```

You should see something similar to:

```text
(venv) PS C:\...\Health-Care-MS>
```

---

## Step 3 — Install Python Dependencies

Install the required backend packages:

```powershell
pip install -r backend\requirements.txt
```

---

## Step 4 — Configure Environment Variables

Create the local `.env` file from the example file:

```powershell
copy .env.example .env
```

Open `.env` and configure the required local settings.

### ⚠️ Security

Never upload the following to GitHub:

```text
.env
API keys
Passwords
Access tokens
Database credentials
Private keys
Authentication secrets
```

Only placeholder values should be included in `.env.example`.

---

# 🎙️ 3. Whisper Model Setup

The Voice Prescription module uses **OpenAI Whisper** for speech-to-text.

If the project contains a dedicated Whisper model download script, run:

```powershell
python backend\download_model.py
```

If the project uses the Whisper Python package to download and initialize the model, run:

```powershell
python -c "import whisper; whisper.load_model('base')"
```

This initializes the **base Whisper model** and downloads it if it is not already available locally.

### Available Whisper Models

```text
tiny
base
small
medium
large
```

For example:

```powershell
python -c "import whisper; whisper.load_model('base')"
```

The Whisper model is normally stored in the local model cache.

### ⚠️ Do Not Upload Model Files

Large downloaded Whisper model files should not be committed to GitHub unless there is a specific reason to distribute them.

---

# ▶️ 4. Start the Python Backend

From the **project root**, run:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

FastAPI interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Keep this terminal running.

---

# 🌐 5. Frontend — HTML, CSS & JavaScript

The frontend is developed using:

* HTML
* CSS
* JavaScript

The frontend can be run using **VS Code Live Server**.

---

## Step 1 — Open a Second Terminal

Keep the Python backend running.

Open another terminal in VS Code:

```powershell
cd frontend
```

---

## Step 2 — Start Frontend Using Live Server

In VS Code:

1. Open the `frontend` folder.
2. Open `index.html`.
3. Right-click `index.html`.
4. Select **Open with Live Server**.
5. The application will open in your browser.

The frontend will normally run at:

```text
http://127.0.0.1:5500
```

or:

```text
http://localhost:5500
```

The exact port depends on your Live Server configuration.

---

# 🔗 6. Run Frontend and Backend Together

Both the frontend and backend should be running at the same time.

### Terminal 1 — Python Backend

```powershell
cd Health-Care-MS
venv\Scripts\activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 — Frontend

```powershell
cd Health-Care-MS\frontend
```

Then open `index.html` using **Live Server**.

---

# 🔄 Frontend + Backend Communication

```text
┌──────────────────────────┐
│       FRONTEND           │
│                          │
│ HTML + CSS + JavaScript  │
│ localhost:5500           │
└────────────┬─────────────┘
             │
             │ REST API / HTTP
             ▼
┌──────────────────────────┐
│     PYTHON BACKEND       │
│                          │
│ Python + FastAPI         │
│ localhost:8000           │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│        DATABASE          │
└──────────────────────────┘
```

---

# 🧪 7. Verify the Installation

After starting the backend, open:

```text
http://127.0.0.1:8000/docs
```

If the Swagger interface loads, the FastAPI backend is running.

Then open the frontend using the Live Server URL.

Check that:

* Login page loads
* Authentication works
* Dashboard loads
* Patient records can be accessed
* Laboratory report module opens
* Voice Prescription module opens
* Medicine search works
* Prescription functionality works
* Admin functionality works according to the assigned role

---

# 🎙️ Voice Prescription Workflow

```text
┌───────────────────────┐
│ Doctor Voice Input    │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Audio Recording       │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Whisper Model         │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Speech-to-Text        │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Recognized Text       │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Medicine Search       │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Fuzzy Matching        │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Select Medicine       │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Prescription          │
│ Management             │
└───────────────────────┘
```

---

# 🧪 Laboratory Report Workflow

```text
Upload Report
      │
      ▼
Report Processing
      │
      ▼
AI Extraction
      │
      ▼
Extract Patient Information
      │
      ▼
Review Extracted Data
      │
      ▼
Save Record
      │
      ▼
Patient Record Management
```

---

# 👥 User Roles

The system uses role-based access control.

| Role                      | Main Responsibilities                 |
| ------------------------- | ------------------------------------- |
| Admin                     | System and user management            |
| Doctor / Healthcare Staff | Patient and prescription operations   |
| Authorized User           | Access permitted healthcare functions |

Actual permissions depend on the application's configuration.

---

# 📋 Medicine Dataset

The medicine catalog is stored in:

```text
backend/
└── data/
    └── medicine.csv
```

The backend loads the medicine catalog when the application starts.

The dataset is used for:

* Medicine searching
* Medicine matching
* Fuzzy matching
* Prescription selection

---

# 🔌 API Integration

The frontend communicates with the Python backend through REST APIs.

```text
Frontend
   │
   │ HTTP Request
   ▼
FastAPI Endpoint
   │
   ▼
Business Logic
   │
   ├── Patient Services
   ├── Laboratory Services
   ├── Voice Services
   ├── Medicine Services
   └── Authentication
   │
   ▼
Database / AI Services
   │
   ▼
JSON Response
   │
   ▼
Frontend
```

---

# 📖 FastAPI API Documentation

FastAPI provides interactive Swagger documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

Swagger can be used to:

* View available endpoints
* Inspect API requests
* Test API endpoints
* View request parameters
* View API responses

---

# 🔒 Security

The repository is intended for safe public source-code sharing.

Sensitive configuration must remain local.

## Never Commit

```text
.env
.env.local
.env.production
credentials.json
API keys
Private keys
Database passwords
Access tokens
Authentication secrets
```

Before committing changes, always run:

```powershell
git status
```

Make sure sensitive files are not listed.

---

# 🧪 Testing

The system can be tested across the following areas.

## Authentication

* User registration
* Login
* Invalid login
* Logout
* Unauthorized access
* Role-based access

## Patient Management

* Add patient
* View patient
* Update patient
* Search patient
* Invalid patient data

## Laboratory Reports

* Upload report
* Process report
* Extract information
* Review extracted data
* Save patient information

## Voice Prescription

* Start recording
* Stop recording
* Speech-to-text
* Medicine search
* Medicine matching
* Select medicine
* Add medicine
* Generate prescription

## Administration

* Admin login
* User management
* Record management
* Role-based access

---

# 📌 Project Components

The Health Care Management System integrates:

```text
Authentication
      +
User Management
      +
Patient Records
      +
Laboratory Report Extraction
      +
Voice Prescription
      +
Medicine Search
      +
Prescription Management
      +
Admin Dashboard
      +
Database
      +
REST APIs
```

---

# 🎯 Project Objectives

1. Centralize healthcare information.
2. Reduce repetitive manual data entry.
3. Simplify patient record management.
4. Assist healthcare staff with voice-based prescription entry.
5. Automate extraction of laboratory report information.
6. Provide medicine search and matching functionality.
7. Implement authentication and role-based access.
8. Provide administrative management capabilities.
9. Integrate frontend, backend, AI, and database components.

---

# 🚀 Future Improvements

Potential future improvements include:

* Advanced patient history and analytics
* Appointment management
* Notification system
* Improved laboratory report extraction
* Multi-language voice recognition
* Enhanced prescription templates
* Cloud deployment
* Audit logging
* Advanced reporting and analytics
* Mobile application integration

---

# 👨‍💻 Developer

**Ahmad Haroon**

AI / Full-Stack Developer

GitHub Username:

`ahmadharoon101-ai`

---

# 📄 License

This project is developed for **educational, internship, and demonstration purposes**.

Add an appropriate open-source license before distributing the project publicly under specific licensing terms.

---

# ⚠️ Disclaimer

This software is a technical project for healthcare workflow management and demonstration purposes.

It should not be treated as a substitute for professional medical judgment, diagnosis, treatment, or clinical decision-making.
