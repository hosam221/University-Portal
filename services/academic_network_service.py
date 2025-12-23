from typing import List, Dict, Optional, Any
import os
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


# Neo4j Connection 
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "test1234")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
def write(query: str,) -> None:
    def _tx(tx):
        tx.run(query)
    with driver.session() as session:
        session.execute_write(_tx)
def read(query: str):
    def _tx(tx):
        return list(tx.run(query))
    with driver.session() as session:
        return session.execute_read(_tx)




# Nodes creation 
def create_student_node(studentID: str, name: str) -> dict:
    try:
        write(f"MERGE (s:Student {{id:'{studentID}'}}) SET s.name = '{name}'")
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}


def create_instructor_node(instructorID: str) -> dict:
    try:
        write(f"MERGE (i:Instructor {{id:'{instructorID}'}})")
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}


def create_course_node(courseID: str) -> dict:
    try:
        write(f"MERGE (c:Course {{id:'{courseID}'}}) ")
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}


def create_assignment_node(assignmentID: str) -> dict:
    try:
        write(f"MERGE (a:Assignment {{id:'{assignmentID}'}})")
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}





# Relationships
def link_instructor_to_course(
    instructorID: str,
    courseID: str,
) -> dict:
    try:
        create_instructor_node(instructorID)
        create_course_node(courseID)

        write(
            f"MATCH (i:Instructor {{id:'{instructorID}'}}), (c:Course {{id:'{courseID}'}}) "
            f"MERGE (i)-[:TEACHES]->(c)"
        )
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}


def link_student_to_course(
    studentID: str,
    studentName: str,
    courseID: str,
) -> dict:
    try:
        create_student_node(studentID,studentName)
        create_course_node(courseID)

        write(
            f"MATCH (s:Student {{id:'{studentID}'}}), (c:Course {{id:'{courseID}'}}) "
            f"MERGE (s)-[:ENROLLED_IN]->(c)"
        )
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}


def link_assignment_to_course(
    assignmentID: str,
    courseID: str,

) -> dict:
    try:
        create_assignment_node(assignmentID)
        create_course_node(courseID)

        write(
            f"MATCH (a:Assignment {{id:'{assignmentID}'}}), (c:Course {{id:'{courseID}'}}) "
            f"MERGE (a)-[:BELONGS_TO]->(c)"
        )
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}


def link_student_to_assignment(
    studentID: str,
    studentName: str,
    assignmentID: str,
) -> dict:
    try:
        create_student_node(studentID,studentName)
        create_assignment_node(assignmentID)

        write(
            f"MATCH (s:Student {{id:'{studentID}'}}), (a:Assignment {{id:'{assignmentID}'}}) "
            f"MERGE (s)-[:SUBMITTED]->(a)"
        )
        return {"success": True}
    except Neo4jError as e:
        return {"error": str(e)}




# Queries
def get_instructor_courses_ids(instructorID: str) -> list[str]:
    try:
        rows = read(
            f"MATCH (i:Instructor {{id:'{instructorID}'}})-[:TEACHES]->(c:Course) "
            f"RETURN c.id"
        )
        return [row["c.id"] for row in rows]

    except Neo4jError:
        return []

    

def get_student_enrolled_course_ids(studentID: str) -> list[str]:
    try:
        rows = read(
            f"MATCH (s:Student {{id:'{studentID}'}})-[:ENROLLED_IN]->(c:Course) "
            f"RETURN c.id"
        )
        return [row["c.id"] for row in rows]

    except Neo4jError:
        return []



def get_course_students(courseID: str) -> dict:
    try:
        rows = read(
            f"MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {{id:'{courseID}'}}) "
            f"RETURN s.id"
        )
        student_ids = [row["s.id"] for row in rows]
        return {"studentIDs": student_ids}

    except Neo4jError as e:
        return {"error": str(e)}


def get_course_assignments(courseID: str) -> dict:
    try:
        rows = read(
            f"MATCH (a:Assignment)-[:BELONGS_TO]->(c:Course {{id:'{courseID}'}}) "
            f"RETURN a.id"
        )
        assignment_ids = [row["a.id"] for row in rows]
        return {"assignmentIDs": assignment_ids}

    except Neo4jError as e:
        return {"error": str(e)}



def get_student_network(studentID: str) -> dict:
    try:
        rows = read(
            f"MATCH (s:Student {{id:'{studentID}'}})-[:ENROLLED_IN]->(c:Course)"
            f"<-[:ENROLLED_IN]-(other:Student) "
            f"RETURN c.id, other.id"
        )
        network = []
        for row in rows:
            network.append({
                "courseID": row["c.id"],
                "studentID": row["other.id"]
            })

        return {"network": network}

    except Neo4jError as e:
        return {"error": str(e)}



def get_student_course_network(studentID: str, courseID: str) -> dict:
    try:
        rows = read(
            f"MATCH (s:Student {{id:'{studentID}'}})-[:ENROLLED_IN]->(c:Course {{id:'{courseID}'}}) "
            f"OPTIONAL MATCH (i:Instructor)-[:TEACHES]->(c) "
            f"OPTIONAL MATCH (other:Student)-[:ENROLLED_IN]->(c) "
            f"WHERE other.id <> s.id "
            f"RETURN c.id, collect(DISTINCT i.id), collect(DISTINCT other.id)"
        )

        if not rows:
            return {
                "course_id": courseID,
                "instructors": [],
                "students": []
            }

        r = rows[0]
        return {
            "course_id": r["c.id"],
            "instructors": r["collect(DISTINCT i.id)"],
            "students": r["collect(DISTINCT other.id)"]
        }

    except Neo4jError as e:
        return {"error": str(e)}



