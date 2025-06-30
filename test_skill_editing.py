import requests
import json

def test_skill_editing():
    base_url = "http://localhost:8000/api"

    # Test data for new employee
    new_employee_data = {
        "name": "Test Skill Editing",
        "skill_list": ["Python", "JavaScript", "React", "Node.js"],
        "email": "",
        "phone": "",
        "location": "",
        "experience_years": 3,
        "hourly_rate": 0,
        "availability": "",
        "notes": ""
    }

    print("1. Creating test employee...")
    response = requests.post(f"{base_url}/employees", json=new_employee_data)

    if response.status_code != 200:
        print(f"❌ Error creating employee: {response.status_code}")
        return

    employee = response.json()
    employee_id = employee['id']
    print(f"✅ Employee created with ID: {employee_id}")
    print(f"Initial skills: {employee['skill_list']}")

    # Test 1: Remove a skill
    print(f"\n2. Testing skill removal...")
    skills_with_removal = ["Python", "JavaScript", "React"]  # Removed "Node.js"
    update_data = {"skill_list": skills_with_removal}

    response = requests.put(f"{base_url}/employees/{employee_id}", json=update_data)

    if response.status_code == 200:
        updated_employee = response.json()
        print(f"✅ Skills after removal: {updated_employee['skill_list']}")
        if "Node.js" not in updated_employee['skill_list']:
            print("✅ Node.js successfully removed")
        else:
            print("❌ Node.js was not removed")
    else:
        print(f"❌ Error updating skills: {response.status_code}")

    # Test 2: Edit a skill name
    print(f"\n3. Testing skill editing...")
    skills_with_edit = ["Python", "JavaScript", "React.js"]  # Changed "React" to "React.js"
    update_data = {"skill_list": skills_with_edit}

    response = requests.put(f"{base_url}/employees/{employee_id}", json=update_data)

    if response.status_code == 200:
        updated_employee = response.json()
        print(f"✅ Skills after editing: {updated_employee['skill_list']}")
        if "React.js" in updated_employee['skill_list'] and "React" not in updated_employee['skill_list']:
            print("✅ React successfully changed to React.js")
        else:
            print("❌ React was not changed to React.js")
    else:
        print(f"❌ Error updating skills: {response.status_code}")

    # Test 3: Add new skills
    print(f"\n4. Testing skill addition...")
    skills_with_addition = ["Python", "JavaScript", "React.js", "TypeScript", "Docker"]
    update_data = {"skill_list": skills_with_addition}

    response = requests.put(f"{base_url}/employees/{employee_id}", json=update_data)

    if response.status_code == 200:
        updated_employee = response.json()
        print(f"✅ Skills after addition: {updated_employee['skill_list']}")
        if "TypeScript" in updated_employee['skill_list'] and "Docker" in updated_employee['skill_list']:
            print("✅ TypeScript and Docker successfully added")
        else:
            print("❌ TypeScript and Docker were not added")
    else:
        print(f"❌ Error updating skills: {response.status_code}")

    # Test 4: Remove all skills
    print(f"\n5. Testing complete skill removal...")
    empty_skills = []
    update_data = {"skill_list": empty_skills}

    response = requests.put(f"{base_url}/employees/{employee_id}", json=update_data)

    if response.status_code == 200:
        updated_employee = response.json()
        print(f"✅ Skills after complete removal: {updated_employee['skill_list']}")
        if len(updated_employee['skill_list']) == 0:
            print("✅ All skills successfully removed")
        else:
            print("❌ Not all skills were removed")
    else:
        print(f"❌ Error updating skills: {response.status_code}")

    # Clean up
    print(f"\n6. Cleaning up - deleting test employee...")
    response = requests.delete(f"{base_url}/employees/{employee_id}")
    if response.status_code == 200:
        print("✅ Test employee deleted")
    else:
        print(f"❌ Error deleting test employee: {response.status_code}")

if __name__ == "__main__":
    test_skill_editing()