"""
author: @philiph
Flask-WTF Form definitions
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class UserPassForm(FlaskForm):
    student_number = StringField(
        "Student number",
        validators=[
            DataRequired(),
            Length(min=9, max=9, message="Student numbers must be 9 numbers"),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be a minimum of 8 characters!"),
        ],
    )


class RegisterForm(UserPassForm):
    first_name = StringField("First name", validators=[DataRequired()])
    confirm_pass = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField(label="Register")


class LoginForm(UserPassForm):
    remember = BooleanField("Remember me?")
    submit = SubmitField(label="Login")


class ChangePassForm(FlaskForm):
    current_pass = PasswordField(
        "Current password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be a minimum of 8 characters!"),
        ],
    )
    new_pass = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be a minimum of 8 characters!"),
        ],
    )
    confirm_new_pass = PasswordField(
        "Confirm new password",
        validators=[
            DataRequired(),
            EqualTo("new_pass", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Change password")


class UploadCodeForm(FlaskForm):
    code = FileField(
        validators=[FileRequired(), FileAllowed(["py"], "Python code only")]
    )
