# Modular CRM

Flask-based CRM with modular routes, SQLAlchemy, automation event dispatch, and a runtime-only cleanup.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

## Running

- App: `http://localhost:5001`
- Health: `GET /api/health`

## Modules

- `deals` — `/deals/api/deals`, pipeline, stages, stats
- `activities` — `/activities/api/activities`, upcoming, overdue, stats
- `contacts` — `/contacts/api/contacts`
- `companies` — `/companies/api/companies`
- `email_templates` — `/email-templates/api/templates`, preview, use
- `automations` — event fire/dispatch in engine
- `dashboard` — dashboard routes/models
- `core` — core routes/models

## Automation

`modules/automations/engine.py` normalizes payloads, resolves deals, applies default actions, uses per-rule savepoint isolation, and records error runs.

## Cleanup

Runtime-only cleanup preserves `app.py`, `config.py`, `database.py`, `models.py`, `modules/`, `run.py`, `runner.sh`, `requirements.txt`, `migrations/`, `static/`, and `templates/`.
