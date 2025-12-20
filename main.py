from menus.login import login_screen
from menus.student import student_dashboard
from menus.instructor import instructor_dashboard
from menus.dean import dean_dashboard
from services.auth_user_service import create_user_session
import time

courses_details = [
    {
        "course_id": "CS101",
        "course_name": "Introduction to Programming",
        "section": "A",
        "schedule": "Sun & Tue 9:00 - 10:30",
        "room": "Lab 1",
        "instructor_name": "Dr. Ahmed Ali",
        "registered_students_count": 25
    },
    {
        "course_id": "CS202",
        "course_name": "Data Structures",
        "section": "B",
        "schedule": "Mon & Wed 11:00 - 12:30",
        "room": "Room 204",
        "instructor_name": "Dr. Sara Hassan",
        "registered_students_count": 30
    },
    {
        "course_id": "CS303",
        "course_name": "Database Systems",
        "section": "A",
        "schedule": "Thu 1:00 - 3:00",
        "room": "Room 310",
        "instructor_name": "Dr. Omar Khaled",
        "registered_students_count": 20
    }
]

while True :
    print("1. login")
    print("2: Exit")
    choice = input("Enter your choice: ")
    match choice:
        case "1":
            current_user  = login_screen()
            session = create_user_session(current_user['userID'], current_user['role'])
            match current_user['role']:
                case "student":
                    # log_student_login(studentID,loginevent)
                    # update_weekly_login_count(studentID)
                    student_dashboard(session)

                case "instructor":
                    # courseIDs = get_instructor_courses_ids(current_user['userID'])
                    # courses_details = get_courses_details(courseIDs)
                    instructor_dashboard(courses_details, session)

                case "dean":
                    dean_dashboard(session)

        case "2":
          break

        case _:
            print("❗Invalid choice, please try again.")
            time.sleep(1)


