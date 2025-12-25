from services.academic_network_service import driver
from services.student_information_service import (
    users_col,
    students_col,
    instructors_col,
    courses_col,
    enrollments_col,
    assignments_col,
    rooms_col
)


def reset_entire_system():
    print("🧹 Resetting MongoDB collections...")

    users_col.delete_many({})
    students_col.delete_many({})
    instructors_col.delete_many({})
    courses_col.delete_many({})
    enrollments_col.delete_many({})
    assignments_col.delete_many({})
    rooms_col.delete_many({})

    print("✅ MongoDB cleared")

    print("🧹 Resetting Neo4j database...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    print("✅ Neo4j cleared")
    print("🎉 System reset completed successfully")
