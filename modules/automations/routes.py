from flask import Blueprint, jsonify, request, render_template

from models import db
from modules.automations.models import AutomationRule, AutomationRun
from modules.automations.engine import TRIGGERS, ACTIONS

bp = Blueprint(
    'automations',
    __name__,
    url_prefix='/automations',
    template_folder='../../templates/automations',
)


@bp.route('/')
def list_page():
    return render_template('automations/list.html')


@bp.route('/runs')
def runs_page():
    return render_template('automations/runs.html')


@bp.route('/new')
def new_page():
    return render_template('automations/form.html', rule=None)


@bp.route('/<id>')
def detail_page(id):
    rule = AutomationRule.query.get_or_404(id)
    return render_template('automations/detail.html', rule=rule)


@bp.route('/<id>/edit')
def edit_page(id):
    rule = AutomationRule.query.get_or_404(id)
    return render_template('automations/form.html', rule=rule)


# ---------- API ----------

@bp.route('/api/rules', methods=['GET'])
def list_rules():
    return jsonify([r.to_dict() for r in AutomationRule.query.order_by(AutomationRule.name).all()])


@bp.route('/api/rules', methods=['POST'])
def create_rule():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('trigger') or not data.get('actions'):
        return jsonify({'error': 'name, trigger, and actions are required'}), 400
    rule = AutomationRule(
        name=data['name'],
        description=data.get('description'),
        trigger=data['trigger'],
        trigger_param=data.get('trigger_param'),
        conditions=data.get('conditions') or [],
        actions=data['actions'],
        is_enabled=bool(data.get('is_enabled', True)),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(rule.to_dict()), 201


@bp.route('/api/rules/<id>', methods=['GET'])
def get_rule(id):
    return jsonify(AutomationRule.query.get_or_404(id).to_dict())


@bp.route('/api/rules/<id>', methods=['PUT', 'PATCH'])
def update_rule(id):
    rule = AutomationRule.query.get_or_404(id)
    data = request.get_json() or {}
    for f in ('name', 'description', 'trigger', 'trigger_param', 'conditions', 'actions'):
        if f in data:
            setattr(rule, f, data[f])
    if 'is_enabled' in data:
        rule.is_enabled = bool(data['is_enabled'])
    db.session.commit()
    return jsonify(rule.to_dict())


@bp.route('/api/rules/<id>', methods=['DELETE'])
def delete_rule(id):
    rule = AutomationRule.query.get_or_404(id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({'deleted': True})


@bp.route('/api/rules/<id>/toggle', methods=['POST'])
def toggle_rule(id):
    rule = AutomationRule.query.get_or_404(id)
    rule.is_enabled = not rule.is_enabled
    db.session.commit()
    return jsonify(rule.to_dict())


@bp.route('/api/runs', methods=['GET'])
def list_runs():
    limit = int(request.args.get('limit', 50))
    q = AutomationRun.query.order_by(AutomationRun.ran_at.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in q])


@bp.route('/api/triggers', methods=['GET'])
def list_triggers():
    labels = {
        'deal_stage_changed': 'When a deal moves to a stage',
        'deal_created':        'When a deal is created',
        'deal_value_changed':  'When a deal value changes',
        'activity_created':    'When an activity is logged',
        'activity_completed':  'When an activity is completed',
        'activity_overdue':    'When an activity becomes overdue',
    }
    return jsonify([{'key': k, 'label': labels.get(k, k)} for k in TRIGGERS.keys()])


@bp.route('/api/actions', methods=['GET'])
def list_actions():
    labels = {
        'create_activity': 'Create an activity (task/call/email/meeting)',
        'update_field':    'Update a field on the related deal',
        'send_email':      'Send an email (logs it as an activity)',
        'log':             'Just log a note',
    }
    return jsonify([{'key': k, 'label': labels.get(k, k)} for k in ACTIONS.keys()])


@bp.route('/api/test', methods=['POST'])
def test_rule():
    """Manually fire a rule against a synthetic payload to validate it works."""
    data = request.get_json() or {}
    rule_id = data.get('rule_id')
    event = data.get('event', 'deal_stage_changed')
    if rule_id:
        rule = AutomationRule.query.get(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        # Force-enable for the test
        rule.is_enabled = True
    from modules.automations.engine import fire
    payload = data.get('payload', {})
    runs = fire(event, payload)
    return jsonify([r.to_dict() for r in runs])
