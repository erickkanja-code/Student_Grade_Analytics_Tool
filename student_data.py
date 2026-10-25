"""Student data models and CSV loading/validation."""

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, TypedDict


class StudentFileNotFoundError(Exception):
    """Raised when the student CSV file cannot be found."""


class StudentFilePermissionError(Exception):
    """Raised when the student CSV file cannot be read due to permissions."""


Grade = Union[int, float]


REQUIRED_COLUMNS = {
    "name", "major", "course1", "course2", "course3", "average"
}


@dataclass
class Student:
    """Store a student's name, major, grades, and average."""

    name: str
    major: str
    course1: float
    course2: float
    course3: float
    average: float


@dataclass
class Course:
    """Store the total grades and number of students in a course."""

    total: float
    no_of_students: int

    def calculate_average(self) -> float:
        """Calculate the average grade for the course."""
        if self.no_of_students == 0:
            return 0.0

        return self.total / self.no_of_students


class CourseAverages(TypedDict):
    """Store averages or medians for the three courses."""

    course1: float
    course2: float
    course3: float


class GradeDistributions(TypedDict):
    """Store grade-band counts for each course."""

    course1: Dict[str, int]
    course2: Dict[str, int]
    course3: Dict[str, int]


class MajorReport(TypedDict):
    """Describe the statistics saved for one major."""

    course_averages: CourseAverages
    overall_average: float
    course_medians: CourseAverages
    course_modes: Dict[str, Optional[Grade]]
    grade_distributions: GradeDistributions


class RankingEntry(TypedDict):
    """Describe one student in a ranking report."""

    rank: int
    name: str
    major: str
    course1: float
    course2: float
    course3: float
    average: float


majors: Dict[str, List[Student]] = defaultdict(list)


def load_students(file_path: Union[str, Path] = "test.csv") -> None:
    """Read, validate, and group student records from a CSV file."""
    majors.clear()

    try:
        with open(file_path, mode="r", encoding="utf-8", newline="") as file:
            rows = csv.DictReader(file, strict=True)

            # Check that the file contains a header row.
            if rows.fieldnames is None:
                raise ValueError("The CSV file is empty or has no header.")

            # Remove extra spaces around column names.
            rows.fieldnames = [
                name.strip() if name else "" for name in rows.fieldnames
            ]

            if "" in rows.fieldnames:
                raise ValueError(
                    "The CSV header contains an empty column name."
                )

            if len(rows.fieldnames) != len(set(rows.fieldnames)):
                raise ValueError(
                    "The CSV header contains duplicate column names."
                )

            missing_columns = REQUIRED_COLUMNS - set(rows.fieldnames)

            if missing_columns:
                raise ValueError(
                    "Missing CSV columns: "
                    + ", ".join(sorted(missing_columns))
                )

            for row_number, row in enumerate(rows, start=2):
                # None as a key means the row contains extra values.
                if None in row:
                    raise ValueError(
                        f"Row {row_number} contains too many values."
                    )

                # None as a value means the row has too few fields.
                if any(value is None for value in row.values()):
                    raise ValueError(
                        f"Row {row_number} contains too few values."
                    )

                # Skip completely blank rows.
                if all(not value.strip() for value in row.values()):
                    continue

                # Check that required fields are not empty.
                for column in REQUIRED_COLUMNS:
                    value = row.get(column)

                    if value is None or not value.strip():
                        raise ValueError(
                            f"Row {row_number}: '{column}' cannot be empty."
                        )

                try:
                    course1 = float(row["course1"])
                    course2 = float(row["course2"])
                    course3 = float(row["course3"])
                    supplied_average = float(row["average"])
                except ValueError as error:
                    raise ValueError(
                        f"Row {row_number}: grades and average "
                        "must be numeric."
                    ) from error

                grades = [
                    course1,
                    course2,
                    course3,
                    supplied_average,
                ]

                # Reject NaN and infinity, which are not valid grades.
                if any(not math.isfinite(grade) for grade in grades):
                    raise ValueError(
                        f"Row {row_number}: grades must be finite numbers."
                    )

                # Grades must be between 0 and 100.
                if any(grade < 0 or grade > 100 for grade in grades):
                    raise ValueError(
                        f"Row {row_number}: grades must be between 0 and 100."
                    )

                name = row["name"].strip()
                major = row["major"].strip()

                # Calculate the average from the three course grades.
                calculated_average = (
                    course1 + course2 + course3
                ) / 3

                if abs(supplied_average - calculated_average) > 0.02:
                    print(
                        f"Warning: row {row_number}'s average does not "
                        "match its course grades. The calculated average "
                        "will be used."
                    )

                new_student = Student(
                    name=name,
                    major=major,
                    course1=course1,
                    course2=course2,
                    course3=course3,
                    average=calculated_average,
                )

                majors[new_student.major].append(new_student)

    except FileNotFoundError as error:
        raise StudentFileNotFoundError(
            f"The student data file '{file_path}' was not found."
        ) from error

    except PermissionError as error:
        raise StudentFilePermissionError(
            f"Permission denied when trying to read '{file_path}'."
        ) from error

    except csv.Error as error:
        raise ValueError(
            f"The CSV file is malformed: {error}"
        ) from error

    # Do not start the menu if there are no usable student records.
    if not majors:
        raise ValueError("The CSV file contains no student records.")