from pathlib import Path

import pytest

from pycs.grader import (
    _read_file,
    _check_header_comments,
    _check_variable_names,
    _check_ipo,
    _grade_pytest,
)

resources = Path(__file__).parent / "resources"


def test__read_file():
    """Read file should return list[str] of each line in the file"""
    actual = _read_file(resources / "lines.txt")
    expected = ["1", "2", "3"]
    assert actual == expected


def test__read_file_fne():
    """Files not found should return None"""
    actual = _read_file(resources / "doesnotexist.txt")
    assert actual is None


def test__check_header_comments_lvl0():
    """Code without header comments should return a score of 0"""
    no_hc = ["print('hey')"]
    score, comments = _check_header_comments(no_hc)
    assert score == 0
    assert "Docstrings are missing" in comments


def test__check_header_comments_lvl2():
    """Code with wrong or incomplete header comments should return a score of 2"""
    file_contents = (
        open((resources / "bad_comments.py"), mode="r", encoding="utf-8")
        .read()
        .splitlines()
    )
    score, comments = _check_header_comments(file_contents)
    assert score == 2
    assert "Missing" in comments


def test__check_header_comments_lvl2_wrong_quotes():
    """Code with good header comments, but the wrong quote, should return a score of 2"""
    file_contents = (
        open((resources / "bad_comments2.py"), mode="r", encoding="utf-8")
        .read()
        .splitlines()
    )
    score, comments = _check_header_comments(file_contents)
    assert score == 2
    assert "While ''' works" in comments


def test__check_header_comments_lvl2_not_closed():
    """Code with header comments that are not closed should return a score of 2"""
    file_contents = (
        open((resources / "bad_comments3.py"), mode="r", encoding="utf-8")
        .read()
        .splitlines()
    )
    score, comments = _check_header_comments(file_contents)
    assert score == 2
    assert "Header comments not closed" in comments


def test__check_header_comments_lvl4():
    """Code with proper header comments should return a score of 4"""
    file_contents = (
        open((resources / "hello.py"), mode="r", encoding="utf-8").read().splitlines()
    )
    score, comments = _check_header_comments(file_contents)
    assert score == 4
    assert "Header comments are good" in comments


def test__check_variable_names_no_vars():
    """Code with no vars should return a score of 4"""
    no_vars = ["print('Hey')"]
    score, comments = _check_variable_names(no_vars)
    assert score == 4
    assert "Variable names are good" in comments


def test__check_variable_names_lvl2():
    """Code with any variables that do not follow snake_case should return a score of 2"""
    no_vars = [
        "greeting = 'Hello",
        "Place = 'world",
        "print(f'{greeting}, {Place}!')",
    ]
    score, comments = _check_variable_names(no_vars)
    assert score == 2
    assert "do not follow class conventions" in comments


def test__check_variable_names_lvl4():
    """Code with any variables that do not follow snake_case should return a score of 2"""
    no_vars = [
        "greeting = 'Hello",
        "place = 'world",
        "print(f'{greeting}, {place}!')",
    ]
    score, comments = _check_variable_names(no_vars)
    assert score == 4
    assert "Variable names are good" in comments


def test__check_ipo_lvl0():
    """Code with no ipo should return a score of 0"""
    no_ipo = ["print('hello')"]
    score, comments = _check_ipo(no_ipo)
    assert score == 0
    assert "Missing IPO comments" in comments


def test__check_ipo_lvl2():
    """Code without completed ipo comments should return a score of 2
    An incomplete ipo does not include input"""
    incomplete_ipo = ["# Processing", "# Output", "print('hello')"]
    score, comments = _check_ipo(incomplete_ipo)
    assert score == 2
    assert "Incomplete or incorrect" in comments


def test__check_ipo_lvl4_valid1():
    """Code with input, output, and processing comments shuld return a score of 4"""
    complete_ipo1 = ["# Input", "# Processing", "# Output", "print('hello')"]
    score, comments = _check_ipo(complete_ipo1)
    assert score == 4
    assert "IPO comments are good" in comments


def test__check_ipo_lvl4_valid2():
    """Code with input and processing / output comments should return a score of 4"""
    complete_ipo2 = ["# Input", "# Processing / Output", "print('hello')"]
    score, comments = _check_ipo(complete_ipo2)
    assert score == 4
    assert "IPO comments are good" in comments


@pytest.mark.parametrize(
    ("pytest_output", "expected_score"),
    (
        ("test1.py::test_1 PASSED [ 5%]\ntest1.py::test_2 PASSED [100%]", 4),
        ("test1.py::test_1 FAILED [ 50%]\ntest1.py::test_2 PASSED [100%]", 2),
        ("test1.py::test_1 FAILED [ 50%]\ntest1.py::test_2 FAILED [100%]", 0),
        (
            "test1.py::test_1 PASSED [ 33%]\ntest1.py::test_2 FAILED [ 67%]\n\ntest1.py::test_2 PASSED [100%]",
            2.7,
        ),
    ),
)
def test__grade_pytest(pytest_output, expected_score, monkeypatch):
    """Code should run pytest command and grade based off of the number of passes and fails"""

    class Fake_shutil:
        def copy2(*args):
            pass

    monkeypatch.setattr("pycs.grader._run_pytest", lambda x, y: pytest_output)
    monkeypatch.setattr("pycs.grader.shutil", Fake_shutil)
    fake_path = Path("/fake/assignment/directory")
    actual_score, _ = _grade_pytest(fake_path)
    assert actual_score == expected_score
