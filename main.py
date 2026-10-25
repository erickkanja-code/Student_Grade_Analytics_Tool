
import csv
import json
from dataclasses import dataclass
from collections import defaultdict, deque, Counter
from pathlib import Path
from exceptions import StudentFileNotFoundError, StudentFilePermissionError

@dataclass
class Student:
    name: str
    major: str
    course1: float
    course2: float
    course3: float
    average: float


@dataclass
class Course:
    total: float
    no_of_students: int

    def calculate_average(self):
        return self.total / self.no_of_students


def get_grade_distributions_per_course(course_results):
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



majors = defaultdict(list)

try:
    with open("test.csv", mode="r", encoding="utf-8") as file:
        rows = csv.DictReader(file)

        for row in rows:
            new_student = Student(
                name=row["name"],
                major=row["major"],
                course1=float(row["course1"]),
                course2=float(row["course2"]),
                course3=float(row["course3"]),
                average=float(row["average"])
            )

            majors[new_student.major].append(new_student)

except FileNotFoundError:
    raise StudentFileNotFoundError(
        "The student data file 'test.csv' was not found."
    )

except PermissionError:
    raise StudentFilePermissionError(
        "Permission denied when trying to read 'test.csv'."
    )


def calculate_major_statistics(major):
    course_1_results = deque()
    course_2_results = deque()
    course_3_results = deque()

    for student in majors[major]:
        course_1_results.append(student.course1)
        course_2_results.append(student.course2)
        course_3_results.append(student.course3)

    c1_sum = sum(int(result) for result in course_1_results)
    c2_sum = sum(int(result) for result in course_2_results)
    c3_sum = sum(int(result) for result in course_3_results)

    course_1 = Course(c1_sum, len(course_1_results))
    course_2 = Course(c2_sum, len(course_2_results))
    course_3 = Course(c3_sum, len(course_3_results))

    course_1_average = course_1.calculate_average()
    course_2_average = course_2.calculate_average()
    course_3_average = course_3.calculate_average()

    major_average = (
        course_1_average + course_2_average + course_3_average
    ) / 3

    return {
        "course_averages": {
            "course1": course_1_average,
            "course2": course_2_average,
            "course3": course_3_average
        },
        "overall_average": round(major_average, 2),
        "grade_distributions": {
            "course1": get_grade_distributions_per_course(course_1_results),
            "course2": get_grade_distributions_per_course(course_2_results),
            "course3": get_grade_distributions_per_course(course_3_results)
        }
    }


def show_averages():
    for major in majors:
        statistics = calculate_major_statistics(major)

        print(f"\n{major} course 1: {statistics['course_averages']['course1']}")
        print(f"{major} course 2: {statistics['course_averages']['course2']}")
        print(f"{major} course 3: {statistics['course_averages']['course3']}")
        print(f"{major}: {statistics['overall_average']}")


def generate_rankings(major):
    ranked_list = sorted(
        majors[major],
        key=lambda student: student.average,
        reverse=True
    )

    print("-------------------- Ranked Performance List --------------------")
    print("   Name  Course 1  Course 2  Course 3  Average")

    for index, student in enumerate(ranked_list, start=1):
        print(
            f"{index}. {student.name}  {student.course1}  "
            f"{student.course2}  {student.course3}  {student.average}"
        )


def generate_json_report():
    report = {}

    for major in majors:
        report[major] = calculate_major_statistics(major)

    report_path = Path("reports")
    report_path.mkdir(exist_ok=True)

    file_path = report_path / "grade_report.json"

    with open(file_path, mode="w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"JSON report saved to: {file_path}")


def generate_rankings_json(major):
    ranked_list = sorted(
        majors[major],
        key=lambda student: student.average,
        reverse=True
    )

    report = []

    for index, student in enumerate(ranked_list, start=1):
        report.append({
            "rank": index,
            "name": student.name,
            "major": student.major,
            "course1": student.course1,
            "course2": student.course2,
            "course3": student.course3,
            "average": student.average
        })

    report_path = Path("reports")
    report_path.mkdir(exist_ok=True)

    file_path = report_path / f"{major.replace(' ', '_')}_rankings.json"

    with open(file_path, mode="w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Rankings report saved to: {file_path}")



def show_menu():
    while True:
        print("\n===== Student Grade Analytics Tool =====")
        print("1. View course and major averages")
        print("2. Generate student rankings")
        print("3. View grade distributions")
        print("4. Generate JSON report")
        print("5. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            show_averages()

        elif choice == "2":
            major = input("Enter the major: ")

            if major in majors:
                generate_rankings(major)
                generate_rankings_json(major)
            else:
                print("Major not found.")

        elif choice == "3":
            major = input("Enter the major: ")

            if major in majors:
                students = majors[major]

                print("\nCourse 1 grade distribution:")
                print(get_grade_distributions_per_course(
                    [student.course1 for student in students]
                ))

                print("\nCourse 2 grade distribution:")
                print(get_grade_distributions_per_course(
                    [student.course2 for student in students]
                ))

                print("\nCourse 3 grade distribution:")
                print(get_grade_distributions_per_course(
                    [student.course3 for student in students]
                ))
            else:
                print("Major not found.")

        elif choice == "4":
            generate_json_report()

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1, 2, 3, 4, or 5.")


try:
    show_menu()

except StudentFileNotFoundError as error:
    print(f"Error: {error}")

except StudentFilePermissionError as error:
    print(f"Error: {error}")
