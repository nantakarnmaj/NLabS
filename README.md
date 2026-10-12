# BreathQuest — Clinical Skills Adventure

BreathQuest is a mobile-first, web-based formative learning game for second-year nursing students reviewing respiratory clinical skills. It emphasizes simulated ward interactions, low-stakes exploration, immediate rationale-based feedback, and safe retries without numeric grades, rankings, or pass/fail labels.

---

## Technology Stack

- **Backend**: Python 3.14, Flask, Flask-SQLAlchemy, SQLAlchemy, Flask-Migrate (Alembic), Waitress WSGI
- **Database**: SQLite (local instance-relative; foreign key constraints enforced)
- **Frontend**: Jinja2 templates, Tailwind CSS (precompiled, self-contained), Vanilla JavaScript
- **Security & Privacy**: Anonymous pseudonymous sessions using 256-bit cryptographically secure tokens (SHA-256 hashed on server), CSRF protection, HttpOnly cookies, local-only Content Security Policy (no external CDN dependencies)

---

## Current Status: Checkpoint E (All 4 Playable Rooms: 501, 502, 503, & 504)

BreathQuest is currently at **Checkpoint E**, featuring complete interactive gameplay across all 4 clinical simulation rooms:

| Room | Title | State in Ward | Behavior |
|---|---|---|---|
| **501** | **Clear the Airway** | **Ready / In Progress / Completed** | Full playable clinical simulation (Mr. Somchai, 68yo intubated male). 10 activities: assessment cues, equipment selection, safety prep, sterile sequence reordering (drag-and-drop & keyboard accessible), critical decision, monitor troubleshooting, post-care, patient outcome, and reflection debrief. Awards the **Airway Explorer** participation badge upon completion. |
| **502** | **Support the Breath** | **Ready / In Progress / Completed** | Full playable clinical simulation (Ms. Anong, 62yo post-cholecystectomy female). 10 activities: hypoxemia cues, low-flow cannula selection, setup flow, fire safety precautions, trend monitoring, device match challenge (`matching` evaluator), desaturation troubleshooting, comfort/skin aftercare, and reflection debrief. Awards the **Oxygen Guardian** participation badge upon completion. |
| **503** | **Open the Airway** | **Ready / In Progress / Completed** | Full playable clinical simulation (Ms. Mali, 55yo acute asthma female). 10 activities: bronchospasm cues, medication 10 Rights verification (`medication_check`), circuit assembly sequence, gas flow calibration (6–8 L/min), "Why No Mist?" troubleshooting, inhalation technique coaching, beta-2 adverse effect reassurance, mouth-rinsing aftercare, and reflection debrief. Awards the **Nebulizer Navigator** participation badge upon completion. |
| **504** | **Respiratory Rescue** | **Locked (until 501–503 done) / Ready / In Progress / Completed** | Capstone integrated emergency simulation (Mr. Prasert, 70yo COPD + secondary pneumonia in acute respiratory distress). 10 activities: assessment triage, emergent pre-oxygenation & sterile endotracheal suctioning, oxygen-driven nebulization, acute deterioration management (mucus plug clearance / non-sedation safety), SBAR escalation handover, stabilization, and capstone debrief. Awards the **Respiratory Ready** badge upon completion, completing all 4 showcase badges. |

---

## Local Development Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ and npm (build-time only, for compiling Tailwind CSS)
- SQLite 3

### 2. Environment Setup
```bash
# Clone or navigate to the repository
cd /path/to/NLabS

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate       # On macOS/Linux
# or .venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements-dev.txt

# Install frontend build dependencies
npm install
```

### 3. Configuration (.env)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Generate a cryptographically secure 32-byte secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Place the output in `.env` under `SECRET_KEY`.

### 4. Database Migrations & Seeding
```bash
# Run database migrations to head
flask db upgrade

# Seed initial ward rooms and prerequisites (idempotent)
flask seed
```

### 5. Build Tailwind CSS
```bash
# One-time build (minified)
npm run build:css

# Or watch mode during development
npm run watch:css
```

### 6. Run the Application
**Development server:**
```bash
FLASK_ENV=development python run.py
# Open http://127.0.0.1:8080
```

**Production WSGI with Waitress:**
```bash
FLASK_ENV=production python run.py
```

---

## Automated Tests

Run the comprehensive automated test suite in an isolated temporary database:
```bash
# Run all tests
pytest -v tests/

# Run with test coverage
pytest --cov=app --cov=seed --cov=config tests/
```

Test coverage includes:
- **Factory & Isolation**: Verifies app startup does not create tables or seed data.
- **Config & Secrets**: Rejection of default/placeholder secrets in production; instance-relative SQLite database resolution.
- **Migrations**: Clean upgrade on an empty database and idempotent re-upgrade preserving sentinel records.
- **Seed**: Idempotent creation of 4 rooms and 3 prerequisites without duplicates or learner data loss.
- **Session Lifecycle**: 256-bit token generation, SHA-256 server storage, CSRF verification, session reuse, and browser client isolation.
- **Ward & Access Control**: Correct room states (501 Ready/preview, 502/503 Coming Soon, 504 Locked); direct access protection; Room 501 preview progress isolation.
- **Health Checks**: `/health/live` (process liveness) and `/health/ready` (database schema readiness).
- **Security & Headers**: Jinja escaping against XSS, CSP headers, nosniff, and zero external CDN dependencies.

---

## Health Check Probes

- `GET /health/live`: Process liveness probe. Returns HTTP 200 `{"status": "alive"}` without querying the database or modifying data.
- `GET /health/ready`: Database readiness probe. Returns HTTP 200 `{"status": "ready"}` when database schema is reachable, or HTTP 503 `{"status": "unready"}` if unavailable.

---

## Production Deployment

For complete Windows Server deployment behind Apache / XAMPP using Waitress, refer to [`docs/DEPLOYMENT_WINDOWS_APACHE.md`](docs/DEPLOYMENT_WINDOWS_APACHE.md).
