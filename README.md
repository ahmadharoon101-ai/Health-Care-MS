# 🏥 Health Care Management System

A full-stack **Health Care Management System** designed to streamline patient record management, laboratory report processing, medicine prescription, authentication, and administrative operations through a centralized web-based platform.

The system combines **AI-powered laboratory report extraction**, **voice-based prescription entry**, **medicine searching**, **patient management**, and **role-based access control** into a single healthcare workflow.

---

## 📌 Project Overview

The Health Care Management System provides healthcare staff with a centralized platform for managing patient information and healthcare-related operations.

The system consists of multiple integrated modules:

* 👤 User Management
* 🧑‍⚕️ Patient Record Management
* 🧪 AI Laboratory Report Extraction
* 🎙️ Voice Prescription
* 💊 Medicine Search & Prescription Management
* 📊 Admin Dashboard
* 🔐 Authentication & Role-Based Access Control

The frontend communicates with a Python/FastAPI backend through REST APIs, while the backend manages application logic, authentication, data processing, and database operations.

---

## ✨ Main Features

### 🔐 Authentication & User Management

* User registration
* Secure login
* Logout
* Role-based access control
* User account management
* Authentication validation
* Protected application routes

---

### 🧑‍⚕️ Patient Record Management

The Patient Record Management module provides a centralized location for maintaining patient information.

Features include:

* Create patient records
* View patient information
* Update patient records
* Search patient records
* Manage patient details
* Store healthcare-related information
* Retrieve patient records when required

---

### 🧪 AI Laboratory Report Extraction

The AI Laboratory Report Extraction module allows users to process laboratory reports and extract useful patient information.

Supported workflow:

1. Upload a laboratory report.
2. Process the report through the backend.
3. Extract relevant patient/report information.
4. Display the extracted information.
5. Review and correct the information if required.
6. Save the information into patient records.

The system is designed to reduce repetitive manual data entry when transferring information from laboratory reports into the healthcare system.

---

### 🎙️ Voice Prescription

The Voice Prescription module allows healthcare professionals to enter medicine information using voice input.

Workflow:

```text
Doctor Voice Input
       ↓
Audio Recording
       ↓
Speech-to-Text
       ↓
Recognized Text
       ↓
Medicine Search
       ↓
Medicine Selection
       ↓
Prescription Management
       ↓
Prescription Generation
```

The system can use speech recognition to convert spoken medicine instructions into text and connect the recognized text with the medicine search functionality.

---

### 💊 Medicine Search & Prescription Management

The medicine module provides functionality for searching and managing medicines during prescription creation.

Features include:

* Medicine search
* Medicine name matching
* Fuzzy medicine matching
* Matching percentage
* Medicine selection
* Prescription item management
* Manual medicine entry
* Prescription generation
* Prescription printing/PDF workflow

The medicine catalog can be loaded from the project's medicine dataset.

---

### 📊 Admin Dashboard

The Admin Dashboard provides administrative functionality for managing the healthcare system.

Depending on the configured user roles and permissions, administrators can monitor and manage:

* Users
* Patients
* System records
* Healthcare modules
* Application activity
* Administrative information

---

## 🏗️ System Architecture

```text
┌───────────────────────────────────────────┐
│                 Frontend                  │
│                                           │
│ HTML / CSS / JavaScript                  │
│ User Interface & Application Screens      │
└───────────────────┬───────────────────────┘
                    │
                    │ REST API
                    ▼
┌───────────────────────────────────────────┐
│                 Backend                   │
│                                           │
│ Python + FastAPI                          │
│ Authentication                            │
│ Business Logic                            │
│ AI Processing                             │
│ Voice Processing                           │
│ Medicine Search                            │
│ Patient Management                         │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│                 Database                  │
│                                           │
│ Users                                     │
│ Patients                                  │
│ Prescriptions                             │
│ Laboratory Records                         │
│ System Data                               │
└───────────────────────────────────────────┘
```

---

## 🛠️ Technologies Used

### Frontend

* HTML5
* CSS3
* JavaScript
* Responsive Web Interface

### Backend

* Python
* FastAPI
* Uvicorn
* REST APIs
* Pydantic
* SQLAlchemy

### AI / Speech Processing

* Speech-to-Text
* OpenAI Whisper
* AI-based laboratory report processing
* Fuzzy medicine matching

### Database

* SQL-based database
* SQLAlchemy ORM

### Development Tools

* Visual Studio Code
* Git
* GitHub
* Python Virtual Environment

---

## 📁 Project Structure

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

> The exact folders may vary depending on the current implementation of the project.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ahmadharoon101-ai/Health-Care-MS.git
```

```bash
cd Health-Care-MS
```

---

### 2. Create a Python Virtual Environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

---

### 3. Install Backend Dependencies

```powershell
pip install -r backend\requirements.txt
```

---

## 🔑 Environment Configuration

This project uses environment variables for configuration and sensitive information.

Create your local environment file from the example:

```powershell
copy .env.example .env
```

Then configure the required values locally.

### ⚠️ Security

**Never commit the real `.env` file to GitHub.**

Do not expose:

* API keys
* AI service keys
* Database passwords
* Authentication secrets
* JWT secrets
* Access tokens
* Private credentials

The repository should contain only safe example configuration such as:

```text
.env.example
```

with placeholder values.

---

## 🗄️ Database Configuration

Configure your local database connection in `.env`.

Example:

```env
DATABASE_URL=your_local_database_connection
```

Use your own local database credentials.

Do not place real production credentials inside:

```text
README.md
.env.example
source code
GitHub repository
```

---

## 🚀 Running the Backend

From the project root:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available locally at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is normally available at:

```text
http://127.0.0.1:8000/docs
```

---

## 🌐 Running the Frontend

Open the frontend directory and run it using your preferred local development server.

For example, with VS Code Live Server:

```text
frontend/
```

Then open the application's frontend URL provided by the local server.

Make sure the frontend API configuration points to your local backend.

---

## 🎙️ Voice Prescription Workflow

```text
Start Prescription
        │
        ▼
