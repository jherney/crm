from datetime import date
from collections import defaultdict

from flask import Blueprint, jsonify, request, render_template

from models import db
from modules.deals.models import Deal, DEAL_STAGES, stage_meta


bp = Blueprint(
    'deals',
    __name__,
    url_prefix='/deals',
    template_folder='../../templates/deals',
)


@bp.route('/')
def list_page():
    return render_template('deals/list.html')


@bp.route('/pipeline')
def pipeline_page():
    return render_template('deals/pipeline.html')


@bp.route('/new')
def new_page():
    return render_template('deals/form.html', deal=None)


@bp.route('/<id>', methods=['GET'])
def detail_page(id):
    deal = Deal.query.get_or_404(id)
    return render_template('deals/detail.html', deal=deal)


@bp.route('/<id>/edit', methods=['GET'])
def edit_page(id):
    deal = Deal.query.get_or_404(id)
    return render_template('deals/form.html', deal=deal)


# ---------- API ----------

@bp.route('/api/deals', methods=['GET'])
def list_deals():
    q = request.args.get('q', '').strip()
    stage = request.args.get('stage', '').strip()
    company_id = request.args.get('company_id', '').strip()
    contact_id = request.args.get('contact_id', '').strip()
    sort = request.args.get('sort', '-created_at')

    query = Deal.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Deal.name.ilike(like), Deal.owner.ilike(like)))
    if stage:
        query = query.filter(Deal.stage == stage)
    if company_id:
        query = query.filter(Deal.company_id == company_id)
    if contact_id:
        query = query.filter(Deal.contact_id == contact_id)

    # Simple sort whitelist to keep the SQL predictable.
    sort_map = {
        'created_at': Deal.created_at,
        '-created_at': Deal.created_at.desc(),
        'name': Deal.name,
        '-name': Deal.name.desc(),
        'value': Deal.value,
        '-value': Deal.value.desc(),
        'expected_close_date': Deal.expected_close_date,
        '-expected_close_date': Deal.expected_close_date.desc(),
    }
    query = query.order_by(sort_map.get(sort, Deal.created_at.desc()))

    return jsonify([d.to_dict() for d in query.all()])


@bp.route('/api/deals', methods=['POST'])
def create_deal():
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'Missing field: name'}), 400
    expected_close = _parse_date(data.get('expected_close_date'))
    deal = Deal(
        name=data['name'],
        value=float(data.get('value') or 0),
        currency=data.get('currency') or 'USD',
        stage=data.get('stage') or 'prospect',
        probability=int(data.get('probability') or stage_meta(data.get('stage') or 'prospect')['probability']),
        expected_close_date=expected_close,
        source=data.get('source'),
        description=data.get('description'),
        tags=data.get('tags') or [],
        owner=data.get('owner'),
        contact_id=data.get('contact_id') or None,
        company_id=data.get('company_id') or None,
    )
    db.session.add(deal)
    db.session.commit()
    _fire_automation('deal_created', {'deal': deal})
    return jsonify(deal.to_dict()), 201


@bp.route('/api/deals/<id>', methods=['GET'])
def get_deal(id):
    deal = Deal.query.get_or_404(id)
    return jsonify(deal.to_dict())


@bp.route('/api/deals/<id>', methods=['PUT', 'PATCH'])
def update_deal(id):
    deal = Deal.query.get_or_404(id)
    data = request.get_json() or {}
    old_stage = deal.stage
    old_value = deal.value
    fields = ['name', 'value', 'currency', 'stage', 'probability',
              'expected_close_date', 'closed_at', 'source',
              'description', 'tags', 'owner', 'contact_id', 'company_id']
    for field in fields:
        if field not in data:
            continue
        if field == 'expected_close_date':
            deal.expected_close_date = _parse_date(data[field])
        elif field == 'closed_at':
            deal.closed_at = _parse_date(data[field])
        elif field == 'value':
            deal.value = float(data[field] or 0)
        elif field == 'probability':
            deal.probability = int(data[field] or 0)
        else:
            setattr(deal, field, data[field])

    # Auto-set the probability and closed_at when the stage changes
    if 'stage' in data:
        meta = stage_meta(deal.stage)
        if 'probability' not in data:
            deal.probability = meta['probability']
        if (meta['is_won'] or meta['is_lost']) and not deal.closed_at:
            deal.closed_at = date.today()

    db.session.commit()
    if deal.stage != old_stage:
        _fire_automation('deal_stage_changed', {
            'deal': deal,
            'old_stage': old_stage,
            'new_stage': deal.stage,
        })
    if deal.value != old_value:
        _fire_automation('deal_value_changed', {
            'deal': deal,
            'old_value': old_value,
            'new_value': deal.value,
        })
    return jsonify(deal.to_dict())


