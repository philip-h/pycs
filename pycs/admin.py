"""
author: @philiph
Flask-Admin configuration
"""

from flask import redirect, url_for
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from .models import User, Assignment, UserAssignment, db
from flask_login import current_user


class AdminMV(ModelView):
    column_display_pk = True

    def is_accessible(self):
        return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("routes.index"))


class AdminUserMV(AdminMV):
    column_searchable_list = [
        "first_name",
    ]
    form_columns = ["password_hash", "role"]
    form_choices = {"role": [("Student", "Student")]}


class AdminAssignmentMV(AdminMV):
    pass


class AdminScoresMV(AdminMV):
    column_list = ["user", "assignment", "score", "uploaded_filepath"]
    column_editable_list = [
        "score",
    ]
    column_filters = ["user.first_name", "assignment.name"]


def init_admin(app):
    admin = Admin(app)
    admin.add_view(AdminUserMV(User, db.session))
    admin.add_view(AdminAssignmentMV(Assignment, db.session))
    admin.add_view(AdminScoresMV(UserAssignment, db.session))

    admin.add_link(MenuLink(name="Pycs", url="/"))
