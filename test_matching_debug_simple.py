#!/usr/bin/env python3
"""Simple test to debug the matching service directly."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.matching_service import MatchingService
import asyncio

async def test_matching_service():
    """Test the matching service directly."""
    print("=== Testing Matching Service Directly ===")

    try:
        db = SessionLocal()

        # Get test data
        employees = db.query(Employee).all()
        projects = db.query(Project).all()

        print(f"Found {len(employees)} employees and {len(projects)} projects")

        if not employees or not projects:
            print("❌ No test data found. Please run the test data creation first.")
            return

        # Test first employee
        employee = employees[0]
        print(f"\nTesting employee: {employee.name}")
        print(f"Employee skills: {employee.get_skill_list()}")

        # Initialize matching service
        matching_service = MatchingService()

        # Call matching service directly
        result = await matching_service.match_employee_to_projects(db, employee.id)

        print(f"\nMatching result:")
        print(f"Employee: {result['employee_name']}")
        print(f"Total projects checked: {result['total_projects_checked']}")
        print(f"Matches found: {len(result['matches'])}")

        for i, match in enumerate(result['matches'][:3], 1):
            print(f"\nMatch {i}: {match['project_title']}")
            print(f"  Match percentage: {match['match_percentage']}%")
            print(f"  Matching skills: {match['matching_skills']}")
            print(f"  Missing skills: {match['missing_skills']}")

        if result['missing_skills_summary']:
            print(f"\nTop missing skills: {result['missing_skills_summary']}")

        db.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_matching_service())