from pathlib import Path
import csv
from dataclasses import dataclass
from collections import defaultdict, deque, Counter

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
    
def get_grade_distributions_per_course(course_1_results):
    grade_distribution = Counter("0-40" if 0 <= int(grade) <=40 
                                 else "41-50" if int(grade) <= 50 
                                 else "51-60" if int(grade) <= 60
                                 else "61-70" if int(grade) <= 70
                                 else "71-80" if int(grade) <= 80
                                 else "80-100"
                                 for grade in course_1_results)
    print(grade_distribution)

def generate_rankings(major):
    ranked_list = sorted(majors[major], key=lambda student: student.average, reverse=True)
    print(f"--------------------Ranked performance List--------------------")
    for student in ranked_list:
        print("   Name  Course 1  Course 2  Course 3  Average")
        print(f"{ranked_list.index(student)}. {student.name}  {student.course1}  {student.course2}  {student.course3}  {student.average}")
    
    
      
majors = defaultdict(list)

with open("test.csv", mode='r') as file:
    rows = csv.DictReader(file)
    for row in rows:
        new_student = Student(name=row['name'], major=row['major'], course1=row['course1'], course2=row['course2'], course3=row['course3'], average=row['average'])
        majors[new_student.major].append(new_student)

for major in majors:
    course_1_results = deque()
    course_2_results = deque()
    course_3_results = deque()
    
    get_grade_distributions_per_course(course_1_results)
    for student in majors[major]:
        course_1_results.append(student.course1)
        course_2_results.append(student.course2)
        course_3_results.append(student.course3)

    c1_sum = 0
    c2_sum = 0
    c3_sum = 0
    
    for result in course_1_results:
        c1_sum += int(result)
        
    for result in course_2_results:
        c2_sum += int(result)
        
    for result in course_3_results:
        c3_sum += int(result)
        
    course_1 = Course(total=c1_sum, no_of_students=len(course_1_results))
    course_2 = Course(total=c2_sum, no_of_students=len(course_2_results))
    course_3 = Course(total=c3_sum, no_of_students=len(course_3_results))

    course_1_average = course_1.calculate_average()
    course_2_average = course_2.calculate_average()
    course_3_average = course_3.calculate_average()
    
    major_average = (course_1_average + course_2_average + course_3_average) / 3
    
    # print(f"{major} course 1: {course_1_average}")
    # print(f"{major} course 2: {course_2_average}")
    # print(f"{major} course 3: {course_3_average}")
 
    # print(f"{major}: {round(major_average,2)}")

    

generate_rankings("Software Engineering")     
             
    

