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


TRIGGERS = {
    'deal_stage_changed': 'deal_stage_changed',
    'deal_created':        'deal_created',
    'deal_value_changed':  'deal_value_changed',
    'activity_created':    'activity_created',
    'activity_completed':  'activity_completed',
    'activity_overdue':    'activity_overdue',
}


ACTIONS = {
    'create_activity': 'create_activity',
    'update_field':    'update_field',
    'send_email':      'send_email',
    'log':             'log',
}


DEAL_IDENTIFYING_FIELDS = {
    'stage', 'value', 'probability', 'currency', 'source', 'owner',
    'contact_id', 'company_id',
}
ACTIVITY_IDENTIFYING_FIELDS = {
    'id', 'type', 'subject', 'body', 'due_date', 'completed',
    'completed_at', 'outcome', 'owner', 'deal_id', 'contact_id',
    'company_id', 'deal', 'contact', 'company',
}


def normalize_payload(payload):
    if payload is None:
        return {}
    if isinstance(payload, dict):
        if _looks_like_deal(payload):
            return {'deal': _normalize_record(payload)}
        if _looks_like_activity(payload):
            return {'activity': _normalize_record(payload)}
        return {
            key: _normalize_value(value)
            for key, value in payload.items()
        }
    if _is_deal_record(payload):
        return {'deal': _normalize_record(payload)}
    if _is_activity_record(payload):
        return {'activity': _normalize_record(payload)}
    if hasattr(payload, '__dict__'):
        return normalize_payload(vars(payload))
    return {'value': _normalize_value(payload)}


def _looks_like_deal(value):
    if not isinstance(value, dict):
        return False
    return bool(set(value).intersection(DEAL_IDENTIFYING_FIELDS))


def _looks_like_activity(value):
    if not isinstance(value, dict):
        return False
    return (
        'subject' in value
        and bool(set(value).intersection(ACTIVITY_IDENTIFYING_FIELDS))
    )


def _is_deal_record(value):
    return (
        hasattr(value, 'stage')
        and hasattr(value, 'value')
        and hasattr(value, 'probability')
    )


def _is_activity_record(value):
    return (
        hasattr(value, 'subject')
        and hasattr(value, 'type')
        and hasattr(value, 'completed')
    )


