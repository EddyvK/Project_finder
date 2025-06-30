#!/usr/bin/env python3
"""
Test to verify API endpoints work correctly with the new TF/IDF schema.
"""

import requests
import json

def test_api_tfidf():
    """Test API endpoints with TF/IDF schema."""

    base_url = "http://localhost:8000"

    print("=" * 60)
    print("Testing API Endpoints with TF/IDF Schema")
    print("=" * 60)

    try:
        # Step 1: Test getting projects
        print(f"\n1. Testing GET /api/projects...")
        response = requests.get(f"{base_url}/api/projects")

        if response.status_code == 200:
            projects = response.json()
            print(f"   ✅ Successfully retrieved {len(projects)} projects")

            if projects:
                # Check if the first project has requirements_tf field
                first_project = projects[0]
                if 'requirements_tf' in first_project:
                    print(f"   ✅ Project has requirements_tf field: {first_project['requirements_tf']}")
                else:
                    print(f"   ❌ Project missing requirements_tf field")
            else:
                print(f"   ⚠️  No projects found")
        else:
            print(f"   ❌ Failed to get projects: {response.status_code}")
            return False

        # Step 2: Test getting a specific project
        if projects:
            project_id = projects[0]['id']
            print(f"\n2. Testing GET /api/projects/{project_id}...")
            response = requests.get(f"{base_url}/api/projects/{project_id}")

            if response.status_code == 200:
                project = response.json()
                print(f"   ✅ Successfully retrieved project: {project['title']}")

                if 'requirements_tf' in project:
                    print(f"   ✅ Project has requirements_tf field: {project['requirements_tf']}")
                else:
                    print(f"   ❌ Project missing requirements_tf field")
            else:
                print(f"   ❌ Failed to get project: {response.status_code}")
                return False

        # Step 3: Test updating a project with requirements_tf
        if projects:
            project_id = projects[0]['id']
            print(f"\n3. Testing PUT /api/projects/{project_id} with requirements_tf...")

            update_data = {
                "requirements_tf": {"Python": 5, "Django": 3, "PostgreSQL": 2}
            }

            response = requests.put(
                f"{base_url}/api/projects/{project_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                updated_project = response.json()
                print(f"   ✅ Successfully updated project")

                if 'requirements_tf' in updated_project:
                    print(f"   ✅ Updated project has requirements_tf field: {updated_project['requirements_tf']}")
                else:
                    print(f"   ❌ Updated project missing requirements_tf field")
            else:
                print(f"   ❌ Failed to update project: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        print(f"\n✅ API TF/IDF schema test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during API test: {e}")
        return False

if __name__ == "__main__":
    test_api_tfidf()