from abc import ABC, abstractmethod
from pathlib import Path

class GradingStrategy(ABC):
    def __init__(self, abs_code_path: Path):
        self.abs_code_path = abs_code_path
        self.file_contents = self._read_code(abs_code_path)

    def _read_code(self, abs_code_path: Path) -> list[str]:
        """Read a students code file into memroy

        Args:
            abs_code_path: The absolute file of student's code

        Returns:
            The file read into memory

        Raises:
            FileNotFoundError if file cannot be found
        """
        with open(abs_code_path, mode="r", encoding="utf-8") as f_in:
            return f_in.read().splitlines()

    @abstractmethod
    def grade_header_comments(self) -> tuple[float, str]:
        """Checks for the presence and correctness of header comments.
        Correctness of header comments are based off of course convensions.

        Returns:
            The achieved level (between 0 and 4) and comments.
        """

    @abstractmethod
    def grade_var_names(self) -> tuple[float, str]:
        """Checks that variable names follow class conventions.

        Returns:
            The achieved level (between 2 and 4) and comments.
        """

    @abstractmethod
    def grade_ipo_comments(self) -> tuple[float, str]:
        """Checks for the presence of IPO comments per class conventions.

        Returns:
            The achieved level (between 0 and 4) and comments.
        """

    @abstractmethod
    def grade_unit_test(self) -> tuple[float, str]:
        """Grade a student based off of the number of unit tests they passed,
        normalized to be a level between 0 and 4

        Returns:
            The achieved level (between 0 and 4) and comments.
        """

    @abstractmethod
    def grade_student(self, abs_code_path: Path) -> tuple[float, str]:
        """Grade a student based off of style (our course convensions) and correctness

        Args:
            abs_code_path: The absolute path of student's submitted code

        Returns:
            The achieved level (between 0 and 4) and comments
        """

