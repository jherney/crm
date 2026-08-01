NAME = 'Activities'
SLUG = 'activities'
DESCRIPTION = 'Calls, emails, meetings, tasks and notes tied to deals and contacts.'
ENABLED = True

from . import models, routes  # noqa: F401  (import models so db.create_all sees them)


def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
