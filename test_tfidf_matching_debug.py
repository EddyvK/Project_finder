#!/usr/bin/env python3
"""
Debug test to understand TF-IDF weighted matching issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee, Skill
from backend.matching_service import MatchingService
from backend.tfidf_service import tfidf_service
import asyncio

async def test_tfidf_matching_debug():
    """Debug TF-IDF weighted matching functionality."""

    print("=" * 60)
    print("Debugging TF-IDF Weighted Matching")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Step 1: Check data
        print(f"\n1. Checking data...")
        projects = db.query(Project).all()
        employees = db.query(Employee).all()
        print(f"   Found {len(projects)} projects and {len(employees)} employees")

        # Step 2: Show employee skills
        print(f"\n2. Employee skills:")
        for i, emp in enumerate(employees):
            skills = emp.get_skill_list()
            print(f"   Employee {i+1} ({emp.name}): {skills}")

        # Step 3: Show project requirements
        print(f"\n3. Project requirements:")
        for i, proj in enumerate(projects):
            requirements = proj.get_requirements_list()
            requirements_tf = proj.get_requirements_tf()
            print(f"   Project {i+1} ({proj.title}): {requirements}")
            print(f"   TF data: {requirements_tf}")

        # Step 4: Test manual matching logic
        print(f"\n4. Testing manual matching logic...")
        test_employee = employees[0]  # John Smith
        test_project = projects[0]   # Full-Stack Web Development

        emp_skills = test_employee.get_skill_list()
        proj_requirements = test_project.get_requirements_list()
        requirements_tf = test_project.get_requirements_tf()

        print(f"   Employee skills: {emp_skills}")
        print(f"   Project requirements: {proj_requirements}")
        print(f"   Project TF data: {requirements_tf}")

        # Test exact matching
        print(f"\n   Testing exact matches:")
        exact_matches = []
        for req in proj_requirements:
            for skill in emp_skills:
                if req.lower() == skill.lower():
                    exact_matches.append((req, skill))
                    print(f"     EXACT MATCH: {req} <-> {skill}")

        # Test case-insensitive matching
        print(f"\n   Testing case-insensitive matches:")
        case_matches = []
        for req in proj_requirements:
            for skill in emp_skills:
                if req.lower() == skill.lower():
                    case_matches.append((req, skill))
                    print(f"     CASE MATCH: {req} <-> {skill}")

        # Step 5: Test TF-IDF calculation manually
        print(f"\n5. Testing TF-IDF calculation manually...")
        if exact_matches:
            req, skill = exact_matches[0]
            tf_weight = requirements_tf.get(req, 1)
            idf_factor = tfidf_service.get_skill_idf_factor(req, db)
            tfidf_weight = tf_weight * idf_factor

            print(f"   For requirement '{req}':")
            print(f"     TF weight: {tf_weight}")
            print(f"     IDF factor: {idf_factor:.4f}")
            print(f"     TF-IDF weight: {tfidf_weight:.4f}")

            # Calculate what the match percentage should be
            total_tfidf_weight = 0
            for r in proj_requirements:
                tf = requirements_tf.get(r, 1)
                idf = tfidf_service.get_skill_idf_factor(r, db)
                total_tfidf_weight += tf * idf

            print(f"   Total TF-IDF weight for project: {total_tfidf_weight:.4f}")
            print(f"   If all requirements matched, percentage would be: {(total_tfidf_weight / total_tfidf_weight) * 100:.2f}%")

        # Step 6: Test the matching service with debug logging
        print(f"\n6. Testing matching service with debug...")
        matching_service = MatchingService()

        # Test a simple case where we know there should be matches
        print(f"   Testing John Smith vs Full-Stack Web Development...")

        # Create a simple test case
        test_emp_skills = ['React', 'Node.js', 'JavaScript', 'MongoDB']
        test_proj_reqs = ['React', 'Node.js', 'TypeScript', 'MongoDB']

        print(f"   Employee skills: {test_emp_skills}")
        print(f"   Project requirements: {test_proj_reqs}")

        # Manual matching
        matches = []
        for req in test_proj_reqs:
            if req in test_emp_skills:
                matches.append(req)
                print(f"     MATCH: {req}")
            else:
                print(f"     NO MATCH: {req}")

        print(f"   Manual matches: {matches}")
        print(f"   Manual match percentage: {(len(matches) / len(test_proj_reqs)) * 100:.2f}%")

        print(f"\n✅ Debug test completed!")
        return True

    except Exception as e:
        print(f"❌ Error during debug test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_tfidf_matching_debug())