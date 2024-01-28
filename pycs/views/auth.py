
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from pycs.controllers import user as user_controller
from pycs.forms import ChangePassForm, LoginForm, RegisterForm

from . import login_required

bp = Blueprint("auth", __name__)

@bp.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration."""
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            new_user = user_controller.create_student(
                student_number=form.student_number.data,
                first_name=form.first_name.data,
                password=form.password.data
            )
            login_user(new_user)
        except IntegrityError:
            form.student_number.errors.append(
                f"Student {form.student_number.data} is already registered."
            )
        else:
            flash("Thanks for registering, please enter the class code to continue", "info")
            return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)

@bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles User login. Uses sessions through Flask-Login"""
    form = LoginForm()
    if form.validate_on_submit():
        remember = bool(form.data.get("remember"))

        user = user_controller.get_user_by_student_number(form.student_number.data)

        if user is None or not user_controller.verify_password(user.password_hash, form.password.data):
            form.student_number.errors.append("Invalid Credentials.")
        else:
            login_user(user, remember)
            return redirect(url_for("main.index"))

    return render_template("auth/login.html", form=form)


@bp.get("/logout")
def logout():
    """Log the user out (Again, thanks Flask-Login)"""
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/changepass", methods=["GET", "POST"])
@login_required
def change_pass():
    """Handles the changing of a user's password."""
    form = ChangePassForm()
    if form.validate_on_submit():
        # Verify current password
        err_msg = user_controller.change_user_password(
            current_user, form.current_pass.data, form.new_pass.data
        )
        if err_msg is None:
            return redirect(url_for("main.index"))
        else:
            form.new_pass.errors.append(err_msg)

    return render_template("auth/changepass.html", form=form)
