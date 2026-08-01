NAME = 'Email Templates'
SLUG = 'email_templates'
DESCRIPTION = 'Reusable email templates with merge fields for contacts, deals, and companies.'
ENABLED = True

from . import models, routes  # noqa: F401


def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
