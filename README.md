# SwasthyaAI — Hospital AI System

A web-based healthcare platform providing **clinical decision support** through a multi-agent system, powered by open-weight medical AI models (MedGemma · MedSigLIP · Whisper/MedASR) running on your own server.

> ⚕️ **Decision support only — not a medical device.** Every AI output carries a disclaimer and never claims diagnostic authority. Until you download the model weights (see [docs/MODELS_SETUP.md](./docs/MODELS_SETUP.md)), the AI runs in a clearly-labeled **demo/stub mode** — the app is fully functional, it just doesn't perform real inference yet.

---

## What it does

| Audience | Capabilities |
| -------- | ------------ |
| **Patients** | Health dashboard, daily check-ins, AI chat, symptom/lab questions, lab-results interpreter, appointment booking, document vault |
| **Doctors** | Patient queue & context, diagnostic support, drug-interaction checks, schedule management, AI-assisted consultations |
| **Admins** | User management, system & AI-model health, audit-log review, operations overview |

### Highlights

- **Multi-agent orchestrator** — 11 specialized agents (triage, diagnostic support, drug info, lab results, image analysis, voice, communication, appointments, referrals, health memory, health support) behind a single `/orchestrator/query` endpoint with intent routing.
- **PWA** — service worker with an offline fallback page; installable on desktop and mobile.
- **Clinical safety** — a safety wrapper enforces disclaimers, emergency escalation, and red-flag detection; AI responses expose a `stub_mode` flag and the UI shows a demo banner when a model isn't loaded.
- **Explainable** — responses include reasoning and confidence; audit trail records every AI interaction.
- **Role-based access** — JWT auth (token mirrored to a cookie so SSR middleware works), with patient/doctor/admin separation and object-level authorization.

---

## Tech stack

**Frontend:** Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS · shadcn/ui · TanStack Query · Zustand · Recharts
**Backend:** FastAPI · SQLAlchemy · SQLite · Uvicorn · python-jose (JWT) · passlib
**AI (local, optional):** MedGemma 4B (text + image) · MedSigLIP 448 (imaging) · Whisper large-v3-turbo or MedASR (voice) via `transformers` + `torch`

---

## Quick start

### Prerequisites

- Python 3.11–3.13
- Node.js 18+ and npm

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_demo_data.py   # optional: load demo users + data
python main.py                     # http://127.0.0.1:8000  (docs at /docs)
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:3000
```

### 3. Log in

Demo accounts (created by `scripts/seed_demo_data.py`):

| Role | Email | Password |
| ---- | ----- | -------- |
| Admin | `admin@swasthya.local` | `Admin@1234` |
| Doctor | `dr.sharma@swasthya.local` | `Doctor@1234` |
| Patient | `patient.rahul@swasthya.local` | `Patient@1234` |

> Self-registration always creates a **patient** account; doctor/admin accounts are provisioned by an admin.

### 4. (Optional) Enable the real medical AI models

The app works in demo/stub mode out of the box. To run real inference, follow **[docs/MODELS_SETUP.md](./docs/MODELS_SETUP.md)** — accept the Hugging Face model licenses, download the weights (~14 GB), and flip the `*_MODE` flags in `backend/.env`. Check status at `GET /api/health/ai-status`.

---

## Project structure

```text
SwasthyaAI/
├── README.md
├── docs/                         # planning specs + setup guides (gitignored)
│   ├── MODELS_SETUP.md
│   ├── AI_MODELS_REFERENCE.md
│   └── 00_MASTER_INDEX.md … 15_*.md
├── backend/
│   ├── main.py                   # FastAPI app + router wiring + startup
│   ├── config.py                 # settings (auth, models, flags)
│   ├── database.py               # SQLAlchemy / SQLite setup
│   ├── agents/                   # 11 agents (triage, diagnostic, lab_results, …)
│   ├── orchestrator/             # intent classifier, registry, safety wrapper, audit
│   ├── inference/                # model inference layer (stub-degrading)
│   ├── services/                 # model_loader + med{gemma,siglip,asr}_service, auth, files
│   ├── routers/                  # auth, orchestrator, patients, documents,
│   │                             #   appointments, lab_results, admin, audit, health
│   ├── models/ · schemas/        # ORM models + Pydantic schemas
│   ├── scripts/                  # seed_demo_data.py, verify_models.py, download_models.py
│   └── tests/                    # pytest suites (agent tests + inference tests)
├── frontend/
│   ├── app/                      # App Router: (auth), (app) groups, landing, offline
│   ├── components/               # ui, layout, chat, appointments, documents,
│   │                             #   records, admin, doctor, patient, landing
│   ├── hooks/ · lib/api.ts · types/  # React Query hooks, API client, shared types
│   ├── middleware.ts             # SSR route protection
│   └── public/                   # PWA manifest, service worker, icons
└── database/                     # SQLite db + uploaded documents (gitignored, auto-created)
```

---

## API overview

All `/api/orchestrator`, `/api/patients`, `/api/documents`, `/api/appointments`, and `/api/lab-results` routes require a Bearer token; `/api/admin` and `/api/audit` require an admin token.

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/api/health` · `/api/health/ai-status` | GET | System & AI-model health |
| `/api/auth/register` · `/login` · `/me` | POST/GET | Auth (register → patient only) |
| `/api/orchestrator/query` (alias `/ask`) | POST | Multi-agent query (text + audio + image) |
| `/api/orchestrator/agents` | GET | List available agents |
| `/api/patients/*` | various | Patient records, check-ins, history |
| `/api/lab-results/interpret · /save · /{patient_id}` | POST/GET | Lab interpretation & history |
| `/api/appointments/* · /availability` | various | Booking with conflict detection |
| `/api/documents/* · /upload · /patient/{id}` | various | Document vault |
| `/api/admin/users · /stats` | various | Admin user management & metrics |
| `/api/audit/logs` | GET | AI interaction audit trail |

Interactive docs: `http://127.0.0.1:8000/docs`.

---

## Testing

```bash
cd backend && source venv/bin/activate
pytest tests/
pytest tests/test_auth.py tests/test_lab_results.py tests/test_api_integration.py

cd ../frontend
npx tsc --noEmit
npx next build
```

---

## Security notes

Implemented: JWT auth with server-derived identity (the orchestrator never trusts a client-supplied `user_id`), forced-patient self-registration, object-level authorization on patient/document/appointment data, an admin role-gate, and a fail-fast check that refuses to boot with placeholder secrets outside development.

**Roadmap (not yet implemented):** encryption-at-rest for the SQLite DB and uploaded files, rate limiting, refresh-token rotation, and audit-log immutability. Do not deploy with PHI until these are in place and strong secrets are set in `backend/.env`.

---

## Future scope

- **Offline mode** — full offline capability with a local-first sync strategy; AI inference in-browser via WebAssembly or a local model server, so the app works without a network connection.
- **Mobile app** — React Native client sharing business logic with the web frontend.
- **Encryption at rest** — SQLCipher for the SQLite database and encrypted document storage.
- **Telemedicine** — integrated video consultation with AI-assisted note-taking.
- **Wearable integration** — real-time health metrics from fitness trackers and medical IoT devices.
- **Multi-tenancy** — hospital/clinic-level data isolation for SaaS deployment.

---

## Acknowledgments

- Google **Health AI Developer Foundations** (MedGemma, MedSigLIP, MedASR)
- FastAPI · Next.js · SQLite
