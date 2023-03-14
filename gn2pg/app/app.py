from gn2pg.app.admin_views import DownloadView,IncrementView,ErrorView
from gn2pg.app.config import Config
from gn2pg.app.database import db
from flask import Flask
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from gn2pg.app.models import DownloadLog,IncrementLog,ErrorLog


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.config["APPLICATION_ROOT"] = app.config["URL_APPLICATION"]
    db.init_app(app)
    app.config["DB"] = db
    admin = Admin(
        app,
        name="GN2PG",
        index_view=AdminIndexView(name="Home", endpoint="gn2pg", url="/gn2pg", template="index.html"),
    )
    admin.add_view(DownloadView(DownloadLog, db.session))
    admin.add_view(IncrementView(IncrementLog, db.session))
    admin.add_view(ErrorView(ErrorLog, db.session))
    # with app.app_context():
    #     from index import routes
    #     app.register_blueprint(routes, url_prefix="/")
    return app

    # app.run(debug=True)
if __name__ == '__main__':
        app = create_app(Config)
        app.run()
        # app.run(debug=True)
        # test= True
