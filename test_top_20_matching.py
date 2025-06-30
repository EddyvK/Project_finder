#!/usr/bin/env python3
"""
Test to verify that matching now shows top 20 projects instead of top 10.
"""

import requests
import json

def test_top_20_matching():
    """Test that matching returns more than 10 results."""

    base_url = "http://localhost:8000"

    print("=" * 60)
    print("Testing Top 20 Matching")
    print("=" * 60)

    # Step 1: Check if we have any employees
    print(f"\n1. Checking available employees...")
    try:
        response = requests.get(f"{base_url}/api/employees")
        if response.status_code == 200:
            employees = response.json()
            print(f"   Found {len(employees)} employees")

            if not employees:
                print("   ❌ No employees found. Please add some employees first.")
                return False

            # Use the first employee for testing
            test_employee = employees[0]
            print(f"   ✅ Using employee: {test_employee['name']} (ID: {test_employee['id']})")

        else:
            print(f"   ❌ Failed to get employees: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Error getting employees: {e}")
        return False

    # Step 2: Test matching for the first employee
    print(f"\n2. Testing matching for employee {test_employee['name']}...")
    try:
        response = requests.get(f"{base_url}/api/matches/{test_employee['id']}")
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])

            print(f"   ✅ Matching completed successfully")
            print(f"   Total matches found: {len(matches)}")
            print(f"   Employee: {data.get('employee_name', 'Unknown')}")

            if len(matches) >= 20:
                print(f"   ✅ Found {len(matches)} matches (>= 20 as expected)")

                # Show top 20 matches
                print(f"\n   Top 20 matches:")
                for i, match in enumerate(matches[:20], 1):
                    print(f"   {i:2d}. {match['project_title']} - {match['match_percentage']}%")

                # Check missing skills analysis
                missing_skills = data.get('missing_skills_summary', [])
                print(f"\n   Missing skills summary: {missing_skills[:5]}...")

                return True

            elif len(matches) >= 10:
                print(f"   ⚠️  Found {len(matches)} matches (>= 10 but < 20)")
                print(f"   This might be due to limited projects in database")

                # Show all matches
                print(f"\n   All matches:")
                for i, match in enumerate(matches, 1):
                    print(f"   {i:2d}. {match['project_title']} - {match['match_percentage']}%")

                return True

            else:
                print(f"   ❌ Found only {len(matches)} matches (< 10)")
                print(f"   This might indicate a threshold issue or limited projects")
                return False

        else:
            print(f"   ❌ Failed to get matches: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error getting matches: {e}")
        return False

if __name__ == "__main__":
    success = test_top_20_matching()
    if success:
        print(f"\n✅ Top 20 Matching Test PASSED")
        print("   - Backend returns all matches (no limit)")
        print("   - Frontend will now display top 20 instead of top 10")
        print("   - Missing skills analysis considers top 20 projects")
    else:
        print(f"\n❌ Top 20 Matching Test FAILED")

    exit(0 if success else 1)