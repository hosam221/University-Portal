import random
import uuid
from datetime import datetime, timedelta

from services.student_information_service import (
    register_student,
    register_instructor,
    create_course,
    get_available_rooms
)

from services.academic_network_service import (
    create_student_node,
    create_instructor_node,
    link_instructor_to_course,
    link_assignment_to_course
)

from services.course_activity_service import create_assignment


def seed_big_data(
    students_count=25000,
    instructors_count=150,
    min_courses_per_instructor=1,
    max_courses_per_instructor=5,
    max_assignments_per_course=5,
    default_password="1234"
):
    print("🚀 Seeding started...")

    # =========================
    # INSTRUCTORS
    # =========================
    instructors = []

    for i in range(instructors_count):
        instructor_id = f"INS{i+1:04}"
        full_name = f"Instructor {i+1}"

        instructorData = {
            "instructor_id": instructor_id,
            "full_name": full_name
        }

        userData = {
            "user_id": instructor_id,
            "password": default_password,
            "role": "instructor"
        }

        register_instructor(instructorData, userData)
        create_instructor_node(instructor_id)

        instructors.append({
            "instructor_id": instructor_id,
            "full_name": full_name
        })

    print(f"✅ {len(instructors)} instructors created")

    # =========================
    # STUDENTS
    # =========================
    for i in range(students_count):
        student_id = f"STD{i+1:06}"
        full_name = f"Student {i+1}"

        studentData = {
            "student_id": student_id,
            "full_name": full_name
        }

        userData = {
            "user_id": student_id,
            "password": default_password,
            "role": "student"
        }

        register_student(studentData, userData)
        create_student_node(student_id, full_name)

        if (i + 1) % 1000 == 0:
            print(f"👤 {i+1} students created")

    print(f"✅ {students_count} students created")

    # =========================
    # COURSES + ASSIGNMENTS
    # =========================
    course_counter = 1

    for instructor in instructors:
        courses_count = random.randint(
            min_courses_per_instructor,
            max_courses_per_instructor
        )

        for _ in range(courses_count):
            course_id = f"C{course_counter:05}"
            course_counter += 1

            schedule = {
                "days": random.sample(
                    ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
                    random.randint(1, 3)
                ),
                "start_time": "10:00",
                "end_time": "12:00"
            }

            rooms = get_available_rooms(schedule)
            if not rooms:
                continue

            room = rooms[0]["room"]

            courseData = {
                "course_id": course_id,
                "details": {
                    "course_name": f"Course {course_id}",
                    "schedule": schedule,
                    "room": room,
                    "instructor_name": instructor["full_name"],
                    "registered_students_count": 0
                }
            }

            create_course(courseData)
            link_instructor_to_course(instructor["instructor_id"], course_id)

            # =========================
            # ASSIGNMENTS
            # =========================
            for a in range(random.randint(0, max_assignments_per_course)):
                assignmentData = {
                    "assignment_id": str(uuid.uuid4()),
                    "title": f"Assignment {a+1}",
                    "description": "Auto generated assignment",
                    "deadline": (
                        datetime.now() +
                        timedelta(days=random.randint(7, 45))
                    ).strftime("%Y-%m-%d %H:%M"),
                    "max_grade": 100
                }

                create_assignment(course_id, assignmentData)
                link_assignment_to_course(
                    assignmentData["assignment_id"],
                    course_id,
                    assignmentData["title"]
                )

    print("🎉 SEEDING COMPLETED SUCCESSFULLY")
