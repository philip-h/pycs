import os

from flask import Flask


def create_app(test_config=None):
    # Create and configure Flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # TODO: Change this
        SQLALCHEMY_DATABASE_URI="sqlite:///pycs.db",
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Make sure instance folder exists!
    try:
        os.makedirs(app.instance_path)
    except OSError:
        print("Instance path could not be created")

    # Test route
    @app.get("/hello")
    def hello():
        return "Yell Banana!"

    return app
