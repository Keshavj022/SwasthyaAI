# Offline-First Hospital AI System

A competition-grade, privacy-preserving healthcare web application using open-weight medical AI models for clinical decision support.

## Overview

This system is a **multi-agent healthcare assistant** designed for:
- Doctors (clinical decision support)
- Patients (health information and communication)
- Hospital operations (scheduling, workflows)

### Key Features

- **Offline-First**: Fully functional without internet connectivity
- **Privacy-Preserving**: All data stored locally, encrypted at rest
- **Multi-Agent Architecture**: Specialized agents for different healthcare tasks
- **Clinical Safety**: Built-in guardrails, disclaimers, and escalation paths
- **Explainable AI**: All outputs include reasoning and confidence scores

## Technology Stack

### Frontend
- **Next.js 15** (App Router)
- **React 19**
- **TypeScript**
- **Tailwind CSS**

### Backend
- **FastAPI** (Python)
- **SQLite** (local database)
- **SQLAlchemy** (ORM)
- **Uvicorn** (ASGI server)

### Future Integration
- **MedGemma** (medical language models)
- **MedSigLIP** (medical image analysis)
- **MedASR** (medical speech recognition)

## Project Structure

```
HospitalAgent/
├── SAFETY_AND_SCOPE.md                    # Medical safety boundaries (READ FIRST)
├── README.md                               # This file
├── IMPLEMENTATION_SUMMARY.md               # Communication Agent summary
├── COMMUNICATION_AGENT_EXAMPLES.md         # Communication Agent API examples & workflows
├── DRUG_INFO_AGENT_EXAMPLES.md             # Drug Info Agent API examples
├── DIAGNOSTIC_AGENT_EXAMPLES.md            # Diagnostic Agent API examples
├── TRIAGE_AGENT_EXAMPLES.md                # Triage Agent rules & examples
├── IMAGE_ANALYSIS_AGENT_EXAMPLES.md        # Image Analysis Agent & MedSigLIP guide
├── VOICE_AGENT_EXAMPLES.md                 # Voice Agent & MedASR integration guide
├── APPOINTMENT_AGENT_EXAMPLES.md           # Appointment Agent scheduling guide
├── NEARBY_DOCTORS_AGENT_EXAMPLES.md        # Nearby Doctors & Referral Agent guide
├── HEALTH_SUPPORT_AGENT_EXAMPLES.md         # Health Support Agent guide (daily check-ins & reminders)
├── MEDGEMMA_INTEGRATION_GUIDE.md           # MedGemma integration guide
├── OFFLINE_FIRST_SUMMARY.md                 # Offline enforcement summary
├── OFFLINE_VALIDATION_CHECKLIST.md          # 150+ offline validation checks
├── DEMO_SCRIPT.md                           # Judge demo script (15-20 min)
├── backend/
│   ├── seed_demo_data.py                    # Populate demo data for judges
│   ├── main.py                             # FastAPI application
│   ├── config.py                           # Configuration
│   ├── database.py                         # SQLite setup
│   ├── requirements.txt                    # Python dependencies
│   ├── test_communication_agent.py         # Communication agent tests
│   ├── test_drug_info_agent.py             # Drug Info agent tests
│   ├── test_diagnostic_agent.py            # Diagnostic agent tests
│   ├── test_triage_agent.py                # Triage agent tests
│   ├── test_image_analysis_agent.py        # Image analysis agent tests
│   ├── test_voice_agent.py                 # Voice agent tests
│   ├── test_appointment_agent.py           # Appointment agent tests
│   ├── test_nearby_doctors_agent.py        # Nearby doctors agent tests
│   ├── test_health_support_agent.py        # Health support agent tests
│   ├── models/                             # Database models
│   │   ├── system.py                      # System health & audit models
│   │   └── patient.py                     # Patient data models
│   ├── routers/                            # API endpoints
│   │   ├── health.py                      # Health check endpoint
│   │   ├── orchestrator.py                # Multi-agent orchestrator
│   │   ├── audit.py                       # Audit log queries
│   │   ├── patients.py                    # Patient data management
│   │   └── documents.py                   # Medical document vault
│   ├── schemas/                            # Pydantic schemas
│   │   ├── patient.py                     # Patient data schemas
│   │   └── orchestrator.py                # Agent request/response schemas
│   ├── agents/                             # AI Agents
│   │   ├── prompts/
│   │   │   └── medgemma_prompts.py        # MedGemma prompt templates (all agents)
│   │   ├── communication_agent.py         # Doctor-patient communication
│   │   ├── drug_info_agent.py             # Medication knowledge & safety
│   │   ├── diagnostic_support_agent.py    # Differential diagnosis
│   │   ├── triage_agent.py                # Emergency triage & urgency classification
│   │   ├── image_analysis_agent.py        # Medical image analysis (MedSigLIP)
│   │   ├── voice_agent.py                 # Voice interaction (MedASR)
│   │   ├── appointment_agent.py           # Appointment scheduling & operations
│   │   ├── nearby_doctors_agent.py        # Nearby doctors & referral search
│   │   ├── health_support_agent.py        # Daily check-ins, reminders, health goals
│   │   ├── health_memory_agent.py         # Patient history retrieval
│   │   └── explainability_agent.py        # Explainable AI
│   ├── orchestrator/                       # Agent Orchestration System
│   │   ├── base.py                        # Base agent class
│   │   ├── orchestrator.py                # Main coordinator
│   │   ├── registry.py                    # Agent registry
│   │   ├── intent_classifier.py           # Intent classification
│   │   ├── safety_wrapper.py              # Safety & Guardrails Agent
│   │   └── audit_logger.py                # Audit logging
│   └── services/
│       └── file_storage.py                # Document storage service
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                     # Root layout
│   │   ├── page.tsx                       # Home page with health dashboard
│   │   └── globals.css                    # Global styles
│   ├── components/                         # React components (future)
│   ├── lib/
│   │   └── api.ts                         # API client
│   ├── package.json                        # Node dependencies
│   ├── tsconfig.json                       # TypeScript config
│   └── next.config.ts                      # Next.js config
└── database/
    ├── hospital.db                         # SQLite database (created at runtime)
    └── documents/                          # Medical document storage
```

