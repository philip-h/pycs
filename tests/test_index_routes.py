"""
When a user logs in, depending on how many classes they are registered in,
the 'landing page' is different.
If the user has 0 classes, they are redirected to /joinclass
If the user has 1 class, they are redirected to /app/{class_id}
If the user has 2+ classes, then / displays a list of classes they can choose from
"""


import pytest


def test_get_index_logged_out(client):
    """GET to / , when logged out, should show welcome message and login/register links"""
    response = client.get("/")
    assert b"To use this tool" in response.data
    assert b"Login" in response.data
    assert b"Register" in response.data


@pytest.mark.parametrize(
    ("student_number", "password", "greeting", "expected_text"),
    (
        # User 1 has 2 classes
        ("123456789", "password1", "Hey user1!", "ics3u"),
        ("123456789", "password1", "Hey user1!", "ics4u"),
        # User 2 has one class
        ("987654321", "password2", "Hey user2!", "Unit 1"),
        # User 3 has no classes
        ("246813579", "password3", "Hey user3!", "Join"),
    ),
)
def test_index_logged_in(client, auth, student_number, password, greeting, expected_text):
    """GET to / , when logged in, should render different pages depending on number of classes student is in (0, 1, 2+)
    Also, when a logged in user visits any page, a greeting including their first name is displayed in the navbar
    """
    # Log into the application
    auth.login(student_number, password)

    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    res_data = response.get_data(as_text=True)
    assert greeting in res_data
    assert expected_text in res_data
