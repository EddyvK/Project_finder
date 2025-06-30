#!/usr/bin/env python3
"""
Test script to verify the matching fixes work correctly.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.matching_service import MatchingService

async def test_matching_fixes():
    """Test that matching produces correct results with fixes."""

    print("=" * 60)
    print("Testing Matching Fixes")
    print("=" * 60)

    db = SessionLocal()
    matching_service = MatchingService()

    try:
        # Get a real employee
        employee = db.query(Employee).filter(
            ~Employee.name.in_(["John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis"])
        ).first()

        if not employee:
            print("No real employees found")
            return

        print(f"Testing with employee: {employee.name}")
        print(f"Employee skills: {employee.get_skill_list()}")

        # Run matching
        result = await matching_service.match_employee_to_projects(db, employee.id)

        if result and result.get('matches'):
            print(f"\nFound {len(result['matches'])} matches")

            # Check first few matches for issues
            for i, match in enumerate(result['matches'][:3]):
                print(f"\nMatch #{i+1}: {match['project_title']}")
                print(f"  Match percentage: {match['match_percentage']}%")
                print(f"  Matching skills: {match['matching_skills']}")
                print(f"  Missing skills: {match['missing_skills']}")

                # Check for duplicates in matching_skills
                matching_set = set(match['matching_skills'])
                if len(match['matching_skills']) != len(matching_set):
                    print(f"  ⚠️  DUPLICATES FOUND: {len(match['matching_skills'])} items, {len(matching_set)} unique")
                else:
                    print(f"  ✅ No duplicates in matching skills")

                # Check if matching_skills contains project requirements (not employee skills)
                employee_skills = set(emp_skill.lower() for emp_skill in employee.get_skill_list())
                matching_skills_lower = set(skill.lower() for skill in match['matching_skills'])

                # Most matching skills should NOT be in employee skills (they should be project requirements)
                overlap = matching_skills_lower.intersection(employee_skills)
                if len(overlap) > len(matching_skills_lower) * 0.5:  # If more than 50% overlap
                    print(f"  ⚠️  SUSPICIOUS: Many matching skills are employee skills: {overlap}")
                else:
                    print(f"  ✅ Matching skills appear to be project requirements")
        else:
            print("No matches found")

    except Exception as e:
        print(f"Error testing matching: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_matching_fixes())