@bp.route('/api/deals/<id>', methods=['DELETE'])
def delete_deal(id):
    deal = Deal.query.get_or_404(id)
    db.session.delete(deal)
    db.session.commit()
    return jsonify({'deleted': True})


@bp.route('/api/deals/<id>/move', methods=['POST'])
def move_deal(id):
    """Dedicated endpoint for Kanban drag-and-drop. Body: {stage, probability?}.
    Sets probability/closed_at automatically based on the destination stage.
    """
    deal = Deal.query.get_or_404(id)
    data = request.get_json() or {}
    new_stage = data.get('stage')
    if not new_stage:
        return jsonify({'error': 'Missing field: stage'}), 400
    if not any(s['key'] == new_stage for s in DEAL_STAGES):
        return jsonify({'error': f'Unknown stage: {new_stage}'}), 400

    old_stage = deal.stage
    deal.stage = new_stage
    meta = stage_meta(new_stage)
    deal.probability = int(data.get('probability') or meta['probability'])
    if (meta['is_won'] or meta['is_lost']) and not deal.closed_at:
        deal.closed_at = date.today()
    db.session.commit()

    # Fire automation rules if stage actually changed.
    if old_stage != new_stage:
        _fire_automation('deal_stage_changed',
                         {'deal': deal, 'old_stage': old_stage,
                          'new_stage': new_stage})

    return jsonify(deal.to_dict())


@bp.route('/api/stages', methods=['GET'])
def list_stages():
    """Stages metadata for the UI. Each entry contains key, label, color, etc."""
    return jsonify(DEAL_STAGES)


@bp.route('/api/pipeline', methods=['GET'])
def pipeline():
    """Return all open deals grouped by stage, plus aggregate stats per stage.
    Closed deals can be included with ?include_closed=true.
    """
    include_closed = request.args.get('include_closed', 'false').lower() == 'true'
    open_keys = [s['key'] for s in DEAL_STAGES if not s['is_won'] and not s['is_lost']]

    q = Deal.query
    if not include_closed:
        q = q.filter(Deal.stage.in_(open_keys))

    deals = q.order_by(Deal.value.desc()).all()

    grouped = defaultdict(list)
    totals = {}
    for stage in DEAL_STAGES:
        totals[stage['key']] = {'count': 0, 'value': 0.0, 'weighted_value': 0.0}

    for d in deals:
        grouped[d.stage].append(d.to_dict())
        totals[d.stage]['count'] += 1
        totals[d.stage]['value'] += d.value or 0
        totals[d.stage]['weighted_value'] += d.computed_value()

    return jsonify({
        'stages': DEAL_STAGES,
        'deals_by_stage': grouped,
        'totals_by_stage': totals,
        'grand_total': {
            'count': len(deals),
            'value': round(sum((d.value or 0) for d in deals), 2),
            'weighted_value': round(sum(d.computed_value() for d in deals), 2),
        },
    })


@bp.route('/api/stats', methods=['GET'])
def stats():
    """Compact stats for the dashboard tile."""
    total = Deal.query.count()
    won = Deal.query.filter(Deal.stage == 'closed_won').count()
    open_count = total - won - Deal.query.filter(Deal.stage == 'closed_lost').count()
    value = sum((d.value or 0) for d in Deal.query.all())
    won_value = sum((d.value or 0) for d in Deal.query.filter(Deal.stage == 'closed_won').all())
    weighted = round(sum(d.computed_value() for d in Deal.query.all()), 2)
    return jsonify({
        'total': total,
        'open': open_count,
        'won': won,
        'lost': Deal.query.filter(Deal.stage == 'closed_lost').count(),
        'value': round(value, 2),
        'won_value': round(won_value, 2),
        'weighted_value': weighted,
    })


def _fire_automation(event, payload):
    from modules.automations.engine import fire
    return fire(event, payload)


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None
