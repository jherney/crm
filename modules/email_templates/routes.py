from flask import Blueprint, jsonify, request, render_template

from models import db
from modules.email_templates.models import EmailTemplate, MERGE_FIELDS


bp = Blueprint(
    'email_templates',
    __name__,
    url_prefix='/email-templates',
    template_folder='../../templates/email_templates',
)


@bp.route('/')
def list_page():
    return render_template('email_templates/list.html')


@bp.route('/new')
def new_page():
    return render_template('email_templates/form.html', template=None)


@bp.route('/<id>')
def detail_page(id):
    tpl = EmailTemplate.query.get_or_404(id)
    return render_template('email_templates/detail.html', template=tpl)


@bp.route('/<id>/edit')
def edit_page(id):
    tpl = EmailTemplate.query.get_or_404(id)
    return render_template('email_templates/form.html', template=tpl)


# ---------- API ----------

@bp.route('/api/templates', methods=['GET'])
def list_templates():
    q = (request.args.get('q') or '').strip()
    category = (request.args.get('category') or '').strip()
    query = EmailTemplate.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(EmailTemplate.name.ilike(like),
                                    EmailTemplate.subject.ilike(like)))
    if category:
        query = query.filter(EmailTemplate.category == category)
    return jsonify([t.to_dict() for t in query.order_by(EmailTemplate.name).all()])


@bp.route('/api/templates', methods=['POST'])
def create_template():
    data = request.get_json() or {}
    for f in ('name', 'subject', 'body'):
        if not data.get(f):
            return jsonify({'error': f'Missing field: {f}'}), 400
    tpl = EmailTemplate(
        name=data['name'],
        subject=data['subject'],
        body=data['body'],
        category=data.get('category', 'general'),
        is_active=bool(data.get('is_active', True)),
    )
    db.session.add(tpl)
    db.session.commit()
    return jsonify(tpl.to_dict()), 201


@bp.route('/api/templates/<id>', methods=['GET'])
def get_template(id):
    tpl = EmailTemplate.query.get_or_404(id)
    return jsonify(tpl.to_dict())


@bp.route('/api/templates/<id>', methods=['PUT', 'PATCH'])
def update_template(id):
    tpl = EmailTemplate.query.get_or_404(id)
    data = request.get_json() or {}
    for f in ('name', 'subject', 'body', 'category'):
        if f in data:
            setattr(tpl, f, data[f])
    if 'is_active' in data:
        tpl.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify(tpl.to_dict())


@bp.route('/api/templates/<id>', methods=['DELETE'])
def delete_template(id):
    tpl = EmailTemplate.query.get_or_404(id)
    db.session.delete(tpl)
    db.session.commit()
    return jsonify({'deleted': True})


@bp.route('/api/templates/<id>/preview', methods=['POST'])
def preview_template(id):
    """Render the template against the supplied context without sending."""
    tpl = EmailTemplate.query.get_or_404(id)
    ctx = request.get_json() or {}
    return jsonify(tpl.render(ctx))


@bp.route('/api/templates/<id>/use', methods=['POST'])
def use_template(id):
    """'Send' (log as an email activity) against the supplied contact/deal.
    Real SMTP integration can be added later; for now this creates an
    Activity of type 'email' so the action is tracked.
    """
    tpl = EmailTemplate.query.get_or_404(id)
    data = request.get_json() or {}
    contact_id = data.get('contact_id')
    deal_id = data.get('deal_id')
    company_id = data.get('company_id')

    from modules.contacts.models import Contact
    from modules.deals.models import Deal
    from modules.companies.models import Company

    ctx = {'user': {'name': data.get('user_name', 'Me'),
                    'email': data.get('user_email', 'me@example.com')}}
    if contact_id:
        c = Contact.query.get(contact_id)
        if c:
            ctx['contact'] = {
                'first_name': c.first_name,
                'last_name': c.last_name,
                'full_name': c.full_name(),
                'email': c.email,
                'title': c.title,
            }
            if not company_id and c.company_id:
                company_id = c.company_id
    if deal_id:
        d = Deal.query.get(deal_id)
        if d:
            ctx['deal'] = {
                'name': d.name, 'value': d.value, 'stage': d.stage,
            }
    if company_id:
        co = Company.query.get(company_id)
        if co:
            ctx['company'] = {'name': co.name, 'industry': co.industry}

    rendered = tpl.render(ctx)

    # Track the email as an activity (real send can be wired later)
    from modules.activities.models import Activity
    activity = Activity(
        type='email',
        subject=rendered['subject'],
        body=rendered['body'],
        outcome='sent',
        deal_id=deal_id,
        contact_id=contact_id,
        company_id=company_id,
        completed=True,
    )
    activity.completed_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    db.session.add(activity)
    tpl.use_count = (tpl.use_count or 0) + 1
    db.session.commit()
    from modules.automations.engine import fire
    fire('activity_created', {'activity': activity})

    return jsonify({
        'rendered': rendered,
        'activity_id': activity.id,
        'use_count': tpl.use_count,
    }), 201


@bp.route('/api/merge-fields', methods=['GET'])
def list_merge_fields():
    return jsonify(MERGE_FIELDS)
