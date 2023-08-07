"""
author: @philiph
The heart and soul of the grader application.
"""

from pathlib import Path
import itertools
import re
import subprocess
import shutil


def _read_file(file_path: Path) -> list[str]:
    """Read data from given file_path and returns a list of lines"""
    with open(file_path, mode="r", encoding="uft-8") as f_in:
        return f_in.read().splitlines()


def _check_header_comments(file_contents: list[str]) -> tuple[int, str]:
    """Checks for the presence of header comments and that they follow class conventions.
    Returns the achieved level and comments.

    Level 0: Docstrings are missing
    Level 2: Docstrings are present but do not follow class conventions
    Level 4: Docstrings are present and follow class conventions
    """

    # Ensure there are no blank lines at the beginning of the script!
    # Lists are "pass by reference", so I copy the list to ensure that I do not destroy the file
    # contents for other functions that need it!
    file_contents = file_contents[::]
    list(itertools.dropwhile(lambda line: line.strip() == "", file_contents))

    # Ensure docstring by checking the first line
    if not file_contents[0] == '"""' and not file_contents[0] == "'''":
        return 0, "Docstrings are missing.\n"
    if file_contents[0] == "'''":
        return 2, "While ''' works, class conventions are \"\"\"\n"

    # Checking class conventions for docstring
    comment = ""
    if not re.match(r"author: [a-zA-Z]+", file_contents[1]):
        comment += "Missing author (or wrong format) in docstring\n"
    if not re.match(r"date: \d\d/\d\d/\d\d\d\d", file_contents[2]):
        comment += "Missing date (or wrong format) in docstring\n"
    if not re.match(r"\w+", file_contents[3]):
        comment += "Missing one sentence description of module in docstring\n"
    if comment != "":
        return 2, comment

    # Ensure docstring is closed
    if file_contents[0] == '"""' and not file_contents[4] == '"""':
        return 2, "Header comments not closed! Any feedback after this is useless!\n"
    if file_contents[0] == "'''" and not file_contents[4] == "'''":
        return 2, "Header comments not closed! Any feedback after this is useless!\n"

    # Good header comments
    return 4, "Header comments are good\n"


def _check_variable_names(file_contents: list[str]) -> tuple[int, str]:
    """Check that variable names follow class conventions.
    Returns achieved level and comments.

    Level 2: There are variable names that do not follow class conventions
    Level 4: All variable names follow class conventions
    """
    # Lists are "pass by reference", so I copy the list to ensure that I do not destroy the file
    # contents for other functions that need it!
    file_contents = file_contents[::]

    variables_in_file: list[str] = []
    for line in file_contents:
        # Match any line that:
        # . starts with any number of spaces / indentations
        # . contains letters (upper or lower), numbers, or underscores
        # . those letters are followed by an equal sign, but only one equal sign
        # . and there may or may not be spaces between the var name and the equal sign
        # . gotta love regex
        var_in_line = re.search(r"\s*[a-zA-Z0-9_]+\s*=[^=]", line)
        if var_in_line:
            beginning, end = var_in_line.span()
            variables_in_file.append(line[beginning : end - 2].strip())

    if not all(var.islower() for var in variables_in_file):
        return 2, "There are variable names that do not follow class conventions\n"

    return 4, "Variable names are good\n"


def _check_ipo(file_contents: list[str]) -> tuple[int, str]:
    """Checks for the presence of IPO comments as a class convention.
    Returns the achieved level and comments.

    Level 0: No IPO comments present
    Level 2: Some IPO comments present
    Level 4: All IPO comments present
    """
    file_contents = "\n".join([line.strip().lower() for line in file_contents])
    has_i = re.search(r"^#\s?input$", file_contents, re.MULTILINE)
    has_p = re.search(r"^#\s?processing$", file_contents, re.MULTILINE)
    has_o = re.search(r"^#\s?output$", file_contents, re.MULTILINE)
    has_po = re.search(r"^#\s?processing\s?/\s?output$", file_contents, re.MULTILINE)

    # Valid ipo comments:
    # All three present
    valid1 = has_i and has_p and has_o
    # Processing and output are combined
    valid2 = has_i and has_po

    if not any([has_i, has_p, has_o, has_po]):
        return 0, "Missing IPO comments\n"

    if not valid1 and not valid2:
        return 2, "Incomplete or incorrect IPO comments\n"

    return 4, "IPO comments are good\n"


def _grade_pytest(assignment_path: Path) -> tuple[int, str]:
    """Grade a student based off of the number of pytest tests they pass
    Returns achieved level and comments.
    """
    assignment_dir = assignment_path.parent
    assignment_name = assignment_path.name
    test_path = assignment_dir.parent / "tests" / f"test_{assignment_name}"
    shutil.copy2(test_path, assignment_dir)

    try:
        process = subprocess.run(
            ["pytest", "--no-header", "-v", f"{test_path.name}"],
            cwd=f"{assignment_dir}",
            capture_output=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (
            1,
            "\n\nYour code has some kind of infinite loop. Either that or your program is waiting for input that my grader won't give it!",
        )

    pytest_output = process.stdout.decode()

    # Calculate their grade based off of how many tests they passed or failed
    pytest_output_lines = pytest_output.splitlines()
    test_lines = [
        line for line in pytest_output_lines if re.search("\[\s?\d+%\]", line)
    ]
    num_failed = sum("FAILED" in line for line in test_lines)
    num_passed = sum("PASSED" in line for line in test_lines)
    # Score is a number between 0 and 1
    score = num_passed / (num_passed + num_failed)

    return score * 4, pytest_output


def grade_student(assignment_path: Path) -> tuple[int, str]:
    """Grade a student based off of their coding style and correctness.
    Returns the achieved level and comments
    """
    file_contents = _read_file(assignment_path)

    # Gather all of the comments and scores
    hc_score, hc_comments = _check_header_comments(file_contents)
    ipo_score, ipo_comments = _check_ipo(file_contents)
    var_score, var_comments = _check_variable_names(file_contents)
    pt_score, pt_comments = _grade_pytest(assignment_path)

    # Calculate weighted score
    scores = [hc_score, ipo_score, var_score, pt_score]
    weights = [1, 1, 1, 4]
    weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

    # Generate output comments
    comments_header = f"{' Grading Comments ':=^80}\n"
    variables_header = f"{' Grading Variable Names ':=^80}\n"

    comments = (
        comments_header
        + hc_comments
        + ipo_comments
        + variables_header
        + var_comments
        + pt_comments
    )

    return round(weighted_score, 1), comments
