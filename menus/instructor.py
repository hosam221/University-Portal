import time
from services.auth_user_service import validate_session, refresh_user_session

def ensure_session(session):

    if not validate_session(session["sessionID"])["valid"]:
        print("⚠️ Session expired. Please login again.")
        time.sleep(2)
        return False
    return True

def is_session_valid(session) -> bool:
    return validate_session(session["sessionID"])["valid"]

def instructor_dashboard(courses_details, session):

    while True:
        if not ensure_session(session):
            break
        print("\n--- Instructor Dashboard ---")
        print("\n=== Courses Assigned to You ===")
        for i, course_details in enumerate(courses_details, start=1):
            print(f"{i}. {course_details['course_name']} - Section {course_details['section']}")

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
            add_course_screen(courses_details[choice - 1], session)

            
def add_course_screen(course_details, session):

    print("\n=== Course Details ===")
    print(f"{course_details['course_name']} - Section {course_details['section']}")
    print("Time:")
    print(f"    {course_details['schedule']}")
    print(f"Room: {course_details['room']}")
    print(f"Registered Students: {course_details['registered_students_count']}")

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
                pass

            case "2":
                pass

            case "3":
                pass

            case "4":
                break

            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)