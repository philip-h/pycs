import functools
from http import HTTPStatus
from flask_login import current_user
from werkzeug.exceptions import abort

# Authorization decorator
def login_required(view):
    """If a route requires the user to be logged in, force a 401 error!"""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated:
            abort(HTTPStatus.NOT_FOUND)

        return view(**kwargs)

    return wrapped_view

# Authorization decorator
def teacher_login_required(view):
    """If a route requires the user to be logged in, force a 401 error!"""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated:
            abort(HTTPStatus.NOT_FOUND)
        if not current_user.is_admin:
            abort(HTTPStatus.NOT_FOUND)

        return view(**kwargs)

    return wrapped_view



def register_views(app):
    from .main import bp as main_bp
    from .auth import bp as auth_bp
    from .teacher import bp as teacher_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
