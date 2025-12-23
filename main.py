from menus.login import login_screen
from menus.student import student_dashboard
from menus.instructor import instructor_dashboard
from menus.dean import dean_dashboard
from services.academic_network_service import get_instructor_courses_ids
from services.auth_user_service import create_user_session
import time

from services.student_information_service import get_course_details, get_courses

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
                    courseIDs = get_instructor_courses_ids(current_user['userID'])
                    courses_details = get_courses(courseIDs)
                    instructor_dashboard(courses_details, session)

                case "dean":
                    dean_dashboard(session)

        case "2":
          break

        case _:
            print("❗Invalid choice, please try again.")
            time.sleep(1)


