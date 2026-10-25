
import csv
import json
from collections import Counter, OrderedDict, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, TypedDict, Union

from exceptions import (
    StudentFileNotFoundError,
    StudentFilePermissionError,
)

# Grades can be whole numbers or decimals.
Grade = Union[int, float]

# Define the columns that must exist in the CSV file.
REQUIRED_COLUMNS = {
    "name",
    "major",
    "course1",
    "course2",
    "course3",
    "average",
}


@dataclass
class Student:
    """Store a student's details and grades."""

    name: str
    major: str
    course1: float
    course2: float
    course3: float
    average: float


@dataclass
class Course:
    """Store a course's total grade and number of students."""

    total: float
    no_of_students: int

    def calculate_average(self) -> float:
        """Calculate the average grade, avoiding division by zero."""
        if self.no_of_students == 0:
            return 0.0

        return self.total / self.no_of_students


# TypedDict documents the expected structure of the JSON report.
class CourseAverages(TypedDict):
    """Store statistics for the three courses."""

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
    """Describe one student's position in the rankings."""

    rank: int
    percentile: float
    name: str
    major: str
    course1: float
    course2: float
    course3: float
    average: float


# defaultdict automatically creates an empty list for each new major.
majors: Dict[str, List[Student]] = defaultdict(list)


