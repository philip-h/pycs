import pytest
from pycs.database import db_session, select
from pycs.models import User


def test_init_db_command(runner, monkeypatch):
    """init-db command should call init_db and output a message"""

    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("pycs.commands.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"])
    assert "Database initialized" in result.output
    assert Recorder.called


def test_create_admin_command(runner):
    """create-admin command should create a teacher and output a message"""

    result = runner.invoke(args=["create-admin", "admin_pass"])
    assert "Administrator created" in result.output
    user = db_session.scalar(select(User).where(User.role == "Teacher"))
    assert user is not None
