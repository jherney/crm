NAME = 'Events'
SLUG = 'events'
DESCRIPTION = 'Manage events, capacity, and attendee RSVPs tied to CRM contacts.'
ENABLED = True

from . import models, routes  # noqa: F401  (import models so db.create_all sees them)


def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
