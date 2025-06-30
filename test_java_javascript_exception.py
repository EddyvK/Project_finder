#!/usr/bin/env python3
"""
Test script to verify that Java and JavaScript are properly distinguished
and don't get falsely matched due to the hardcoded exception.
"""

import asyncio
import sys
import os
import sqlite3
from sqlalchemy import inspect

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.matching_service import MatchingService
from backend.database import get_db, DATABASE_URL
from backend.models.core_models import Employee, Project, Skill
from backend.config_manager import config_manager

async def test_java_javascript_exception():
    """Test that Java and JavaScript are properly distinguished."""

    print("Testing Java/JavaScript hardcoded exception...")

    # Print the database URL and absolute path
    print(f"Database URL: {DATABASE_URL}")
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        abs_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), db_path))
        print(f"Resolved database file: {abs_db_path}")
        if not os.path.exists(abs_db_path):
            print(f"WARNING: Database file does not exist at {abs_db_path}")
    else:
        print("Non-SQLite database in use.")

    # Get database session
    db = next(get_db())

    # Check for table existence
    inspector = inspect(db.bind)
    required_tables = ["employees", "projects", "skills"]
    missing_tables = [t for t in required_tables if not inspector.has_table(t)]
    if missing_tables:
        print(f"ERROR: Missing required tables: {missing_tables}")
        db.close()
        return

    def print_employees_table():
        employees = db.execute("SELECT id, name, skill_list FROM employees").fetchall()
        print(f"Current employees table ({len(employees)} rows):")
        for row in employees:
            print(f"  id={row[0]}, name={row[1]}, skill_list={row[2]}")

    print("\nEmployees table BEFORE test:")
    print_employees_table()

    try:
        # Create test employee with Java skill
        java_employee = Employee(
            name="Java Developer",
            skill_list='["Java", "Spring Boot", "Maven"]'
        )
        db.add(java_employee)
        db.commit()

        # Create test employee with JavaScript skill
        js_employee = Employee(
            name="JavaScript Developer",
            skill_list='["JavaScript", "React", "Node.js"]'
        )
        db.add(js_employee)
        db.commit()

        # Create test project requiring Java
        java_project = Project(
            title="Java Backend Development",
            requirements_tf='{"Java": 1, "Spring Boot": 1, "REST API": 1}'
        )
        db.add(java_project)
        db.commit()

        # Create test project requiring JavaScript
        js_project = Project(
            title="JavaScript Frontend Development",
            requirements_tf='{"JavaScript": 1, "React": 1, "HTML": 1, "CSS": 1}'
        )
        db.add(js_project)
        db.commit()

        # Initialize matching service
        matching_service = MatchingService()

        print(f"\n1. Testing Java employee with Java project:")
        result1 = await matching_service.match_employee_to_projects(db, java_employee.id)
        for match in result1["matches"]:
            if "Java" in match["project_title"]:
                print(f"   Java employee matched with Java project: {match['match_percentage']}%")
                print(f"   Matching skills: {match['matching_skills']}")
                print(f"   Missing skills: {match['missing_skills']}")

        print(f"\n2. Testing Java employee with JavaScript project:")
        for match in result1["matches"]:
            if "JavaScript" in match["project_title"]:
                print(f"   Java employee matched with JavaScript project: {match['match_percentage']}%")
                print(f"   Matching skills: {match['matching_skills']}")
                print(f"   Missing skills: {match['missing_skills']}")

        print(f"\n3. Testing JavaScript employee with JavaScript project:")
        result2 = await matching_service.match_employee_to_projects(db, js_employee.id)
        for match in result2["matches"]:
            if "JavaScript" in match["project_title"]:
                print(f"   JavaScript employee matched with JavaScript project: {match['match_percentage']}%")
                print(f"   Matching skills: {match['matching_skills']}")
                print(f"   Missing skills: {match['missing_skills']}")

        print(f"\n4. Testing JavaScript employee with Java project:")
        for match in result2["matches"]:
            if "Java" in match["project_title"]:
                print(f"   JavaScript employee matched with Java project: {match['match_percentage']}%")
                print(f"   Matching skills: {match['matching_skills']}")
                print(f"   Missing skills: {match['missing_skills']}")

        # Clean up test data
        db.delete(java_employee)
        db.delete(js_employee)
        db.delete(java_project)
        db.delete(js_project)
        db.commit()

        print("\nEmployees table AFTER test:")
        print_employees_table()

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Error during test: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_java_javascript_exception())