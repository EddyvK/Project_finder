#!/usr/bin/env python3
"""
Test to verify TF-IDF weighted matching algorithm works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee, Skill
from backend.matching_service import MatchingService
from backend.tfidf_service import tfidf_service
import asyncio

async def test_tfidf_matching():
    """Test TF-IDF weighted matching functionality."""

    print("=" * 60)
    print("Testing TF-IDF Weighted Matching")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Step 1: Check if we have projects and employees
        print(f"\n1. Checking existing data...")
        projects = db.query(Project).all()
        employees = db.query(Employee).all()
        print(f"   Found {len(projects)} projects and {len(employees)} employees")

        if len(projects) == 0 or len(employees) == 0:
            print("   ❌ Need both projects and employees for testing")
            return False

        # Step 2: Ensure TF-IDF factors are calculated
        print(f"\n2. Ensuring TF-IDF factors are calculated...")
        idf_factors = tfidf_service.update_skills_idf_factors(db)
        print(f"   Updated {len(idf_factors)} skills with IDF factors")

        # Step 3: Test matching with TF-IDF weighting
        print(f"\n3. Testing TF-IDF weighted matching...")
        matching_service = MatchingService()

        # Test with the first employee
        test_employee = employees[0]
        print(f"   Testing with employee: {test_employee.name}")
        print(f"   Employee skills: {test_employee.get_skill_list()}")

        # Get matches
        matches = await matching_service.match_employee_to_projects(db, test_employee.id)

        if matches and matches.get('matches'):
            print(f"   Found {len(matches['matches'])} project matches")

            # Show top 3 matches with details
            for i, match in enumerate(matches['matches'][:3]):
                print(f"\n   Match {i+1}: {match['project_title']}")
                print(f"     Match percentage: {match['match_percentage']}%")
                print(f"     Matching skills: {match['matching_skills']}")
                print(f"     Missing skills: {match['missing_skills']}")

                # Get the project to show TF-IDF details
                project = db.query(Project).filter(Project.id == match['project_id']).first()
                if project:
                    requirements_tf = project.get_requirements_tf()
                    print(f"     Project requirements with TF: {requirements_tf}")

                    # Show TF-IDF weights for each requirement
                    print(f"     TF-IDF weights:")
                    for req in project.get_requirements_list():
                        tf_weight = requirements_tf.get(req, 1)
                        idf_factor = tfidf_service.get_skill_idf_factor(req, db)
                        tfidf_weight = tf_weight * idf_factor
                        print(f"       {req}: TF={tf_weight}, IDF={idf_factor:.4f}, TF-IDF={tfidf_weight:.4f}")
        else:
            print(f"   No matches found")

        # Step 4: Test specific project matching to see TF-IDF weighting in action
        print(f"\n4. Testing specific project matching...")
        if projects:
            test_project = projects[0]
            print(f"   Testing project: {test_project.title}")
            print(f"   Requirements: {test_project.get_requirements_list()}")
            print(f"   Requirements TF: {test_project.get_requirements_tf()}")

            # Test matching this specific project
            match_result = await matching_service._match_project(
                db, test_project, test_employee.get_skill_list(), {}, 0.8
            )

            if match_result:
                print(f"   Match result: {match_result['match_percentage']}%")
                print(f"   Matching skills: {match_result['matching_skills']}")
                print(f"   Missing skills: {match_result['missing_skills']}")

        print(f"\n✅ TF-IDF weighted matching test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during TF-IDF matching test: {e}")
        return False

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_tfidf_matching())