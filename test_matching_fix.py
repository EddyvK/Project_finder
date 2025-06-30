#!/usr/bin/env python3
"""
Test script to verify that matching scoring is working correctly.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.matching_service import MatchingService

async def test_matching_fix():
    """Test that matching produces correct scores."""

    print("=" * 60)
    print("Testing Matching Score Fix")
    print("=" * 60)

    db = SessionLocal()
    matching_service = MatchingService()

    try:
        # Get test employee (John Smith has React, Node.js, JavaScript, MongoDB)
        employee = db.query(Employee).filter(Employee.name == "John Smith").first()
        if not employee:
            print("❌ Test employee 'John Smith' not found")
            return False

        print(f"Testing employee: {employee.name}")
        print(f"Employee skills: {employee.get_skill_list()}")

        # Get all projects
        projects = db.query(Project).all()
        print(f"Found {len(projects)} projects to test")

        # Test matching
        match_result = await matching_service.match_employee_to_projects(db, employee.id)

        if not match_result:
            print("❌ No match result returned")
            return False

        print(f"\nMatch Results for {match_result['employee_name']}:")
        print(f"Total projects checked: {match_result['total_projects_checked']}")

        for match in match_result['matches']:
            print(f"\nProject: {match['project_title']}")
            print(f"  Match Percentage: {match['match_percentage']}%")
            print(f"  Matching Skills: {match['matching_skills']}")
            print(f"  Missing Skills: {match['missing_skills']}")

            # Check if all requirements are matched
            project = db.query(Project).filter(Project.id == match['project_id']).first()
            if project:
                project_requirements = project.get_requirements_list()
                if len(match['missing_skills']) == 0:
                    print(f"  ✅ All {len(project_requirements)} requirements matched - Score should be 100%")
                    if match['match_percentage'] == 100.0:
                        print(f"  ✅ CORRECT: Score is 100%")
                    else:
                        print(f"  ❌ ERROR: Score is {match['match_percentage']}% but should be 100%")
                else:
                    print(f"  📊 {len(match['matching_skills'])}/{len(project_requirements)} requirements matched")

        print(f"\n✅ Matching test completed!")
        return True

    except Exception as e:
        print(f"❌ Error during matching test: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_matching_fix())