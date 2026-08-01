# Modular CRM

A Flask-based modular CRM built for easy feature expansion. Each feature lives in its own module (blueprint) with models, routes, templates, and tests.

## Quick Start

```bash
cd modular-crm
pip install -r requirements.txt
./runner.sh start
# Open http://localhost:5001
```

## Commands

| Command | Description |
|---------|-------------|
| `./runner.sh start` | Start server in background on port 5001 |
| `./runner.sh stop` | Stop background server |
| `./runner.sh restart` | Restart server |
| `./runner.sh dev` | Run server in foreground (Flask dev mode) |
| `./runner.sh test` | Run smoke tests |
| `./runner.sh status` | Check if server is running |

## Modules

| Module | Slug | Description |
|--------|------|-------------|
| Core | `core` | App shell, home route |
| Dashboard | `dashboard` | Metrics and quick actions |
| Contacts | `contacts` | People: leads, customers, partners |
| Companies | `companies` | Organizations and accounts |

## How to add a new module

1. Create `modules/<name>/`:
   ```
   modules/<name>/
   ├── __init__.py   # NAME, SLUG, DESCRIPTION, register(app)
   ├── models.py     # SQLAlchemy models
   └── routes.py     # Blueprint + API endpoints
   ```

2. Add templates in `templates/<name>/`.

3. Register the module in `modules/__init__.py`:
   ```python
   from modules import core, dashboard, contacts, companies, <name>
   MODULES = [core, dashboard, contacts, companies, <name>]
   ```

4. Restart the server.

## Future feature ideas

- Deals / pipeline
- Tasks and activities
- Notes and email history
- Calendar and reminders
- Reports and analytics
- Users, roles, and permissions
- Email integration
- AI enrichment

## Tech Stack

- Flask + Flask-SQLAlchemy
- SQLite (default, configurable via `CRM_DATABASE_URL`)
- Jinja2 templates
- Vanilla JavaScript + CSS
- PWA-ready (manifest + service worker)
