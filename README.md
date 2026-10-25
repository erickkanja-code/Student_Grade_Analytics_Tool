# Student Grade Analytics Tool

A Python application that reads student grades from a CSV file, calculates statistics, ranks students, and generates JSON reports.

The project demonstrates the use of Python dataclasses, advanced collections, type hints, file handling, and basic input validation.

## Features

- Read student records from a CSV file.
- Group students by major using `defaultdict`.
- Calculate course averages and overall major averages.
- Calculate medians and modes.
- Count grade distributions using `Counter`.
- Rank students by average grade and calculate percentile positions.
- Calculate rolling averages using `deque`.
- Generate JSON reports for course statistics and student rankings.
- Validate CSV headers, required fields, numeric grades, and grade ranges.
- Handle missing files and permission errors using custom exceptions.

## Requirements

- Python 3.11 or later
- No third-party packages are required to run the application.

The application uses Python's standard library, including `csv`, `json`, `pathlib`, `dataclasses`, `collections`, and `statistics`.

## Project Structure

```text
student-grade-analytics/
├── main.py
├── exceptions.py
├── test.csv
├── reports/
│   ├── grade_report.json
│   └── ...
├── tests/
│   └── test_main.py
└── README.md
```

The `reports/` directory is created automatically when a report is generated.&#x20;

## Setup

1. Install Python 3.11 or later.
2. Clone the repository or download the project files.
3. Open a terminal in the project directory.
4. Make sure `main.py`, `exceptions.py`, and `test.csv` are in the project directory.

Run the application:

```bash
python main.py
```

On Windows, if `python` does not work, try:

```bash
py main.py
```

## CSV Input Format

The application expects a CSV file named `test.csv` with these columns:

```csv
name,major,course1,course2,course3,average
Alice,Computer Science,85,90,88,87.67
Brian,Information Systems,72,78,80,76.67
Carol,Computer Science,92,95,91,92.67
David,Information Systems,65,70,68,67.67
```

Each row represents one student.

- `name`: Student's name.
- `major`: Student's academic major.
- `course1`, `course2`, `course3`: Numeric grades from 0 to 100.
- `average`: The supplied average, which is validated. The application calculates the average again from the three course grades for its analysis.

## Using the Application

When you run the program, a menu appears.

1. **View course and major averages:** Displays average grades, medians, and modes for each major.
2. **Generate student rankings:** Sorts students in a selected major by average grade and saves a ranking report.
3. **View grade distributions:** Counts grades within predefined score ranges for a selected major.
4. **Generate JSON report:** Saves statistics for every major.
5. **View rolling averages:** Calculates rolling averages for a selected course and major.
6. **Exit:** Closes the application.

## Example JSON Output

A grade report contains statistics grouped by major. A shortened example is shown below:

```json
{
    "Computer Science": {
        "course_averages": {
            "course1": 88.5,
            "course2": 92.5,
            "course3": 89.5
        },
        "overall_average": 90.17,
        "course_medians": {
            "course1": 88.5,
            "course2": 92.5,
            "course3": 89.5
        },
        "course_modes": {
            "course1": null,
            "course2": null,
            "course3": null
        },
        "grade_distributions": {
            "course1": {
                "81-100": 2
            },
            "course2": {
                "81-100": 2
            },
            "course3": {
                "81-100": 2
            }
        }
    }
}
```

The values above illustrate the report format; actual values depend on the contents of `test.csv`. A mode is `null` in JSON when no grade is repeated.

Reports are saved in the `reports/` directory:

- `reports/grade_report.json`
- `reports/<major>_rankings.json`

Spaces in a major's name are replaced with underscores when generating a ranking filename.

## Collections Used

| Collection          | Purpose                                                               |
| ------------------- | --------------------------------------------------------------------- |
| `defaultdict(list)` | Groups students by major without manually creating each list.         |
| `Counter`           | Counts grades in each grade range.                                    |
| `deque`             | Stores grades and maintains a fixed-size window for rolling averages. |
| `OrderedDict`       | Explicitly preserves the insertion order of majors in the report.     |

Regular dictionaries also preserve insertion order in modern Python, but `OrderedDict` is included to demonstrate the requested collection.

## Data Models and Type Hints

- `Student` and `Course` are dataclasses that organize related data.
- `TypedDict` describes the expected structure of the JSON report.
- `Grade` uses a union type to represent integer or decimal grades.
- Function annotations describe expected inputs and return values.

Type hints help developers and static analysis tools understand the code. They do not automatically validate input at runtime, so the CSV loader performs its own checks.

## Input Validation and Error Handling

The application checks that:

- Required CSV columns exist.
- Required fields are not blank.
- Grades and the supplied average are numeric.
- Grades are between 0 and 100.
- Grades are finite numbers rather than `NaN` or infinity.
- The CSV contains student records.

The program displays an error message when the input file is missing, cannot be read, or contains invalid data. A warning is printed if a supplied average differs from the average calculated from the three course grades.

## Performance and Memory Notes

The application stores all students in memory and groups them by major. This is convenient for repeated analysis, but memory use increases with the number of students.

- `Counter` provides convenient frequency counting.
- `defaultdict` simplifies grouping.
- `deque` supports efficient addition and removal at its ends and is useful for fixed-size rolling windows.
- Sorting student records for rankings takes approximately O(n log n) time for a major with n students.
- Calculating a median generally requires sorting the values, so it takes O(n log n) time for n grades.
- A rolling average in this implementation recalculates the sum of the current window each time. For a window of size w and n grades, this takes O(n × w) time. A running sum could improve this to O(n).

The current program loads all records into memory, so it is suitable for small and medium-sized datasets. Processing extremely large files could be improved by using generators or streaming records where the required calculations allow it.

## Testing

Tests can be written using `pytest`.

Install the testing tools:

```bash
python -m pip install pytest mypy
```

Run tests:

```bash
python -m pytest
```

Run static type checking:

```bash
python -m mypy main.py exceptions.py
```

These commands assume the tools are installed and the test files have been created. The project should include tests for calculations, rankings, grade boundaries, invalid CSV input, and JSON report generation.

## Limitations

- The input filename is currently fixed as `test.csv`.
- The application assumes three courses per student.
- Rolling averages follow the order in which student rows appear in the CSV; semester-specific trend analysis requires semester data.
- Percentiles are calculated from rank positions. Students with tied grades may receive different percentile positions because ties are not grouped.
- The program generates JSON reports but does not create graphical visualizations.
