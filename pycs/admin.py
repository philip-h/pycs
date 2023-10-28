"""
author: @philiph
Flask-Admin configuration
"""

import os

from flask import Flask, redirect, url_for, current_app
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename

from .models import User, Assignment, UserAssignment, Classroom
from .database import db_session


class AdminMV(ModelView):
    """Parent ModelView for Flask-Admin"""

    column_display_pk = True

    def is_accessible(self):
        return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("routes.index"))


class AdminUserMV(AdminMV):
    """Flask-Admin user page"""

    column_searchable_list = [
        "first_name",
    ]
    form_columns = ["password_hash", "role"]
    form_choices = {"role": [("Student", "Student")]}


class AdminAssignmentMV(AdminMV):
    """Flask-Admin Assignment Page"""

    def scaffold_form(self):
        form_class = super(AdminAssignmentMV, self).scaffold_form()
        form_class.pytest_file = FileField("Pytest File")
        return form_class

    def update_model(self, form, model):
        form.populate_obj(model)
        pytest_file = form.pytest_file.data
        if pytest_file:
            filename = secure_filename(pytest_file.filename)
            upload_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], "tests", filename
            )
            pytest_file.save(upload_path)


class AdminScoresMV(AdminMV):
    """Flask-Admin User-Assignment Association page"""

    column_list = ["user", "assignment", "score", "uploaded_filepath"]
    column_editable_list = [
        "score",
    ]
    column_filters = ["user.first_name", "assignment.name"]


def init_admin(app: Flask):
    """Used to register Flask-Admin with local Flask app context"""
    admin = Admin(app)
    admin.add_view(AdminUserMV(User, db_session))
    admin.add_view(AdminAssignmentMV(Assignment, db_session))
    admin.add_view(AdminScoresMV(UserAssignment, db_session))
    admin.add_view(ModelView(Classroom, db_session))

    admin.add_link(MenuLink(name="Pycs", url="/"))
