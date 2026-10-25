
import csv
import json
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, deque, Counter
from statistics import median
from typing import List, Dict, Optional, Union, TypedDict

from exceptions import StudentFileNotFoundError, StudentFilePermissionError


# A grade can be an integer or a decimal number.
Grade = Union[int, float]

# These columns must exist in the CSV file.
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


# TypedDict describes the expected structure of the JSON report.
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


# defaultdict creates an empty list automatically for each new major.
majors: Dict[str, List[Student]] = defaultdict(list)


def load_students(file_path: Union[str, Path] = "test.csv") -> None:
    """Read, validate, and group student records from a CSV file."""
    majors.clear()

    try:
        with open(file_path, mode="r", encoding="utf-8", newline="") as file:
            rows = csv.DictReader(file)

            # Check that the file contains a header row.
            if rows.fieldnames is None:
                raise ValueError("The CSV file is empty or has no header.")

            # Remove extra spaces around column names.
            rows.fieldnames = [
                name.strip() if name else "" for name in rows.fieldnames
            ]

            missing_columns = REQUIRED_COLUMNS - set(rows.fieldnames)

            if missing_columns:
                raise ValueError(
                    "Missing CSV columns: "
                    + ", ".join(sorted(missing_columns))
                )

            for row_number, row in enumerate(rows, start=2):
                # Skip completely blank rows.
                if all(
                    value is None or not value.strip()
                    for value in row.values()
                ):
                    continue

                # None as a key means the row contains extra values.
                if None in row:
                    raise ValueError(
                        f"Row {row_number} contains too many values."
                    )

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

                grades = [course1, course2, course3, supplied_average]

                # Reject NaN and infinity, which are not valid grades.
                if any(
                    grade != grade or abs(grade) == float("inf")
                    for grade in grades
                ):
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
                calculated_average = (course1 + course2 + course3) / 3

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

    # Do not start the menu if there are no usable student records.
    if not majors:
        raise ValueError("The CSV file contains no student records.")


def get_grade_distributions_per_course(
    course_results: Union[List[Grade], deque],
) -> Dict[str, int]:
    """Count grades in the predefined score ranges using Counter."""
    grade_distribution = Counter(
        "0-40" if 0 <= int(grade) <= 40
        else "41-50" if int(grade) <= 50
        else "51-60" if int(grade) <= 60
        else "61-70" if int(grade) <= 70
        else "71-80" if int(grade) <= 80
        else "81-100"
        for grade in course_results
    )

    return dict(grade_distribution)


def calculate_median(
    grades: Union[List[Grade], deque],
) -> float:
    """Calculate the median grade."""
    if not grades:
        return 0.0

    return float(median(grades))


def calculate_mode(
    grades: Union[List[Grade], deque],
) -> Optional[Grade]:
    """Return the most frequent grade, or None if there are no grades."""
    grade_counts = Counter(grades)

    if not grade_counts:
        return None

    return grade_counts.most_common(1)[0][0]


def calculate_major_statistics(major: str) -> MajorReport:
    """Calculate averages, medians, modes, and distributions for a major."""
    if major not in majors or not majors[major]:
        raise ValueError(f"No students found for major '{major}'.")

    course_1_results = deque()
    course_2_results = deque()
    course_3_results = deque()

    for student in majors[major]:
        course_1_results.append(student.course1)
        course_2_results.append(student.course2)
        course_3_results.append(student.course3)

    # Sum the original grades to preserve decimal values.
    course_1 = Course(sum(course_1_results), len(course_1_results))
    course_2 = Course(sum(course_2_results), len(course_2_results))
    course_3 = Course(sum(course_3_results), len(course_3_results))

    course_1_average = course_1.calculate_average()
    course_2_average = course_2.calculate_average()
    course_3_average = course_3.calculate_average()

    # Calculate the mean of the three course averages.
    major_average = (
        course_1_average + course_2_average + course_3_average
    ) / 3

    course_medians: CourseAverages = {
        "course1": calculate_median(course_1_results),
        "course2": calculate_median(course_2_results),
        "course3": calculate_median(course_3_results),
    }

    course_modes: Dict[str, Optional[Grade]] = {
        "course1": calculate_mode(course_1_results),
        "course2": calculate_mode(course_2_results),
        "course3": calculate_mode(course_3_results),
    }

    return {
        "course_averages": {
            "course1": course_1_average,
            "course2": course_2_average,
            "course3": course_3_average,
        },
        "overall_average": round(major_average, 2),
        "course_medians": course_medians,
        "course_modes": course_modes,
        "grade_distributions": {
            "course1": get_grade_distributions_per_course(
                course_1_results
            ),
            "course2": get_grade_distributions_per_course(
                course_2_results
            ),
            "course3": get_grade_distributions_per_course(
                course_3_results
            ),
        },
    }