def _normalize_record(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return _normalize_mapping(value)

    normalized = None
    if hasattr(value, 'to_dict') and callable(value.to_dict):
        try:
            normalized = _normalize_mapping(value.to_dict())
        except Exception:
            pass
    if normalized is None and hasattr(value, '__table__'):
        data = {
            column.name: getattr(value, column.name, None)
            for column in value.__table__.columns
        }
        normalized = _normalize_mapping(data)
    if normalized is None and hasattr(value, '__dict__'):
        normalized = _normalize_mapping(vars(value))
    if normalized is None and hasattr(value, 'isoformat'):
        try:
            normalized = value.isoformat()
        except Exception:
            normalized = str(value)
    if normalized is None and (
        value is None or isinstance(value, (str, int, float, bool))
    ):
        normalized = value
    if normalized is None:
        normalized = str(value)
    if _is_activity_record(value):
        for relationship in ('deal', 'contact', 'company'):
            related = getattr(value, relationship, None)
            if related is not None:
                normalized[relationship] = _normalize_record(related)
    return normalized


def _normalize_mapping(value):
    normalized = {}
    for key, item in value.items():
        normalized[key] = _normalize_value(item)
    return normalized


def _normalize_value(value):
    if isinstance(value, dict):
        return _normalize_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    if _is_deal_record(value) or _is_activity_record(value):
        return _normalize_record(value)
    if hasattr(value, 'to_dict') and callable(value.to_dict):
        return _normalize_record(value)
    if hasattr(value, '__table__'):
        return _normalize_record(value)
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except Exception:
            pass
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _safe_json(payload):
    try:
        return json.dumps(normalize_payload(payload), default=str)[:4000]
    except Exception:
        return json.dumps({'repr': repr(payload)})[:4000]


class AutomationActionAdapter:
    def execute(self, action, payload):
        kind = action.get('type')
        if kind == 'create_activity':
            _action_create_activity(action, payload)
            return 'activity created'
        if kind == 'update_field':
            _action_update_field(action, payload)
            return 'field updated'
        if kind == 'send_email':
            _action_send_email(action, payload)
            return 'email logged'
        if kind == 'log':
            return str(action.get('message', 'log'))
        raise ValueError(f'unknown action type: {kind}')


class AutomationEngine:
    def __init__(self, action_adapter=None):
        self.action_adapter = action_adapter or AutomationActionAdapter()

    def fire(self, event_name, payload):
        trigger_key = TRIGGERS.get(event_name)
        if not trigger_key:
            return []

        try:
            normalized_payload = normalize_payload(payload)
            rules = AutomationRule.query.filter_by(
                trigger=trigger_key, is_enabled=True
            ).order_by(AutomationRule.id).all()
        except Exception as exc:
            try:
                return [self._record_error(
                    None, event_name, payload, exc
                )]
            except Exception:
                return []

        results = []
        for rule in rules:
            try:
                with db.session.begin_nested():
                    run = self._evaluate_and_run(
                        rule, normalized_payload, payload
                    )
                db.session.commit()
                results.append(run)
            except Exception as exc:
                results.append(self._record_error(
                    rule, event_name, normalized_payload, exc
                ))
        return results

    def _evaluate_and_run(self, rule, normalized_payload, payload):
        if not _conditions_match(rule, normalized_payload):
            run = AutomationRun(
                rule_id=rule.id,
                event=rule.trigger,
                payload=_safe_json(normalized_payload),
                status='skipped',
                message='conditions not met',
                ran_at=datetime.now(timezone.utc),
            )
            db.session.add(run)
            return run

        messages = []
        for action in rule.actions or []:
            messages.append(self.action_adapter.execute(action, payload))

        run = AutomationRun(
            rule_id=rule.id,
            event=rule.trigger,
            payload=_safe_json(normalized_payload),
            status='success',
            message='; '.join(messages),
            ran_at=datetime.now(timezone.utc),
        )
        db.session.add(run)
        return run

    def _record_error(self, rule, event_name, normalized_payload, exc):
        run = AutomationRun(
            rule_id=rule.id if rule else None,
            event=event_name,
            payload=_safe_json(normalized_payload),
            status='error',
            message=str(exc),
            ran_at=datetime.now(timezone.utc),
        )
        db.session.add(run)
        db.session.commit()
        return run


engine = AutomationEngine()


def fire(event_name, payload):
    return engine.fire(event_name, payload)


def _conditions_match(rule, payload):
    conds = rule.conditions or []
    for condition in conds:
        field = condition.get('field', '')
        op = condition.get('op', 'equals')
        expected = condition.get('value')
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
        if op not in ('equals', 'not_equals', 'gt', 'lt', 'in'):
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
            if part in cur:
                cur = cur.get(part)
            elif part in payload:
                cur = payload.get(part)
            else:
                return None
        else:
            return None
    if callable(cur):
        try:
            cur = cur()
        except Exception:
            cur = None
    return cur


def _get_value(record, field, default=None):
    if isinstance(record, dict):
        return record.get(field, default)
    return getattr(record, field, default)


def _resolve_activity(payload):
    if _is_activity_record(payload):
        return payload
    if isinstance(payload, dict):
        activity = payload.get('activity')
        if _is_activity_record(activity) or _looks_like_activity(activity):
            return activity
        if _looks_like_activity(payload):
            return payload
    return None


def _resolve_deal(payload):
    if _is_deal_record(payload) or _looks_like_deal(payload):
        return payload
    if isinstance(payload, dict):
        deal = payload.get('deal')
        if _is_deal_record(deal) or _looks_like_deal(deal):
            return deal

    activity = _resolve_activity(payload)
    if activity:
        related = _get_value(activity, 'deal', None)
        if related:
            return related
        deal_id = _get_value(activity, 'deal_id', None)
        if deal_id:
            from modules.deals.models import Deal
            return Deal.query.get(deal_id)
    return None


def _action_create_activity(action, payload):
    from modules.activities.models import Activity

    activity = _resolve_activity(payload)
    deal = _resolve_deal(payload)
    activity_deal = _get_value(activity, 'deal', None) if activity else None
    a = Activity(
        type=action.get('activity_type', 'task'),
        subject=action.get('subject', 'Follow up'),
        body=action.get('body'),
        deal_id=(
            _get_value(activity, 'deal_id', None)
            if activity else None
        ) or _get_value(activity_deal, 'id', None) or (
            _get_value(deal, 'id', None) if deal else None
        ),
        contact_id=_get_value(activity, 'contact_id', None) or (
            _get_value(deal, 'contact_id', None) if deal else None
        ),
        company_id=_get_value(activity, 'company_id', None) or (
            _get_value(deal, 'company_id', None) if deal else None
        ),
        owner=action.get('owner'),
    )
    due_offset_days = action.get('due_in_days')
    if due_offset_days is not None:
        a.due_date = datetime.now(timezone.utc) + timedelta(days=int(due_offset_days))
    db.session.add(a)


def _action_update_field(action, payload):
    deal = _resolve_deal(payload)
    if not deal:
        return
    field = action.get('field')
    value = action.get('value')
    if not field:
        return
    if isinstance(deal, dict):
        deal[field] = value
    elif hasattr(deal, field):
        setattr(deal, field, value)
        db.session.add(deal)


def _action_send_email(action, payload):
    from modules.activities.models import Activity

    deal = _resolve_deal(payload)
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
                    'name': _get_value(deal, 'name', None),
                    'value': _get_value(deal, 'value', None),
                    'stage': _get_value(deal, 'stage', None),
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
        a.deal_id = _get_value(deal, 'id', None)
        a.contact_id = _get_value(deal, 'contact_id', None)
        a.company_id = _get_value(deal, 'company_id', None)
    db.session.add(a)


def _evaluate_and_run(rule, payload):
    normalized_payload = normalize_payload(payload)
    try:
        with db.session.begin_nested():
            run = engine._evaluate_and_run(
                rule, normalized_payload, payload
            )
        db.session.commit()
        return run
    except Exception as exc:
        return engine._record_error(
            rule, rule.trigger, normalized_payload, exc
        )
