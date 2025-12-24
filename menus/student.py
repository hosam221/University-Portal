import time
from services.academic_network_service import get_student_enrolled_course_ids, link_student_to_assignment, link_student_to_course
from services.auth_user_service import validate_session, refresh_user_session
from services.course_activity_service import cache_available_courses, cache_student_course_details, cache_student_courses, create_answer_document, get_cached_available_courses, get_cached_student_course_details, get_cached_student_courses, invalidate_enrolled_students_cache, invalidate_student_available_courses_cache, invalidate_student_course_details_cache, invalidate_student_courses_cache, invalidate_student_pending_task_cache
from services.student_information_service import enroll_in_course, get_available_courses_for_registration, get_course_details, get_courses

from pymongo import MongoClient
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["university_portal"]
rooms_col = mongo_db["rooms"]
students_col = mongo_db["students"]

def ensure_session(session):
    if not validate_session(session["sessionID"])["valid"]:
        print("⚠️ Session expired. Please login again.")
        time.sleep(2)
        return False
    return True

def is_session_valid(session) -> bool:
    return validate_session(session["sessionID"])["valid"]

def student_dashboard(session, user_id):

    while True:
        if not ensure_session(session):
            break
        print("\n--- Student Menu ---")
        print("1. Register for Course")
        print("2. My Courses")
        print("3. Pending Tasks")
        print("4. Exit")
        choice = input("Enter your choice: ")
        if not ensure_session(session):
            break
        refresh_user_session(session["sessionID"])
        match choice:
            case "1":
                register_course_screen(session, user_id)

            case "2":
                my_courses_screen(session, user_id)

            case "3":
                pass

            case "4":
                break

            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)

def register_course_screen(session, user_id):
    available_courses = get_cached_available_courses(user_id)
    if not available_courses:
        enrolled_ids = get_student_enrolled_course_ids(user_id)
        available_courses = get_available_courses_for_registration(enrolled_ids)
        cache_available_courses(user_id, available_courses)
        print("from mongo")
    else:
        print("from redis")
    print("\n--- Available Courses ---")
    while True:
        for idx, course in enumerate(available_courses, start=1):
            details = course.get("details", {})
            schedule = details.get("schedule", {})

            course_name = details.get("course_name", "Unknown Course")
            section = details.get("section", "X")
            instructor = details.get("instructor_name", "Unknown Instructor")
            room = details.get("room", "Unknown Room")
            registered = details.get("registered_students_count", 0)

            room_doc = rooms_col.find_one({"room": room})
            capacity = room_doc["capacity"] if room_doc and "capacity" in room_doc else "?"

            days = schedule.get("days", [])
            start = schedule.get("start_time", "")
            end = schedule.get("end_time", "")

            days_str = " & ".join(days) if days else "N/A"
            time_str = f"{days_str} {start}-{end}" if start and end else "N/A"

            print(f"{idx}. {course_name} Section {section}")
            print(f"   Instructor: {instructor}")
            print(f"   Time: {time_str}")
            print(f"   Room: {room}")
            print(f"   Registered Students: {registered}/{capacity}\n")
        print(f"{len(available_courses) + 1}. Exit")
        choice = input("Enter your choice: ")
        if not is_session_valid(session):
            return
        refresh_user_session(session["sessionID"])
        if not choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        choice = int(choice)
        if choice == (len(available_courses) + 1):
            return
        if choice < 1 or choice > len(available_courses):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            course_id = available_courses[choice - 1]['course_id']
            student_doc = students_col.find_one({"student_id": user_id}, {"_id": 0, "full_name": 1})
            full_name = student_doc["full_name"] if student_doc else "Unknown"
            enroll_in_course(user_id, course_id)
            link_student_to_course(user_id, full_name, course_id)
            invalidate_student_courses_cache(user_id)
            invalidate_student_available_courses_cache(user_id)
            invalidate_enrolled_students_cache(course_id)
            # log_student_event (studentID, courseID, addCourse, timestamp)
            break

