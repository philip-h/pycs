import itertools
from pathlib import Path
import re
import shutil
import subprocess

from . import GradingStrategy


class ICS3UGrader(GradingStrategy):
    def __init__(self, abs_code_path: Path):
        super().__init__(abs_code_path)

    def grade_header_comments(self) -> tuple[float, str]:
        # Ensure there are no blank lines at the beginning of the script!
        # Lists are "pass by reference", so I copy the list to ensure that I do not destroy the file
        # contents for other functions that need it!
        file_contents = self.file_contents[::]
        file_contents = list(
            itertools.dropwhile(lambda line: line.strip() == "", file_contents)
        )

        if not file_contents:
            return 0, "Your file is blank... double check WHICh file you've uploaded"
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
            return (
                2,
                "Header comments not closed! Any feedback after this is useless!\n",
            )

        # Good header comments
        return 4, "Header comments are good\n"

    def grade_var_names(self) -> tuple[float, str]:
        # Lists are "pass by reference", so I copy the list to ensure that I do not destroy the file
        # contents for other functions that need it!
        file_contents = self.file_contents[::]

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

        def __is_snake_case(*, var):
            # All CAPS is okay!
            if var.isupper():
                return True
            # Otherwise, can't contain caps (all or nothing)
            return var.islower()

        bad_var_names = [
            var for var in variables_in_file if not __is_snake_case(var=var)
        ]
        if bad_var_names:
            return (
                2,
                "There are variable names that do not follow class conventions:\t"
                + ",".join(bad_var_names)
                + "\n",
            )

        return 4, "Variable names are good\n"

    def grade_ipo_comments(self) -> tuple[float, str]:
        file_string = "\n".join([line.strip().lower() for line in self.file_contents])
        has_i = re.search(r"^#\s?[Ii]nput", file_string, re.MULTILINE)
        has_p = re.search(r"^#\s?[Pp]rocessing", file_string, re.MULTILINE)
        has_o = re.search(r"^#\s?[Oo]utput", file_string, re.MULTILINE)
        has_po = re.search(r"^#\s?[Pp]rocessing\s?/\s?[Oo]utput", file_string, re.MULTILINE)

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

    def _run_pytest(self):
        """Run the pytest application with a given test_*.py file and a given assignment directory"""
        # Move pytest file to student's assignment directory
        student_dir = self.abs_code_path.parent
        code_filename = self.abs_code_path.name
        abs_pytest_path = student_dir.parent / "tests" / f"test_{code_filename}"
        shutil.copy2(abs_pytest_path, student_dir)

        try:
            process = subprocess.run(
                [
                    "pytest",
                    "--no-header",
                    "-v",
                    "--tb=short",
                    f"{abs_pytest_path.name}",
                ],
                cwd=f"{student_dir}",
                capture_output=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None

        return process.stdout.decode()

    def grade_unit_test(self) -> tuple[float, str]:
        # Run the pytest
        pytest_output = self._run_pytest()
        if pytest_output is None:
            return (
                1,
                "\n\nYour code has some kind of infinite loop. Either that or your program is waiting for input that my grader won't give it!",
            )

        # Calculate their grade based off of how many tests they passed or failed
        pytest_output_lines = pytest_output.splitlines()
        test_lines = [
            line for line in pytest_output_lines if re.search(r"[\s*\d+%]", line)
        ]
        num_failed = sum("FAILED" in line for line in test_lines)
        num_passed = sum("PASSED" in line for line in test_lines)
        # Score is a number between 0 and 1
        try:
            score = num_passed / (num_passed + num_failed)
        except ZeroDivisionError:
            # Happens if pytest fails to run due to code that does not compile
            return (
                1,
                "\n\nTwo possible problems. 1) Your code does not run (try running it in VS Code. If it doesn't run there, it won't run on pycs.) 2) We are in a functions unit and you didn't name your functions correctly. Please double check your function names. 3) You added your functions INSIDE of the main function. `def <func_name>` needs to be at the very left of the screen.",
            )

        return round(score * 4, 1), pytest_output

    def grade_student(self) -> tuple[float, str]:
        # Gather all of the comments and scores
        hc_score, hc_comments = self.grade_header_comments()
        ipo_score, ipo_comments = self.grade_ipo_comments()
        var_score, var_comments = self.grade_var_names()
        ut_score, ut_comments = self.grade_unit_test()

        # Calculate weighted score
        scores = [hc_score, ipo_score, var_score, ut_score]
        weights = [1, 1, 1, 4]
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        # Generate output comments
        comments_header = f"{' Grading Comments ':=^80}\n"
        variables_header = f"{' Grading Variable Names ':=^80}\n"
        unit_test_header = f"{' Grading Correctness ':=^80}\n"

        comments = (
            comments_header
            + hc_comments
            + ipo_comments
            + variables_header
            + var_comments
            + unit_test_header
            + ut_comments
        )

        return round(weighted_score, 1), comments
