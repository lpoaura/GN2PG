from admin_views import DownloadView
from config import Config
from database import db
from flask import Flask
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from models import DownloadLog

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)
#     db.init_app(app)
#     app.config["DB"] = db
#     admin = Admin(app)
#     return app
app = Flask(__name__)
app.config.from_object(Config)
app.config["APPLICATION_ROOT"] = app.config["URL_APPLICATION"]
db.init_app(app)
app.config["DB"] = db
admin = Admin(
    app,
    name="GN2PG",
    index_view=AdminIndexView(name="Home", endpoint="gn2pg", url="/gn2pg", template="index.html"),
)
admin.add_view(DownloadView(DownloadLog, db.session))

# with app.app_context():
#     from index import routes
#     app.register_blueprint(routes, url_prefix="/")


app.run(debug=True)
# if __name__ == '__main__':
#     # app = create_app()
#     # app.run()
#     app.run(debug=True)
#     test= True
