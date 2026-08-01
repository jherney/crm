#!/usr/bin/env bash
# runner.sh — start/stop/restart the Modular CRM
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$ROOT/.crm.pid"
PORT="${CRM_PORT:-5001}"

# Ensure user-site-packages (psycopg2, sqlalchemy, flask) are importable
# when this shell doesn't already have PYTHONUSERBASES set (cron, systemd, etc).
if [ -z "${PYTHONPATH:-}" ] && [ -d "/home/jherney/.local/lib/python3.14/site-packages" ]; then
    export PYTHONPATH="/home/jherney/.local/lib/python3.14/site-packages"
fi

# Determine the database URL.
# Priority:
#   1. CRM_DATABASE_URL env var (verbatim)
#   2. AUTO_PG=1 with running podman container `crm-postgres` → build URL
#      from container env (so users don't have to retype the password)
#   3. file $ROOT/.pg-url (Mode 600, plain text)
#   4. Default to local SQLite.
DEFAULT_SQLITE="sqlite:///$ROOT/crm.db"
if [ -n "${CRM_DATABASE_URL:-}" ]; then
    DB_URL="$CRM_DATABASE_URL"
elif [ "${AUTO_PG:-0}" = "1" ] && command -v podman >/dev/null 2>&1 \
     && podman container exists crm-postgres 2>/dev/null; then
    PG_HOST="${PG_HOST:-127.0.0.1}"
    PG_PORT="${PG_PORT:-5433}"
    PG_USER="${PG_USER:-crm}"
    PG_DB="${PG_DB:-crm}"
    PG_PW="$(podman exec crm-postgres printenv POSTGRES_PASSWORD 2>/dev/null || true)"
    if [ -n "$PG_PW" ]; then
        # DB_URL built entirely in shell so the password is never visible
        # in the parent shell history. HEREDOC-driven.
        DB_URL="$(printf 'postgresql://%s:%s@%s:%s/%s' \
            "$PG_USER" "$PG_PW" "$PG_HOST" "$PG_PORT" "$PG_DB")"
        echo "[runner] Auto-built Postgres URL from crm-postgres container"
    else
        DB_URL="$DEFAULT_SQLITE"
    fi
elif [ -f "$ROOT/.pg-url" ]; then
    DB_URL="$(cat "$ROOT/.pg-url")"
else
    DB_URL="$DEFAULT_SQLITE"
fi
export CRM_DATABASE_URL="$DB_URL"
case "$DB_URL" in
    postgresql://*) echo "[runner] CRM_DATABASE_URL=postgresql://***@${DB_URL#*@}" ;;
    *)              echo "[runner] CRM_DATABASE_URL=$DB_URL" ;;
esac

case "${1:-help}" in
    start)
        if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
            echo "CRM already running on PID $(cat "$PIDFILE")"
            exit 0
        fi
        cd "$ROOT"
        nohup python3 run.py > "$ROOT/crm.log" 2>&1 &
        echo $! > "$PIDFILE"
        echo "CRM started on http://0.0.0.0:$PORT (PID $!)"
        ;;
    stop)
        if [ -f "$PIDFILE" ]; then
            kill "$(cat "$PIDFILE")" 2>/dev/null || true
            rm -f "$PIDFILE"
            echo "CRM stopped"
        else
            echo "No PID file found"
        fi
        ;;
    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;
    dev)
        cd "$ROOT"
        python3 run.py
        ;;
    test)
        cd "$ROOT"
        python3 tests/test_smoke.py
        ;;
    status)
        if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
            echo "CRM running on PID $(cat "$PIDFILE")"
        else
            echo "CRM not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|dev|test|status}"
        ;;
esac
