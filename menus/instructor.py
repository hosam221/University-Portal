import time
import uuid
from services.academic_network_service import link_assignment_to_course
from services.auth_user_service import validate_session, refresh_user_session
from services.course_activity_service import create_assignment, invalidate_course_details_cache, invalidate_instructor_course_assignments_cache

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
                pass

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
    link_assignment_to_course(assignmentData["assignment_id"], course_id, )
    invalidate_instructor_course_assignments_cache(user_id)
    invalidate_course_details_cache(course_id)