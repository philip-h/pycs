"""
author: @philiph
All Pycs application routes.
"""

from flask import (
    Blueprint,
    redirect,
    render_template,
    url_for,
    current_app,
    request,
)
from flask_login import LoginManager, login_user, logout_user, current_user
from sqlalchemy import exc
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

import os
from datetime import datetime
import functools
from http import HTTPStatus

from .forms import RegisterForm, LoginForm, ChangePassForm, UploadCodeForm
from .models import Assignment, User, UserAssignment, db

routes = Blueprint("routes", __name__)
login_manager = LoginManager()


###############################################################################
# Authentication Routes
###############################################################################


# Authorization decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated:
            # return redirect(url_for(".index"))
            abort(HTTPStatus.UNAUTHORIZED)

        return view(**kwargs)

    return wrapped_view


@routes.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(
            student_number=form.student_number.data,
            first_name=form.first_name.data,
            password=form.password.data,
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except exc.IntegrityError as e:
            form.student_number.errors.append(
                f"Student {form.student_number.data} is already registered."
            )
        else:
            login_user(new_user, remember=False)
            return redirect(url_for(".index"))

    return render_template("register.html", form=form)


@routes.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        remember = bool(form.data.get("remember"))

        user = db.session.execute(
            db.select(User).filter_by(student_number=form.student_number.data)
        ).scalar_one_or_none()

        if user is None or not user.verify_password(form.password.data):
            form.student_number.errors.append("Invalid Credentials.")
        else:
            login_user(user, remember)
            return redirect(url_for(".index"))

    return render_template("login.html", form=form)


@routes.route("/changepass", methods=["GET", "POST"])
@login_required
def change_pass():
    form = ChangePassForm()
    if form.validate_on_submit():
        # Verify current password
        if not current_user.verify_password(form.current_pass.data):
            form.current_pass.errors.append(
                "Current password does not match password in database."
            )
        elif current_user.verify_password(form.new_pass.data):
            form.new_pass.errors.append(
                "New password cannot mactch password in database."
            )
        else:
            current_user.password = form.new_pass.data
            db.session.commit()
            return redirect(url_for(".index"))

    return render_template("changepass.html", form=form)


@routes.get("/logout")
def logout():
    logout_user()
    return redirect(url_for(".index"))


###############################################################################
# Application Routes
###############################################################################


@routes.get("/")
def index():
    # Authentication required for this route!
    # Stated explicitly here because @login_required always
    # redirects to index
    if not current_user.is_authenticated:
        return render_template("landing.html")

    # Query database to get all assignments, with optional UserAssignment join
    # If the currently logged in user has submitted an assignment.
    # This is to eventually get the score out into the template
    assignments_scores = db.session.execute(
        db.select(Assignment, UserAssignment).outerjoin(
            UserAssignment,
            (Assignment.id == UserAssignment.assignment_id)
            & (UserAssignment.user_id == current_user.id),
        )
    )
    assignments_scores = list(assignments_scores)
    # Calculate studen't average
    scores, totals = 0, 0
    for a, ua in assignments_scores:
        if ua:
            scores += ua.score
            totals += a.total_points

    if totals == 0:
        avg = "0"
    else:
        avg = round((scores / totals) * 100, 2)

    return render_template(
        "app.html", assignments_scores=assignments_scores, avg=avg, today=datetime.now()
    )


@routes.route("/<int:id>/assignment", methods=["GET", "POST"])
@login_required
def assignment(id):
    # assignment = db.get_or_404(Assignment, id)
    assignment, user_assignment = db.session.execute(
        db.select(Assignment, UserAssignment)
        .outerjoin(
            UserAssignment,
            (UserAssignment.assignment_id == id)
            & (UserAssignment.user_id == current_user.id),
        )
        .filter(Assignment.id == id)
    ).first()

    # SQLite only really does incremental primary keys.
    # This bit of code stopes snoopy students from checking
    # assignments that I've created that are not supposed to
    # be viseble yet.
    if not assignment.visible and not current_user.is_admin:
        abort(HTTPStatus.NOT_FOUND)

    form = UploadCodeForm()

    if form.validate_on_submit():
        # Make student directory if it dne
        student_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            f"{current_user.student_number}"
        )
        if not os.path.exists(student_dir):
            os.makedirs(student_dir)

        code_file = form.code.data
        filename = secure_filename(code_file.filename)
        if assignment.verify_filename(filename):
            upload_path = os.path.join(
                student_dir,
                f"{filename}",
            )

            # Score the user's submission
            # score = _calculate_score(upload_path)

            score = 2
            # Create the association
            user_assignment = UserAssignment(score=score, uploaded_filepath=upload_path)
            user_assignment.assignment = assignment
            current_user.assignment_associations.append(user_assignment)

            db.session.commit()
            code_file.save(upload_path)
            return redirect(request.url)
        else:
            form.code.errors.append(
                f"Uploaded file must be named {assignment.required_filename}."
            )

    return render_template(
        "assignment.html", assignment=assignment, data=user_assignment, form=form
    )
