from datetime import datetime

from flask import Blueprint, jsonify, request, render_template

from models import db
from modules.events.models import Event, RSVP, EVENT_STATUSES, RSVP_STATUSES


bp = Blueprint(
    'events',
    __name__,
    url_prefix='/events',
    template_folder='../../templates/events',
)


@bp.route('/')
def list_page():
    return render_template('events/list.html')


@bp.route('/new')
def new_page():
    return render_template('events/form.html', event=None)


@bp.route('/<id>/edit')
def edit_page(id):
    event = Event.query.get_or_404(id)
    return render_template('events/form.html', event=event)


@bp.route('/<id>')
def detail_page(id):
    event = Event.query.get_or_404(id)
    return render_template('events/detail.html', event=event)


# ---------- API ----------

@bp.route('/api/events', methods=['GET'])
def list_events():
    q = (request.args.get('q') or '').strip()
    status = (request.args.get('status') or '').strip()
    upcoming_only = (request.args.get('upcoming') or '').lower() in ('1', 'true')
    sort = request.args.get('sort', '-date')

    query = Event.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Event.title.ilike(like),
                                    Event.description.ilike(like),
                                    Event.location.ilike(like)))
    if status:
        query = query.filter(Event.status == status)

    now = _utc_now()
    if upcoming_only:
        query = query.filter(Event.date >= now)

    sort_map = {
        'date': Event.date.asc(),
        '-date': Event.date.desc(),
        'title': Event.title,
        '-title': Event.title.desc(),
        'created_at': Event.created_at,
        '-created_at': Event.created_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Event.date.desc()))

    return jsonify([e.to_dict() for e in query.all()])


@bp.route('/api/events', methods=['POST'])
def create_event():
    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({'error': 'Missing field: title'}), 400
    event = Event(
        title=data['title'],
        description=data.get('description'),
        date=_parse_dt(data.get('date')),
        end_date=_parse_dt(data.get('end_date')),
        location=data.get('location'),
        organizer=data.get('organizer'),
        capacity=int(data.get('capacity') or 0),
        status=data.get('status', 'draft'),
    )
    if event.status not in EVENT_STATUSES:
        return jsonify({'error': f"Invalid status: {event.status}"}), 400
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@bp.route('/api/events/<id>', methods=['GET'])
def get_event(id):
    event = Event.query.get_or_404(id)
    return jsonify(event.to_dict(include_rsvps=True))


@bp.route('/api/events/<id>', methods=['PUT', 'PATCH'])
def update_event(id):
    event = Event.query.get_or_404(id)
    data = request.get_json() or {}
    for field in ('title', 'description', 'location', 'organizer'):
        if field in data:
            setattr(event, field, data[field])
    if 'date' in data:
        event.date = _parse_dt(data['date'])
    if 'end_date' in data:
        event.end_date = _parse_dt(data['end_date'])
    if 'capacity' in data:
        event.capacity = int(data['capacity'] or 0)
    if 'status' in data:
        if data['status'] not in EVENT_STATUSES:
            return jsonify({'error': f"Invalid status: {data['status']}"}), 400
        event.status = data['status']
    db.session.commit()
    return jsonify(event.to_dict())


@bp.route('/api/events/<id>', methods=['DELETE'])
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'deleted': True})


@bp.route('/api/events/<id>/rsvps', methods=['GET'])
def list_rsvps(id):
    event = Event.query.get_or_404(id)
    return jsonify([r.to_dict() for r in event.rsvps])


@bp.route('/api/events/<id>/rsvps', methods=['POST'])
def create_rsvp(id):
    event = Event.query.get_or_404(id)
    data = request.get_json() or {}
    status = data.get('status', 'attending')
    if status not in RSVP_STATUSES:
        return jsonify({'error': f"Invalid RSVP status: {status}"}), 400

    contact_id = data.get('contact_id') or None
    user_id = (data.get('user_id') or '').strip() or None
    if not contact_id and not user_id:
        return jsonify({'error': 'contact_id or user_id is required'}), 400

    # Keep one RSVP per attendee per event: update the existing one in place.
    rsvp = RSVP.query.filter_by(event_id=event.id, contact_id=contact_id, user_id=user_id).first()
    if rsvp:
        rsvp.status = status
        if 'notes' in data:
            rsvp.notes = data['notes']
    else:
        if status == 'attending' and event.is_full:
            status = 'waitlist'
        rsvp = RSVP(
            event_id=event.id,
            contact_id=contact_id,
            user_id=user_id,
            status=status,
            notes=data.get('notes', ''),
        )
        db.session.add(rsvp)
    db.session.commit()
    return jsonify(rsvp.to_dict()), 201


@bp.route('/api/events/<id>/rsvps/<rsvp_id>', methods=['PUT', 'PATCH'])
def update_rsvp(id, rsvp_id):
    event = Event.query.get_or_404(id)
    rsvp = RSVP.query.filter_by(id=rsvp_id, event_id=event.id).first_or_404()
    data = request.get_json() or {}
    if 'status' in data:
        if data['status'] not in RSVP_STATUSES:
            return jsonify({'error': f"Invalid RSVP status: {data['status']}"}), 400
        rsvp.status = data['status']
    if 'notes' in data:
        rsvp.notes = data['notes']
    db.session.commit()
    return jsonify(rsvp.to_dict())


@bp.route('/api/events/<id>/rsvps/<rsvp_id>', methods=['DELETE'])
def delete_rsvp(id, rsvp_id):
    event = Event.query.get_or_404(id)
    rsvp = RSVP.query.filter_by(id=rsvp_id, event_id=event.id).first_or_404()
    db.session.delete(rsvp)
    db.session.commit()
    return jsonify({'deleted': True})


@bp.route('/api/upcoming', methods=['GET'])
def upcoming():
    limit = int(request.args.get('limit', 10))
    q = Event.query.filter(
        Event.date >= _utc_now(),
        Event.status != 'cancelled',
    ).order_by(Event.date.asc())
    return jsonify([e.to_dict() for e in q.limit(limit).all()])


@bp.route('/api/stats', methods=['GET'])
def stats():
    total = Event.query.count()
    by_status = {s: Event.query.filter(Event.status == s).count() for s in EVENT_STATUSES}
    upcoming = Event.query.filter(
        Event.date >= _utc_now(), Event.status != 'cancelled'
    ).count()
    total_rsvps = RSVP.query.count()
    attending = RSVP.query.filter(RSVP.status == 'attending').count()
    return jsonify({
        'total_events': total,
        'upcoming': upcoming,
        'by_status': by_status,
        'total_rsvps': total_rsvps,
        'attending_rsvps': attending,
    })


@bp.route('/api/statuses', methods=['GET'])
def list_statuses():
    return jsonify({'event': EVENT_STATUSES, 'rsvp': RSVP_STATUSES})


def _utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


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
        return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None
