from pymongo import MongoClient
from datetime import datetime
import uuid
import bcrypt



mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["University_Portal"]

users_col = mongo_db["users"]
students_col = mongo_db["students"]
instructors_col = mongo_db["instructors"]
courses_col = mongo_db["courses"]
enrollments_col = mongo_db["enrollments"]
assignments_col = mongo_db["assignments"]
rooms_col = mongo_db["rooms"]




# Helpers fn
# ==============================

def generate_id(role):
    return f"{role}_{uuid.uuid4().hex}"


def validate_required_fields(data, required_fields):
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing field: {field}")



def has_time_conflict(student_id, new_course):
    enrolled_courses_ids = enrollments_col.find(
        {"student_id": student_id},
        {"course_id": 1, "_id": 0}
    )

    enrolled_ids = [e["course_id"] for e in enrolled_courses_ids]

    if not enrolled_ids:
        return False

    enrolled_courses = courses_col.find(
        {"course_id": {"$in": enrolled_ids}},
        {"schedule": 1}
    )

    for course in enrolled_courses:
        s1 = course["schedule"]["start_time"]
        e1 = course["schedule"]["end_time"]

        s2 = new_course["schedule"]["start_time"]
        e2 = new_course["schedule"]["end_time"]

        days1 = set(course["schedule"]["days"])
        days2 = set(new_course["schedule"]["days"])

        if days1 & days2:  # common day
            if s1 < e2 and s2 < e1:
                return True

    return False



# ==============================
# Creation Functions
# ==============================
# 
def create_user(userData):
    validate_required_fields(userData, ["user_id", "password", "role"])
    
    target_role = userData["role"]
    target_id = userData["user_id"] #     student_id or instructor_id

    if target_role == "student":
        entity = students_col.find_one({"student_id": target_id})
        if not entity:
            raise ValueError(f"No Student profile found with ID {target_id}. Create student first.")

    elif target_role == "instructor":
        entity = instructors_col.find_one({"instructor_id": target_id})
        if not entity:
            raise ValueError(f"No Instructor profile found with ID {target_id}. Create instructor first.")

    elif target_role == "dean":
        pass 

    else:
        raise ValueError("Invalid role")
    
    existing_user = users_col.find_one({"user_id": target_id})
    if existing_user:
        raise ValueError("User account already exists for this ID")

    password = bcrypt.hashpw(
        userData["password"].encode("utf-8"),
        bcrypt.gensalt()
    )

    user_doc = {
        "u_id": generate_id("user"),
        "user_id": target_id,     
        "password": password.decode("utf-8"),
        "role": target_role
    }
    users_col.insert_one(user_doc)
    
    return {
        "message": "User created successfully",
        "user_id": user_doc["user_id"]   
    }

def create_student(studentData):
    validate_required_fields(studentData, ["student_id", "full_name"])
    
    existing_student = students_col.find_one(
        {"student_id": studentData["student_id"]}
    )
    
    if existing_student:
        raise ValueError("Student with this student_id already exists")
    
    studentData["s_id"] = generate_id("student")
    result = students_col.insert_one(studentData)

    return {
        "message": "Student Created!",
        "s_id": studentData["s_id"]
    }

def create_instructor(instructorData):
    validate_required_fields(instructorData,["instructor_id", "full_name"])
    existing_instructor = instructors_col.find_one(
        {"instructor_id": instructorData["instructor_id"]}
    )
    if existing_instructor:
        raise ValueError("instructor with this instructor_id already exists")
    instructorData["i_id"] = generate_id("instructor")
    result=instructors_col.insert_one(instructorData)
    
    return {
        "message": "Instructor Created!",
        "i_id": instructorData["i_id"]
    }

def create_course(courseData):

    validate_required_fields(courseData,
                             ["course_id","course_name",
                               "section","schedule","room",
                              "instructor_name","registered_student_count"])
    existing_course = courses_col.find_one(
        {
            "course_id": courseData["course_id"],
            "section": courseData["section"]
        }
    )

    if existing_course:
        raise ValueError(
            f"Course {courseData['course_id']} section {courseData['section']} already exists"
        )

# 3. --- Time/Room Conflict Check ---
    available_rooms = get_available_rooms(courseData["schedule"])
    if courseData["room"] not in available_rooms:
        raise ValueError(f"Room {courseData['room']} is not available at this time!")

# 4. --- Instructor Conflict Check ---
    available_instructors = get_available_instructors(courseData["schedule"])
    if courseData["instructor_name"] not in available_instructors:
        raise ValueError(f"Instructor {courseData['instructor_name']} is busy at this time!")    

    courseData["c_id"] = generate_id("course")
    result=courses_col.insert_one(courseData)
    return {
        "message": "Course Created!",
        "mongo_id": str(result.inserted_id),
        "c_id": courseData["c_id"]
    }

def register_student(studentData,userData):
    student=None
    try:
        student=create_student(studentData)

        userData["user_id"] = studentData["student_id"]
        userData["role"] = "student"
        create_user(userData)

        return " student and user created successfully"
    # Rollback
    except Exception as e:
        if student:
            students_col.delete_one({"s_id":student["s_id"]})
        raise e

def register_instructor(instructorData,userData):
    instructor=None
    try:
        instructor=create_instructor(instructorData)
        userData["user_id"] = instructorData["instructor_id"]
        userData["role"] = "instructor"
        create_user(userData)
        return " instructor and user created successfully"
    # Rollback
    except Exception as e:
        if instructor:
            instructors_col.delete_one({"i_id":instructor["i_id"]})
        raise e

# ==============================
# Retrieval Functions
# ==============================

