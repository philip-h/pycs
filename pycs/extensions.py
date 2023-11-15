import click
from flask import current_app
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash


# Flask SQLAlchemy
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Flask Login
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from pycs.models import User

    return db.session.execute(
        db.select(User).where(User.id == user_id)
    ).scalar_one_or_none()


def init_db(teacherpass: str):
    """Clear existing data and create new tables"""
    from pycs.models import Assignment, Classroom, User, UserAssignment, user_classroom

    with current_app.app_context():
        db.create_all()
        teacher = User(
            student_number="001310455",
            first_name="Mr. Habib",
            password_hash=generate_password_hash(teacherpass),
            role="Teacher",
        )
        db.session.add(teacher)
        db.session.commit()


# ClI commands
@click.command("init-db")
@click.argument("teacherpass")
def command_init_db(teacherpass: str):
    init_db(teacherpass)
    click.echo("Database initialized")


def init_app(app):
    db.init_app(app)
    login_manager.init_app(app)
    app.cli.add_command(command_init_db)
