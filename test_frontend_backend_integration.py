#!/usr/bin/env python3
"""Test frontend-backend integration for matching functionality."""

import requests
import json
import time

def test_frontend_backend_integration():
    """Test that the frontend can access the backend API correctly."""
    print("=== Testing Frontend-Backend Integration ===")

    base_url = "http://localhost:8000"

    try:
        # 1. Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("   ✅ Backend is healthy")
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return

        # 2. Create test data
        print("\n2. Creating test data...")
        response = requests.post(f"{base_url}/api/test-data")
        if response.status_code == 200:
            print("   ✅ Test data created successfully")
        else:
            print(f"   ❌ Failed to create test data: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        # 3. Wait a moment for data to be processed
        print("\n3. Waiting for data processing...")
        time.sleep(2)

        # 4. Get employees
        print("\n4. Getting employees...")
        response = requests.get(f"{base_url}/api/employees")
        if response.status_code == 200:
            employees = response.json()
            print(f"   ✅ Found {len(employees)} employees")

            if employees:
                employee_id = employees[0]['id']
                employee_name = employees[0]['name']
                print(f"   Testing with employee: {employee_name} (ID: {employee_id})")

                # 5. Test matching
                print(f"\n5. Testing matching for employee {employee_id}...")
                response = requests.get(f"{base_url}/api/matches/{employee_id}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Matching successful!")
                    print(f"   Employee: {result['employee_name']}")
                    print(f"   Total projects checked: {result['total_projects_checked']}")
                    print(f"   Matches found: {len(result['matches'])}")

                    if result['matches']:
                        for i, match in enumerate(result['matches'][:3], 1):
                            print(f"\n   Match {i}: {match['project_title']}")
                            print(f"     Match percentage: {match['match_percentage']}%")
                            print(f"     Matching skills: {match['matching_skills']}")
                            print(f"     Missing skills: {match['missing_skills']}")

                        # Check if we have any non-zero matches
                        non_zero_matches = [m for m in result['matches'] if m['match_percentage'] > 0]
                        if non_zero_matches:
                            print(f"\n   ✅ Found {len(non_zero_matches)} projects with non-zero matches!")
                        else:
                            print(f"\n   ⚠️  All matches are 0% - this might indicate an issue")
                    else:
                        print("   ⚠️  No matches found")

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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_backend_integration()