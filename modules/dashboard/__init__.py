NAME = 'Dashboard'
SLUG = 'dashboard'
DESCRIPTION = 'Overview, KPIs, pipeline totals, and recent activity.'
ENABLED = True

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from database import db


bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@bp.route('/')
def index():
    return render_template('dashboard.html')


@bp.route('/api/stats')
def stats():
    contacts_count = _count('contacts')
    companies_count = _count('companies')
    deals_count = _count('deals')

    recent_contacts = db.session.execute(
        text("SELECT id, first_name, last_name, email, status, created_at "
             "FROM contacts ORDER BY created_at DESC LIMIT 5")
    ).mappings().all()

    recent_deals = db.session.execute(
        text("SELECT id, name, value, currency, stage, probability, expected_close_date "
             "FROM deals ORDER BY created_at DESC LIMIT 5")
    ).mappings().all()

    pipeline_row = db.session.execute(
        text("SELECT COUNT(*) AS c, COALESCE(SUM(value),0) AS value_sum, "
             "COALESCE(SUM(value * probability / 100.0),0) AS weighted_sum "
             "FROM deals WHERE stage NOT IN ('closed_won','closed_lost')")
    ).mappings().first()

    won_row = db.session.execute(
        text("SELECT COUNT(*) AS c, COALESCE(SUM(value),0) AS value_sum "
             "FROM deals WHERE stage = 'closed_won'")
    ).mappings().first()

    upcoming_activities = db.session.execute(
        text("SELECT a.id, a.subject, a.due_date, a.completed, a.type, "
             "       d.id AS deal_id, d.name AS deal_name "
             "FROM activities a LEFT JOIN deals d ON d.id = a.deal_id "
             "WHERE a.completed = false "
             "ORDER BY (a.due_date IS NULL), a.due_date ASC "
             "LIMIT 8")
    ).mappings().all()

    # Activities aggregate (total / open / overdue)
    from datetime import datetime, timezone
    iso_now = datetime.now(timezone.utc).isoformat()
    activities_stats = db.session.execute(
        text("SELECT "
             "  COUNT(*) AS total, "
             "  SUM(CASE WHEN completed = false THEN 1 ELSE 0 END) AS open_count, "
             "  SUM(CASE WHEN completed = false AND due_date IS NOT NULL AND due_date < :now THEN 1 ELSE 0 END) AS overdue "
             "FROM activities"),
        {'now': iso_now}
    ).mappings().first()

    return jsonify({
        'contacts': contacts_count,
        'companies': companies_count,
        'deals': deals_count,
        'pipeline': {
            'open_count': pipeline_row['c'] if pipeline_row else 0,
            'open_value': round(pipeline_row['value_sum'] or 0, 2) if pipeline_row else 0,
            'weighted_value': round(pipeline_row['weighted_sum'] or 0, 2) if pipeline_row else 0,
            'won_count': won_row['c'] if won_row else 0,
            'won_value': round(won_row['value_sum'] or 0, 2) if won_row else 0,
        },
        'activities': {
            'total': (activities_stats['total'] if activities_stats else 0) or 0,
            'open': (activities_stats['open_count'] if activities_stats else 0) or 0,
            'overdue': (activities_stats['overdue'] if activities_stats else 0) or 0,
        },
        'recent_contacts': [_serialize_contact(c) for c in recent_contacts],
        'recent_deals': [_serialize_deal(d) for d in recent_deals],
        'upcoming_activities': [_serialize_activity(a) for a in upcoming_activities],
    })


