import pytest
from pycs.database import db_session, select
from pycs.models import User
from flask_login import current_user


def test_register_get(client):
    """GET to register page should return a 200"""
    assert client.get("/register").status_code == 200


def test_register_post(client, app):
    """POST to register page should create a new user"""
    register_data = dict(
        student_number="000000000",
        first_name="a",
        password="aaaaaaaa",
        confirm_pass="aaaaaaaa",
    )
    res = client.post("/register", data=register_data)
    assert res.headers["Location"] == "/"

    user = db_session.scalar(select(User).where(User.first_name == "a"))
    assert user is not None


@pytest.mark.parametrize(
    ("student_number", "first_name", "password", "confirm_pass", "message"),
    (
        ("", "a", "a", "a", b"This field is required"),
        ("1", "", "a", "a", b"This field is required"),
        ("1", "a", "", "", b"This field is required"),
        ("1", "a", "a", "b", b"Passwords must match."),
        ("1", "a", "a", "a", b"Student numbers must be 9 numbers"),
        ("777777777", "a", "a", "a", b"Password must be a minimum of 8 characters!"),
        (
            "999999999",
            "Tester",
            "thepassword",
            "thepassword",
            b"Student 999999999 is already registered.",
        ),
    ),
)
def test_register_valid_input(
    client, student_number, first_name, password, confirm_pass, message
):
    """POST to register page with invalid inputs should produce appropriate error messages"""
    post_data = dict(
        student_number=student_number,
        first_name=first_name,
        password=password,
        confirm_pass=confirm_pass,
    )
    res = client.post("/register", data=post_data)
    assert message in res.data


def test_login_get(client, auth):
    """GET to login should return a 200"""
    assert client.get("/login").status_code == 200


def test_login_post(client):
    """POST to login should redirect to index, display user name, and log in current_user"""
    login_data = dict(student_number="999999999", password="thepassword")
    res = client.post("/login", data=login_data)
    assert res.headers["Location"] == "/"
    with client:
        res = client.get("/")
        assert b"Hey Tester" in res.data
        assert current_user.is_authenticated


@pytest.mark.parametrize(
    ("student_number", "password", "message"),
    (
        ("", "a", b"This field is required"),
        ("1", "", b"This field is required"),
        ("1", "a", b"Student numbers must be 9 numbers"),
        ("777777777", "a", b"Password must be a minimum of 8 characters!"),
        ("777777777", "aaaaaaaaa", b"Invalid Credentials"),
        ("999999999", "aaaaaaaaa", b"Invalid Credentials"),
    ),
)
def test_login_validate_input(auth, student_number, password, message):
    """POST to login page with invalid inputs should produce appropriate error messages"""
    res = auth.login(student_number, password)
    assert message in res.data


def test_logout(client, auth):
    """GET to logout should redirect to index and log current user out"""
    auth.login()

    with client:
        res = auth.logout()
        assert res.headers["Location"] == "/"
        assert current_user.is_anonymous
