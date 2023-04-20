"""Custom home template"""

from flask import Blueprint, render_template

routes = Blueprint("index", __name__)


@routes.route("/")
def index():
    """Home"""
    return render_template("index.html")