def load_students(file_path: Union[str, Path] = "test.csv") -> None:
    """Read student records, validate the CSV, and group students by major."""
    majors.clear()
    path = Path(file_path)

    try:
        with path.open(mode="r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            # A CSV must have a header row.
            if reader.fieldnames is None:
                raise ValueError("The CSV file is empty or has no header row.")

            # Remove surrounding spaces from column names.
            reader.fieldnames = [
                name.strip() if name else ""
                for name in reader.fieldnames
            ]

            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(
                    f"CSV is missing required columns: {missing}"
                )

            for row_number, row in enumerate(reader, start=2):
                # Ignore completely blank rows.
                if not row or all(
                    not value or not value.strip()
                    for value in row.values()
                    if value is not None
                ):
                    continue

                # Reject rows with extra values that have no column name.
                if None in row:
                    raise ValueError(
                        f"Row {row_number} contains too many values."
                    )

                # Check that required fields contain values.
                for column in REQUIRED_COLUMNS:
                    value = row.get(column)

                    if value is None or not value.strip():
                        raise ValueError(
                            f"Row {row_number}: '{column}' cannot be empty."
                        )

                name = row["name"].strip()
                major = row["major"].strip()

                try:
                    course1 = float(row["course1"])
                    course2 = float(row["course2"])
                    course3 = float(row["course3"])
                    supplied_average = float(row["average"])
                except ValueError as error:
                    raise ValueError(
                        f"Row {row_number}: grades and average "
                        "must be numbers."
                    ) from error

                grades = [course1, course2, course3, supplied_average]

                # Reject NaN, infinity, and grades outside the valid range.
                if any(
                    not 0 <= grade <= 100
                    for grade in grades
                    if grade == grade and abs(grade) != float("inf")
                ):
                    raise ValueError(
                        f"Row {row_number}: grades must be between 0 and 100."
                    )

                if any(
                    grade != grade or abs(grade) == float("inf")
                    for grade in grades
                ):
                    raise ValueError(
                        f"Row {row_number}: grades must be finite numbers."
                    )

                # Calculate the average from the three course grades so
                # rankings do not depend on an incorrect CSV average.
                calculated_average = (course1 + course2 + course3) / 3

                # Warn when the supplied average does not match the grades.
                if abs(supplied_average - calculated_average) > 0.02:
                    print(
                        f"Warning: row {row_number}'s supplied average "
                        "does not match its course grades. "
                        "The calculated average will be used."
                    )

                student = Student(
                    name=name,
                    major=major,
                    course1=course1,
                    course2=course2,
                    course3=course3,
                    average=calculated_average,
                )

                majors[student.major].append(student)

    except FileNotFoundError as error:
        raise StudentFileNotFoundError(
            f"Student data file '{path}' was not found."
        ) from error

    except PermissionError as error:
        raise StudentFilePermissionError(
            f"Permission denied when reading '{path}'."
        ) from error

    if not majors:
        raise ValueError("The CSV file contains no student records.")


def get_grade_distributions_per_course(
    course_results: Union[List[Grade], deque],
) -> Dict[str, int]:
    """Count grades in predefined score ranges using Counter."""
    # Use the original numeric grade, preserving decimal boundaries.
    distribution = Counter()

    for grade in course_results:
        if 0 <= grade <= 40:
            band = "0-40"
        elif grade <= 50:
            band = "41-50"
        elif grade <= 60:
            band = "51-60"
        elif grade <= 70:
            band = "61-70"
        elif grade <= 80:
            band = "71-80"
        else:
            band = "81-100"

        distribution[band] += 1

    return dict(distribution)


def calculate_median(grades: Union[List[Grade], deque]) -> float:
    """Return the middle grade, or the mean of the two middle grades."""
    if not grades:
        return 0.0

    return float(median(grades))


def calculate_mode(
    grades: Union[List[Grade], deque],
) -> Optional[Grade]:
    """Return the most frequent grade, or None when no grades exist."""
    grade_counts = Counter(grades)

    if not grade_counts:
        return None

    # If several grades tie, Counter returns the first encountered grade.
    return grade_counts.most_common(1)[0][0]


def calculate_major_statistics(major: str) -> MajorReport:
    """Calculate averages, medians, modes, and distributions for a major."""
    if major not in majors or not majors[major]:
        raise ValueError(f"No students were found for major '{major}'.")

    course_1_results = deque()
    course_2_results = deque()
    course_3_results = deque()

    for student in majors[major]:
        course_1_results.append(student.course1)
        course_2_results.append(student.course2)
        course_3_results.append(student.course3)

    # Keep decimal grades instead of converting them to integers.
    course_1 = Course(sum(course_1_results), len(course_1_results))
    course_2 = Course(sum(course_2_results), len(course_2_results))
    course_3 = Course(sum(course_3_results), len(course_3_results))

    course_1_average = course_1.calculate_average()
    course_2_average = course_2.calculate_average()
    course_3_average = course_3.calculate_average()

    # Each course contributes equally to the overall major average.
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
            "course1": round(course_1_average, 2),
            "course2": round(course_2_average, 2),
            "course3": round(course_3_average, 2),
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
    """Print course averages and other statistics for every major."""
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


def calculate_percentile(rank: int, total_students: int) -> float:
    """Calculate percentile from rank, with rank 1 representing the top."""
    if total_students <= 1:
        return 100.0

    return round(
        (total_students - rank) / (total_students - 1) * 100,
        2,
    )


def build_rankings(major: str) -> List[RankingEntry]:
    """Return students sorted by average, including their percentiles."""
    if major not in majors or not majors[major]:
        raise ValueError(f"No students were found for major '{major}'.")

    ranked_students = sorted(
        majors[major],
        key=lambda student: student.average,
        reverse=True,
    )

    report: List[RankingEntry] = []
    total_students = len(ranked_students)

    for rank, student in enumerate(ranked_students, start=1):
        report.append({
            "rank": rank,
            "percentile": calculate_percentile(rank, total_students),
            "name": student.name,
            "major": student.major,
            "course1": student.course1,
            "course2": student.course2,
            "course3": student.course3,
            "average": round(student.average, 2),
        })

    return report


def generate_rankings(major: str) -> None:
    """Print the ranking report for a major."""
    report = build_rankings(major)

    print(
        "\n-------------------- Ranked Performance List "
        "--------------------"
    )
    print("Rank  Name  Course 1  Course 2  Course 3  Average  Percentile")

    for student in report:
        print(
            f"{student['rank']}. {student['name']}  "
            f"{student['course1']}  {student['course2']}  "
            f"{student['course3']}  {student['average']}  "
            f"{student['percentile']}%"
        )


def generate_rankings_json(major: str) -> None:
    """Save the ranking report for a major as a JSON file."""
    report = build_rankings(major)

    report_path = Path("reports")
    report_path.mkdir(parents=True, exist_ok=True)

    # Replace spaces so the major name can be used in a filename.
    safe_major_name = major.replace(" ", "_")
    file_path = report_path / f"{safe_major_name}_rankings.json"

    with file_path.open(mode="w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Rankings report saved to: {file_path}")


def generate_json_report() -> None:
    """Save statistics for all majors in one JSON report."""
    # OrderedDict explicitly preserves the order in which majors are added.
    report: Dict[str, MajorReport] = OrderedDict()

    for major in majors:
        report[major] = calculate_major_statistics(major)

    report_path = Path("reports")
    report_path.mkdir(parents=True, exist_ok=True)
    file_path = report_path / "grade_report.json"

    with file_path.open(mode="w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Grade report saved to: {file_path}")


def calculate_rolling_averages(
    grades: List[Grade],
    window: int,
) -> List[float]:
    """Calculate a rolling average using the most recent grades."""
    if window <= 0:
        raise ValueError("The rolling-average window must be greater than 0.")

    recent_grades = deque(maxlen=window)
    averages = []

    for grade in grades:
        recent_grades.append(grade)
        averages.append(round(sum(recent_grades) / len(recent_grades), 2))

    return averages


def show_rolling_averages() -> None:
    """Display rolling averages for a selected major and course."""
    major = input("Enter the major: ").strip()

    if major not in majors:
        print("Major not found.")
        return

    course = input("Enter course (course1, course2, or course3): ").strip()

    if course not in {"course1", "course2", "course3"}:
        print("Invalid course name.")
        return

    try:
        window = int(input("Enter rolling-average window size: "))
        if window <= 0:
            print("Window size must be greater than 0.")
            return
    except ValueError:
        print("Window size must be a whole number.")
        return

    grades = [getattr(student, course) for student in majors[major]]
    averages = calculate_rolling_averages(grades, window)

    print(f"Rolling averages for {major}, {course}:")
    print(averages)


def show_grade_distributions() -> None:
    """Print grade distributions for each course in a selected major."""
    major = input("Enter the major: ").strip()

    if major not in majors:
        print("Major not found.")
        return

    students = majors[major]
    print(f"\nGrade distributions for {major}")

    for course in ("course1", "course2", "course3"):
        grades = [getattr(student, course) for student in students]
        distribution = get_grade_distributions_per_course(grades)
        print(f"{course}: {distribution}")


def show_menu() -> None:
    """Display the menu and handle the user's choices."""
    while True:
        print("\n===== Student Grade Analytics Tool =====")
        print("1. View course and major averages")
        print("2. Generate student rankings")
        print("3. View grade distributions")
        print("4. Generate JSON report")
        print("5. View rolling averages")
        print("6. Exit")

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
            show_rolling_averages()

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please choose a number from 1 to 6.")


def main() -> None:
    """Load student data and start the application."""
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
