"""
author: @philph
Flask-Login configuration
"""

from flask import Flask
from flask_login import LoginManager
from .database import db_session, select
from .models import User

login_manager = LoginManager()


def init_login_manager(app: Flask):
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db_session.scalars(select(User).where(User.id == user_id)).first()
