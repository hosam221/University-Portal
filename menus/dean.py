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
                pass

            case "3":
                pass

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
    start_time  = input("Enter start time and end time: ")
    end_time  = input("Enter start time and end time: ")
    input("Press any key to Find Availability...")
    if not is_session_valid(session):
        return
    refresh_user_session(session["sessionID"])
    # available_rooms = get_available_rooms(time, days)
    # available_instructors = get_available_instructors(time, days)
    print(", ".join(days), f": {start_time} - {end_time}")
    available_rooms = ["bbb", "ccc"]
    available_instructors = ["a", 'b']
    print("Rooms:")
    for i, room in enumerate(available_rooms, start=1):
        print(f"{i}.  - {room}")

    print("Instructors:")
    for i, instructor in enumerate(available_instructors, start=1):
        print(f"{i}.  - {instructor}")

    # course_name = input("Insert Course Name: ")
    # section = input("Insert Course Section: ")