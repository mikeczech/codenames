import os

from flask import Flask
from flask import jsonify

from codenames.errors import InvalidUsage


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev", DATABASE=os.path.join(app.instance_path, "codenames.sqlite"))

    from . import codenames
    app.register_blueprint(codenames.bp)
    app.add_url_rule("/", endpoint="index")

    from . import db
    db.init_app(app)

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    return app

