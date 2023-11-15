import itertools
from pathlib import Path
import re
import subprocess
import shutil

from . import GradingStrategy


class ICS4UGrader(GradingStrategy):
    def __init__(self, abs_code_path: Path):
        super().__init__(abs_code_path)

    def grade_header_comments(self) -> tuple[float, str]:
        # Ensure there are no blank lines at the beginning of the script!
        # Lists are "pass by reference", so I copy the list to ensure that I do not destroy the file
        # contents for other functions that need it!
        file_contents = self.file_contents[::]
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
        if not re.match(r" ?\* @?[Aa]uthor:? [a-zA-Z]+", file_contents[1]):
            comment += "Missing author (or wrong format) in docstring\n"
        if not re.match(r" ?\* @?[Dd]ate:? \d\d/\d\d/\d\d\d\d", file_contents[2]):
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

    def grade_var_names(self) -> tuple[float, str]:
        # Lists are "pass by reference", so I copy the list to ensure that I do not destroy the file
        # contents for other functions that need it!
        file_contents = self.file_contents[::]

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

    def grade_ipo_comments(self) -> tuple[float, str]:
        file_string = "\n".join([line.strip().lower() for line in self.file_contents])
        has_i = re.search(r"^\/\/\s?[Ii]nput$", file_string, re.MULTILINE)
        has_p = re.search(r"^\/\/\s?[Pp]rocessing$", file_string, re.MULTILINE)
        has_o = re.search(r"^\/\/\s?[Oo]utput$", file_string, re.MULTILINE)
        has_po = re.search(
            r"^\/\/\s?[Pp]rocessing\s?/\s?[Oo]utput$", file_string, re.MULTILINE
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
        self, code_filename: str, student_dir: Path
    ) -> tuple[bool, str | None]:
        """Check if the given java code compiles"""
        try:
            process = subprocess.run(
                ["javac", f"{code_filename}"],
                cwd=f"{student_dir}",
                capture_output=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, None
        if process.returncode == 0:
            return True, process.stdout.decode()
        else:
            return False, process.stderr.decode()

    def _run_junit(
        self, student_dir: Path, code_filename: str, junit_test_filename: str
    ) -> tuple[bool, str]:
        """Run the junit jar file with a given Test*.java file and a given assignment directory"""
        try:
            process = subprocess.run(
                [
                    "javac",
                    "-cp",
                    str(
                        student_dir.parent
                        / "lib"
                        / "junit-platform-console-standalone-1.7.0-all.jar"
                    ),
                    str(code_filename),
                    str(junit_test_filename),
                ],
                cwd=f"{student_dir}",
                capture_output=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return (
                False,
                "I think you have an infinite loop in your code (OR infinite recursion!)",
            )

        if process.returncode != 0:
            return False, process.stderr.decode()

        process = subprocess.run(
            [
                "java",
                "-jar",
                str(
                    student_dir.parent
                    / "lib"
                    / "junit-platform-console-standalone-1.7.0-all.jar"
                ),
                "-cp",
                ".",
                "-c",
                f"{junit_test_filename.removesuffix('.java')}",
                "--disable-banner",
                "--disable-ansi-colors",
            ],
            cwd=f"{student_dir}",
            capture_output=True,
            timeout=5,
            check=False,
        )

        return True, process.stdout.decode()

    def grade_unit_test(self) -> tuple[float, str]:
        # Move Test file to student's assignment directory
        student_dir = self.abs_code_path.parent
        code_filename = self.abs_code_path.name
        junit_test_filename = f"Test{code_filename}"
        abs_junit_test_path = student_dir.parent / "tests-java" / junit_test_filename 
        shutil.copy2(abs_junit_test_path, student_dir)

        # Check if java code compiles
        code_compiles, err_message = self._does_code_compile(code_filename, student_dir)
        if not code_compiles:
            return (1, f"\n\nError: {err_message}")

        junit_did_succeed, junit_output = self._run_junit(student_dir, code_filename, junit_test_filename)
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