def show_averages() -> None:
    """Print course and overall averages, medians, and modes."""
    for major in majors:
        stats = calculate_major_statistics(major)

        print(f"\nStatistics for {major}")
        print("------------------------------")
        print(f"Course 1 average: {stats['course_averages']['course1']}")
        print(f"Course 2 average: {stats['course_averages']['course2']}")
        print(f"Course 3 average: {stats['course_averages']['course3']}")
        print(f"Overall major average: {stats['overall_average']}")
        print("Course medians:", stats["course_medians"])
        print("Course modes:", stats["course_modes"])


def generate_rankings(major: str) -> None:
    """Print students in descending order of their average grade."""
    ranked_list = sorted(
        majors[major],
        key=lambda student: student.average,
        reverse=True,
    )

    print("\n-------------------- Ranked Performance List --------------------")
    print("Rank  Name  Course 1  Course 2  Course 3  Average")

    for index, student in enumerate(ranked_list, start=1):
        print(
            f"{index}. {student.name}  "
            f"{student.course1}  "
            f"{student.course2}  "
            f"{student.course3}  "
            f"{student.average}"
        )


def generate_rankings_json(major: str) -> None:
    """Save a major's student rankings as a JSON file."""
    ranked_list = sorted(
        majors[major],
        key=lambda student: student.average,
        reverse=True,
    )

    report: List[RankingEntry] = []

    for index, student in enumerate(ranked_list, start=1):
        report.append({
            "rank": index,
            "name": student.name,
            "major": student.major,
            "course1": student.course1,
            "course2": student.course2,
            "course3": student.course3,
            "average": student.average,
        })

    report_path = Path("reports")
    report_path.mkdir(parents=True, exist_ok=True)

    # Replace spaces in the major name to create a valid filename.
    safe_major_name = major.replace(" ", "_")
    file_path = report_path / f"{safe_major_name}_rankings.json"

    with file_path.open(mode="w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Rankings report saved to: {file_path}")


def generate_json_report() -> None:
    """Save statistics for all majors in a JSON report."""
    report: Dict[str, MajorReport] = {}

    for major in majors:
        report[major] = calculate_major_statistics(major)

    report_path = Path("reports")
    report_path.mkdir(parents=True, exist_ok=True)
    file_path = report_path / "grade_report.json"

    with file_path.open(mode="w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Grade report saved to: {file_path}")


def show_grade_distributions() -> None:
    """Print grade distributions for a major selected by the user."""
    major = input("Enter the major: ").strip()

    if major not in majors:
        print("Major not found.")
        return

    students = majors[major]

    print(f"\nGrade distributions for {major}")

    print(
        "Course 1:",
        get_grade_distributions_per_course(
            [student.course1 for student in students]
        ),
    )
    print(
        "Course 2:",
        get_grade_distributions_per_course(
            [student.course2 for student in students]
        ),
    )
    print(
        "Course 3:",
        get_grade_distributions_per_course(
            [student.course3 for student in students]
        ),
    )


def show_menu() -> None:
    """Display the menu and respond to the user's selection."""
    while True:
        print("\n===== Student Grade Analytics Tool =====")
        print("1. View course and major averages")
        print("2. Generate student rankings")
        print("3. View grade distributions")
        print("4. Generate JSON report")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_averages()

        elif choice == "2":
            major = input("Enter the major: ").strip()

            if major in majors:
                generate_rankings(major)
                generate_rankings_json(major)
            else:
                print("Major not found.")

        elif choice == "3":
            show_grade_distributions()

        elif choice == "4":
            generate_json_report()

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")


def main() -> None:
    """Load the student records and start the menu."""
    try:
        load_students("test.csv")
        show_menu()

    except (
        StudentFileNotFoundError,
        StudentFilePermissionError,
        ValueError,
    ) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
