NAME = 'Deals'
SLUG = 'deals'
DESCRIPTION = 'Track opportunities, deals, and pipeline revenue.'
ENABLED = True

from . import routes


def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
