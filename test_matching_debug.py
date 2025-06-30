#!/usr/bin/env python3
"""
Debug test to understand what's happening in the matching service.
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal, engine
from backend.models.core_models import Base, Project, Employee, Skill
from backend.tfidf_service import tfidf_service
from backend.matching_service import MatchingService
from backend.config_manager import config_manager

def create_test_data():
    """Create test data in the database."""
    db = SessionLocal()

    try:
        # Clear existing data
        db.query(Project).delete()
        db.query(Employee).delete()
        db.query(Skill).delete()
        db.commit()

        print("Cleared existing data")

        # Create test projects with requirements_tf
        test_projects = [
            {
                "title": "Python Web Development",
                "url": "https://example.com/project1",
                "project_id": "PRJ001",
                "location": "Berlin",
                "duration": "6 months",
                "start_date": datetime.now() + timedelta(days=30),
                "release_date": datetime.now() - timedelta(days=5),
                "tenderer": "TechCorp",
                "rate": "€80/hour",
                "requirements_tf": {
                    "Python": 3,
                    "Django": 2,
                    "PostgreSQL": 1,
                    "JavaScript": 1,
                    "HTML": 1,
                    "CSS": 1
                }
            }
        ]

        # Create projects
        created_projects = []
        for project_data in test_projects:
            project = Project(
                title=project_data["title"],
                url=project_data["url"],
                project_id=project_data["project_id"],
                location=project_data["location"],
                duration=project_data["duration"],
                start_date=str(project_data["start_date"].date()),
                release_date=str(project_data["release_date"].date()),
                tenderer=project_data["tenderer"],
                rate=project_data["rate"],
                requirements_tf=json.dumps(project_data["requirements_tf"])
            )
            db.add(project)
            created_projects.append(project)

        # Create test employees
        test_employees = [
            {
                "name": "Alice Johnson",
                "skills": ["Python", "Django", "PostgreSQL", "JavaScript", "HTML", "CSS"],
                "experience_years": 5
            }
        ]

        # Create employees
        created_employees = []
        for emp_data in test_employees:
            employee = Employee(
                name=emp_data["name"],
                skill_list=json.dumps(emp_data["skills"]),
                experience_years=emp_data["experience_years"]
            )
            db.add(employee)
            created_employees.append(employee)

        db.commit()
        print(f"Created {len(created_projects)} projects and {len(created_employees)} employees")

        return created_projects, created_employees

    except Exception as e:
        print(f"Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def debug_matching_service():
    """Debug the matching service step by step."""
    db = SessionLocal()

    try:
        print("\n=== Debugging Matching Service ===")

        # Calculate IDF factors
        print("1. Calculating IDF factors...")
        idf_factors = tfidf_service.update_skills_idf_factors(db)

        # Get employee and project
        employee = db.query(Employee).first()
        project = db.query(Project).first()

        if not employee or not project:
            print("❌ Employee or project not found")
            return

        print(f"\n2. Employee: {employee.name}")
        print(f"   Skills: {employee.get_skill_list()}")
        print(f"\n3. Project: {project.title}")
        print(f"   Requirements: {project.get_requirements_list()}")
        print(f"   Requirements TF: {project.get_requirements_tf()}")

        # Test matching service
        print(f"\n4. Testing matching service...")
        matching_service = MatchingService()

        try:
            # Test with very low threshold
            result = await matching_service.match_employee_to_projects(db, employee.id, threshold=0.1)

            print(f"Result: {result}")

            if result['matches']:
                print("✅ Matches found!")
                for match in result['matches']:
                    print(f"  Project: {match['project_title']}")
                    print(f"  Match: {match['match_percentage']}%")
                    print(f"  Matching skills: {match['matching_skills']}")
                    print(f"  Missing skills: {match['missing_skills']}")
            else:
                print("❌ No matches found")
                print(f"Total projects checked: {result['total_projects_checked']}")
                print(f"Missing skills summary: {result['missing_skills_summary']}")

        except Exception as e:
            print(f"❌ Error in matching service: {e}")
            import traceback
            traceback.print_exc()

        return True

    except Exception as e:
        print(f"Error debugging matching service: {e}")
        return False
    finally:
        db.close()

async def main():
    """Main test function."""
    print("=== Matching Service Debug Test ===")

    try:
        # Create test data
        create_test_data()

        # Debug matching service
        await debug_matching_service()

        print("\n✅ Debug test completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())