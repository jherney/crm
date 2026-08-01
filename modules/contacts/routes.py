from flask import Blueprint, jsonify, request, render_template, abort
from models import db, or_
from modules.contacts.models import Contact

bp = Blueprint('contacts', __name__, url_prefix='/contacts')

@bp.route('/')
def list_page():
    return render_template('contacts/list.html')

@bp.route('/new')
def new_page():
    return render_template('contacts/form.html', contact=None)

@bp.route('/<id>')
def detail_page(id):
    contact = Contact.query.get_or_404(id)
    return render_template('contacts/detail.html', contact=contact)

@bp.route('/<id>/edit')
def edit_page(id):
    contact = Contact.query.get_or_404(id)
    return render_template('contacts/form.html', contact=contact)

@bp.route('/api/contacts', methods=['GET'])
def list_contacts():
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    query = Contact.query
    if q:
        query = query.filter(
            db.or_(
                Contact.first_name.ilike(f'%{q}%'),
                Contact.last_name.ilike(f'%{q}%'),
                Contact.email.ilike(f'%{q}%')
            )
        )
    if status:
        query = query.filter(Contact.status == status)
    contacts = query.order_by(Contact.created_at.desc()).all()
    return jsonify([c.to_dict() for c in contacts])

@bp.route('/api/contacts', methods=['POST'])
def create_contact():
    data = request.get_json() or {}
    required = ['first_name']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
    contact = Contact(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data.get('email'),
        phone=data.get('phone'),
        title=data.get('title'),
        status=data.get('status', 'lead'),
        tags=data.get('tags', []),
        notes=data.get('notes'),
        company_id=data.get('company_id')
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify(contact.to_dict()), 201

@bp.route('/api/contacts/<id>', methods=['GET'])
def get_contact(id):
    contact = Contact.query.get_or_404(id)
    return jsonify(contact.to_dict())

@bp.route('/api/contacts/<id>', methods=['PUT', 'PATCH'])
def update_contact(id):
    contact = Contact.query.get_or_404(id)
    data = request.get_json() or {}
    fields = ['first_name', 'last_name', 'email', 'phone', 'title', 'status', 'tags', 'notes', 'company_id']
    for field in fields:
        if field in data:
            setattr(contact, field, data[field])
    db.session.commit()
    return jsonify(contact.to_dict())

@bp.route('/api/contacts/<id>', methods=['DELETE'])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'deleted': True}), 200

@bp.route('/api/contacts/statuses', methods=['GET'])
def contact_statuses():
    return jsonify(['lead', 'prospect', 'customer', 'partner', 'vendor'])
