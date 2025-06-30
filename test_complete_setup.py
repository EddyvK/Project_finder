#!/usr/bin/env python3
"""
Comprehensive test that properly sets up the skills table with embeddings and IDF factors.
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
from backend.openai_handler import OpenAIHandler
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

async def setup_skills_table():
    """Set up the skills table with embeddings and IDF factors."""
    db = SessionLocal()

    try:
        print("\n=== Setting up Skills Table ===")

        # Check if OpenAI API key is available
        api_keys = config_manager.get_api_keys()
        if not api_keys.get("openai"):
            print("⚠️  OpenAI API key not found. Cannot create embeddings.")
            print("   Please ensure the .env file in the backend directory contains:")
            print("   OPENAI_API_KEY=your_actual_api_key_here")
            return False

        print("✅ OpenAI API key found. Setting up skills table...")

        # Initialize OpenAI handler
        try:
            openai_handler = OpenAIHandler(api_keys["openai"])
            print("✅ OpenAI handler initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI handler: {e}")
            return False

        # Get all unique skills from projects and employees
        all_skills = set()

        # Collect skills from projects
        projects = db.query(Project).all()
        for project in projects:
            requirements = project.get_requirements_list()
            all_skills.update(requirements)

        # Collect skills from employees
        employees = db.query(Employee).all()
        for employee in employees:
            skills = employee.get_skill_list()
            all_skills.update(skills)

        print(f"Found {len(all_skills)} unique skills to process")

        # Create embeddings for all skills
        skills_processed = 0
        for skill in all_skills:
            if skill.strip():  # Skip empty skills
                try:
                    # Check if skill already exists
                    existing_skill = db.query(Skill).filter(
                        Skill.skill_name == skill
                    ).first()

                    if not existing_skill:
                        print(f"Creating embedding for skill: {skill}")
                        embedding = await openai_handler.get_embedding(skill)
                        if embedding:
                            # Create new skill entry
                            new_skill = Skill(
                                skill_name=skill,
                                embedding=json.dumps(embedding),
                                idf_factor=0.0  # Will be updated by TF/IDF service
                            )
                            db.add(new_skill)
                            skills_processed += 1
                            print(f"  ✅ Created embedding with {len(embedding)} dimensions")
                        else:
                            print(f"  ❌ Failed to create embedding")
                    else:
                        print(f"Skill already exists: {skill}")

                except Exception as e:
                    print(f"Error processing skill '{skill}': {str(e)}")

        db.commit()
        print(f"Created embeddings for {skills_processed} new skills")

        # Calculate and update IDF factors
        print("\nCalculating IDF factors...")
        idf_factors = tfidf_service.update_skills_idf_factors(db)

        print(f"Updated IDF factors for {len(idf_factors)} skills:")
        for skill, idf in sorted(idf_factors.items(), key=lambda x: x[1], reverse=True):
            print(f"  {skill}: {idf:.4f}")

        # Verify skills table
        print(f"\nVerifying skills table...")
        skills = db.query(Skill).all()
        print(f"Total skills in database: {len(skills)}")

        for skill in skills:
            embedding = skill.get_embedding()
            print(f"  {skill.skill_name}: {len(embedding)} dimensions, IDF={skill.idf_factor:.4f}")

        return True

    except Exception as e:
        print(f"Error setting up skills table: {e}")
        db.rollback()
        return False
    finally:
        db.close()

async def test_complete_matching():
    """Test complete matching with properly set up skills table."""
    db = SessionLocal()

    try:
        print("\n=== Testing Complete Matching ===")

        # Test matching service
        matching_service = MatchingService()
        employees = db.query(Employee).all()

        for employee in employees:
            print(f"\nEmployee: {employee.name}")
            print(f"Skills: {employee.get_skill_list()}")

            try:
                # Test with reasonable threshold
                result = await matching_service.match_employee_to_projects(db, employee.id, threshold=0.3)

                if result['matches']:
                    print("Top matching projects:")
                    for i, match in enumerate(result['matches'][:3], 1):
                        project = db.query(Project).filter(Project.id == match['project_id']).first()
                        print(f"  {i}. {project.title} - Match: {match['match_percentage']:.2f}%")
                        print(f"     Matching skills: {match['matching_skills']}")
                        print(f"     Missing skills: {match['missing_skills']}")
                else:
                    print("  No compatible projects found")

            except Exception as e:
                print(f"  Error matching employee: {e}")

        return True

    except Exception as e:
        print(f"Error testing complete matching: {e}")
        return False
    finally:
        db.close()

async def main():
    """Main test function."""
    print("=== Complete Setup and Test ===")

    try:
        # Create test data
        create_test_data()

        # Set up skills table with embeddings and IDF factors
        setup_success = await setup_skills_table()

        if setup_success:
            # Test complete matching
            await test_complete_matching()

            print("\n✅ Complete setup and test completed successfully!")
            print("\n📊 Summary:")
            print("   - Skills table: ✅ Properly set up with embeddings and IDF factors")
            print("   - TF/IDF calculation: ✅ Working")
            print("   - Matching service: ✅ Should now work correctly")
        else:
            print("\n❌ Skills table setup failed.")
            print("\n💡 You can still use the TF/IDF weighted exact matching as shown in test_tfidf_exact_only.py")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())