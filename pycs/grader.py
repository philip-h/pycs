"""
author: @philiph
The heart and soul of the grader application.
"""

from enum import Enum, auto
from pathlib import Path
import itertools
import re
import subprocess
import sys
import shutil


def _read_file(file_path: Path) -> list[str]:
    """"""
    with open(file_path, mode="r") as f_in:
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
        return 2, "Header comments not closed! Any feedback after this is useless!"
    if file_contents[0] == "'''" and not file_contents[4] == "'''":
        return 2, "Header comments not closed! Any feedback after this is useless!"

    # Good header comments
    return 4, "Header comments are good\n"


def _check_variable_names(file_contents: list[str]) -> tuple[int, str]:
    """Check that variable names follow class conventions.
    Returns achieved level and comments.

    Level 1: There are variable names that do not follow class conventions
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
        return 1, "There are variable names that do not follow class conventions"

    return 4, "Variable names are good"


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
        return 0, "Missing IPO comments"

    if not valid1 and not valid2:
        return 2, "Incomplete or incorrect IPO comments"

    return 4, "IPO comments are good"


class MatchType(Enum):
    """Match type enum because enums > strings"""

    Contains = auto()
    Exact = auto()


class OutputType(Enum):
    """Output type enum because enums > strings"""

    Returns = auto()
    Prints = auto()


def _safe_decode_stderr(stderr: bytes) -> str:
    """I don't want students to know the absolute path of where the server saved their code!"""
    decoded = stderr.decode()
    if "File" not in decoded:
        return decoded

    full_file_path = re.search('".*\.py"', decoded)
    b, e = full_file_path.span()
    file_name = re.search("\d{9}_[a-z_]+.py", decoded)
    b2, e2 = file_name.span()
    return decoded.replace(decoded[b:e], decoded[b2:e2])


def grade_io(
    file_path: Path,
    py_input: str | None,
    output: str,
    match_type: MatchType = MatchType.Contains,
) -> tuple[int, str]:
    """Check to see if the program produces the given `output` provided the `input`
    Returns achieved level and comments.

    Level 1: The output does not match
    Level 4: The output does match
    """
    run_command = [sys.executable, file_path]
    try:
        actual_output = subprocess.run(
            run_command, input=py_input, capture_output=True, timeout=5
        )
    except subprocess.TimeoutExpired:
        return (
            1,
            "Your code timed out. Either you have an infinite loop or your are using an input() function without one being required",
        )

    if actual_output.returncode != 0:
        return 1, _safe_decode_stderr(actual_output.stderr)

    if match_type == MatchType.Contains:
        if output not in actual_output.stdout.decode():
            return (
                1,
                f"The output {output} does not match the output {actual_output.stdout.decode()}",
            )

    elif match_type == MatchType.Exact:
        if output != actual_output.stdout.decode().strip():
            return (
                1,
                f"The output {output} is not exactly the same as {actual_output.stdout.decode()}",
            )

    # If all else fails, then you did a good job
    return 4, "The outpts match. Nice!"


def grade_function(
    file_path: Path,
    fun_name: str,
    fun_input: tuple[str] | None,
    output: str,
    output_type: OutputType,
    match_type: MatchType,
) -> tuple[int, str]:
    """Check to see if the given function produces the given output provided the arguments
    Returns achieved level and comments.

    Level 1: The output does not match
    Level 4: The output does match
    """

    function_arguments = "()"
    if fun_input is not None:
        function_arguments = f"({fun_input})"

    # Create "actual_output_string" based on the fact that returns should just be the last line
    # But prints should be the entire thing because who knows what the student did....
    if output_type == OutputType.Prints:
        run_str = f"import sys; sys.path.append('{file_path.parent}'); from {file_path.stem} import {fun_name}; {fun_name}{function_arguments}"
    else:
        run_str = f"import sys; sys.path.append('{file_path.parent}'); from {file_path.stem} import {fun_name}; print({fun_name}{function_arguments})"

    run_command = [sys.executable, "-c", run_str]
    try:
        actual_output = subprocess.run(run_command, capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return (
            1,
            "Your code timed out. Either you have an infinite loop or your are using an input() function without one being required",
        )

    if actual_output.returncode != 0:
        return 1, _safe_decode_stderr(actual_output.stderr)

    if match_type == MatchType.Contains:
        if output not in actual_output.stdout.decode():
            return (
                1,
                f"The output {output} does not match the output {actual_output.stdout.decode()}",
            )

    # if match_type

    print(actual_output.stdout)


# def grade(file_path: Path) -> tuple[int, str]:
#     """Grade the student's work"""
#     file_contents = _read_file(file_path)


def grade_pytest(assignment_path: Path) -> tuple[int, str]:
    """Grade a student based off of the number of pytest tests they pass
    Returns achieved level and comments.
    """
    assignment_dir = assignment_path.parent
    assignment_name = assignment_path.name
    test_path = assignment_dir.parent / "tests" / f"test_{assignment_name}"
    shutil.copy2(test_path, assignment_dir)

    process = subprocess.run(["pytest", "--no-header", "-v", f"{test_path.name}"],
        cwd=f"{assignment_dir}" ,capture_output=True
    )
    pytest_output = process.stdout.decode()

    # Calculate their grade based off of how many tests they passed or failed
    pytest_output_lines = pytest_output.splitlines()
    test_lines = [line for line in pytest_output_lines if re.search("\[\s?\d+%\]", line)]
    num_failed = sum("FAILED" in line for line in test_lines)
    num_passed = sum("PASSED" in line for line in test_lines) 
    score = num_passed / (num_passed + num_failed)

    return score, pytest_output



def main():
    hello_path = Path(
        "/Users/philiphabib/dev/zfmg/pycs/instance/code/001310455/hello.py"
    )
    score, comment = grade_pytest(hello_path)
    print(score)


if __name__ == "__main__":
    main()