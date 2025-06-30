import sqlite3
import json

def clean_skill(skill):
    # Remove leading/trailing whitespace and quotes
    return skill.strip().strip('"').strip("'")

def fix_employee_skills(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, skill_list FROM employees')
    employees = cursor.fetchall()
    fixed_count = 0
    for emp_id, skill_list in employees:
        if not skill_list:
            continue
        try:
            skills = json.loads(skill_list)
            cleaned_skills = [clean_skill(skill) for skill in skills]
            if skills != cleaned_skills:
                cursor.execute('UPDATE employees SET skill_list = ? WHERE id = ?', (json.dumps(cleaned_skills, ensure_ascii=False), emp_id))
                print(f"Fixed employee ID {emp_id}: {skills} -> {cleaned_skills}")
                fixed_count += 1
        except Exception as e:
            print(f"Error fixing employee ID {emp_id}: {e}")
    conn.commit()
    print(f"Fixed {fixed_count} employees with quoted or malformed skills.")

def fix_skills_table(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, skill_name FROM skills')
    skills = cursor.fetchall()
    fixed_count = 0
    groups = {}
    # Group skill IDs by cleaned name
    for skill_id, skill_name in skills:
        cleaned_name = clean_skill(skill_name)
        groups.setdefault(cleaned_name, []).append((skill_id, skill_name))
    # For each group, keep one, delete the rest, then update the keeper
    for cleaned_name, id_name_list in groups.items():
        # Sort by ID to keep the lowest
        id_name_list.sort()
        keeper_id, keeper_orig_name = id_name_list[0]
        # Delete all others first
        for dup_id, dup_name in id_name_list[1:]:
            cursor.execute('DELETE FROM skills WHERE id = ?', (dup_id,))
            print(f"Removed duplicate skill ID {dup_id}: {dup_name}")
        # Now update the keeper
        if keeper_orig_name != cleaned_name:
            cursor.execute('UPDATE skills SET skill_name = ? WHERE id = ?', (cleaned_name, keeper_id))
            print(f"Updated skill ID {keeper_id}: {keeper_orig_name} -> {cleaned_name}")
            fixed_count += 1
    conn.commit()
    print(f"Fixed {fixed_count} skills and removed duplicates in skills table.")

def main():
    conn = sqlite3.connect('../project_finder.db')
    fix_employee_skills(conn)
    fix_skills_table(conn)
    conn.close()

if __name__ == "__main__":
    main()