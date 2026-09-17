from datetime import datetime, timezone, timedelta

from flask import Blueprint, jsonify, request, render_template

from models import db
from modules.activities.models import Activity, ACTIVITY_TYPES, ACTIVITY_OUTCOMES

bp = Blueprint(
    'activities',
    __name__,
    url_prefix='/activities',
    template_folder='../../templates/activities',
)


@bp.route('/')
def list_page():
    return render_template('activities/list.html')


@bp.route('/new')
def new_page():
    return render_template('activities/form.html', activity=None)


@bp.route('/<id>/edit')
def edit_page(id):
    activity = Activity.query.get_or_404(id)
    return render_template('activities/form.html', activity=activity)


# ---------- API ----------

@bp.route('/api/activities', methods=['GET'])
def list_activities():
    q = (request.args.get('q') or '').strip()
    type_ = (request.args.get('type') or '').strip()
    status = (request.args.get('status') or '').strip()  # 'open', 'completed', 'overdue'
    deal_id = (request.args.get('deal_id') or '').strip()
    contact_id = (request.args.get('contact_id') or '').strip()
    company_id = (request.args.get('company_id') or '').strip()
    sort = request.args.get('sort', '-due_date')

    query = Activity.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Activity.subject.ilike(like), Activity.body.ilike(like)))
    if type_:
        query = query.filter(Activity.type == type_)
    if deal_id:
        query = query.filter(Activity.deal_id == deal_id)
    if contact_id:
        query = query.filter(Activity.contact_id == contact_id)
    if company_id:
        query = query.filter(Activity.company_id == company_id)
    if status:
        if status == 'open':
            query = query.filter(Activity.completed == False)
        elif status == 'completed':
            query = query.filter(Activity.completed == True)
        elif status == 'overdue':
            query = query.filter(Activity.completed == False)
            query = query.filter(Activity.due_date < datetime.now(timezone.utc))

    sort_map = {
        'created_at': Activity.created_at,
        '-created_at': Activity.created_at.desc(),
        'due_date': Activity.due_date.asc(),
        '-due_date': Activity.due_date.desc(),
        'subject': Activity.subject,
        '-subject': Activity.subject.desc(),
    }
    # SQLite doesn't support nullslast() — fall back to created_at when ordering
    # by due_date if the chosen order isn't supported.
    sort_expr = sort_map.get(sort, Activity.created_at.desc())
    try:
        query = query.order_by(sort_expr)
    except Exception:
        query = query.order_by(Activity.created_at.desc())
    return jsonify([a.to_dict() for a in query.all()])


@bp.route('/api/activities', methods=['POST'])
def create_activity():
    data = request.get_json() or {}
    if not data.get('subject'):
        return jsonify({'error': 'Missing field: subject'}), 400
    activity = Activity(
        type=data.get('type', 'task'),
        subject=data['subject'],
        body=data.get('body'),
        due_date=_parse_dt(data.get('due_date')),
        completed=bool(data.get('completed', False)),
        outcome=data.get('outcome', ''),
        owner=data.get('owner'),
        deal_id=data.get('deal_id') or None,
        contact_id=data.get('contact_id') or None,
        company_id=data.get('company_id') or None,
    )
    db.session.add(activity)
    db.session.commit()
    _fire_automation('activity_created', {'activity': activity})
    return jsonify(activity.to_dict()), 201


@bp.route('/api/activities/<id>', methods=['GET'])
def get_activity(id):
    a = Activity.query.get_or_404(id)
    return jsonify(a.to_dict())


@bp.route('/api/activities/<id>', methods=['PUT', 'PATCH'])
def update_activity(id):
    a = Activity.query.get_or_404(id)
    data = request.get_json() or {}
    was_completed = a.completed
    for field in ['type', 'subject', 'body', 'outcome', 'owner',
                  'deal_id', 'contact_id', 'company_id']:
        if field in data:
            setattr(a, field, data[field])
    if 'due_date' in data:
        a.due_date = _parse_dt(data['due_date'])
    if 'completed' in data:
        a.completed = bool(data['completed'])
        if not was_completed and a.completed:
            a.completed_at = datetime.now(timezone.utc)
        elif was_completed and not a.completed:
            a.completed_at = None
    db.session.commit()
    if not was_completed and a.completed:
        _fire_automation('activity_completed', {'activity': a})
    return jsonify(a.to_dict())


@bp.route('/api/activities/<id>', methods=['DELETE'])
def delete_activity(id):
    a = Activity.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    return jsonify({'deleted': True})


@bp.route('/api/activities/<id>/complete', methods=['POST'])
def complete_activity(id):
    """Convenience endpoint for the UI's 'Mark complete' button."""
    a = Activity.query.get_or_404(id)
    was_completed = a.completed
    a.completed = True
    a.completed_at = datetime.now(timezone.utc)
    data = request.get_json(silent=True) or {}
    if 'outcome' in data:
        a.outcome = data['outcome']
    db.session.commit()
    if not was_completed:
        _fire_automation('activity_completed', {'activity': a})
    return jsonify(a.to_dict())


@bp.route('/api/upcoming', methods=['GET'])
def upcoming():
    """Open activities with due_date >= now, ordered."""
    limit = int(request.args.get('limit', 10))
    q = Activity.query.filter(
        Activity.completed == False,
    ).order_by(Activity.due_date.asc().nullslast())
    return jsonify([a.to_dict() for a in q.limit(limit).all()])


@bp.route('/api/overdue', methods=['GET'])
def overdue():
    q = Activity.query.filter(
        Activity.completed == False,
        Activity.due_date < datetime.now(timezone.utc),
    ).order_by(Activity.due_date.asc())
    return jsonify([a.to_dict() for a in q.all()])


@bp.route('/api/stats', methods=['GET'])
def stats():
    now = datetime.now(timezone.utc)
    total = Activity.query.count()
    open_ = Activity.query.filter(Activity.completed == False).count()
    overdue = Activity.query.filter(
        Activity.completed == False, Activity.due_date < now
    ).count()
    done_24h = Activity.query.filter(
        Activity.completed == True,
        Activity.completed_at >= now - timedelta(hours=24),
    ).count()
    by_type = {}
    for t in ACTIVITY_TYPES:
        by_type[t] = Activity.query.filter(Activity.type == t).count()
    return jsonify({
        'total': total,
        'open': open_,
        'overdue': overdue,
        'completed_last_24h': done_24h,
        'by_type': by_type,
    })


@bp.route('/api/types', methods=['GET'])
def list_types():
    return jsonify(ACTIVITY_TYPES)


@bp.route('/api/outcomes', methods=['GET'])
def list_outcomes():
    return jsonify(ACTIVITY_OUTCOMES)


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value)
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        # ISO format
        return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None


def _fire_automation(event, payload):
    from modules.automations.engine import fire
    return fire(event, payload)


def _dispatch(event, payload):
    return _fire_automation(event, payload)
