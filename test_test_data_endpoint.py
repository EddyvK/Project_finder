#!/usr/bin/env python3
"""Test script to verify the test data endpoint functionality."""

import requests
import json

def test_test_data_endpoint():
    """Test the test data creation endpoint."""
    print("Testing test data endpoint...")

    try:
        # Test the endpoint
        response = requests.post('http://localhost:8000/api/test-data')

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Test data endpoint works!")
            print(f"Message: {result.get('message')}")
            print(f"Projects created: {result.get('projects_created')}")
            print(f"Employees created: {result.get('employees_created')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server. Make sure the backend is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_test_data_endpoint()