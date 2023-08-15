"""
author: @philiph
Flask application factory
"""

import os

from flask import Flask, render_template
from .commands import *


def create_app(test_config=None):
    """Create and configure the Flask app"""
    app = Flask(__name__, instance_relative_config=True)
    # Default configuration for development
    app.config.from_mapping(
        SECRET_KEY="dev",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "code"),
    )

    # Override configuration for testing
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    # Override configuration for production
    else:
        app.config.from_mapping(test_config)

    # Make sure instance folder exists!
    try:
        os.makedirs(app.instance_path)
    except FileExistsError:
        print("Instance path already exists :)")

    # Make sure uploads folder exists!
    try:
        os.makedirs(os.path.join(app.instance_path, app.config["UPLOAD_FOLDER"]))
    except FileExistsError:
        print("Uploads folder already exists :)")

    # Make sure pytest folder exists!
    try:
        os.makedirs(
            os.path.join(app.instance_path, app.config["UPLOAD_FOLDER"], "tests")
        )
    except FileExistsError:
        print("Tests folder already exists :)")

    # Register click commands
    app.cli.add_command(command_init_db)
    app.cli.add_command(command_create_admin)

    # Setup login manager
    from .login import init_login_manager

    init_login_manager(app)

    # Initialize routes blueprint
    from .routes import routes

    app.register_blueprint(routes)

    # Admin Panel
    from .admin import init_admin

    init_admin(app)

    @app.get("/hello")
    def hello():
        """Test route"""
        return "Yell Banana!"

    ###############################################################################
    # Database shutdown
    ###############################################################################
    from .database import db_session

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()


    ###############################################################################
    # Error Handling
    ###############################################################################
    @app.errorhandler(401)
    def unauthorized(error):
        """Customm 401 Unauthorized page"""
        return render_template("401.html", error=error), 401

    @app.errorhandler(404)
    def not_found(error):
        """Custom 404 Not Found page"""
        return render_template("404.html", error=error), 404

    return app
