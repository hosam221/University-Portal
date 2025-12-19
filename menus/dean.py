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
                pass

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