## Prerequisites

### Required
- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **npm** or **yarn** (package manager)

### Optional
- **Git** (for version control)
- **SQLite viewer** (e.g., DB Browser for SQLite)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HospitalAgent
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI installed successfully')"
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Verify installation
npm list next react
```

## Running the Application (Offline Mode)

### Step 1: Start the Backend Server

```bash
# From the backend directory
cd backend

# Activate virtual environment if not already active
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Run the FastAPI server
python main.py
```

**Expected output:**
```
🏥 Starting Offline-First Hospital AI System v0.1.0
📍 Environment: development
🔌 Offline-first mode: ENABLED
✓ Database initialized at: sqlite:///../database/hospital.db

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start the Frontend Server

**In a new terminal:**

```bash
# From the frontend directory
cd frontend

# Run the Next.js development server
npm run dev
```

**Expected output:**
```
▲ Next.js 15.1.6
- Local:        http://localhost:3000
- Ready in 2.5s
```

### Step 3: Access the Application

Open your browser and navigate to:
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

## Verifying Offline Functionality

To verify the system works without internet:

1. **Disconnect from the internet** (turn off WiFi/ethernet)
2. Ensure both servers are running (backend on :8000, frontend on :3000)
3. Navigate to [http://localhost:3000](http://localhost:3000)
4. Verify:
   - ✅ Frontend loads successfully
   - ✅ Health check shows "healthy" status
   - ✅ Database status shows "connected"
   - ✅ Offline mode shows "ENABLED"

All core functionality should work without internet connectivity.

## API Endpoints

### Current Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with system info |
| `/api/health` | GET | Full system health check |
| `/api/health/ping` | GET | Quick connectivity test |
| `/docs` | GET | Interactive API documentation (Swagger UI) |

### Implemented Endpoints

| Endpoint                  | Method  | Description                | Status        |
|---------------------------|---------|----------------------------|---------------|
| `/api/orchestrator/ask`   | POST    | Multi-agent orchestrator   | ✅ Complete   |
| `/api/audit/logs`         | GET     | Query audit logs           | ✅ Complete   |
| `/api/patients/*`         | Various | Patient data management    | ✅ Complete   |
| `/api/documents/*`        | Various | Medical document vault     | ✅ Complete   |

### Future Endpoints (Coming Soon)

- `/api/agents/diagnostic` - Diagnostic support agent
- `/api/agents/image-analysis` - Medical image analysis (MedSigLIP)
- `/api/agents/voice` - Voice interaction (MedASR)
- `/api/appointments` - Appointment scheduling

## Database

### Location
- **Path**: `database/hospital.db`
- **Type**: SQLite3 (local file-based database)
- **Auto-created**: Database is automatically created on first backend startup

### Current Tables

- `system_health` - System health check logs
- `audit_logs` - AI interaction audit trail (per SAFETY_AND_SCOPE.md §7.2)

### Viewing the Database

```bash
# Using SQLite CLI
sqlite3 database/hospital.db
.tables
.schema audit_logs
.quit

# Or use a GUI tool like DB Browser for SQLite
```

## Development Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload (development)
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Development

```bash
cd frontend

# Development server with hot-reload
npm run dev

# Type checking
npx tsc --noEmit

# Linting
npm run lint
```

## Environment Variables

### Backend (.env file - optional)

Create `backend/.env` for custom configuration:

```env
# Application
APP_NAME="Offline-First Hospital AI System"
ENVIRONMENT=development

# Server
HOST=127.0.0.1
PORT=8000

# Security (CHANGE IN PRODUCTION)
SECRET_KEY=your-secret-key-here
```

### Frontend (.env.local file - optional)

Create `frontend/.env.local` for custom API URL:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Production Build

### Backend

```bash
cd backend

# Install production dependencies
pip install -r requirements.txt

# Run with production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start
```

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
- **Solution**: Ensure virtual environment is activated and dependencies installed
  ```bash
  source backend/venv/bin/activate
  pip install -r backend/requirements.txt
  ```

**Error**: `Address already in use` (port 8000)
- **Solution**: Kill existing process or change port
  ```bash
  # Find and kill process on port 8000 (macOS/Linux)
  lsof -ti:8000 | xargs kill -9

  # Or change port in backend/config.py
  PORT=8001
  ```

### Frontend won't start

**Error**: `Module not found` or dependency errors
- **Solution**: Delete node_modules and reinstall
  ```bash
  cd frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

**Error**: `Port 3000 already in use`
- **Solution**: Use a different port
  ```bash
  npm run dev -- -p 3001
  ```

### Frontend can't connect to backend

**Error**: `Failed to connect to backend` in browser
- **Verify backend is running**: Check [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Check CORS settings**: Verify `backend/config.py` allows `http://localhost:3000`
- **Try direct API call**: Open [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Database issues

**Error**: Database file locked
- **Solution**: Close all connections and restart backend
  ```bash
  # Kill backend process
  # Delete lock files
  rm database/*.db-journal database/*.db-wal
  # Restart backend
  ```

## Safety & Clinical Boundaries

**IMPORTANT**: Before developing any medical features, read:

📋 **[SAFETY_AND_SCOPE.md](./SAFETY_AND_SCOPE.md)**

This document defines:
- What the AI system is allowed to do
- What the AI must NEVER do
- Medical disclaimers for all outputs
- Emergency escalation rules
- Confidence thresholds

**All agents must comply with these safety boundaries.**

## Implementation Status

### ✅ Completed Components

1. **Agent Orchestration System**
   - ✅ Multi-agent orchestrator with intent classification
   - ✅ Safety & Guardrails Agent (enforces SAFETY_AND_SCOPE.md)
   - ✅ Explainability & Audit Agent
   - ✅ Comprehensive audit logging

2. **Doctor-Patient Communication Agent** (MedGemma-powered)
   - ✅ Medical Q&A
   - ✅ Text simplification
   - ✅ Visit summaries
   - ✅ Lab results explanation
   - ✅ Medication information
   - ✅ Symptom assessment
   - ⏭️ **Next:** Integrate real MedGemma model (see [MEDGEMMA_INTEGRATION_GUIDE.md](MEDGEMMA_INTEGRATION_GUIDE.md))

3. **Prescription & Medicine Knowledge Agent** (Drug Info)
   - ✅ Medication explanation (purpose, mechanism, side effects)
   - ✅ Drug interaction detection (major/moderate/minor severity)
   - ✅ Allergy safety checking (direct matches + cross-reactivity)
   - ✅ Dosage education with warnings
   - ✅ Comprehensive safety assessment
   - ✅ NO PRESCRIBING AUTHORITY (decision support only)

4. **Diagnostic Support Agent** (MedGemma-powered)
   - ✅ Symptom analysis and differential diagnosis generation
   - ✅ Ranked diagnoses with confidence scores
   - ✅ Emergency symptom detection and red flags
   - ✅ Evidence-based reasoning (supporting/contradicting features)
   - ✅ Missing information identification
   - ✅ Recommended workup suggestions
   - ✅ NO DEFINITIVE DIAGNOSES (decision support only)

5. **Triage & Emergency Risk Agent** (Rule-Based)
   - ✅ 4-level urgency classification (EMERGENCY, URGENT, ROUTINE, SELF_CARE)
   - ✅ Life-threatening emergency detection (911-worthy symptoms)
   - ✅ Rule-based triage logic with conservative safety thresholds
   - ✅ Vital signs analysis (age-appropriate thresholds)
   - ✅ Special population support (pediatric, elderly, pregnant, immunocompromised)
   - ✅ Clear action recommendations with timeframes
   - ✅ Escalation criteria and warning signs

6. **Medical Image Analysis Agent** (MedSigLIP-powered)
   - ✅ Multi-modality support (Chest X-ray, CT, MRI, dermatology, pathology)
   - ✅ Finding detection with structured output
   - ✅ Abnormality classification (normal vs abnormal)
   - ✅ Natural language region descriptions
   - ✅ Confidence scoring for all findings
   - ✅ Red flag detection for critical findings
   - ✅ Mandatory imaging disclaimers
   - ⏭️ **Next:** Integrate real MedSigLIP model (see examples documentation)

7. **Voice Interaction Agent** (MedASR-powered)
   - ✅ Multi-mode support (symptom reporting, medical dictation, voice queries, general)
   - ✅ Medical terminology recognition and extraction
   - ✅ Multi-language support (English, Spanish, French, German, Portuguese, Chinese)
   - ✅ Word-level timestamps and confidence scores
   - ✅ Alternative transcriptions for accuracy verification
   - ✅ Intelligent routing to appropriate agents
   - ✅ Error handling (missing audio, unsupported modes/languages)
   - ⏭️ **Next:** Integrate real MedASR model (see [VOICE_AGENT_EXAMPLES.md](VOICE_AGENT_EXAMPLES.md))

8. **Appointment & Hospital Operations Agent** (Administrative)
   - ✅ Offline-first appointment scheduling with local database
   - ✅ Automatic conflict detection (prevents double-booking)
   - ✅ Doctor availability checking by specialty or name
   - ✅ Appointment rescheduling with conflict handling
   - ✅ Appointment cancellation with refund policy
   - ✅ Patient appointment history (upcoming and past)
   - ✅ Automated follow-up scheduling
   - ✅ Multi-specialty support (9 specialties)
   - ✅ 6 appointment types with duration-based scheduling
   - ✅ Clinic hours enforcement (prevents bookings outside hours)
   - ✅ Next available slot suggestions on conflicts
   - ⏭️ **Note:** This is an ADMINISTRATIVE agent (no medical AI)

9. **Nearby Doctors & Referral Agent** (Directory Service)
   - ✅ Condition-to-specialty matching (20+ medical conditions)
   - ✅ Cached local doctor directory search
   - ✅ Distance-based filtering (Haversine formula, zip code proximity)
   - ✅ Insurance verification and filtering
   - ✅ Accepting new patients filter
   - ✅ Referral letter generation with explanations
   - ✅ Multiple urgency levels (routine, urgent, emergency)
   - ✅ Multi-criteria search (specialty, location, insurance, availability)
   - ✅ Doctor ratings and experience display
   - ✅ Comprehensive error handling and suggestions
   - ⏭️ **Note:** This is a DIRECTORY/REFERRAL agent (no medical AI)

10. **AI Health Support / Daily Update Agent** (Wellness Monitoring)
    - ✅ Daily wellness check-ins (mood, energy, sleep tracking)
    - ✅ Chronic condition monitoring (diabetes, hypertension, asthma, heart disease, COPD, arthritis)
    - ✅ Automatic threshold-based alerts for concerning metrics
    - ✅ Medication and appointment reminder management
    - ✅ Symptom logging with automatic escalation for severe symptoms
    - ✅ Health goal tracking with progress analytics
    - ✅ Comprehensive health summaries (daily, weekly, monthly)
    - ✅ Trend analysis for condition metrics
    - ✅ 7 tasks: daily check-in, track condition, get reminders, log symptoms, track goals, get summary, schedule reminder
    - ✅ 22 comprehensive tests (all passing)
    - ⏭️ **Note:** This is a SUPPORT/MONITORING tool (non-intrusive, non-diagnostic)

11. **Patient Data Management**
    - ✅ Health Memory Agent (patient history retrieval)
    - ✅ Patient records (demographics, visits, prescriptions, diagnoses, allergies, labs)
    - ✅ Medical Document Vault (images, PDFs, DICOM files)

### 🚧 Next Steps

#### Immediate (AI Model Integration)

1. **Integrate Real MedGemma** - Replace stub responses with actual model (Communication, Diagnostic agents)
2. **Integrate Real MedSigLIP** - Replace stub responses with actual model (Image Analysis agent)
3. **Integrate Real MedASR** - Replace stub responses with actual model (Voice Interaction agent)
4. **Lab Results Interpreter** - Structured lab data analysis with trending and abnormality detection

#### Short-term (Frontend & UX)

1. **User Authentication** - Role-based access (doctor/patient/admin)
2. **Patient Dashboard** - Frontend for patient data visualization
3. **Communication Interface** - Chat UI for doctor-patient communication
4. **Document Viewer** - Medical image and PDF viewer

#### Medium-term (Advanced Features)

1. **Enhanced Drug Interaction Checker** - Integration with DrugBank/FDA APIs
2. **Appointment Reminders & Notifications** - SMS/email reminders, waitlist management
3. **Offline PWA** - Progressive Web App for mobile devices
4. **Real-time Monitoring** - Vital signs integration and alerts

#### Long-term (Competition Polish)

1. **Multi-language Support** - Translate to patient's primary language
2. **Data Export/Import** - Hospital transfer compatibility
3. **Accessibility** - WCAG compliance for screen readers
4. **Fine-tuning** - Custom medical models on hospital data

## Contributing

When contributing to this project:

1. **Safety First**: All medical features MUST comply with SAFETY_AND_SCOPE.md
2. **Privacy**: Never commit patient data or database files
3. **Offline-First**: Test all features without internet connectivity
4. **Explainability**: All AI outputs must include reasoning and confidence
5. **Audit Trail**: Log all medical AI interactions

## License

[To be determined - consult competition rules]

## Acknowledgments

- **Google Health AI Developer Foundations (HAI-DEF)** for open-weight medical models
- **FastAPI** for the excellent Python web framework
- **Next.js** for the React framework
- **SQLite** for reliable local storage

---

## Quick Reference Commands

### Start Both Servers (Offline Mode)

**Terminal 1 (Backend):**
```bash
cd backend && source venv/bin/activate && python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend && npm run dev
```

**Access:** [http://localhost:3000](http://localhost:3000)

---

**System Status**: Offline-Ready ✅
**Last Updated**: 2026-02-02
