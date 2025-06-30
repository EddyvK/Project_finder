import sqlite3
import json

def check_employees():
    conn = sqlite3.connect('project_finder.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, name, skill_list, updated_at FROM employees')
    rows = cursor.fetchall()

    print("Employee data in database:")
    print("-" * 50)
    for row in rows:
        employee_id, name, skill_list, updated_at = row
        print(f"ID: {employee_id}")
        print(f"Name: {name}")
        print(f"Skills (raw): {skill_list}")

        if skill_list:
            try:
                skills = json.loads(skill_list)
                print(f"Skills (parsed): {skills}")
            except json.JSONDecodeError as e:
                print(f"Error parsing skills: {e}")
        else:
            print("Skills: None")

        print(f"Updated: {updated_at}")
        print("-" * 30)

    conn.close()

if __name__ == "__main__":
    check_employees()