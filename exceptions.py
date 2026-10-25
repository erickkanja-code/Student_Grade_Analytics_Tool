
class StudentFileNotFoundError(Exception):
    """Raised when the student CSV file cannot be found."""

    pass


class StudentFilePermissionError(Exception):
    """Raised when the program cannot access a file."""

    pass
