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
├── SAFETY_AND_SCOPE.md          # Medical safety boundaries (READ FIRST)
├── README.md                     # This file
├── backend/
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration
│   ├── database.py               # SQLite setup
│   ├── requirements.txt          # Python dependencies
│   ├── models/                   # Database models
│   │   └── system.py            # System health & audit models
│   ├── routers/                  # API endpoints
│   │   └── health.py            # Health check endpoint
│   └── schemas/                  # Pydantic schemas (future)
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Home page with health dashboard
│   │   └── globals.css          # Global styles
│   ├── components/               # React components (future)
│   ├── lib/
│   │   └── api.ts               # API client
│   ├── package.json             # Node dependencies
│   ├── tsconfig.json            # TypeScript config
│   └── next.config.ts           # Next.js config
└── database/
    └── hospital.db              # SQLite database (created at runtime)
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

### Future Endpoints (Coming Soon)

- `/api/agents/diagnostic` - Diagnostic support agent
- `/api/agents/image-analysis` - Medical image analysis
- `/api/agents/triage` - Emergency triage classification
- `/api/agents/drug-info` - Drug interaction checker
- `/api/patients` - Patient record management
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

## Next Steps

### Immediate (MVP)
1. Implement Safety & Guardrails Agent (enforces SAFETY_AND_SCOPE.md)
2. Implement Triage & Emergency Risk Agent
3. Add user authentication and role-based access
4. Implement basic patient record storage

### Short-term (Core Agents)
1. Diagnostic Support Agent (with MedGemma)
2. Medical Image Analysis Agent (with MedSigLIP)
3. Drug Interaction Checker
4. Doctor-Patient Communication Agent

### Medium-term (Advanced Features)
1. Voice Agent (MedASR integration)
2. Appointment Scheduling Agent
3. Medical Document Vault
4. Personalized Health Memory Agent

### Long-term (Competition Polish)
1. Offline PWA (Progressive Web App)
2. Data export/import for hospital transfers
3. Multi-language support
4. Accessibility improvements (WCAG compliance)

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
**Last Updated**: 2026-01-31
