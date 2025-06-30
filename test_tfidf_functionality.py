#!/usr/bin/env python3
"""
Test to verify TF/IDF functionality works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Skill
from backend.tfidf_service import tfidf_service
import json

def test_tfidf_functionality():
    """Test TF/IDF calculation functionality."""

    print("=" * 60)
    print("Testing TF/IDF Functionality")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Step 1: Check if we have any projects with requirements
        print(f"\n1. Checking existing projects...")
        projects = db.query(Project).filter(Project.requirements_tf.isnot(None)).all()
        print(f"   Found {len(projects)} projects with requirements")

        if len(projects) == 0:
            print("   ⚠️  No projects with requirements found. Creating test data...")

            # Create some test projects with requirements
            test_projects = [
                {
                    "title": "Test Project 1",
                    "description": "A test project for TF/IDF",
                    "requirements_tf": {"Python": 3, "SQL": 2, "JavaScript": 1}
                },
                {
                    "title": "Test Project 2",
                    "description": "Another test project",
                    "requirements_tf": {"Python": 2, "Java": 4, "Docker": 1}
                },
                {
                    "title": "Test Project 3",
                    "description": "Third test project",
                    "requirements_tf": {"JavaScript": 3, "React": 2, "Node.js": 1}
                }
            ]

            for project_data in test_projects:
                project = Project(
                    title=project_data["title"],
                    description=project_data["description"],
                    release_date="01.01.2024",
                    location="Remote",
                    tenderer="Test Company"
                )
                project.set_requirements_tf(project_data["requirements_tf"])
                project.set_requirements_list(list(project_data["requirements_tf"].keys()))
                db.add(project)

            db.commit()
            print("   ✅ Created test projects")

            # Re-query projects
            projects = db.query(Project).filter(Project.requirements_tf.isnot(None)).all()
            print(f"   Now have {len(projects)} projects with requirements")

        # Step 2: Test IDF factor calculation
        print(f"\n2. Testing IDF factor calculation...")
        idf_factors = tfidf_service.calculate_idf_factors(db)
        print(f"   Calculated IDF factors for {len(idf_factors)} skills:")

        for skill, idf in idf_factors.items():
            print(f"     {skill}: {idf:.4f}")

        # Step 3: Test updating skills table
        print(f"\n3. Testing skills table update...")
        updated_factors = tfidf_service.update_skills_idf_factors(db)
        print(f"   Updated {len(updated_factors)} skills in database")

        # Step 4: Verify skills in database
        print(f"\n4. Verifying skills in database...")
        skills = db.query(Skill).all()
        print(f"   Found {len(skills)} skills in database:")

        for skill in skills:
            print(f"     {skill.skill_name}: IDF = {skill.idf_factor:.4f}")

        # Step 5: Test TF-IDF score calculation
        print(f"\n5. Testing TF-IDF score calculation...")
        if projects:
            test_project = projects[0]
            print(f"   Testing with project: {test_project.title}")

            requirements_tf = test_project.get_requirements_tf()
            print(f"   Requirements with TF: {requirements_tf}")

            tfidf_scores = tfidf_service.get_project_tfidf_scores(test_project, db)
            print(f"   TF-IDF scores:")
            for skill, score in tfidf_scores.items():
                print(f"     {skill}: {score:.4f}")

        print(f"\n✅ TF/IDF functionality test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during TF/IDF test: {e}")
        return False

    finally:
        db.close()

if __name__ == "__main__":
    test_tfidf_functionality()