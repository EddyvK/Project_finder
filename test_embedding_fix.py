#!/usr/bin/env python3
"""
Test script to diagnose and fix the embedding creation issue.
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

async def test_embedding_creation():
    """Test embedding creation directly."""
    try:
        print("\n=== Testing Embedding Creation ===")

        # Check if OpenAI API key is available
        api_keys = config_manager.get_api_keys()
        if not api_keys.get("openai"):
            print("⚠️  OpenAI API key not found in environment variables.")
            print("   Please ensure the .env file in the backend directory contains:")
            print("   OPENAI_API_KEY=your_actual_api_key_here")
            return False

        print("✅ OpenAI API key found. Testing embedding creation...")

        # Test OpenAI handler directly
        try:
            openai_handler = OpenAIHandler(api_keys["openai"])
            print("✅ OpenAI handler initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI handler: {e}")
            return False

        # Test embedding creation for a simple skill
        test_skill = "Python"
        print(f"\nTesting embedding creation for skill: '{test_skill}'")

        try:
            embedding = await openai_handler.get_embedding(test_skill)
            if embedding and len(embedding) > 0:
                print(f"✅ Successfully created embedding with {len(embedding)} dimensions")
                print(f"   First 5 values: {embedding[:5]}")
            else:
                print("❌ Embedding creation returned empty result")
                return False
        except Exception as e:
            print(f"❌ Error creating embedding: {e}")
            return False

        # Test storing embedding in database
        db = SessionLocal()
        try:
            print(f"\nTesting embedding storage in database...")

            # Create a skill entry
            skill = Skill(
                skill_name=test_skill,
                embedding=json.dumps(embedding),
                idf_factor=1.0
            )
            db.add(skill)
            db.commit()
            print("✅ Successfully stored embedding in database")

            # Retrieve and verify
            retrieved_skill = db.query(Skill).filter(Skill.skill_name == test_skill).first()
            if retrieved_skill:
                retrieved_embedding = retrieved_skill.get_embedding()
                if len(retrieved_embedding) == len(embedding):
                    print("✅ Successfully retrieved embedding from database")
                else:
                    print("❌ Retrieved embedding has wrong dimensions")
                    return False
            else:
                print("❌ Could not retrieve skill from database")
                return False

        except Exception as e:
            print(f"❌ Error storing/retrieving embedding: {e}")
            return False
        finally:
            db.close()

        return True

    except Exception as e:
        print(f"Error testing embedding creation: {e}")
        return False

async def test_matching_with_embeddings():
    """Test matching with embeddings."""
    db = SessionLocal()

    try:
        print("\n=== Testing Matching with Embeddings ===")

        # Check if OpenAI API key is available
        api_keys = config_manager.get_api_keys()
        if not api_keys.get("openai"):
            print("⚠️  OpenAI API key not found. Skipping embedding-based matching.")
            return True

        print("✅ OpenAI API key found. Testing matching with embeddings...")

        # Test matching service
        matching_service = MatchingService()
        employee = db.query(Employee).first()

        if employee:
            print(f"Testing matching for employee: {employee.name}")

            try:
                # Test with low threshold
                result = await matching_service.match_employee_to_projects(db, employee.id, threshold=0.3)

                if result['matches']:
                    print("✅ Matching with embeddings works!")
                    for i, match in enumerate(result['matches'][:3], 1):
                        project = db.query(Project).filter(Project.id == match['project_id']).first()
                        print(f"  {i}. {project.title} - Match: {match['match_percentage']:.2f}%")
                else:
                    print("❌ No matches found even with low threshold")

            except Exception as e:
                print(f"❌ Error in matching service: {e}")
                return False

        return True

    except Exception as e:
        print(f"Error testing matching with embeddings: {e}")
        return False
    finally:
        db.close()

async def main():
    """Main test function."""
    print("=== Embedding Fix Test ===")

    try:
        # Create test data
        create_test_data()

        # Test embedding creation
        embedding_success = await test_embedding_creation()

        if embedding_success:
            # Test matching with embeddings
            await test_matching_with_embeddings()

            print("\n✅ Embedding creation and matching tests completed!")
            print("\n💡 If embeddings are working, the matching service should now work correctly.")
            print("   If not, you can still use the TF/IDF weighted exact matching as shown in test_tfidf_exact_only.py")
        else:
            print("\n❌ Embedding creation failed.")
            print("\n💡 Solutions:")
            print("   1. Check your OpenAI API key in backend/.env")
            print("   2. Ensure the API key is valid and has credits")
            print("   3. Use the TF/IDF weighted exact matching instead")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())