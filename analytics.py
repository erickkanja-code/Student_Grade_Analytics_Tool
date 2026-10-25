"""Grade calculations and report generation."""

import json
from collections import Counter, deque
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Union

from student_data import (
    Course,
    CourseAverages,
    Grade,
    GradeDistributions,
    MajorReport,
    RankingEntry,
    Student,
    majors,
)


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