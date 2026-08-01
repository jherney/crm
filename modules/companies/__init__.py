NAME = 'Companies'
SLUG = 'companies'
DESCRIPTION = 'Manage organizations and accounts.'
ENABLED = True

from . import routes

def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