@bp.route('/api/forecast')
def forecast():
    """Returns pipeline-by-stage (excluding closed) and a months-out forecast
    based on each open deal's expected_close_date.
    """
    # Pipeline by stage (open only) — read like the deals pipeline endpoint
    open_stages_rows = db.session.execute(
        text("SELECT stage, COUNT(*) AS count, COALESCE(SUM(value),0) AS value, "
             "       COALESCE(SUM(value * probability / 100.0), 0) AS weighted_value "
             "FROM deals "
             "WHERE stage NOT IN ('closed_won', 'closed_lost') "
             "GROUP BY stage")
    ).mappings().all()

    desired_order = ['prospect', 'qualified', 'proposal', 'negotiation']
    buckets = {k: {'stage': k, 'count': 0, 'value': 0.0, 'weighted_value': 0.0}
               for k in desired_order}
    for row in open_stages_rows:
        if row['stage'] in buckets:
            buckets[row['stage']] = {
                'stage': row['stage'],
                'count': row['count'],
                'value': round(row['value'] or 0, 2),
                'weighted_value': round(row['weighted_value'] or 0, 2),
            }
    pipeline_by_stage = [buckets[k] for k in desired_order]

    # Forecast by month (next 6 months from now)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(day=1)
    months = []
    for i in range(6):
        m = _add_months(now, i)
        months.append({'label': m.strftime('%b %Y'),
                       'start': m.isoformat(),
                       'value': 0.0, 'weighted_value': 0.0, 'count': 0})

    forecast_rows = db.session.execute(
        text("SELECT id, name, value, probability, expected_close_date "
             "FROM deals "
             "WHERE stage NOT IN ('closed_won', 'closed_lost') "
             "AND expected_close_date IS NOT NULL")
    ).mappings().all()

    for d in forecast_rows:
        if not d['expected_close_date']:
            continue
        d_close = d['expected_close_date']
        # Group by YYYY-MM
        key = d_close.strftime('%Y-%m')
        for m in months:
            if m['label'].endswith(key.split('-')[0] + ' ' + _ym_label(d_close)):
                pass
        # Simpler: bucket by matching the month string inside the label
        m_label_short = d_close.strftime('%b %Y')
        for m in months:
            if m['label'] == m_label_short:
                m['value'] += (d['value'] or 0)
                m['weighted_value'] += (d['value'] or 0) * (d['probability'] or 0) / 100.0
                m['count'] += 1
                break

    for m in months:
        m['value'] = round(m['value'], 2)
        m['weighted_value'] = round(m['weighted_value'], 2)

    return jsonify({
        'pipeline_by_stage': pipeline_by_stage,
        'monthly': months,
    })


@bp.route('/api/winrate')
def winrate():
    """Won vs Lost deals by month (last 6 months)."""
    from datetime import datetime, timezone
    months = []
    now = datetime.now(timezone.utc).replace(day=1)
    for i in range(5, -1, -1):
        m = _add_months(now, -i)
        months.append({'label': m.strftime('%b %Y'), 'start': m,
                       'won': 0, 'lost': 0})

    rows = db.session.execute(
        text("SELECT stage, closed_at FROM deals "
             "WHERE stage IN ('closed_won', 'closed_lost') "
             "AND closed_at IS NOT NULL")
    ).all()
    for stage, closed_at in rows:
        if not closed_at:
            continue
        m_label = closed_at.strftime('%b %Y')
        for m in months:
            if m['label'] == m_label:
                if stage == 'closed_won':
                    m['won'] += 1
                elif stage == 'closed_lost':
                    m['lost'] += 1
                break
    return jsonify(months)


@bp.route('/api/activity-by-type')
def activity_by_type():
    cutoff = datetime.utcnow() - timedelta(days=30)
    rows = db.session.execute(
        text("SELECT type, COUNT(*) AS count FROM activities "
             "WHERE created_at >= :cutoff "
             "GROUP BY type ORDER BY count DESC"),
        {'cutoff': cutoff}
    ).mappings().all()
    return jsonify([{'type': r['type'], 'count': r['count']} for r in rows])


def _count(table):
    try:
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        return int(result or 0)
    except Exception:
        return 0


def _add_months(dt, n):
    import calendar
    year = dt.year + (dt.month - 1 + n) // 12
    month = (dt.month - 1 + n) % 12 + 1
    return dt.replace(year=year, month=month, day=1)


def _ym_label(dt):
    return dt.strftime('%b %Y')


def _serialize_contact(row):
    return {
        'id': row['id'],
        'full_name': f"{row['first_name']} {row['last_name'] or ''}".strip(),
        'email': row['email'],
        'status': row['status'],
        'created_at': str(row['created_at']) if row['created_at'] else None,
    }


def _serialize_deal(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'value': row['value'] or 0,
        'currency': row['currency'] or 'USD',
        'stage': row['stage'],
        'probability': row['probability'] or 0,
        'expected_close_date': str(row['expected_close_date']) if row['expected_close_date'] else None,
    }


def _serialize_activity(row):
    return {
        'id': row['id'],
        'subject': row['subject'],
        'due_date': str(row['due_date']) if row['due_date'] else None,
        'completed': bool(row['completed']),
        'type': row['type'],
        'deal': {'id': row['deal_id'], 'name': row['deal_name']} if row['deal_id'] else None,
    }


def register(app):
    app.register_blueprint(bp)
    return bp
