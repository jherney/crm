NAME = 'Contacts'
SLUG = 'contacts'
DESCRIPTION = 'Manage people: leads, customers, partners, and vendors.'
ENABLED = True

from . import routes

def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
