#!/usr/bin/env python3
"""
Script to debug real project and employee data to understand matching issues.
"""

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.matching_service import MatchingService
import asyncio

async def debug_real_data():
    db = SessionLocal()
    matching_service = MatchingService()

    try:
        print("=" * 60)
        print("Debugging Real Project and Employee Data")
        print("=" * 60)

        # Check real projects (non-test)
        print("\nReal Projects (non-test):")
        real_projects = db.query(Project).filter(Project.tenderer != "Test").all()
        print(f"Found {len(real_projects)} real projects")

        for p in real_projects:
            print(f"\nProject {p.id}: {p.title}")
            print(f"  Tenderer: {p.tenderer}")
            print(f"  Requirements TF: {p.get_requirements_tf()}")
            print(f"  Requirements List: {p.get_requirements_list()}")
            print(f"  Requirements Count: {len(p.get_requirements_list())}")

        # Check real employees
        print("\nReal Employees:")
        real_employees = db.query(Employee).filter(
            ~Employee.name.in_(["John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis"])
        ).all()
        print(f"Found {len(real_employees)} real employees")

        for e in real_employees:
            print(f"\nEmployee {e.id}: {e.name}")
            print(f"  Skills: {e.get_skill_list()}")
            print(f"  Skills Count: {len(e.get_skill_list())}")

        # Test matching for one real employee
        if real_employees:
            test_employee = real_employees[0]
            print(f"\n\nTesting matching for: {test_employee.name}")
            print(f"Employee skills: {test_employee.get_skill_list()}")

            # Test matching against one real project
            if real_projects:
                test_project = real_projects[0]
                print(f"\nTesting against project: {test_project.title}")
                print(f"Project requirements: {test_project.get_requirements_list()}")

                # Manual matching test
                employee_skills = test_employee.get_skill_list()
                project_requirements = test_project.get_requirements_list()

                print(f"\nManual matching test:")
                matching_skills = []
                missing_skills = []

                for req in project_requirements:
                    if req in employee_skills:
                        matching_skills.append(req)
                        print(f"  ✅ MATCH: {req}")
                    else:
                        missing_skills.append(req)
                        print(f"  ❌ MISSING: {req}")

                print(f"\nResults:")
                print(f"  Matching: {matching_skills}")
                print(f"  Missing: {missing_skills}")
                print(f"  Match rate: {len(matching_skills)}/{len(project_requirements)} = {len(matching_skills)/len(project_requirements)*100:.1f}%")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_real_data())