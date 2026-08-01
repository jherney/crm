"""
Rule engine for automations.

A rule has:
- trigger: one of TRIGGERS, with optional params (e.g. stage_change:negotiation)
- conditions: a small DSL, currently just a list of equality tests
- actions: a list of one or more action dicts

fire(event_name, payload) is called from elsewhere (deal move, activity
created, etc.). It loads all enabled rules whose trigger matches the
event, evaluates the conditions, and runs the matching actions.
"""
import json
from datetime import datetime, timezone, timedelta

from models import db
from modules.automations.models import AutomationRule, AutomationRun


# event_name -> registered trigger key
TRIGGERS = {
    'deal_stage_changed': 'deal_stage_changed',
    'deal_created':        'deal_created',
    'deal_value_changed':  'deal_value_changed',
    'activity_created':    'activity_created',
    'activity_completed':  'activity_completed',
    'activity_overdue':    'activity_overdue',
}


# action types
ACTIONS = {
    'create_activity': 'create_activity',
    'update_field':    'update_field',
    'send_email':      'send_email',
    'log':             'log',
}


def fire(event_name, payload):
    """Dispatch a single event to every matching rule.

    `payload` is a domain object:
      - deal payload: {deal: <Deal>, old_stage?, new_stage?}
      - activity payload: {activity: <Activity>}

    Returns a list of AutomationRun rows.
    """
    trigger_key = TRIGGERS.get(event_name)
    if not trigger_key:
        return []

    rules = AutomationRule.query.filter_by(
        trigger=trigger_key, is_enabled=True
    ).all()

    results = []
    for rule in rules:
        try:
            ran = _evaluate_and_run(rule, payload)
            results.append(ran)
        except Exception as e:  # never let one rule break the rest
            run = AutomationRun(
                rule_id=rule.id,
                event=event_name,
                payload=_safe_json(payload),
                status='error',
                message=str(e),
                ran_at=datetime.now(timezone.utc),
            )
            db.session.add(run)
            db.session.commit()
            results.append(run)
    return results


def _safe_json(payload):
    try:
        from modules.deals.models import Deal
        from modules.activities.models import Activity
        out = {}
        if 'deal' in payload and isinstance(payload['deal'], Deal):
            d = payload['deal']
            out['deal'] = {'id': d.id, 'name': d.name, 'stage': d.stage,
                           'value': d.value, 'probability': d.probability}
        if 'activity' in payload and isinstance(payload['activity'], Activity):
            a = payload['activity']
            out['activity'] = {'id': a.id, 'subject': a.subject, 'type': a.type}
        out['extra'] = {k: v for k, v in payload.items()
                        if k not in ('deal', 'activity')}
        return json.dumps(out, default=str)[:4000]
    except Exception:
        return json.dumps({'repr': repr(payload)})[:4000]


def _evaluate_and_run(rule, payload):
    if not _conditions_match(rule, payload):
        run = AutomationRun(rule_id=rule.id, event=rule.trigger,
                            payload=_safe_json(payload),
                            status='skipped', message='conditions not met',
                            ran_at=datetime.now(timezone.utc))
        db.session.add(run)
        db.session.commit()
        return run

    actions = rule.actions or []
    messages = []
    for action in actions:
        kind = action.get('type')
        if kind == 'create_activity':
            _action_create_activity(action, payload)
            messages.append('activity created')
        elif kind == 'update_field':
            _action_update_field(action, payload)
            messages.append('field updated')
        elif kind == 'send_email':
            _action_send_email(action, payload)
            messages.append('email logged')
        elif kind == 'log':
            messages.append(str(action.get('message', 'log')))
        else:
            messages.append(f'unknown action: {kind}')

    run = AutomationRun(rule_id=rule.id, event=rule.trigger,
                        payload=_safe_json(payload), status='success',
                        message='; '.join(messages),
                        ran_at=datetime.now(timezone.utc))
    db.session.add(run)
    db.session.commit()
    return run


def _conditions_match(rule, payload):
    """Each condition is `{field, op, value}`. op ∈ equals, not_equals, gt.
    `field` is dotted: deal.value, deal.stage, deal.contact_id, etc.
    Newer/wilder fields return None (≡ not matched).
    """
    conds = rule.conditions or []
    for c in conds:
        field = c.get('field', '')
        op = c.get('op', 'equals')
        expected = c.get('value')
        actual = _resolve_field(field, payload)
        if op == 'equals' and str(actual) != str(expected):
            return False
        if op == 'not_equals' and str(actual) == str(expected):
            return False
        if op == 'gt':
            try:
                if not (float(actual) > float(expected)):
                    return False
            except (TypeError, ValueError):
                return False
        if op == 'lt':
            try:
                if not (float(actual) < float(expected)):
                    return False
            except (TypeError, ValueError):
                return False
        if op == 'in' and actual not in (expected or []):
            return False
    return True


def _resolve_field(field, payload):
    cur = payload
    for part in field.split('.'):
        if cur is None:
            return None
        if hasattr(cur, part):
            cur = getattr(cur, part)
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    if callable(cur):
        try:
            cur = cur()
        except Exception:
            cur = None
    return cur


# ---------- Actions ----------

def _action_create_activity(action, payload):
    from modules.activities.models import Activity
    deal = payload.get('deal')
    activity = payload.get('activity')
    a = Activity(
        type=action.get('activity_type', 'task'),
        subject=action.get('subject', 'Follow up'),
        body=action.get('body'),
        deal_id=getattr(deal, 'id', None) if deal else None,
        contact_id=getattr(activity, 'contact_id', None) or (
            getattr(deal, 'contact_id', None) if deal else None
        ),
        company_id=getattr(activity, 'company_id', None) or (
            getattr(deal, 'company_id', None) if deal else None
        ),
        owner=action.get('owner'),
    )
    due_offset_days = action.get('due_in_days')
    if due_offset_days is not None:
        a.due_date = datetime.now(timezone.utc) + timedelta(days=int(due_offset_days))
    db.session.add(a)


def _action_update_field(action, payload):
    deal = payload.get('deal')
    if not deal:
        return
    field = action.get('field')
    value = action.get('value')
    if not field or not hasattr(deal, field):
        return
    setattr(deal, field, value)
    db.session.add(deal)
    # Will be committed alongside the AutomationRun in _evaluate_and_run


def _action_send_email(action, payload):
    """Log an email activity using a template (or a literal subject/body).
    Real SMTP can be wired later; for now this creates an Activity row.
    """
    from modules.activities.models import Activity
    deal = payload.get('deal')
    template_id = action.get('template_id')
    subject = action.get('subject', 'Email from automation')
    body = action.get('body', '')

    if template_id:
        from modules.email_templates.models import EmailTemplate
        tpl = EmailTemplate.query.get(template_id)
        if tpl:
            ctx = {
                'user': {'name': 'Automation', 'email': 'bot@example.com'},
                'deal': {
                    'name': getattr(deal, 'name', None),
                    'value': getattr(deal, 'value', None),
                    'stage': getattr(deal, 'stage', None),
                } if deal else {},
            }
            rendered = tpl.render(ctx)
            subject = rendered['subject']
            body = rendered['body']

    a = Activity(
        type='email',
        subject=subject,
        body=body,
        outcome='sent',
        completed=True,
    )
    a.completed_at = datetime.now(timezone.utc)
    if deal:
        a.deal_id = deal.id
        a.contact_id = getattr(deal, 'contact_id', None)
        a.company_id = getattr(deal, 'company_id', None)
    db.session.add(a)
