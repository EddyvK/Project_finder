import requests
import json

def test_new_employee():
    base_url = "http://localhost:8000/api"

    # Test data for new employee
    new_employee_data = {
        "name": "Test Employee",
        "skill_list": ["Python", "JavaScript", "React"],
        "email": "",
        "phone": "",
        "location": "",
        "experience_years": 5,
        "hourly_rate": 0,
        "availability": "",
        "notes": ""
    }

    print("Adding new test employee...")
    print(f"Skills to add: {new_employee_data['skill_list']}")

    response = requests.post(f"{base_url}/employees", json=new_employee_data)

    if response.status_code == 200:
        employee = response.json()
        print(f"✅ Employee created successfully!")
        print(f"Employee ID: {employee['id']}")
        print(f"Employee name: {employee['name']}")
        print(f"Stored skills: {employee['skill_list']}")

        # Check if skills have quotes
        has_quotes = any(skill.startswith('"') and skill.endswith('"') for skill in employee['skill_list'])
        if has_quotes:
            print("❌ Skills are stored with quotes!")
        else:
            print("✅ Skills are stored without quotes")

        # Now test updating the skills
        print(f"\nTesting skill update...")
        updated_skills = ["Python", "JavaScript", "React", "Node.js"]
        update_data = {
            "skill_list": updated_skills
        }

        response = requests.put(f"{base_url}/employees/{employee['id']}", json=update_data)

        if response.status_code == 200:
            updated_employee = response.json()
            print(f"✅ Skills updated successfully!")
            print(f"Updated skills: {updated_employee['skill_list']}")

            # Check if updated skills have quotes
            has_quotes = any(skill.startswith('"') and skill.endswith('"') for skill in updated_employee['skill_list'])
            if has_quotes:
                print("❌ Updated skills still have quotes!")
            else:
                print("✅ Updated skills are stored without quotes")
        else:
            print(f"❌ Error updating skills: {response.status_code}")
            print(f"Response: {response.text}")

        # Clean up - delete the test employee
        print(f"\nCleaning up - deleting test employee...")
        response = requests.delete(f"{base_url}/employees/{employee['id']}")
        if response.status_code == 200:
            print("✅ Test employee deleted")
        else:
            print(f"❌ Error deleting test employee: {response.status_code}")

    else:
        print(f"❌ Error creating employee: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_new_employee()