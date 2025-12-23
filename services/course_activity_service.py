from typing import Any, List, Optional
import redis
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import json

mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["university_portal"]
assignments_col: Collection = mongo_db["assignments"]

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

DEFAULT_CACHE_TTL = 600 


# Redis Key Helpers

def _k_instructor_courses(instructor_id: str) -> str:
    return f"instructor_courses:{instructor_id}"

def _k_available_courses(student_id: str) -> str:
    return f"available_courses:{student_id}"

def _k_instructor_course_assignments(instructor_id: str) -> str:
    return f"instructor_course_assignments:{instructor_id}"

def _k_course_assignments(course_id: str) -> str:
    return f"assignment_list:{course_id}"

def _k_enrolled_students(course_id: str) -> str:
    return f"enrolled_students:{course_id}"

def _k_student_courses(student_id: str) -> str:
    return f"student_courses:{student_id}"

def _k_student_course_details(student_id: str, course_id: str) -> str:
    return f"student_course_details:{student_id}:{course_id}"

def _k_pending_tasks(student_id: str) -> str:
    return f"pending_tasks:{student_id}"


# Redis Invalidation Functions

def invalidate_instructor_courses_cache(instructorID: str) -> dict:
    redis_client.delete(_k_instructor_courses(instructorID))
    return {"success": True}

def invalidate_available_courses_cache() -> dict:
    keys = redis_client.keys("available_courses:*")
    if keys:
        redis_client.delete(*keys)
    return {"success": True, "deleted_keys": len(keys)}

def invalidate_student_available_courses_cache(student_id) -> dict:
    redis_client.delete(_k_available_courses(student_id)) 
    return {"success": True}

def invalidate_instructor_course_assignments_cache(instructorID: str) -> dict:
    redis_client.delete(_k_instructor_course_assignments(instructorID))
    return {"success": True}

def invalidate_student_course_details_cache(studentID: str, courseID: str) -> dict:
    redis_client.delete(_k_student_course_details(studentID, courseID))
    return {"success": True}

def invalidate_enrolled_students_cache(courseID: str) -> dict:
    redis_client.delete(_k_enrolled_students(courseID))
    return {"success": True}

def invalidate_student_courses_cache(studentID: str) -> dict:
    redis_client.delete(_k_student_courses(studentID))
    return {"success": True}

def invalidate_student_pending_task_cache(studentID: str) -> dict:
    redis_client.delete(_k_pending_tasks(studentID))
    return {"success": True}


# Redis Cache Functions

def cache_instructor_courses(instructorID: str, courses: List[dict]) -> dict:
    key = _k_instructor_courses(instructorID)
    redis_client.set(key, json.dumps(courses))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

def cache_course_assignments(courseID: str, assignments: List[dict]) -> dict:
    key = _k_course_assignments(courseID)
    redis_client.set(key, json.dumps(assignments))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

def cache_enrolled_students(courseID: str, students: List[dict]) -> dict:
    key = _k_enrolled_students(courseID)
    redis_client.set(key, json.dumps(students))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

def cache_available_courses(studentID: str, courses: List[dict]) -> dict:
    key = _k_available_courses(studentID)
    redis_client.set(key, json.dumps(courses))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

def cache_student_courses(studentID: str, courses: List[dict]) -> dict:
    key = _k_student_courses(studentID)
    redis_client.set(key, json.dumps(courses))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

def cache_student_course_details(studentID: str, courseID: str, courseDetails: dict) -> dict:
    key = _k_student_course_details(studentID, courseID)
    redis_client.set(key, json.dumps(courseDetails))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

def cache_pending_tasks(studentID: str, tasks: List[dict]) -> dict:
    key = _k_pending_tasks(studentID)
    redis_client.set(key, json.dumps(tasks))
    redis_client.expire(key, DEFAULT_CACHE_TTL)
    return {"success": True}

import json
from typing import List, Optional

def get_cached_instructor_courses(instructorID: str) -> Optional[List[dict]]:
    key = _k_instructor_courses(instructorID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

def get_cached_course_assignments(courseID: str) -> Optional[List[dict]]:
    key = _k_course_assignments(courseID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

def get_cached_enrolled_students(courseID: str) -> Optional[List[dict]]:
    key = _k_enrolled_students(courseID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

def get_cached_available_courses(studentID: str) -> Optional[List[dict]]:
    key = _k_available_courses(studentID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

def get_cached_student_courses(studentID: str) -> Optional[List[dict]]:
    key = _k_student_courses(studentID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

def get_cached_student_course_details(studentID: str, courseID: str) -> Optional[dict]:
    key = _k_student_course_details(studentID, courseID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)

def get_cached_pending_tasks(studentID: str) -> Optional[List[dict]]:
    key = _k_pending_tasks(studentID)
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)


# MongoDB Functions

def create_assignment(courseID: str, assignmentData: dict) -> dict:
    """
    assignmentData must include:
    - assignment_id
    - title
    - description
    - deadline
    - max_grade
    """
    try:
        doc = {
            "course_id": courseID,
            **assignmentData,
            "grades": [],
            "answer_text": []
        }
        assignments_col.insert_one(doc)
        return {"success": True}
    except PyMongoError as e:
        return {"success": False, "error": str(e)}


def get_answer(studentID: str, assignmentID: str) -> dict:
    assignment = assignments_col.find_one({"assignment_id": assignmentID}, {"_id": 0, "answer_text": 1})

    if not assignment:
        return {"success": False, "answer": None}

    for ans in assignment.get("answer_text", []):
        if ans["student_id"] == studentID:
            return {"success": True, "answer": ans}

    return {"success": False, "answer": None}


def update_grades(assignmentID: str, studentID: str, grade: Any) -> dict:
    try:
        assignments_col.update_one(
            {"assignment_id": assignmentID},
            {"$pull": {"grades": {"student_id": studentID}}}
        )

        assignments_col.update_one(
            {"assignment_id": assignmentID},
            {"$push": {"grades": {"student_id": studentID, "grade": grade}}}
        )

        return {"success": True}
    except PyMongoError as e:
        return {"success": False, "error": str(e)}


def create_answer_document(studentID: str, assignmentID: str, answerData: dict) -> dict:
    """
    answerData must include:
    - student_id
    - text
    """
    try:
        assignments_col.update_one(
            {"assignment_id": assignmentID},
            {"$pull": {"answer_text": {"student_id": studentID}}}
        )

        assignments_col.update_one(
            {"assignment_id": assignmentID},
            {"$push": {
                "answer_text": {
                    "student_id": studentID,
                    "text": answerData["text"]
                }
            }}
        )

        return {"success": True}
    except PyMongoError as e:
        return {"success": False, "error": str(e)}


def get_pending_assignments_for_courses(studentID: str, courseIDs: List[str]) -> dict:
    try:
        assignments = list(assignments_col.find(
            {"course_id": {"$in": courseIDs}},
            {"_id": 0}
        ))

        pending = []

        for a in assignments:
            submitted_students = {
                ans["student_id"] for ans in a.get("answer_text", [])
            }
            if studentID not in submitted_students:
                pending.append(a)

        return {"success": True, "tasks": pending}
    except PyMongoError as e:
        return {"success": False, "error": str(e)}
