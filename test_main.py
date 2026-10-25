"""Tests for the Student Grade Analytics Tool.

Run these tests from the project folder with:
    pytest -v
"""

import json
from collections import defaultdict

import pytest

import main


def add_sample_students():
    """Put a small, predictable set of students into the app's data."""
    main.majors.clear()
    main.majors["Computer Science"] = [
        main.Student("Amina", "Computer Science", 80, 90, 70, 80),
        main.Student("Brian", "Computer Science", 60, 70, 80, 70),
    ]
    main.majors["Business"] = [
        main.Student("Chantal", "Business", 50, 60, 70, 60),
    ]


def test_course_calculate_average():
    course = main.Course(total=180, no_of_students=3)

    assert course.calculate_average() == 60


def test_course_average_with_no_students():
    course = main.Course(total=0, no_of_students=0)

    assert course.calculate_average() == 0.0


def test_grade_distribution_counts_each_range():
    grades = [40, 41, 50, 51, 60, 61, 70, 71, 80, 81, 100]

    result = main.get_grade_distributions_per_course(grades)

    assert result == {
        "0-40": 1,
        "41-50": 2,
        "51-60": 2,
        "61-70": 2,
        "71-80": 2,
        "81-100": 2,
    }


def test_median_returns_middle_grade():
    assert main.calculate_median([10, 20, 30]) == 20.0


def test_median_returns_zero_for_empty_list():
    assert main.calculate_median([]) == 0.0


def test_mode_returns_most_frequent_grade():
    assert main.calculate_mode([70, 80, 80, 90]) == 80


def test_mode_returns_none_for_empty_list():
    assert main.calculate_mode([]) is None


def test_calculate_major_statistics():
    add_sample_students()

    result = main.calculate_major_statistics("Computer Science")

    assert result["course_averages"] == {
        "course1": 70.0,
        "course2": 80.0,
        "course3": 75.0,
    }
    assert result["overall_average"] == 75.0
    assert result["course_medians"] == {
        "course1": 70.0,
        "course2": 80.0,
        "course3": 75.0,
    }


def test_calculate_statistics_for_unknown_major_raises_error():
    main.majors.clear()

    with pytest.raises(ValueError, match="No students found"):
        main.calculate_major_statistics("Unknown Major")


def test_load_students_reads_csv_and_calculates_average(tmp_path):
    csv_file = tmp_path / "students.csv"