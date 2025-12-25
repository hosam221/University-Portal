import time
from services.academic_network_service import create_instructor_node, create_student_node, link_instructor_to_course
from services.auth_user_service import validate_session, refresh_user_session
from services.course_activity_service import invalidate_available_courses_cache, invalidate_instructor_courses_cache
from services.student_information_service import create_course, get_available_instructors, get_available_rooms, register_instructor, register_student
import secrets
import string

def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def save_credentials(filename, user_id, full_name, password):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{user_id} | {full_name} | {password}\n")

def ensure_session(session):

    if not validate_session(session["sessionID"])["valid"]:
        print("⚠️ Session expired. Please login again.")
        time.sleep(2)
        return False
    return True

def is_session_valid(session) -> bool:
    return validate_session(session["sessionID"])["valid"]

def dean_dashboard(session):

    while True:
        if not ensure_session(session):
            break
        print("\n--- Dean Menu ---")
        print("1. Add Course")
        print("2. Create Student")
        print("3. Create Instructor")
        print("4. Student Stats")
        print("5. Exit")
        choice = input("Enter your choice: ")
        if not ensure_session(session):
            break
        refresh_user_session(session["sessionID"])
        match choice:
            case "1":
                add_course_screen(session)

            case "2":
                create_student_screen(session)

            case "3":
                create_instructor_screen(session)

            case "4":
                pass

            case "5":
                break

            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)

def add_course_screen(session):
    days = [] 
    while True:
        print("===Select the day(s):===")
        print("1. Sunday")
        print("2. Monday")
        print("3. Tuesday")
        print("4. Wednesday")
        print("5. Thursday")
        print("6. Done")
        print("7. Exit")
        choice = input("Enter your choice: ")
        match choice:
            case "1":
                days.append("Sunday")

            case "2":
                days.append("Monday")

            case "3":
                days.append("Tuesday")

            case "4":
                days.append("Wednesday")
                
            case "5":
                days.append("Thursday")

            case "6":
                break

            case "7":
                return

            case _:
                print("❗Invalid choice, please try again.")
                time.sleep(1)
    
    print("Time format: HH:M - e.g. 14:30")
    start_time  = input("Enter start time: ")
    end_time  = input("Enter end time: ")
    schedule = {
        "days": days,
        "start_time": start_time,
        "end_time": end_time
    }
    input("Press any key to Find Availability...")
    if not is_session_valid(session):
        return
    refresh_user_session(session["sessionID"])
    available_rooms = get_available_rooms(schedule)
    available_instructors = get_available_instructors(schedule)
    print(", ".join(days), f": {start_time} - {end_time}")
    if not available_rooms:
        print("❌ No rooms available at this time.")
        time.sleep(1)
        return
    
    while True:
        print("\n--- Available Rooms ---")
        print("-" * 35)

        for i, room in enumerate(available_rooms, start=1):
            print(f"{i:>2}. Room: {room['room']}")
            print(f"     👥 Capacity: {room['capacity']}")
            print("-" * 35)

        room_choice = input("Enter your choice: ")
        if not room_choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        room_index = int(room_choice)

        if room_index < 1 or room_index > len(available_rooms):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            selected_room = available_rooms[room_index - 1]['room']
            break

    if not available_instructors:
        print("❌ No instructors available at this time.")
        time.sleep(1)
        return
    
    while True:
        print("Instructors:")
        for i, instructor in enumerate(available_instructors, start=1):
            print(f"{i}.  - {instructor['full_name']}")

        instructor_choice = input("Enter your choice: ")
        if not instructor_choice.isdigit():
            print("❗ Invalid choice, please enter a number.")
            time.sleep(1)
            continue
        instructor_index = int(instructor_choice)

        if instructor_index < 1 or instructor_index > len(available_instructors):
            print("❗Invalid choice, please try again.")
            time.sleep(1)
        else:
            selected_instructor = available_instructors[instructor_index - 1]
            instructor_id = selected_instructor['instructor_id']
            break
    course_id = input("Enter course code (e.g. 8999): ").strip().upper()
    course_name = input("Insert Course Name: ")
    courseData = {
        "course_id": course_id,
        "details": {
            "course_name": course_name,
            "schedule": schedule,
            "room": selected_room,
            "instructor_name": selected_instructor['full_name'],
            "registered_students_count": 0
        }
    }
    input("Press any key to  Create Course...")
    if not is_session_valid(session):
        return
    refresh_user_session(session["sessionID"])
    result = create_course(courseData)
    if not result["success"]:
        print("⚠️", result["error"])
    else:
        print("✅", result["message"])
        link_instructor_to_course(selected_instructor['instructor_id'], course_id)
    invalidate_instructor_courses_cache(selected_instructor['instructor_id'])
    invalidate_available_courses_cache()


def create_student_screen(session):
    print("===Create Student===")
    full_name = input("Insert full name: ")
    student_id = input("Insert Student ID: ")
    password = generate_password()
    input("Press any key to  Create Student...")
    if not is_session_valid(session):
        return
    refresh_user_session(session["sessionID"])
    studentData = {
        "student_id": student_id,
        "full_name": full_name
    }
    userData = {
        "user_id": student_id,
        "password": password,
        "role": "student"
    }

    result = register_student(studentData, userData)
    create_student_node(student_id, full_name)
    if result["success"]:
        save_credentials(
            "students_credentials.txt",
            student_id,
            full_name,
            password
        )
        print("✅ Student created successfully")

def create_instructor_screen(session):
    print("===Create Instructor===")
    full_name = input("Insert full name: ")
    instructor_id = input("Insert instructor ID: ")
    password = generate_password()
    input("Press any key to  Create instructor...")
    if not is_session_valid(session):
        return
    refresh_user_session(session["sessionID"])
    instructorData = {
        "instructor_id": instructor_id,
        "full_name": full_name
    }
    userData = {
        "user_id": instructor_id,
        "password": password,
        "role": "instructor"
    }

    result = register_instructor(instructorData, userData)
    create_instructor_node(instructor_id)
    if result["success"]:
        save_credentials(
            "instructors_credentials.txt",
            instructor_id,
            full_name,
            password
        )
        print("✅ Instructor created successfully")
        