NAME = 'Core'
SLUG = 'core'
DESCRIPTION = 'Core CRM functionality and shared utilities.'
ENABLED = True

from flask import Blueprint, render_template, jsonify

bp = Blueprint('core', __name__, url_prefix='/')

def register(app):
    app.register_blueprint(bp)
    return bp

@bp.route('/')
def index():
    return render_template('dashboard.html')

@bp.route('/api/')
def api_root():
    return jsonify({'name': 'Modular CRM', 'version': '0.1.0'})
