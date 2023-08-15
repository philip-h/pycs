"""
author: @philiph
cli commands for flask
"""

import os
import click

from .database import init_db, db_session
from .models import User


@click.command("init-db")
def command_init_db():
    init_db()
    click.echo("Database initialized")


@click.command("create-admin")
@click.argument("password")
def command_create_admin(password: str):
    admin = User("001310455", "Mr. Habib", password, "Teacher")
    db_session.add(admin)
    db_session.commit()
    click.echo("Administrator created")


