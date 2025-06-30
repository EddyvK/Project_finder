#!/usr/bin/env python3
"""
Script to fix empty embeddings by calling the rebuild embeddings API endpoint.
"""

import requests
import json
import time

def fix_embeddings():
    """Call the rebuild embeddings API to fix empty embeddings."""

    print("=" * 60)
    print("Fixing Empty Embeddings")
    print("=" * 60)

    # API endpoint
    url = "http://localhost:8000/api/embeddings/rebuild"

    try:
        print("Calling rebuild embeddings API...")
        print("This may take several minutes depending on the number of skills...")

        # Make the API call
        response = requests.post(url, timeout=300)  # 5 minute timeout

        if response.status_code == 200:
            result = response.json()
            print("\n✅ Embeddings rebuild completed successfully!")
            print(f"Skills processed: {result.get('skills_processed', 0)}")
            print(f"Employees processed: {result.get('employees_processed', 0)}")
            print(f"Total unique skills: {result.get('total_unique_skills', 0)}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("\n❌ Request timed out. The rebuild process may still be running.")
        print("Check the backend logs for progress.")
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to the backend server.")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    fix_embeddings()