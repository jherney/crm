NAME = 'Automations'
SLUG = 'automations'
DESCRIPTION = 'No-code rules: when something happens, do something else.'
ENABLED = True

from . import models, routes  # noqa: F401


def register(app):
    app.register_blueprint(routes.bp)
    return routes.bp
