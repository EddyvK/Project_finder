#!/usr/bin/env python3
"""Test the API matching endpoint directly."""

import requests
import json

def test_api_matching():
    """Test the API matching endpoint."""
    print("=== Testing API Matching Endpoint ===")

    base_url = "http://localhost:8000"

    try:
        # First, get employees to find an employee ID
        print("1. Getting employees...")
        response = requests.get(f"{base_url}/api/employees")

        if response.status_code == 200:
            employees = response.json()
            print(f"   ✅ Found {len(employees)} employees")

            if employees:
                employee_id = employees[0]['id']
                employee_name = employees[0]['name']
                print(f"   Testing with employee: {employee_name} (ID: {employee_id})")

                # Test matching endpoint
                print(f"\n2. Testing matching for employee {employee_id}...")
                response = requests.get(f"{base_url}/api/matches/{employee_id}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Matching successful!")
                    print(f"   Employee: {result['employee_name']}")
                    print(f"   Total projects checked: {result['total_projects_checked']}")
                    print(f"   Matches found: {len(result['matches'])}")

                    for i, match in enumerate(result['matches'][:3], 1):
                        print(f"\n   Match {i}: {match['project_title']}")
                        print(f"     Match percentage: {match['match_percentage']}%")
                        print(f"     Matching skills: {match['matching_skills']}")
                        print(f"     Missing skills: {match['missing_skills']}")

                    if result['missing_skills_summary']:
                        print(f"\n   Top missing skills: {result['missing_skills_summary']}")

                else:
                    print(f"   ❌ Matching failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                print("   ⚠️  No employees found")
        else:
            print(f"   ❌ Failed to get employees: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_matching()