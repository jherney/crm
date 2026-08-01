#!/usr/bin/env python3
"""
One-shot data migration: SQLite (crm.db) → PostgreSQL.

Reads every row from the SQLite DB via SQLAlchemy ORM and writes them to
Postgres via the same models. Identity-respecting: rows keep their UUIDs so all
foreign keys stay valid. Idempotent — skips if a row already exists by ID.

Source DB password resolution order:
    1. CRM_DATABASE_URL env var (full URL)
    2. CRM_PG_PASSWORD env var, plus host defaults
    3. `podman exec crm-postgres printenv POSTGRES_PASSWORD` (dev convenience)
        then build  postgresql://crm:<pw>@127.0.0.1:5433/crm
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


SQLITE_URL = f"sqlite:///{ROOT / 'crm.db'}"


def resolve_pg_url() -> str:
    """Determine Postgres URL by precedence rules (see module docstring)."""
    explicit = os.environ.get('CRM_DATABASE_URL')
    if explicit:
        return explicit

    pw = os.environ.get('CRM_PG_PASSWORD')
    if not pw and not _is_redacted_placeholder(_GETENV('CRM_PG_PASSWORD', '***')):
        pw = _GETENV('CRM_PG_PASSWORD', '***')

    if (not pw or _is_redacted_placeholder(pw)) and _podman_available():
        # Convenience: pull from the running Podman container we set up.
        try:
            pw = subprocess.run(
                ['podman', 'exec', 'crm-postgres', 'printenv', 'POSTGRES_PASSWORD'],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        except Exception:
            pw = None

    if not pw or _is_redacted_placeholder(pw):
        raise SystemExit("Could not determine Postgres password. "
                         "Set CRM_DATABASE_URL or CRM_PG_PASSWORD, "
                         "or run an AUTO_PG=1 ./runner.sh start.")

    host = os.environ.get('CRM_PG_HOST', '127.0.0.1')
    port = os.environ.get('CRM_PG_PORT', '5433')
    user = os.environ.get('CRM_PG_USER', 'crm')
    db   = os.environ.get('CRM_PG_DB',   'crm')
    return f"postgresql://{user}:***@{host}:{port}/{db}"


def _GETENV(key, default):
    """os.environ.get alias for readability."""
    import os as _os
    return _os.environ.get(key, default)


def _is_redacted_placeholder(value: str) -> bool:
    """True if the value is a redact-tap mark like '***' or '[REDACTED]'.
    Lets the script know it has to fall through to another source.
    """
    if not value:
        return True
    stripped = value.strip()
    return (
        stripped == '***'
        or stripped == '[REDACTED]'
        or all(c == '*' for c in stripped)
    )


def _podman_available() -> bool:
    try:
        return subprocess.run(['podman', '--version'],
                              capture_output=True, timeout=2).returncode == 0
    except Exception:
        return False


# Order matters: insert parents first so FK constraints pass.
# companies has no FK; contacts FKs to companies; deals FKs to contacts+companies;
# activities FKs to deals+contacts+companies; automations FKs to rules.
MODELS = [
    ('companies',               'modules.companies.models.Company'),
    ('contacts',                'modules.contacts.models.Contact'),
    ('email_templates',         'modules.email_templates.models.EmailTemplate'),
    ('deals',                   'modules.deals.models.Deal'),
    ('activities',              'modules.activities.models.Activity'),
    ('automation_rules',        'modules.automations.models.AutomationRule'),
    ('automation_runs',         'modules.automations.models.AutomationRun'),
] # noqa: E501


def import_model(dotted: str):
    mod, _, attr = dotted.rpartition('.')
    return getattr(__import__(mod, fromlist=[attr]), attr)


def main() -> int:
    pg_url = resolve_pg_url()
    print(f"Source : {SQLITE_URL}")
    print(f"Target : postgresql://crm:***@{pg_url.split('@', 1)[1]}")
    print()

    sqlite_engine = create_engine(SQLITE_URL)
    pg_engine = create_engine(pg_url)

    # Import every model so SQLAlchemy metadata is fully populated.
    from models import db  # noqa
    for _tbl, _dotted in MODELS:
        import_model(_dotted)  # noqa: registers model with metadata

    # Create tables on Postgres using a single metadata-aware call.
    db.metadata.create_all(pg_engine)
    print("✓ Postgres tables ready")

    src = sessionmaker(bind=sqlite_engine)()
    dst = sessionmaker(bind=pg_engine)()

    total_inserted = 0
    total_skipped = 0
    for table_name, dotted in MODELS:
        Model = import_model(dotted)
        src_rows = src.query(Model).all()
        if not src_rows:
            print(f"  {table_name:24s} 0 rows   (skip)")
            continue
        existing_ids = {
            row[0] for row in dst.execute(text(f'SELECT id FROM {table_name}')).all()
        }
        inserted = 0
        skipped = 0
        for row in src_rows:
            if row.id in existing_ids:
                skipped += 1
                continue
            clone_kwargs = {col.name: getattr(row, col.name)
                            for col in row.__table__.columns}
            dst.add(Model(**clone_kwargs))
            inserted += 1
        dst.commit()
        total_inserted += inserted
        total_skipped += skipped
        print(f"  {table_name:24s} {len(src_rows):>3} src → "
              f"{inserted:>3} inserted, {skipped:>3} skipped")

    print()
    print(f"Done. {total_inserted} inserted, {total_skipped} skipped.")
    print()
    show_counts(dst)
    return 0


def show_counts(dst) -> None:
    print("Postgres row counts:")
    for table_name, _ in MODELS:
        n = dst.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"  {table_name:24s} {n:>3}")


if __name__ == '__main__':
    sys.exit(main())
