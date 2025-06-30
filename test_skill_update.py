import requests
import json

def test_skill_update():
    base_url = "http://localhost:8000/api"

    # First, get current employees
    print("Getting current employees...")
    response = requests.get(f"{base_url}/employees")
    if response.status_code != 200:
        print(f"Error getting employees: {response.status_code}")
        return

    employees = response.json()
    print(f"Found {len(employees)} employees")

    if not employees:
        print("No employees found to test with")
        return

    # Test updating skills for the first employee
    employee = employees[0]
    employee_id = employee['id']
    current_skills = employee['skill_list']

    print(f"\nTesting skill update for employee: {employee['name']} (ID: {employee_id})")
    print(f"Current skills: {current_skills}")

    # Add a test skill
    new_skills = current_skills + ["TestSkill123"]
    print(f"New skills to set: {new_skills}")

    # Update the skills
    update_data = {
        "skill_list": new_skills
    }

    print(f"\nSending PUT request to {base_url}/employees/{employee_id}")
    print(f"Update data: {json.dumps(update_data, indent=2)}")

    response = requests.put(f"{base_url}/employees/{employee_id}", json=update_data)

    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        updated_employee = response.json()
        print(f"Updated employee skills: {updated_employee['skill_list']}")

        # Verify the update
        if "TestSkill123" in updated_employee['skill_list']:
            print("✅ Skill update successful!")
        else:
            print("❌ Skill update failed - TestSkill123 not found in updated skills")
    else:
        print(f"❌ Error updating skills: {response.status_code}")
        print(f"Response: {response.text}")

    # Now remove the test skill to restore original state
    print(f"\nRestoring original skills...")
    restore_data = {
        "skill_list": current_skills
    }

    response = requests.put(f"{base_url}/employees/{employee_id}", json=restore_data)

    if response.status_code == 200:
        restored_employee = response.json()
        print(f"Restored employee skills: {restored_employee['skill_list']}")
        print("✅ Skills restored successfully")
    else:
        print(f"❌ Error restoring skills: {response.status_code}")

if __name__ == "__main__":
    test_skill_update()