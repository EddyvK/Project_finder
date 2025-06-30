"""Debug script to examine project data and matching results."""

from database import SessionLocal
from models.core_models import Project, Employee
import json

def debug_project_data():
    """Debug project data to understand the matching issue."""
    db = SessionLocal()

    try:
        # Check some projects
        print("=== PROJECT DATA ===")
        projects = db.query(Project).limit(10).all()
        for project in projects:
            print(f"\nProject {project.id}: {project.title}")
            print(f"Requirements (raw): {project.requirements}")
            try:
                requirements_list = project.get_requirements_list()
                print(f"Requirements (parsed): {requirements_list}")
                print(f"Requirements type: {type(requirements_list)}")
            except Exception as e:
                print(f"Error parsing requirements: {e}")

        # Check some employees
        print("\n=== EMPLOYEE DATA ===")
        employees = db.query(Employee).limit(3).all()
        for employee in employees:
            print(f"\nEmployee {employee.id}: {employee.name}")
            print(f"Skills (raw): {employee.skill_list}")
            try:
                skills_list = employee.get_skill_list()
                print(f"Skills (parsed): {skills_list}")
                print(f"Skills type: {type(skills_list)}")
            except Exception as e:
                print(f"Error parsing skills: {e}")

        # Check a specific problematic project
        print("\n=== PROBLEMATIC PROJECTS ===")
        problematic_projects = db.query(Project).filter(
            Project.requirements.like('%{title%')
        ).limit(5).all()

        for project in problematic_projects:
            print(f"\nProblematic Project {project.id}: {project.title}")
            print(f"Requirements: {project.requirements}")
            try:
                requirements_list = project.get_requirements_list()
                print(f"Parsed: {requirements_list}")
            except Exception as e:
                print(f"Parse error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    debug_project_data()