import pytest
from pycs import create_app
from pycs.database import init_db, clear_db, db_session
from pycs.models import User, Assignment
from datetime import datetime


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    init_db()
    new_user = User(
        student_number="999999999", first_name="Tester", password="thepassword"
    )
    new_assignment = Assignment(
        name="hello ass",
        required_filename="hello.py",
        due_date=datetime.today(),
        visible=True,
    )
    invisible_assignment = Assignment(
        name="invis",
        required_filename="invis.py",
        due_date=datetime.today(),
        visible=False,
    )
    second_assignment = Assignment(
        name="other one",
        required_filename="other.py",
        due_date=datetime.today(),
        visible=True,
    )

    db_session.add_all([new_user, new_assignment, invisible_assignment, second_assignment])
    db_session.commit()
    yield app
    clear_db()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, student_number="999999999", password="thepassword"):
        login_data = dict(student_number=student_number, password=password)

        return self._client.post("/login", data=login_data)

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
