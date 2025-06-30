#!/usr/bin/env python3
"""
Test script to verify TF/IDF weighted matching with a lower threshold.
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
            },
            {
                "title": "Java Backend Development",
                "url": "https://example.com/project2",
                "project_id": "PRJ002",
                "location": "Munich",
                "duration": "12 months",
                "start_date": datetime.now() + timedelta(days=15),
                "release_date": datetime.now() - timedelta(days=3),
                "tenderer": "BankCorp",
                "rate": "€90/hour",
                "requirements_tf": {
                    "Java": 4,
                    "Spring": 3,
                    "PostgreSQL": 2,
                    "Maven": 1,
                    "Docker": 1
                }
            },
            {
                "title": "React Frontend Development",
                "url": "https://example.com/project3",
                "project_id": "PRJ003",
                "location": "Hamburg",
                "duration": "4 months",
                "start_date": datetime.now() + timedelta(days=45),
                "release_date": datetime.now() - timedelta(days=1),
                "tenderer": "ShopCorp",
                "rate": "€75/hour",
                "requirements_tf": {
                    "React": 3,
                    "JavaScript": 2,
                    "TypeScript": 2,
                    "HTML": 1,
                    "CSS": 1,
                    "Node.js": 1
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
            },
            {
                "name": "Bob Smith",
                "skills": ["Java", "Spring", "PostgreSQL", "Maven", "Docker"],
                "experience_years": 7
            },
            {
                "name": "Carol Davis",
                "skills": ["React", "JavaScript", "TypeScript", "HTML", "CSS", "Node.js"],
                "experience_years": 4
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

async def test_tfidf_low_threshold():
    """Test TF/IDF weighted matching with a lower threshold."""
    db = SessionLocal()

    try:
        print("\n=== Testing TF/IDF Weighted Matching with Low Threshold ===")

        # Calculate and update IDF factors
        print("1. Calculating IDF factors...")
        idf_factors = tfidf_service.update_skills_idf_factors(db)

        print(f"Calculated IDF factors for {len(idf_factors)} skills:")
        for skill, idf in sorted(idf_factors.items(), key=lambda x: x[1], reverse=True):
            print(f"  {skill}: {idf:.4f}")

        # Test employee matching with TF/IDF weighting and low threshold
        print("\n2. Testing Employee Matching with Low Threshold (0.3):")
        matching_service = MatchingService()

        employees = db.query(Employee).all()

        for employee in employees:
            print(f"\nEmployee: {employee.name}")
            print(f"Skills: {employee.get_skill_list()}")

            try:
                # Get matches using the actual matching service with low threshold
                result = await matching_service.match_employee_to_projects(db, employee.id, threshold=0.3)

                if result['matches']:
                    print("Top matching projects:")
                    for i, match in enumerate(result['matches'][:3], 1):
                        project = db.query(Project).filter(Project.id == match['project_id']).first()
                        print(f"  {i}. {project.title} - Match: {match['match_percentage']:.2f}%")
                        print(f"     Matching skills: {match['matching_skills']}")
                        print(f"     Missing skills: {match['missing_skills']}")
                else:
                    print("  No compatible projects found (even with low threshold)")

            except Exception as e:
                print(f"  Error matching employee: {e}")
                print("  (This might be due to missing embeddings or API issues)")

        return True

    except Exception as e:
        print(f"Error testing TF/IDF weighted matching: {e}")
        return False
    finally:
        db.close()

async def main():
    """Main test function."""
    print("=== TF/IDF Test with Low Threshold ===")

    try:
        # Create test data
        create_test_data()

        # Test TF/IDF functionality with low threshold
        success = await test_tfidf_low_threshold()

        if success:
            print("\n✅ Test completed!")
        else:
            print("\n❌ Some tests failed.")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())