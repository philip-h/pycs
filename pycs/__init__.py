import os

from flask import Flask, render_template


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI = "sqlite:///2023.sem2.ics3u.db",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "code"),
        EXPORTED_FILES=os.path.join(app.instance_path, "exports"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # ensure uploads folder exists!
    try:
        os.makedirs(os.path.join(app.instance_path, app.config["UPLOAD_FOLDER"]))
    except FileExistsError:
        print("Uploads folder already exists :)")

    # ensure pytest folder exists!
    try:
        os.makedirs(
            os.path.join(app.instance_path, app.config["UPLOAD_FOLDER"], "tests")
        )
    except FileExistsError:
        print("Python tests folder already exists :)")

    # ensure junit test folder exists!
    try:
        os.makedirs(
            os.path.join(app.instance_path, app.config["UPLOAD_FOLDER"], "tests-java")
        )
    except FileExistsError:
        print("Java tests folder already exists :)")

    # ensure exports folder exists!
    try:
        os.makedirs(
            os.path.join(app.instance_path, app.config["EXPORTED_FILES"])
        )
    except FileExistsError:
        print("Exports folder already exists :)")


    # Configure extensions
    from .extensions import init_app
    init_app(app)

    # Register blueprints
    from .views import register_views
    register_views(app)

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return "Hello, World!"
    
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