def my_courses_screen(session, user_id):
    student_courses = get_cached_student_courses(user_id)
    if not student_courses :
        courseIDs = get_student_enrolled_course_ids(user_id)
        student_courses = get_courses(courseIDs)
        cache_student_courses(user_id, student_courses)
        print("from mongo")
    else:
        print("from redis")
    while True:
        print("\n--- My Courses ---")
        for i, course in enumerate(student_courses, start=1):
            details = course.get("details", {})
            course_name = details.get("course_name", "Unknown")
            section = details.get("section", "X")
            print(f"{i}. {course_name} - Section {section}")
        print(f"{len(student_courses) + 1}. Exit")
        choice = input("Enter your choice: ")
        if not is_session_valid(session):
            return
        refresh_user_session(session["sessionID"])
        if not choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        choice = int(choice)
        if choice == (len(student_courses) + 1):
            return
        if choice < 1 or choice > len(student_courses):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            course_id = student_courses[choice - 1]['course_id']
            student_course_details = get_cached_student_course_details(user_id, course_id)
            # log_student_event (studentID, courseID, VisitCourse, timestamp)
            if not student_course_details:
                student_course_details = get_course_details(course_id, user_id)
                cache_student_course_details(user_id, course_id, student_course_details)
                print("From mongo")
            else:
                print("From redis")
            break
    print("\n--- Course Details ---")

    if not student_course_details or "course" not in student_course_details:
        print("❗ No course details found.")
        return

    course = student_course_details.get("course", {})
    details = course.get("details", {})
    schedule = details.get("schedule", {})

    course_name = details.get("course_name", "Unknown Course")
    section = details.get("section", "X")
    instructor = details.get("instructor_name", "Unknown Instructor")

    days = schedule.get("days", [])
    start = schedule.get("start_time", "")
    end = schedule.get("end_time", "")
    days_str = " & ".join(days) if days else "N/A"
    time_str = f"{days_str} {start}-{end}" if start and end else "N/A"

    room = details.get("room", "Unknown Room")
    if isinstance(room, dict):  # in case old data stored room as dict
        room = room.get("room", "Unknown Room")

    print("\n" + "=" * 55)
    print(f"📘 {course_name}  |  Section {section}")
    print(f"👨‍🏫 Instructor: {instructor}")
    print(f"⏰ Time       : {time_str}")
    print(f"🏫 Room       : {room}")
    print("=" * 55)

    while True:
        print("1. Pending Tasks")
        print("2. Completed Tasks")
        print("3. Exit")
        choice = input("Enter your choice: ")
        if not is_session_valid(session):
            return
        refresh_user_session(session["sessionID"])

        match choice:
            case "1":
                pending = student_course_details.get("pending_tasks", []) or []
                pending_tasks(session, user_id, pending, course_id)

            case "2":
                completed = student_course_details.get("completed_tasks", []) or []
                print("\n✅ Completed Tasks")
                print("-" * 55)
                if not completed:
                    print("❗ No completed tasks yet.")
                else:
                    for i, t in enumerate(completed, start=1):
                        title = t.get("title", "Untitled")
                        desc = t.get("description", "")
                        max_grade = t.get("max_grade", "?")
                        grade = t.get("grade", None)
                        answer = t.get("answer", '')

                        grade_str = "Not graded yet" if grade is None else f"{grade}/{max_grade}"

                        print(f"{i}. {title}")
                        if desc:
                            print(f"   Description: {desc}")
                        print(f"   Grade      : {grade_str}")
                        print(f"   Answer     : {answer}")
                        print("-" * 55)


            case "3":
                return

            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)



def pending_tasks(session, user_id, pending, course_id):
    print("\n🕒 Pending Tasks")
    print("-" * 55)
    
    if not pending:
        print("✅ No pending tasks.")
        return
    
    for i, t in enumerate(pending, start=1):
        title = t.get("title", "Untitled")
        description = t.get("description", "No description provided.")
        deadline = t.get("deadline", "N/A")
        max_grade = t.get("max_grade", "?")
        notes = t.get("notes", "")  # أي ملاحظات إضافية
        
        print(f"{i}. {title}")
        print(f"   Description : {description}")
        print(f"   Deadline    : {deadline}")
        print(f"   Max Grade   : {max_grade}")
        print("-" * 55)
    print(f"{len(pending) + 1}. Exit")
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
        if choice == (len(pending) + 1):
            return
        if choice < 1 or choice > len(pending):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            assignment = pending[choice - 1]
            assignment_id = assignment['assignment_id']
            print(f"Title : {assignment['title']}")
            print(f"   Description : {assignment['description']}")
            print(f"   Deadline    : {assignment['deadline']}")
            print(f"   Max Grade   : {assignment['max_grade']}")
            print("-" * 55)
            answer_text = input("Enter your answer: ")
            if not is_session_valid(session):
                return
            refresh_user_session(session["sessionID"])

            answerData = {
                "student_id": user_id,
                "text": answer_text
            }

            result = create_answer_document(user_id, assignment_id, answerData)

            if result.get("success"):
                print("✅ Your answer has been submitted successfully!")
                student_doc = students_col.find_one({"student_id": user_id}, {"_id": 0, "full_name": 1})
                full_name = student_doc["full_name"] if student_doc else "Unknown"
                link_student_to_assignment(user_id, full_name, assignment_id)
                # log_student_event(studentID, courseID, assignmentID, submit assignment, timestamp)
                invalidate_student_pending_task_cache(user_id)
                invalidate_student_course_details_cache(user_id, course_id)
                pending = [t for t in pending if t['assignment_id'] != assignment_id]
                return
            else:
                print(f"❌ Failed to submit answer: {result.get('error')}")
            break


        
