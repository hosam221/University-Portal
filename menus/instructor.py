import time
import uuid
from services.academic_network_service import get_course_assignments, get_course_students, link_assignment_to_course
from services.auth_user_service import validate_session, refresh_user_session
from services.course_activity_service import cache_course_assignments, cache_enrolled_students, create_assignment, get_answer, get_cached_course_assignments, get_cached_enrolled_students, invalidate_course_details_cache, invalidate_instructor_course_assignments_cache, invalidate_pending_tasks_cache_for_course, invalidate_student_course_details_cache, invalidate_student_pending_task_cache, update_grades

def ensure_session(session):

    if not validate_session(session["sessionID"])["valid"]:
        print("⚠️ Session expired. Please login again.")
        time.sleep(2)
        return False
    return True

def is_session_valid(session) -> bool:
    return validate_session(session["sessionID"])["valid"]

def instructor_dashboard(courses_details, session, user_id):

    while True:
        if not ensure_session(session):
            break
        print("\n--- Instructor Dashboard ---")
        print("\n=== Courses Assigned to You ===")
        for i, course_details in enumerate(courses_details, start=1):
            print(
                f"{i}. {course_details['details']['course_name']} "
            )

        print(f"{len(courses_details) + 1}. Exit")
        choice = input("Enter your choice: ")
        if not ensure_session(session):
            break
        refresh_user_session(session["sessionID"])
        if not choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        choice = int(choice)
        if choice == (len(courses_details) + 1):
            break
        if choice < 1 or choice > len(courses_details):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            view_course_screen(courses_details[choice - 1], session, user_id)

            
def view_course_screen(course_details, session, user_id):

    print("\n=== Course Details ===")
    print(f"{course_details['details']['course_name']}")
    print("Time:")
    schedule = course_details["details"]["schedule"]
    print(
        f"Days: {', '.join(schedule['days'])} | "
        f"Time: {schedule['start_time']} - {schedule['end_time']}"
    )

    print(f"Room: {course_details['details']['room']}")
    print(f"Registered Students: {course_details['details']['registered_students_count']}")

    while True:
        if not is_session_valid(session):
            break
        print("\n1. Add Assignment")
        print("2. Insert Grades")
        print("3. View Enrolled Students")
        print("4. Exit")
        choice = input("Enter your choice: ")
        if not is_session_valid(session):
            break
        refresh_user_session(session["sessionID"])
        match choice:
            case "1":
                add_assignment_screen(session, course_details['course_id'],  user_id,)

            case "2":
                grade_assignment_screen(session, course_details['course_id'])

            case "3":
                pass

            case "4":
                break

            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)

def add_assignment_screen(session, course_id, user_id):
    assignment_title = input("Enter Assignment title: ")
    description = input("Enter Description: ")
    end_date = input("Enter deadline end date (YYYY-MM-DD): ")
    end_time = input("Enter deadline end time (HH:MM): ")
    max_grade = input("Enter assignment maximum grade: ")
    assignmentData = {
        "assignment_id": str(uuid.uuid4()),
        "title": assignment_title,
        "description": description,
        "deadline": f"{end_date} {end_time}",
        "max_grade": max_grade
    }
    input("Press any key to add assignment...")
    if not is_session_valid(session):
        return
    refresh_user_session(session["sessionID"])
    create_assignment(course_id, assignmentData)
    link_assignment_to_course(assignmentData["assignment_id"], course_id, assignmentData["title"])
    invalidate_instructor_course_assignments_cache(course_id)
    invalidate_course_details_cache(course_id)
    invalidate_pending_tasks_cache_for_course(course_id)

def grade_assignment_screen(session, course_id):
    course_assignments = get_cached_course_assignments(course_id)
    if not course_assignments:
        course_assignments = get_course_assignments(course_id)
        cache_course_assignments(course_id, course_assignments)
        print("from neo4j")
    else:
        print("from redis")

    assignments = course_assignments.get("assignments", [])

    if not assignments:
        print("No assignments found for this course.")
        input("Press any key to back...")
        return
    else:
        print("Assignments:")
        for i, s in enumerate(assignments, start=1):
            print(f"{i}. {s['assignmentTitle']}")

    print(f"{len(assignments) + 1}. Exit")

    while True:
        choice = input("Enter your choice: ")
        if not is_session_valid(session):
            return
        refresh_user_session(session["sessionID"])
        if not choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        choice = int(choice)
        if choice == (len(assignments) + 1):
            return
        if choice < 1 or choice > len(assignments):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            assignment = assignments[choice - 1]
            break

    enrolled_students = get_cached_enrolled_students(course_id)
    if not enrolled_students:
        enrolled_students = get_course_students(course_id)
        cache_enrolled_students(course_id, enrolled_students)
        print("from neo4j")
    else:
        print("from redis")

    students = enrolled_students.get("students", [])

    if not students:
        print("No students enrolled in this course.")
        input("Press any key to back...")
        return
    else:
        print("Students:")
        for i, s in enumerate(students, start=1):
            print(f"{i}. {s['studentName']}")

    print(f"{len(students) + 1}. Exit")

    while True:
        choice = input("Enter your choice: ")
        if not is_session_valid(session):
            return
        refresh_user_session(session["sessionID"])
        if not choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        choice = int(choice)
        if choice == (len(students) + 1):
            return
        if choice < 1 or choice > len(students):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            student = students[choice - 1]
            break
    student_name = student['studentName']
    assignment_title = assignment['assignmentTitle']
    student_id = student['studentID']
    assignment_id = assignment['assignmentID']
    student_assignment = get_answer(student_id, assignment_id)
    student_answer = student_assignment['answer']
    max_grade = student_assignment.get('maxGrade', "00")
    grade_str = student_assignment.get('grade', "Not graded yet")
    print("\n--- Student Assignment ---")
    print(f"Student Name : {student_name}")
    print(f"Assignment   : {assignment_title}")
    print(f"Answer       : {student_answer if student_answer else 'No answer submitted'}")
    print(f"Max Grade    : {max_grade}")
    print(f"Grade        : {grade_str}")
    print("-------------------------\n")
    while True:
        print("1. Input the grade")
        print("2. Exit")
        choice = input("Enter your choice: ")
        match choice:
            case "1":
                grade_input = input("Enter the grade for this assignment: ")
                input("Press any key to submit grade...")
                if not is_session_valid(session):
                    return
                refresh_user_session(session["sessionID"])
                update_grades(assignment_id, student_id, grade_input)
                invalidate_student_course_details_cache(student_id, course_id)
                return

            case "2":
                return
            
            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)
    