def get_course_details(courseID):
    course=courses_col.find_one({"course_id":courseID},{"_id": 0})
    if not course:
        raise ValueError(f"Course with ID '{courseID}' not found.")
    return course


def get_courses(courseIDs):
    if not courseIDs:
        return []
    course_pointer = courses_col.find({"course_id": {"$in": courseIDs}},{"_id": 0})


    return list(course_pointer)


def get_available_rooms(schedule):
    target_days = schedule["days"]
    target_start = schedule["start_time"]
    target_end = schedule["end_time"]

    cursor_rooms = rooms_col.find({}, {"room": 1, "_id": 0})
    all_rooms = [r["room"] for r in cursor_rooms]

    busy_cursor = courses_col.find(
        {
            "schedule.days": {
                "$all": target_days,
                "$size": len(target_days)
            }
        },
        {"room": 1, "schedule": 1, "_id": 0}
    )

    busy_rooms = []

    for doc in busy_cursor:
        existing_start = doc["schedule"]["start_time"]
        existing_end = doc["schedule"]["end_time"]
        if existing_start < target_end and target_start < existing_end:
            busy_rooms.append(doc["room"])

    available_rooms = []

    for room in all_rooms:
        if room not in busy_rooms:
            available_rooms.append(room)
    return available_rooms


def get_available_instructors(schedule):
    target_days = schedule["days"]
    target_start = schedule["start_time"]
    target_end = schedule["end_time"]

    cursor_instructors = instructors_col.find({}, {"full_name": 1, "_id": 0})
    # Create list of all available instructor names
    all_instructors = [i["full_name"] for i in cursor_instructors]
    
    busy_cursor = courses_col.find(
        {
            "schedule.days": {
                "$all": target_days,# Checks if course has ALL these days
                "$size": len(target_days)
            }
        },
        {"instructor_name": 1, "schedule": 1, "_id": 0}
    )

    busy_instructors = []

    for doc in busy_cursor:
        existing_start = doc["schedule"]["start_time"]
        existing_end = doc["schedule"]["end_time"]

        if existing_start < target_end and target_start < existing_end:
            busy_instructors.append(doc["instructor_name"])

    available = []

    for instructor in all_instructors:
        if instructor not in busy_instructors:
            available.append(instructor)

    return available


# ==============================
# Enrollment Functions
# ==============================

def enroll_in_course(studentID, courseID):
    student = students_col.find_one({"student_id": studentID})
    if not student:
        raise ValueError(f"Student with ID '{studentID}' not found.")
    
    course = courses_col.find_one({"course_id": courseID})
    if not course:
        raise ValueError(f"Course with ID '{courseID}' not found.")
    
    existing_enrollment = enrollments_col.find_one(
        {"student_id": studentID, "course_id": courseID}
    )
    if existing_enrollment:
        raise ValueError("Student is already enrolled in this course.")
    # -------------------------------------
    # check capacity:
    room = course.get("room")
    current_count = course.get("registered_student_count", 0)

    room_doc = rooms_col.find_one({"room": room})

    if room_doc:
        # Default to 20 if capacity is missing
        max_capacity = room_doc.get("capacity", 20)
        
        if current_count >= max_capacity:
            raise ValueError(f"Course is full! (Capacity: {max_capacity})")
    else:
        pass

    # --------------------------
    if has_time_conflict(studentID, course):
        raise ValueError("Schedule conflict with another enrolled course.")

    enrollmentData = {
        "e_id": generate_id("enrollment"),
        "student_id": studentID,
        "course_id": courseID,
        "grade": "00"
    }
    enrollments_col.insert_one(enrollmentData)

    courses_col.update_one( {"course_id": courseID}, {"$inc": {"registered_student_count": 1}} )
    return "Enrolled Successfully"


def get_available_courses_for_registration(enrolled_ids):
    if not enrolled_ids:
        cursor = courses_col.find(
            {},
            {"course_name": 1, "course_id": 1, "_id": 0}
        )
    else:
        cursor = courses_col.find(
            {"course_id": {"$nin": enrolled_ids}},
            {"course_name": 1, "course_id": 1, "_id": 0}
        )

    return list(cursor)



# ==============================
# Performance Functions
# ==============================
def get_student_performance(studentID):
    enrollments_cursor = enrollments_col.find({"student_id": studentID})
    
    student_report = []
    
    for enrollment in enrollments_cursor:
        c_id = enrollment["course_id"]
        grade = enrollment["grade"] 
        course_doc = courses_col.find_one({"course_id": c_id})
        course_name = course_doc["course_name"] if course_doc else "Unknown"
        
        performance_card={
            "course_id": c_id,
            "course_name": course_name,
            "total_grade": grade
        }
        student_report.append(performance_card)
    return student_report

def get_student_course_performance(studentID, courseID):
    enrollment = enrollments_col.find_one({"student_id": studentID, "course_id": courseID})
    if not enrollment:
        return {"error": "Student is not enrolled in this course."}

    grade = enrollment.get("grade", "Not Graded yet")

    course_doc = courses_col.find_one({"course_id": courseID})
    # --------------------------if the course is not found--------------------------
    course_name = course_doc.get("course_name", "Unknown") if course_doc else "Unknown"
    performance_card = {
        "course_id": courseID,
        "course_name": course_name,
        "total_grade": grade
    }

    return performance_card

# Run this once to add capacity to your rooms
# rooms_col.update_one({"room": "C101"}, {"$set": {"capacity": 20}})
# rooms_col.update_one({"room": "C102"}, {"$set": {"capacity": 20}})
# rooms_col.update_one({"room": "C103"}, {"$set": {"capacity": 20}})
# # Default for others
# rooms_col.update_many({"capacity": {"$exists": False}}, {"$set": {"capacity": 20}})


