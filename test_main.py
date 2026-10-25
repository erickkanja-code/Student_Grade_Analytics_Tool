"""Tests for the Student Grade Analytics Tool.

Run these tests from the project folder with:
    python -m pytest -v
"""

import json

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
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,80,90,70,80\n"
        "Brian,Computer Science,60,70,80,70\n",
        encoding="utf-8",
    )

    main.load_students(csv_file)

    assert len(main.majors["Computer Science"]) == 2
    assert main.majors["Computer Science"][0].name == "Amina"
    assert main.majors["Computer Science"][0].average == 80.0


def test_load_students_rejects_missing_required_columns(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1\n"
        "Amina,Computer Science,80\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing CSV columns"):
        main.load_students(csv_file)


def test_load_students_rejects_grade_outside_zero_to_one_hundred(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,105,90,70,88.33\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="between 0 and 100"):
        main.load_students(csv_file)


def test_load_students_rejects_non_numeric_grade(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,eighty,90,70,80\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be numeric"):
        main.load_students(csv_file)


def test_load_students_warns_and_uses_calculated_average(tmp_path, capsys):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,80,90,70,50\n",
        encoding="utf-8",
    )

    main.load_students(csv_file)

    captured = capsys.readouterr()

    assert "Warning" in captured.out
    assert main.majors["Computer Science"][0].average == 80.0


def test_load_students_missing_file_raises_custom_exception(tmp_path):
    missing_file = tmp_path / "does_not_exist.csv"

    with pytest.raises(main.StudentFileNotFoundError):
        main.load_students(missing_file)


def test_generate_rankings_json_saves_highest_average_first(
    tmp_path, monkeypatch
):
    add_sample_students()
    monkeypatch.chdir(tmp_path)

    main.generate_rankings_json("Computer Science")

    report_file = tmp_path / "reports" / "Computer_Science_rankings.json"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report[0]["name"] == "Amina"
    assert report[0]["rank"] == 1
    assert report[1]["name"] == "Brian"
    assert report[1]["rank"] == 2


def test_generate_json_report_saves_each_major(tmp_path, monkeypatch):
    add_sample_students()
    monkeypatch.chdir(tmp_path)

    main.generate_json_report()

    report_file = tmp_path / "reports" / "grade_report.json"
    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert "Computer Science" in report
    assert "Business" in report
    assert report["Computer Science"]["overall_average"] == 75.0


def test_show_grade_distributions_handles_unknown_major(
    monkeypatch, capsys
):
    add_sample_students()
    monkeypatch.setattr("builtins.input", lambda prompt: "Medicine")

    main.show_grade_distributions()

    captured = capsys.readouterr()

    assert "Major not found." in captured.out


def test_load_students_rejects_row_with_extra_values(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,80,90,70,80,extra\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="too many values"):
        main.load_students(csv_file)


def test_load_students_rejects_row_with_missing_values(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,80,90,70\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="too few values"):
        main.load_students(csv_file)


def test_load_students_rejects_duplicate_header_names(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,course3\n"
        "Amina,Computer Science,80,90,70,80\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate column names"):
        main.load_students(csv_file)


def test_load_students_rejects_empty_required_field(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        "Amina,Computer Science,80,,70,80\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="course2.*cannot be empty"):
        main.load_students(csv_file)


@pytest.mark.parametrize("invalid_grade", ["nan", "inf", "-inf"])
def test_load_students_rejects_nan_and_infinity(tmp_path, invalid_grade):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        f"Amina,Computer Science,{invalid_grade},90,70,80\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="finite numbers"):
        main.load_students(csv_file)


def test_load_students_rejects_malformed_csv_quoting(tmp_path):
    csv_file = tmp_path / "students.csv"
    csv_file.write_text(
        "name,major,course1,course2,course3,average\n"
        '"Amina,Computer Science,80,90,70,80',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CSV file is malformed"):
        main.load_students(csv_file)