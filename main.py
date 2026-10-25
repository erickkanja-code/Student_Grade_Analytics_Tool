"""Command-line interface for the Student Grade Analytics Tool."""

from analytics import (
    calculate_major_statistics,
    calculate_median,
    calculate_mode,
    generate_json_report,
    generate_rankings,
    generate_rankings_json,
    get_grade_distributions_per_course,
    show_averages,
)
from student_data import (
    Course,
    CourseAverages,
    Grade,
    GradeDistributions,
    MajorReport,
    REQUIRED_COLUMNS,
    RankingEntry,
    Student,
    StudentFileNotFoundError,
    StudentFilePermissionError,
    load_students,
    majors,
)


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