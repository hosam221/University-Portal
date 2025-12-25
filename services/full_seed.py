import random
import uuid
import secrets
import string
import time


# =========================
# SEED MODE
# =========================
SEED_MODE = True   # False في الإنتاج


# =========================
# PASSWORD
# =========================
def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))


# =========================
# SAVE CREDENTIALS
# =========================
def save_credentials(filename, user_id, full_name, password):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{user_id} | {full_name} | {password}\n")


# =========================
# IMPORTS
# =========================
from services.student_information_service import (
    rooms_col,
    register_student,
    register_instructor,
    create_course,
    enroll_in_course,
    has_time_conflict
)

from services.academic_network_service import (
    create_student_node,
    create_instructor_node,
    create_course_node,
    create_assignment_node,
    link_student_to_course,
    link_instructor_to_course
)

from services.course_activity_service import create_assignment


# =========================
# CONFIG
# =========================
STUDENTS_COUNT = 300
INSTRUCTORS_COUNT = 20
COURSES_PER_INSTRUCTOR = 2
ASSIGNMENTS_PER_COURSE = 3
COURSES_PER_STUDENT = 4

STUDENT_ID_START = 220000
INSTRUCTOR_ID_PREFIX = "II"

STUDENTS_FILE = "students_credentials.txt"
INSTRUCTORS_FILE = "instructors_credentials.txt"


# =========================
# ROOMS
# =========================
def seed_rooms():
    print("🏫 Creating rooms...")
    start = time.perf_counter()

    rooms_col.delete_many({})
    rooms = [
        {"room": f"R{i:03}", "capacity": random.randint(80, 200)}
        for i in range(1, 21)
    ]
    rooms_col.insert_many(rooms)

    print(f"🏫 Rooms: {len(rooms)} created in {time.perf_counter() - start:.2f}s")
    return rooms


# =========================
# INSTRUCTORS
# =========================
def seed_instructors():
    print("👨‍🏫 Creating instructors...")
    instructors = []

    open(INSTRUCTORS_FILE, "w", encoding="utf-8").close()

    start = time.perf_counter()

    for i in range(INSTRUCTORS_COUNT):
        instructor_id = f"{INSTRUCTOR_ID_PREFIX}{i:04}"
        full_name = f"Instructor {i + 1}"
        password = generate_password()

        register_instructor(
            {"instructor_id": instructor_id, "full_name": full_name},
            {"user_id": instructor_id, "password": password, "role": "instructor"}
        )

        create_instructor_node(instructor_id)

        save_credentials(INSTRUCTORS_FILE, instructor_id, full_name, password)

        instructors.append({
            "id": instructor_id,
            "name": full_name
        })

    print(f"✅ Instructors done in {time.perf_counter() - start:.2f}s")
    return instructors


# =========================
# COURSES & ASSIGNMENTS
# =========================
def seed_courses_and_assignments(instructors, rooms):
    print("📘 Creating courses & assignments...")
    start = time.perf_counter()

    courses = []
    schedules = [
        {"days": ["Sunday", "Tuesday"], "start_time": "09:00", "end_time": "11:00"},
        {"days": ["Sunday", "Tuesday"], "start_time": "11:00", "end_time": "13:00"},
        {"days": ["Monday", "Wednesday"], "start_time": "09:00", "end_time": "11:00"},
        {"days": ["Monday", "Wednesday"], "start_time": "11:00", "end_time": "13:00"},
    ]

    room_index = 0
    course_counter = 1

    for instructor in instructors:
        for _ in range(COURSES_PER_INSTRUCTOR):
            course_id = f"C{course_counter:04}"
            course_counter += 1

            courseData = {
                "course_id": course_id,
                "details": {
                    "course_name": f"Course {course_id}",
                    "schedule": schedules[len(courses) % len(schedules)],
                    "room": rooms[room_index % len(rooms)]["room"],
                    "instructor_name": instructor["name"],
                    "registered_students_count": 0
                }
            }
            room_index += 1

            result = create_course(courseData)
            if not result["success"]:
                continue

            # Mongo + Neo4j
            create_course_node(course_id)
            link_instructor_to_course(instructor["id"], course_id)

            courses.append(course_id)

            for a in range(ASSIGNMENTS_PER_COURSE):
                assignment_id = str(uuid.uuid4())
                title = f"Assignment {a + 1}"

                create_assignment(course_id, {
                    "assignment_id": assignment_id,
                    "title": title,
                    "description": "Seeded assignment",
                    "deadline": "2025-12-31 23:59",
                    "max_grade": 100
                })

                create_assignment_node(assignment_id, title)

    print(f"📘 Courses & assignments in {time.perf_counter() - start:.2f}s")
    return courses


# =========================
# STUDENTS & ENROLLMENTS
# =========================
def seed_students_and_enrollments(courses):
    print("👨‍🎓 Creating students & enrollments...")
    open(STUDENTS_FILE, "w", encoding="utf-8").close()

    start = time.perf_counter()

    for i in range(STUDENTS_COUNT):
        student_id = str(STUDENT_ID_START + i)
        full_name = f"Student {i + 1}"
        password = generate_password()

        register_student(
            {"student_id": student_id, "full_name": full_name},
            {"user_id": student_id, "password": password, "role": "student"}
        )

        create_student_node(student_id, full_name)

        selected_courses = random.sample(courses, COURSES_PER_STUDENT)
        for cid in selected_courses:
            result = enroll_in_course(student_id, cid)
            if result["success"]:
                link_student_to_course(student_id, full_name, cid)

        save_credentials(STUDENTS_FILE, student_id, full_name, password)

        if (i + 1) % 500 == 0:
            print(f"  ↳ {i + 1} students processed")

    print(f"✅ Students done in {time.perf_counter() - start:.2f}s")


# =========================
# MASTER
# =========================
def run_full_seed():
    print("\n🚀 STARTING FULL SEED\n")

    rooms = seed_rooms()
    instructors = seed_instructors()
    courses = seed_courses_and_assignments(instructors, rooms)
    seed_students_and_enrollments(courses)

    print("\n📄 Credentials generated:")
    print(f" - {INSTRUCTORS_FILE}")
    print(f" - {STUDENTS_FILE}")

    print("\n🎉 FULL SEED COMPLETED SUCCESSFULLY\n")
