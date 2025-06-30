#!/usr/bin/env python3
"""
Check Eduard's skills and investigate matching issues.
"""

import sqlite3
import json

def check_eduard_skills():
    conn = sqlite3.connect('project_finder.db')
    cursor = conn.cursor()

    # Get all employees
    cursor.execute('SELECT id, name, skill_list FROM employees')
    employees = cursor.fetchall()

    print("All employees in database:")
    print("-" * 50)

    for employee_id, name, skill_list in employees:
        print(f"ID: {employee_id}")
        print(f"Name: {name}")

        if skill_list:
            try:
                skills = json.loads(skill_list)
                print(f"Skills: {skills}")

                # Check if this is Eduard
                if "Eduard" in name or "eduard" in name.lower():
                    print("*** THIS IS EDUARD ***")
                    print(f"Has 'Migration': {'Migration' in skills}")
                    print(f"Has 'Routing': {'Routing' in skills}")

            except json.JSONDecodeError as e:
                print(f"Error parsing skills: {e}")
        else:
            print("Skills: None")

        print("-" * 30)

    # Check skills table for Migration and Routing
    print("\nChecking skills table for 'Migration' and 'Routing':")
    print("-" * 50)

    cursor.execute("SELECT id, skill_name, embedding FROM skills WHERE skill_name IN ('Migration', 'Routing')")
    skills = cursor.fetchall()

    for skill_id, skill_name, embedding in skills:
        print(f"Skill: {skill_name} (ID: {skill_id})")
        if embedding:
            try:
                embedding_data = json.loads(embedding)
                print(f"  Has embedding: {len(embedding_data) > 0}")
                print(f"  Embedding length: {len(embedding_data)}")
            except json.JSONDecodeError:
                print(f"  Error parsing embedding")
        else:
            print(f"  No embedding")
        print()

    conn.close()

if __name__ == "__main__":
    check_eduard_skills()