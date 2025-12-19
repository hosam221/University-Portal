from services.auth_user_service import authenticate_user
import time

def login_screen():
    while True:
        user_id = input("Insert UserID: ")
        password = input("Insert password: ")
        result = authenticate_user(user_id, password)
        if result['success'] == False:
            print("⚠️ Login failed. Please check your user ID and password.")
            time.sleep(1)
        else:
            return result
# def login_screen():
#     while True:
#         user_id = input("Insert UserID: ")
#         password = input("Insert password: ")
#         result = authenticate_user(user_id, password)
#         if result['success'] == False:
#             print("Something Wrong!")
#         else:
#             match result['role']:
#                 case "student":
#                     print("Hello Student")
#                     session = create_user_session(result['userID'], result['role'])
#                     input("press any key to continue")
#                     session_data = validate_session(session["sessionID"])
#                     if(session_data["valid"] == True):
#                         print("Welcome to next page")
#                         break
#                     else:
#                         print("Your Session has been done!")


#                 case "instructor":
#                     print("Hello instructor")

#                 case "dean":
#                     print("Hello dean")