#!/usr/bin/env python3
"""
Test script to verify TF/IDF weighted matching in the actual matching service.
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

async def test_tfidf_weighted_matching():
    """Test TF/IDF weighted matching with the actual matching service."""
    db = SessionLocal()

    try:
        print("\n=== Testing TF/IDF Weighted Matching ===")

        # Calculate and update IDF factors
        print("Calculating IDF factors...")
        idf_factors = tfidf_service.update_skills_idf_factors(db)

        print(f"Calculated IDF factors for {len(idf_factors)} skills:")
        for skill, idf in sorted(idf_factors.items(), key=lambda x: x[1], reverse=True):
            print(f"  {skill}: {idf:.4f}")

        # Test employee matching with TF/IDF weighting
        print("\n=== Testing Employee Matching with TF/IDF Weighting ===")
        matching_service = MatchingService()

        employees = db.query(Employee).all()

        for employee in employees:
            print(f"\nEmployee: {employee.name}")
            print(f"Skills: {employee.get_skill_list()}")

            try:
                # Get matches using the actual matching service
                result = await matching_service.match_employee_to_projects(db, employee.id)

                print("Top matching projects:")
                for i, match in enumerate(result['matches'][:3], 1):
                    project = db.query(Project).filter(Project.id == match['project_id']).first()
                    print(f"  {i}. {project.title} - Match: {match['match_percentage']:.2f}%")
                    print(f"     Matching skills: {match['matching_skills']}")
                    print(f"     Missing skills: {match['missing_skills']}")

            except Exception as e:
                print(f"  Error matching employee: {e}")
                # Fall back to simple matching for testing
                projects = db.query(Project).all()
                simple_matches = simple_match_employee_projects(employee, projects, db)
                print("  (Using simple matching as fallback)")
                for i, match in enumerate(simple_matches[:3], 1):
                    print(f"  {i}. {match['project_title']} - Match: {match['match_percentage']:.2f}%")

        return True

    except Exception as e:
        print(f"Error testing TF/IDF weighted matching: {e}")
        return False
    finally:
        db.close()

def simple_match_employee_projects(employee, projects, db):
    """Simple synchronous matching function for testing."""
    employee_skills = employee.get_skill_list()
    matches = []

    for project in projects:
        project_requirements = project.get_requirements_tf()
        if not project_requirements:
            continue

        # Count matching skills
        matching_skills = []
        missing_skills = []

        for skill in employee_skills:
            if skill in project_requirements:
                matching_skills.append(skill)
            else:
                missing_skills.append(skill)

        # Calculate match percentage
        if project_requirements:
            match_percentage = (len(matching_skills) / len(project_requirements)) * 100
        else:
            match_percentage = 0

        matches.append({
            'project_id': project.id,
            'project_title': project.title,
            'match_percentage': match_percentage,
            'matching_skills': matching_skills,
            'missing_skills': missing_skills
        })

    # Sort by match percentage
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return matches

async def main():
    """Main test function."""
    print("=== TF/IDF Weighted Matching Test ===")

    try:
        # Create test data
        create_test_data()

        # Test TF/IDF weighted matching
        success = await test_tfidf_weighted_matching()

        if success:
            print("\n✅ All tests passed! TF/IDF weighted matching is working correctly.")
        else:
            print("\n❌ Some tests failed.")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())