"""Dashboard app runner"""

from flask import Flask
from flask_admin import Admin, AdminIndexView
from werkzeug.middleware.proxy_fix import ProxyFix

from gn2pg import _
from gn2pg.app.admin_views import DownloadView, ErrorView, IncrementView
from gn2pg.app.config import FlaskConfig
from gn2pg.app.database import db
from gn2pg.app.models import DownloadLog, ErrorLog, IncrementLog


def create_app(config=FlaskConfig):
    """Create app"""

    app = Flask(__name__, static_url_path=config.APPLICATION_ROOT)
    app.config.from_object(config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_host=1)
    db.init_app(app)
    app.config["DB"] = db
    url_base = app.config["APPLICATION_ROOT"]
    admin = Admin(
        app,
        name="GN2PG",
        index_view=AdminIndexView(
            name=_("Home"), endpoint="gn2pg", url=url_base, template="index.html"
        ),
        template_mode="bootstrap4",
    )
    admin.add_view(DownloadView(DownloadLog, db.session, name=_("Full downloads")))
    admin.add_view(IncrementView(IncrementLog, db.session, name=_("Incremental downloads")))
    admin.add_view(ErrorView(ErrorLog, db.session, name=_("Error logs")))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
