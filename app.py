import os
from flask import Flask, jsonify, request
from sqlalchemy import text

from config import Config
from database import init_app as init_db
from models import db
from modules import MODULES


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='public', template_folder='templates')
    app.config.from_object(config_class)
    init_db(app)

    register_modules(app)
    register_global_routes(app)
    register_cors(app)

    return app


app = create_app()


def register_modules(app):
    for module in MODULES:
        if getattr(module, 'ENABLED', True):
            getattr(module, 'register', lambda a: None)(app)


def register_global_routes(app):
    @app.route('/api/health')
    def health():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify({'status': 'ok', 'db': 'connected'})
        except Exception as e:
            return jsonify({'status': 'error', 'db': str(e)}), 500

    @app.route('/api/modules')
    def list_modules():
        return jsonify([{
            'name': m.NAME,
            'slug': m.SLUG,
            'description': m.DESCRIPTION,
            'enabled': getattr(m, 'ENABLED', True)
        } for m in MODULES])


def register_cors(app):
    origin = app.config.get('CORS_ORIGIN', '*')

    @app.after_request
    def add_cors(response):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response

    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            response = app.make_response('')
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            return response


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=app.config['DEBUG'])
