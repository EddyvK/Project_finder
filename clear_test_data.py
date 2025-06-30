#!/usr/bin/env python3
"""
Script to clear existing test data so new test data can be created.
"""

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee, Skill

def clear_test_data():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Clearing Test Data")
        print("=" * 60)

        # Count existing test data
        test_projects = db.query(Project).filter(Project.tenderer == "Test").all()
        test_employees = db.query(Employee).filter(Employee.name.in_([
            "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis"
        ])).all()

        print(f"Found {len(test_projects)} test projects")
        print(f"Found {len(test_employees)} test employees")

        if len(test_projects) == 0 and len(test_employees) == 0:
            print("No test data found to clear.")
            return

        # Delete test projects
        for project in test_projects:
            print(f"Deleting test project: {project.title}")
            db.delete(project)

        # Delete test employees
        for employee in test_employees:
            print(f"Deleting test employee: {employee.name}")
            db.delete(employee)

        # Commit the deletions
        db.commit()
        print("✅ Test data cleared successfully")

        # Verify deletion
        remaining_test_projects = db.query(Project).filter(Project.tenderer == "Test").count()
        remaining_test_employees = db.query(Employee).filter(Employee.name.in_([
            "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis"
        ])).count()

        print(f"Remaining test projects: {remaining_test_projects}")
        print(f"Remaining test employees: {remaining_test_employees}")

    except Exception as e:
        print(f"❌ Error clearing test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_test_data()