"""
author: @philiph
Flask application factory
"""

import os

from flask import Flask, render_template


def create_app(test_config=None):
    # Create and configure Flask app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # TODO: Change this
        SQLALCHEMY_DATABASE_URI="sqlite:///pycs.db",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "code"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Make sure instance folder exists!
    try:
        os.makedirs(app.instance_path)
    except FileExistsError:
        print("Instance path already exists :)")
    except OSError as e:
        print("Instance path could not be created", e)

    # Make sure uploads folder exists!
    try:
        os.makedirs(os.path.join(app.instance_path, app.config["UPLOAD_FOLDER"]))
    except FileExistsError:
        print("Uploads folder already exists :)")
    except OSError as e:
        print("Uploads folder could not be created", e)

    # Setup database
    from . import models

    models.register_init_db(app)
    models.register_populate_db(app)
    # Setup login manager
    from .routes import login_manager

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User

        return models.db.session.execute(
            models.db.select(User).filter_by(id=user_id)
        ).scalar_one()

    from .routes import routes

    app.register_blueprint(routes)

    # Admin Panel
    from . import admin

    admin.init_admin(app)

    # Test route
    @app.get("/hello")
    def hello():
        return "Yell Banana!"

    ###############################################################################
    # Error Handling
    ###############################################################################
    @app.errorhandler(401)
    def unauthorized(error):
        return render_template("401.html", error=error), 401

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html", error=error), 404

    return app
