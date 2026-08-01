from flask import Blueprint, jsonify, request, render_template
from models import db, or_
from modules.companies.models import Company

bp = Blueprint('companies', __name__, url_prefix='/companies')

@bp.route('/')
def list_page():
    return render_template('companies/list.html')

@bp.route('/new')
def new_page():
    return render_template('companies/form.html', company=None)

@bp.route('/<id>')
def detail_page(id):
    company = Company.query.get_or_404(id)
    return render_template('companies/detail.html', company=company)

@bp.route('/<id>/edit')
def edit_page(id):
    company = Company.query.get_or_404(id)
    return render_template('companies/form.html', company=company)

@bp.route('/api/companies', methods=['GET'])
def list_companies():
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    query = Company.query
    if q:
        query = query.filter(
            db.or_(
                Company.name.ilike(f'%{q}%'),
                Company.industry.ilike(f'%{q}%'),
                Company.email.ilike(f'%{q}%')
            )
        )
    if status:
        query = query.filter(Company.status == status)
    companies = query.order_by(Company.created_at.desc()).all()
    return jsonify([c.to_dict() for c in companies])

@bp.route('/api/companies', methods=['POST'])
def create_company():
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'Missing field: name'}), 400
    company = Company(
        name=data.get('name'),
        industry=data.get('industry'),
        website=data.get('website'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        status=data.get('status', 'prospect'),
        tags=data.get('tags', []),
        notes=data.get('notes')
    )
    db.session.add(company)
    db.session.commit()
    return jsonify(company.to_dict()), 201

@bp.route('/api/companies/<id>', methods=['GET'])
def get_company(id):
    company = Company.query.get_or_404(id)
    return jsonify(company.to_dict())

@bp.route('/api/companies/<id>', methods=['PUT', 'PATCH'])
def update_company(id):
    company = Company.query.get_or_404(id)
    data = request.get_json() or {}
    fields = ['name', 'industry', 'website', 'email', 'phone', 'address', 'status', 'tags', 'notes']
    for field in fields:
        if field in data:
            setattr(company, field, data[field])
    db.session.commit()
    return jsonify(company.to_dict())

@bp.route('/api/companies/<id>', methods=['DELETE'])
def delete_company(id):
    company = Company.query.get_or_404(id)
    db.session.delete(company)
    db.session.commit()
    return jsonify({'deleted': True}), 200

@bp.route('/api/companies/statuses', methods=['GET'])
def company_statuses():
    return jsonify(['prospect', 'customer', 'partner', 'vendor', 'competitor'])
