import os
from datetime import datetime
from pathlib import Path

from werkzeug.security import check_password_hash

from pycs.database import db_session, select
from pycs.models import User, Assignment, UserAssignment


def test_index_logged_out(client):
    """Index should show intro message and links to log in if logged out"""
    res = client.get("/")
    assert b"To use this tool" in res.data
    assert b"Login" in res.data
    assert b"Register" in res.data


def test_index_logged_in(client, auth):
    """Index should show links to log out and change password if logged in"""
    auth.login()
    res = client.get("/")
    assert b"Logout" in res.data
    assert b"Change Password" in res.data


def test_changepass_logged_out(client):
    """If you are not logged in, changepass page should return a 401 UNAUTHORIZED"""
    assert client.get("/changepass").status_code == 401
    assert client.post("/changepass").status_code == 401


def test_get_changepass_logged_in(client, auth):
    """GET request from logged in user should return a 200 OK"""
    auth.login()
    assert client.get("/changepass").status_code == 200


def test_post_changepass_logged_in(client, auth):
    """POST requset to changepass should redirect to index and change user's password"""
    auth.login()
    changepass_data = dict(
        current_pass="thepassword",
        new_pass="thestrongerpassword",
        confirm_new_pass="thestrongerpassword",
    )
    res = client.post("/changepass", data=changepass_data)
    assert res.headers["Location"] == "/"
    user = db_session.scalar(select(User))
    assert check_password_hash(user.password, "thestrongerpassword")


def test_get_assignment_logged_out(client):
    """If you are not logged in, assignment pages should return 401 UNAUTHORIZED"""
    assert client.get("/1/assignment").status_code == 401
    assert client.post("/1/assignment").status_code == 401


def test_get_assignment_logged_in(client, auth):
    """Assignment page should display assignment name"""
    auth.login()
    res = client.get("/1/assignment")
    assert res.status_code == 200
    assert b"hello ass" in res.data


def test_cannot_access_invisible_assignment(client, auth):
    """Invisible assignments should return 404 NOT FOUND (must be logged in)"""
    auth.login()
    assert client.get("/2/assignment").status_code == 404

def test_post_assignment_logged_in(client, auth, monkeypatch, app):
    """Uploaded assignment creates assignment association in sqlalchemy and displays grader comment"""
    monkeypatch.setattr("pycs.routes.grade_student", lambda _: (4, "nice"))
    current_path = Path(__file__).parent
    resources = current_path / "resources"
    os.chdir(resources)
    upload_data = dict(code=open("hello.py", "rb"))
    os.chdir(current_path)

    auth.login()
    res = client.post("/1/assignment", data=upload_data)
    assert res.status_code == 302 # Successful upload
    res = client.get("/1/assignment")
    assert b"nice" in res.data
    user = db_session.scalar(select(User))
    assert len(user.assignments) == 1


def test_post_assignment_logged_in_wrong_filename(client, auth, monkeypatch, app):
    """Must upload hello.py filename in first assignment"""
    current_path = Path(__file__).parent
    resources = current_path / "resources"
    os.chdir(resources)
    upload_data = dict(code=open("goodbye.py", "rb"))
    os.chdir(current_path)

    auth.login()
    res = client.post("/1/assignment", data=upload_data, follow_redirects=True)
    assert b"Uploaded file must be named hello.py." in res.data
