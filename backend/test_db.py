"""Test script to debug database and model issues."""

import sys
import traceback
from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.models.schemas import ProjectResponse, EmployeeResponse

def test_database_connection():
    """Test database connection and basic queries."""
    try:
        print("Testing database connection...")
        db = SessionLocal()

        # Test basic query
        print("Testing Project query...")
        projects = db.query(Project).all()
        print(f"Found {len(projects)} projects")

        print("Testing Employee query...")
        employees = db.query(Employee).all()
        print(f"Found {len(employees)} employees")

        # Test schema conversion
        if projects:
            print("Testing ProjectResponse schema...")
            project = projects[0]
            response = ProjectResponse(
                id=project.id,
                title=project.title,
                description=project.description,
                release_date=project.release_date,
                start_date=project.start_date,
                location=project.location,
                tenderer=project.tenderer,
                project_id=project.project_id,
                requirements=project.get_requirements_list(),
                rate=project.rate,
                url=project.url,
                budget=project.budget,
                duration=project.duration,
                workload=project.workload,
                last_scan=project.last_scan.isoformat() if project.last_scan else None
            )
            print("ProjectResponse created successfully")
            print(f"Project: {response.title}")
            print(f"Requirements: {response.requirements}")
            print(f"Workload: {response.workload}")

        if employees:
            print("Testing EmployeeResponse schema...")
            employee = employees[0]
            response = EmployeeResponse(
                id=employee.id,
                name=employee.name,
                skill_list=employee.get_skill_list(),
                experience_years=employee.experience_years,
                created_at=employee.created_at,
                updated_at=employee.updated_at
            )
            print("EmployeeResponse created successfully")
            print(f"Employee: {employee.name}")
            print(f"Skills: {employee.get_skill_list()}")
            print(f"Experience: {employee.experience_years} years")
            print(f"Created: {employee.created_at}")
            print(f"Updated: {employee.updated_at}")
            print("---")

        db.close()
        print("Database connection test completed successfully!")

    except Exception as e:
        print(f"Error testing database: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_database_connection()