"""
author: @philiph
Flask-WTF Form definitions
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, Length


class UserPassForm(FlaskForm):
    """A parent form that contains student_number and password fields"""

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
    """Registration requires a first name and another field to confirm their password"""

    first_name = StringField("First name", validators=[DataRequired()])
    confirm_pass = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    join_code = StringField("Join Code", validators=[DataRequired()])
    submit = SubmitField(label="Register")


class LoginForm(UserPassForm):
    """Login form gives user's the option to remember their session (Thanks Flask-Login)"""

    remember = BooleanField("Remember me?")
    submit = SubmitField(label="Login")


class ChangePassForm(FlaskForm):
    """Change password form"""

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
    """Upload code Form"""

    code = FileField(
        validators=[
            FileRequired(),
            FileAllowed(["py", "java"], "Python code (or java code) only"),
        ]
    )


class UploadMarksForm(FlaskForm):
    """Upload marks Form"""

    marks = FileField(
        validators=[
            FileRequired(),
            FileAllowed(["csv"], "Marks must be in CSV format."),
        ]
    )
    submit = SubmitField("Upload marks")


class AssignmentForm(FlaskForm):
    """New / Edit assignment form"""

    name = StringField("Name", validators=[DataRequired()])
    instructions = TextAreaField("Instructions", validators=[DataRequired()])
    unit_name = StringField("Unit Name", validators=[DataRequired()])
    submission_required = BooleanField("Submission Required?")
    required_filename = StringField("Required Filename")
    total_points = IntegerField("Total Points", validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[DataRequired()])
    visible = BooleanField("Visible?")
    weight = IntegerField("Weight", validators=[DataRequired()])
    class_id = IntegerField("Class Id", validators=[DataRequired()])
    unit_test_upload = FileField(
        validators=[
            FileAllowed(["py", "java"], "Python code (or java code) only"),
        ]
    )
    submit = SubmitField(label="Submit")


class ClassroomForm(FlaskForm):
    """New / Edit assignment form"""

    course_code = StringField("Course Code", validators=[DataRequired()])
    year = IntegerField("Year", validators=[DataRequired()])
    sem = IntegerField("Semester", validators=[DataRequired()])
    teacher_id = IntegerField("Teacher Id", validators=[DataRequired()])
    submit = SubmitField(label="Submit")
