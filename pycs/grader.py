"""
author: @philiph
The heart and soul of the grader application.
"""

from pathlib import Path
import itertools
import re
import subprocess
import shutil


def read_code(file_path: Path) -> list[str] | None:
    """Read data from given file_path and returns a list of lines"""
    try:
        with open(file_path, mode="r", encoding="utf-8") as f_in:
            return f_in.read().splitlines()
    except FileNotFoundError:
        return None


class CodingClass:
    """A class with a grade_student method"""

    def grade_student(self, assignment_path: Path) -> tuple[int, str]:
        """Grade a student based off of their coding style and correctness.
        Returns the achieved level and comments
        """


class ICS3U(CodingClass):
    def _check_header_comments(self, file_contents: list[str]) -> tuple[int, str]:
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

    def _check_variable_names(self, file_contents: list[str]) -> tuple[int, str]:
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

    def _check_ipo(self, file_contents: list[str]) -> tuple[int, str]:
        """Checks for the presence of IPO comments as a class convention.
        Returns the achieved level and comments.

        Level 0: No IPO comments present
        Level 2: Some IPO comments present
        Level 4: All IPO comments present
        """
        file_string = "\n".join([line.strip().lower() for line in file_contents])
        has_i = re.search(r"^#\s?input$", file_string, re.MULTILINE)
        has_p = re.search(r"^#\s?processing$", file_string, re.MULTILINE)
        has_o = re.search(r"^#\s?output$", file_string, re.MULTILINE)
        has_po = re.search(r"^#\s?processing\s?/\s?output$", file_string, re.MULTILINE)

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

    def _run_pytest(self, test_path: Path, assignment_dir: Path) -> str | None:
        """Run the pytest application with a given test_*.py file and a given assignment directory"""
        try:
            process = subprocess.run(
                ["pytest", "--no-header", "-v", "--tb=short", f"{test_path.name}"],
                cwd=f"{assignment_dir}",
                capture_output=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None

        return process.stdout.decode()

    def _grade_pytest(self, assignment_path: Path) -> tuple[int, str]:
        """Grade a student based off of the number of pytest tests they pass
        Returns achieved level and comments.
        """
        # Move pytest file to student's assignment directory
        assignment_dir = assignment_path.parent
        assignment_name = assignment_path.name
        test_path = assignment_dir.parent / "tests" / f"test_{assignment_name}"
        shutil.copy2(test_path, assignment_dir)

        # Run the pytest
        pytest_output = self._run_pytest(test_path, assignment_dir)
        if pytest_output is None:
            return (
                1,
                "\n\nYour code has some kind of infinite loop. Either that or your program is waiting for input that my grader won't give it!",
            )

        # Calculate their grade based off of how many tests they passed or failed
        pytest_output_lines = pytest_output.splitlines()
        test_lines = [
            line for line in pytest_output_lines if re.search("[\s*\d+%]", line)
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

    def grade_student(self, assignment_path: Path) -> tuple[int, str]:
        """Grade a student based off of their coding style and correctness.
        Returns the achieved level and comments
        """
        file_contents = read_code(assignment_path)
        if file_contents is None:
            return 0, "File could not be read... try re-uploading or telling Mr. Habib"

        # Gather all of the comments and scores
        hc_score, hc_comments = self._check_header_comments(file_contents)
        ipo_score, ipo_comments = self._check_ipo(file_contents)
        var_score, var_comments = self._check_variable_names(file_contents)
        pt_score, pt_comments = self._grade_pytest(assignment_path)

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


class ICS4U(CodingClass):
    def _check_header_comments(self, file_contents: list[str]) -> tuple[int, str]:
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
        file_contents = list(
            itertools.dropwhile(
                lambda line: (line.strip() == "" or "import" in line), file_contents
            )
        )

        if not file_contents:
            return 0, "Your file is blank... double check WHICh file you've uploaded"
        # Ensure docstring by checking the first line
        if not file_contents[0] == "/**":
            return 0, "Header comments are missing.\n"

        # Checking class conventions for docstring
        comment = ""
        if not re.match(r" ?\* @?author:? [a-zA-Z]+", file_contents[1]):
            comment += "Missing author (or wrong format) in docstring\n"
        if not re.match(r" ?\* @?date:? \d\d/\d\d/\d\d\d\d", file_contents[2]):
            comment += "Missing date (or wrong format) in docstring\n"
        if not re.match(r" ?\* \w+", file_contents[3]):
            comment += "Missing one sentence description of module in docstring\n"
        if comment != "":
            return 2, comment

        # Ensure docstring is closed
        if file_contents[0] == "/**" and not "*/" in file_contents[4].replace(" ", ""):
            return (
                2,
                "Header comments not closed! Any feedback after this is useless!\n",
            )

        # Good header comments
        return 4, "Header comments are good\n"

    def _check_variable_names(self, file_contents: list[str]) -> tuple[int, str]:
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
            # . Starts with any number of spaces / indentations
            # . Contains only letters (datatypes)
            # . Followed by a space
            # . Followed by all the letters
            # . Followed by one equal sign or a semi colon
            var_in_line = re.search(r"^\s*[a-zA-Z]+ ([a-zA-Z_$][\w$]*)\s*[=;]", line)
            if var_in_line:
                beginning, end = var_in_line.span()
                var = line[beginning:end].strip().split()[1].removesuffix(";")
                variables_in_file.append(var)

        def __is_camel_case(*, var):
            # All CAPS is okay!
            if var.isupper():
                return True
            # Otherwise, can't start with caps and can't have underscore
            return not var[0].isupper() and "_" not in var

        bad_var_names = [
            var for var in variables_in_file if not __is_camel_case(var=var)
        ]
        if bad_var_names:
            return (
                2,
                "There are variable names that do not follow class conventions:\t"
                + ",".join(bad_var_names)
                + "\n",
            )

        return 4, "Variable names are good\n"

    def _check_ipo(self, file_contents: list[str]) -> tuple[int, str]:
        """Checks for the presence of IPO comments as a class convention.
        Returns the achieved level and comments.

        Level 0: No IPO comments present
        Level 2: Some IPO comments present
        Level 4: All IPO comments present
        """
        file_string = "\n".join([line.strip().lower() for line in file_contents])
        has_i = re.search(r"^\/\/\s?[iI]nput$", file_string, re.MULTILINE)
        has_p = re.search(r"^\/\/\s?[pP]rocessing$", file_string, re.MULTILINE)
        has_o = re.search(r"^\/\/\s?[oO]utput$", file_string, re.MULTILINE)
        has_po = re.search(
            r"^\/\/\s?[pP]rocessing\s?/\s?[oO]utput$", file_string, re.MULTILINE
        )

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

    def _does_code_compile(
        self, assignment_path: Path, assignment_dir: Path
    ) -> tuple[bool, str | None]:
        """Check if the given java code compiles"""
        try:
            process = subprocess.run(
                ["javac", f"{assignment_path.name}"],
                cwd=f"{assignment_dir}",
                capture_output=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, None

        return process.returncode == 0, process.stderr.decode()

    def _run_junit(
        self, assignment_dir: Path, assignment_file: str, test_file: str
    ) -> tuple[bool, str]:
        """Run the junit jar file with a given Test*.java file and a given assignment directory"""
        try:
            process = subprocess.run(
                [
                    "javac",
                    "-cp",
                    str(
                        assignment_dir.parent
                        / "lib"
                        / "junit-platform-console-standalone-1.7.0-all.jar"
                    ),
                    str(assignment_file),
                    str(test_file),
                ],
                cwd=f"{assignment_dir}",
                capture_output=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, "I think you have an infinite loop in your code (OR infinite recursion!)"

        if process.returncode != 0:
            return False, process.stderr.decode()

        process = subprocess.run(
            [
                "java",
                "-jar",
                str(
                    assignment_dir.parent
                    / "lib"
                    / "junit-platform-console-standalone-1.7.0-all.jar"
                ),
                "-cp",
                ".",
                "-c",
                f"{test_file.removesuffix('.java')}",
                "--disable-banner",
                "--disable-ansi-colors",
            ],
            cwd=f"{assignment_dir}",
            capture_output=True,
            timeout=5,
            check=False,
        )

        return True, process.stdout.decode()

    def _grade_junit(self, assignment_path: Path) -> tuple[int, str]:
        """Grade a student based off of the number of pytest tests they pass
        Returns achieved level and comments.
        """
        # Move pytest file to student's assignment directory
        assignment_dir = assignment_path.parent
        assignment_file = assignment_path.name
        test_file_path = assignment_dir.parent / "tests-java" / f"Test{assignment_file}"
        shutil.copy2(test_file_path, assignment_dir)
        test_file = f"Test{assignment_file}"

        # Check if code compiles
        code_compiles, err = self._does_code_compile(assignment_path, assignment_dir)
        if not code_compiles:
            return (1, f"\n\nError: {err}")

        junit_did_succeed, junit_output = self._run_junit(assignment_dir, assignment_file, test_file)
        if not junit_did_succeed:
            return (1, junit_output)

        # Calculate their grade based off of how many tests they passed or failed
        # The last two lines of output indicate the number of passed and failed tests
        junit_output_lines = junit_output.splitlines()[-3:-1]

        def __find_number_in_str(string: str) -> int:
            maybe_number = re.search(r"\d+", string)
            if maybe_number is None:
                return 0
            number = maybe_number.group()
            try:
                number = int(number)
            except ValueError:
                return 0
            return number

        num_passed = __find_number_in_str(junit_output_lines[0])
        num_failed = __find_number_in_str(junit_output_lines[1])
        
        # Score is a number between 0 and 1
        try:
            score = num_passed / (num_passed + num_failed)
        except ZeroDivisionError:
            # Happens if pytest fails to run due to code that does not compile
            return (
                1,
                "\n\nTwo possible problems.\n" +
                "1) Your code does not run (try running it in Eclipse. If it doesn't run there, it won't run on pycs.\n"+ 
                "2) We are in a functions unit and you didn't name your functions correctly. Please double check your function names."
            )

        return round(score * 4, 1), junit_output

    def grade_student(self, assignment_path: Path) -> tuple[int, str]:
        """Grade a student based off of their coding style and correctness.
        Returns the achieved level and comments
        """
        file_contents = read_code(assignment_path)
        if file_contents is None:
            return 0, "File could not be read... try re-uploading or telling Mr. Habib"

        # Gather all of the comments and scores
        hc_score, hc_comments = self._check_header_comments(file_contents)
        ipo_score, ipo_comments = self._check_ipo(file_contents)
        var_score, var_comments = self._check_variable_names(file_contents)
        ju_score, ju_comments = self._grade_junit(assignment_path)

        # Calculate weighted score
        scores = [hc_score, ipo_score, var_score, ju_score]
        weights = [1, 1, 1, 4]
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        # Generate output comments
        comments_header = f"{' Grading Comments ':=^80}\n"
        variables_header = f"{' Grading Variable Names ':=^80}\n"
        junit_header = f"{' JUnit Tests ^.^ ':=^80}\n"

        comments = (
            comments_header
            + hc_comments
            + ipo_comments
            + variables_header
            + var_comments
            + junit_header
            + ju_comments
        )

        return round(weighted_score, 1), comments


def Grader(class_id: int) -> CodingClass:
    """Gives back a class-appropriate code grading interface"""
    if class_id == 1:
        return ICS3U()
    else:
        return ICS4U()
