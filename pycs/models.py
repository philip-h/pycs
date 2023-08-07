"""
author: @philiph
Database models for Pycs using Flask-SQLAlchemy
"""

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import click
from datetime import datetime

db = SQLAlchemy()


class UserAssignment(db.Model):
    __tablename__ = "user_assignment"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("assignment.id"), primary_key=True
    )
    score = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.String, nullable=False)

    user = db.relationship("User", back_populates="assignment_associations")
    assignment = db.relationship("Assignment", back_populates="user_associations")


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="Student")
    assignment_associations = db.relationship("UserAssignment", back_populates="user")
    assignments = association_proxy("assignment_associations", "assignment")

    def __init__(self, student_number, first_name, password, role="Student"):
        self.student_number = student_number
        self.first_name = first_name
        self.password_hash = generate_password_hash(password)
        self.role = role

    def __repr__(self):
        return f"<User {self.first_name}>"

    @hybrid_property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, new_password):
        self.password_hash = generate_password_hash(new_password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "Teacher"


class Assignment(db.Model):
    __tablename__ = "assignment"

    id = db.Column(db.Integer, primary_key=True)
    unit = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    total_points = db.Column(db.Integer, nullable=False, default=4)
    required_filename = db.Column(db.String, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    visible = db.Column(db.Boolean, nullable=False, default=True)

    user_associations = db.relationship("UserAssignment", back_populates="assignment")
    users = association_proxy("user_associations", "user")

    def __repr__(self):
        return f"<Assignment {self.name}>"

    def __str__(self):
        return f"Name: {self.name}"

    def verify_filename(self, filename):
        return filename == self.required_filename


# Initializing DB
def init_database():
    """Initialize / reset database"""
    with current_app.app_context():
        db.drop_all()
        db.create_all()

    admin_user = User(
        student_number="001310455",
        first_name="Mr. Habib",
        password=input("Enter admin password: "),
        role="Teacher",
    )

    with current_app.app_context():
        db.session.add(admin_user)
        db.session.commit()


def add_test_data_to_database():
    init_database()

    test_user = User(
        student_number="123456789",
        first_name="Tester",
        password="123test321",
    )

    test_user2 = User(
        student_number="123456788",
        first_name="Tester 2",
        password="123test321",
    )

    test_user3 = User(
        student_number="123456787",
        first_name="Tester 3",
        password="123test321",
    )

    import os

    try:
        os.makedirs(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"], f"{test_user.student_number}"
            )
        )
        os.makedirs(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"], f"{test_user2.student_number}"
            )
        )
        os.makedirs(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"], f"{test_user3.student_number}"
            )
        )
    except FileExistsError:
        pass

    hello_assignment = Assignment(
        unit=0,
        name="Hello World",
        total_points=4,
        required_filename="hello.py",
        due_date=datetime(year=2023, month=9, day=1),
        visible=True,
    )

    goodbye_assignment = Assignment(
        unit=0,
        name="Good Bye",
        total_points=4,
        required_filename="goodbye.py",
        due_date=datetime(year=2022, month=1, day=1),
        visible=True,
    )

    invisible_assignment = Assignment(
        unit=0,
        name="Invisible",
        total_points=2,
        required_filename="invisible.py",
        visible=False,
    )

    test_user_hello_assignment = UserAssignment(
        score=3,
        comments=f"Do better",
    )
    test_user.assignment_associations.append(test_user_hello_assignment)
    hello_assignment.user_associations.append(test_user_hello_assignment)

    test_user2_hello_assignment = UserAssignment(
        score=4,
        comments="Not bad!",
    )
    test_user2.assignment_associations.append(test_user2_hello_assignment)
    hello_assignment.user_associations.append(test_user2_hello_assignment)

    test_user_3_goobdye_assignment = UserAssignment(
        score=2,
        comments="Chump...",
    )
    test_user3.assignment_associations.append(test_user_3_goobdye_assignment)
    goodbye_assignment.user_associations.append(test_user_3_goobdye_assignment)

    with current_app.app_context():
        db.session.add(test_user)
        db.session.add(test_user2)
        db.session.add(test_user2)
        db.session.add(hello_assignment)
        db.session.add(goodbye_assignment)
        db.session.add(invisible_assignment)
        db.session.commit()


@click.command("init-db")
def init_db_command():
    init_database()
    click.echo("Initialized the database!")


@click.command("populate-db")
def populate_db_command():
    add_test_data_to_database()
    click.echo("Added test data to database")


def register_init_db(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)


def register_populate_db(app):
    app.cli.add_command(populate_db_command)
