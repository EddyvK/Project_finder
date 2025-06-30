#!/usr/bin/env python3
"""
Debug test to show the embedding issue and test exact string matching.
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

def test_exact_matching():
    """Test exact string matching without embeddings."""
    db = SessionLocal()

    try:
        print("\n=== Testing Exact String Matching ===")

        # Calculate and update IDF factors
        print("1. Calculating IDF factors...")
        idf_factors = tfidf_service.update_skills_idf_factors(db)

        print(f"Calculated IDF factors for {len(idf_factors)} skills:")
        for skill, idf in sorted(idf_factors.items(), key=lambda x: x[1], reverse=True):
            print(f"  {skill}: {idf:.4f}")

        # Test simple matching logic
        print("\n2. Testing Simple Matching Logic:")
        employees = db.query(Employee).all()
        projects = db.query(Project).all()

        for employee in employees:
            print(f"\nEmployee: {employee.name}")
            print(f"Skills: {employee.get_skill_list()}")

            for project in projects:
                print(f"\n  Project: {project.title}")
                project_requirements = project.get_requirements_list()
                print(f"  Requirements: {project_requirements}")

                employee_skills = employee.get_skill_list()
                matching_skills = []
                missing_skills = []

                for req in project_requirements:
                    # Check for exact match
                    if req in employee_skills:
                        matching_skills.append(req)
                        print(f"    ✅ MATCH: {req}")
                    else:
                        missing_skills.append(req)
                        print(f"    ❌ MISSING: {req}")

                if matching_skills:
                    match_percentage = (len(matching_skills) / len(project_requirements)) * 100
                    print(f"  Match: {match_percentage:.2f}% ({len(matching_skills)}/{len(project_requirements)})")
                else:
                    print(f"  Match: 0.00% (0/{len(project_requirements)})")

        return True

    except Exception as e:
        print(f"Error testing exact matching: {e}")
        return False
    finally:
        db.close()

async def test_embedding_issue():
    """Test to show the embedding issue."""
    db = SessionLocal()

    try:
        print("\n=== Testing Embedding Issue ===")

        # Check if OpenAI API key is available
        api_keys = config_manager.get_api_keys()
        if not api_keys.get("openai"):
            print("⚠️  OpenAI API key not found. Cannot test embeddings.")
            return True

        print("✅ OpenAI API key found. Testing embedding creation...")

        # Test embedding creation for a simple skill
        matching_service = MatchingService()
        project = db.query(Project).first()

        if project:
            print(f"Testing project: {project.title}")
            project_requirements = project.get_requirements_list()
            print(f"Requirements: {project_requirements}")

            # Test getting embeddings
            embeddings = await matching_service._get_project_embeddings(db, project)
            print(f"Created embeddings for {len(embeddings)} requirements:")
            for req, embedding in embeddings.items():
                print(f"  {req}: {len(embedding) if embedding else 0} dimensions")

        return True

    except Exception as e:
        print(f"Error testing embedding issue: {e}")
        return False
    finally:
        db.close()

async def main():
    """Main test function."""
    print("=== TF/IDF Debug Test ===")

    try:
        # Create test data
        create_test_data()

        # Test exact matching
        test_exact_matching()

        # Test embedding issue
        await test_embedding_issue()

        print("\n✅ Debug test completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())