"""Test script for matching threshold changes."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_matching_threshold():
    """Test the matching algorithm with the new threshold."""
    print("Testing matching algorithm with new threshold...")

    try:
        # Test matching for employee ID 1
        response = requests.get('http://localhost:8000/api/matches/1')

        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])

            print(f"Status: {response.status_code}")
            print(f"Employee: {data.get('employee_name', 'Unknown')}")
            print(f"Total matches found: {len(matches)}")
            print(f"Threshold used: {data.get('threshold', 'Not specified')}")

            if matches:
                print("\nTop 5 matches:")
                for i, match in enumerate(matches[:5], 1):
                    print(f"  {i}. {match['project_title']}: {match['match_percentage']}%")
                    print(f"     Matching skills: {len(match['matching_skills'])}")
                    print(f"     Missing skills: {len(match['missing_skills'])}")
            else:
                print("\nNo matches found - threshold is working correctly!")

            print(f"\nMissing skills summary: {data.get('missing_skills_summary', [])[:5]}")

        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error testing matching: {e}")

if __name__ == "__main__":
    test_matching_threshold()
