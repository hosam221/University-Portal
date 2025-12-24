from pymongo import MongoClient
from datetime import datetime
import uuid
import bcrypt



mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["university_portal"]

users_col = mongo_db["users"]
students_col = mongo_db["students"]
instructors_col = mongo_db["instructors"]
courses_col = mongo_db["courses"]
enrollments_col = mongo_db["enrollments"]
assignments_col = mongo_db["assignments"]
rooms_col = mongo_db["rooms"]

courses_col.create_index(
    [("course_id", 1), ("details.section", 1)],
    unique=True
)



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
        {"details.schedule": 1}
    )

    for course in enrolled_courses:
        s1 = course["details"]["schedule"]["start_time"]
        e1 = course["details"]["schedule"]["end_time"]

        s2 = new_course["details"]["schedule"]["start_time"]
        e2 = new_course["details"]["schedule"]["end_time"]

        days1 = set(course["details"]["schedule"]["days"])
        days2 = set(new_course["details"]["schedule"]["days"])

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

    validate_required_fields(courseData["details"], [
    "course_name",
    "section",
    "schedule",
    "room",
    "instructor_name",
    "registered_students_count"
])

    existing_course = courses_col.find_one(
        {
            "course_id": courseData["course_id"],
            "details.section": courseData["details"]["section"]
        }
    )

    if existing_course:
        raise ValueError(
            f"Course {courseData['course_id']} section {courseData['details']['section']} already exists"
        )

# 3. --- Time/Room Conflict Check ---
    schedule = courseData["details"]["schedule"]
    room = courseData["details"]["room"]

    available_rooms = [r["room"] for r in get_available_rooms(schedule)]
    if room not in available_rooms:
        raise ValueError(f"Room {courseData['details']['room']} is not available at this time!")

# 4. --- Instructor Conflict Check ---
    instructor = courseData["details"]["instructor_name"]

    available_instructors = get_available_instructors(schedule)
    available_names = [
    i["full_name"] for i in available_instructors
    ]
    if instructor not in available_names:
        raise ValueError(f"Instructor {courseData['details']['instructor_name']} is busy at this time!")    

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

def get_course_details(courseID: str, studentID: str) -> dict:
    course = courses_col.find_one(
        {"course_id": courseID},
        {"_id": 0}
    )

    if not course:
        return {"error": "Course not found"}

    assignments = list(assignments_col.find(
        {"course_id": courseID},
        {"_id": 0}
    ))

    completed_tasks = []
    pending_tasks = []
    for a in assignments:
        submitted_students = {
            ans["student_id"] for ans in a.get("answer_text", [])
        }
        student_answer_text = None
        for ans in a.get("answer_text", []):
            if ans["student_id"] == studentID:
                student_answer_text = ans.get("text")
                break
        task_info = {
            "assignment_id": a.get("assignment_id"),
            "title": a.get("title"),
            "description": a.get("description"),
            "deadline": a.get("deadline"),
            "max_grade": a.get("max_grade")
        }

        if studentID in submitted_students:
            grade = None
            for g in a.get("grades", []):
                if g["student_id"] == studentID:
                    grade = g.get("grade")
                    break

            completed_tasks.append({
                **task_info,
                "grade": grade,
                "answer": student_answer_text
            })
        else:
            pending_tasks.append(task_info)

    return {
        "course": course,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks
    }




def get_courses(courseIDs):
    if not courseIDs:
        return []
    course_pointer = courses_col.find({"course_id": {"$in": courseIDs}},{"_id": 0})


    return list(course_pointer)

def get_available_rooms(schedule):
    target_days = schedule["days"]
    target_start = schedule["start_time"]
    target_end = schedule["end_time"]

    all_rooms = list(rooms_col.find({}, {"_id": 0}))

    busy_cursor = courses_col.find(
    {
        "details.schedule.days": {
            "$all": target_days,
            "$size": len(target_days)
        }
    },
    {"details.room": 1, "details.schedule": 1, "_id": 0}
)




    busy_rooms = []

    for doc in busy_cursor:
        existing_start = doc["details"]["schedule"]["start_time"]
        existing_end = doc["details"]["schedule"]["end_time"]
        if existing_start < target_end and target_start < existing_end:
            busy_rooms.append(doc["details"]["room"])

    available_rooms = []

    for room_doc in all_rooms:
        if room_doc["room"] not in busy_rooms:
            available_rooms.append(room_doc)

    return available_rooms


def get_available_instructors(schedule):
    target_days = schedule["days"]
    target_start = schedule["start_time"]
    target_end = schedule["end_time"]

    cursor_instructors = instructors_col.find({}, {"instructor_id": 1, "full_name": 1, "_id": 0})
    # Create list of all available instructor names
    all_instructors = [
    {
        "instructor_id": i["instructor_id"],
        "full_name": i["full_name"]
    }
    for i in cursor_instructors
]
    
    busy_cursor = courses_col.find(
        {
            "details.schedule.days": {
                "$all": target_days,# Checks if course has ALL these days
                "$size": len(target_days)
            }
        },
        {"details.instructor_name": 1, "details.schedule": 1, "_id": 0}
    )

    busy_instructors = []

    for doc in busy_cursor:
        existing_start = doc["details"]["schedule"]["start_time"]
        existing_end = doc["details"]["schedule"]["end_time"]

        if existing_start < target_end and target_start < existing_end:
            busy_instructors.append(doc["details"]["instructor_name"])

    available = []

    for instructor in all_instructors:
        if instructor["full_name"] not in busy_instructors:
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
    room = course["details"]["room"]
    current_count = course["details"]["registered_students_count"]


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

    courses_col.update_one( {"course_id": courseID}, {"$inc": {"details.registered_students_count": 1}} )
    return "Enrolled Successfully"


def get_available_courses_for_registration(enrolled_ids):
    if not enrolled_ids:
        cursor = courses_col.find(
            {},
            {"_id": 0}
        )
    else:
        cursor = courses_col.find(
            {"course_id": {"$nin": enrolled_ids}},
            {"_id": 0}
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
        course_name = course_doc["details"]["course_name"] if course_doc else "Unknown"
        
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
    course_name = course_doc["details"].get("course_name", "Unknown") if course_doc else "Unknown"
    performance_card = {
        "course_id": courseID,
        "course_name": course_name,
        "total_grade": grade
    }

    return performance_card
# print(get_available_rooms({
#     "days": ["Monday"],
#     "start_time": "10:00",
#     "end_time": "11:00"
# }))

# rooms_col.insert_many([
#     {"room": "C101", "capacity": 20},
#     {"room": "C102", "capacity": 20},
#     {"room": "C103", "capacity": 20}
# ])
# courseData = {
#     "course_id": "CS101",
#     "course_name": "Introduction to Computer Science",
#     "section": "1",
#     "schedule": {
#         "days": ["Monday", "Wednesday"],
#         "start_time": "10:00",
#         "end_time": "11:00"
#     },
#     "room": "C101",
#     "instructor_name": "Dr. Ahmad Ali",
#     "registered_students_count": 0
# }
# courseData["instructor_name"] = "Dr. Sara Hassan"

# result = create_course(courseData)
# print(result)