Click Microphone
        │
        ▼
Record Doctor's Voice
        │
        ▼
Speech-to-Text Processing
        │
        ▼
Recognized Medicine Text
        │
        ▼
Medicine Search
        │
        ▼
Fuzzy Matching
        │
        ▼
Select Medicine
        │
        ▼
Add to Prescription
        │
        ▼
Generate / Print Prescription
```

---

## 🧪 Laboratory Report Workflow

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

## 👥 User Roles

The system supports role-based access so that application functionality can be controlled according to the authenticated user's permissions.

Typical roles can include:

| Role                      | Main Responsibilities                 |
| ------------------------- | ------------------------------------- |
| Admin                     | System and user management            |
| Doctor / Healthcare Staff | Patient and prescription operations   |
| Authorized User           | Access permitted healthcare functions |

The exact permissions depend on the application's configured authorization rules.

---

## 🔒 Security Considerations

Security is an important part of the project.

The repository intentionally does **not** contain private credentials or production secrets.

Recommended security practices:

* Store secrets in `.env`
* Keep `.env` in `.gitignore`
* Use environment variables for API credentials
* Never hard-code API keys
* Never commit database passwords
* Use strong authentication secrets
* Restrict administrative functionality using role-based access
* Validate API input
* Use HTTPS when deployed to production
* Keep dependencies updated

---

## 🧪 Testing

The system can be tested across its major workflows, including:

### Authentication

* Valid registration
* Invalid registration
* Valid login
* Invalid login
* Logout
* Unauthorized access

### Patient Management

* Add patient
* View patient
* Update patient
* Search patient
* Invalid patient information

### Laboratory Reports

* Upload valid report
* Upload unsupported file
* Extract report information
* Review extracted information
* Save extracted patient data

### Voice Prescription

* Start voice recording
* Stop recording
* Convert speech to text
* Search medicine
* Select medicine
* Add medicine to prescription
* Generate prescription

### Administration

* Admin login
* User management
* Record management
* Access control

---

## 📋 Medicine Dataset

The system can use a medicine CSV dataset for medicine searching and matching.

Example structure:

```text
backend/
└── data/
    └── medicine.csv
```

The backend loads the medicine catalog during application startup when the dataset is configured correctly.

---

## 🔄 API Integration

The frontend communicates with the FastAPI backend through HTTP requests.

Example architecture:

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
   ▼
Database / AI / Medicine Service
   │
   ▼
JSON Response
   │
   ▼
Frontend
```

---

## 📖 API Documentation

When the backend is running locally, FastAPI provides interactive API documentation through Swagger UI.

```text
http://127.0.0.1:8000/docs
```

The exact endpoints depend on the current backend implementation.

---

## 🛡️ GitHub Upload Safety

Before pushing this project to GitHub, verify:

```powershell
git status
```

Make sure sensitive files such as the following are not staged:

```text
.env
.env.local
.env.production
credentials.json
secret files
private keys
API key files
database password files
```

The `.gitignore` file should prevent sensitive configuration from being tracked.

---

## 📌 Current Project Status

The project includes the following major healthcare functionality:

* [ ] User authentication
* [ ] Role-based access control
* [ ] Patient record management
* [ ] AI laboratory report extraction
* [ ] Voice prescription workflow
* [ ] Medicine searching
* [ ] Fuzzy medicine matching
* [ ] Prescription management
* [ ] Admin dashboard
* [ ] Frontend/backend integration
* [ ] Database integration
* [ ] System testing

---

## 🎯 Project Objectives

The main objectives of the Health Care Management System are to:

1. Centralize healthcare information.
2. Reduce repetitive manual data entry.
3. Simplify patient record management.
4. Assist healthcare staff with voice-based prescription entry.
5. Automate extraction of information from laboratory reports.
6. Provide medicine search and matching functionality.
7. Implement controlled access through authentication and roles.
8. Provide administrative management capabilities.
9. Integrate frontend, backend, AI, and database components into one system.

---

## 🚀 Future Improvements

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

## 👨‍💻 Developer

**Ahmad Haroon**

AI / Full-Stack Developer

GitHub:
https://github.com/ahmadharoon101-ai

---

## 📄 License

This project is developed for educational, internship, and demonstration purposes.

Add an appropriate open-source license before distributing the project publicly under specific licensing terms.

---

## ⭐ Acknowledgements

The project uses open-source technologies and development resources including:

* FastAPI
* Python
* SQLAlchemy
* OpenAI Whisper
* HTML
* CSS
* JavaScript

---

## ⚠️ Disclaimer

This software is a technical project for healthcare workflow management and demonstration purposes. It should not be treated as a substitute for professional medical judgment, diagnosis, or clinical decision-making.
