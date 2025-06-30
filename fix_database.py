#!/usr/bin/env python3
"""Fix database by adding workload column to the correct database file."""

import sqlite3
import os

def fix_database():
    """Add workload column to the correct database file."""
    db_path = 'project_finder.db'

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if workload column already exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'workload' in columns:
            print("✅ Workload column already exists in projects table")
            conn.close()
            return True

        # Add workload column
        print("🔄 Adding workload column to projects table...")
        cursor.execute("ALTER TABLE projects ADD COLUMN workload VARCHAR(100)")

        # Commit changes
        conn.commit()

        # Verify the column was added
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'workload' in columns:
            print("✅ Workload column successfully added to projects table")
            conn.close()
            return True
        else:
            print("❌ Failed to add workload column")
            conn.close()
            return False

    except Exception as e:
        print(f"❌ Error during database fix: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Fixing database: Add workload field to projects table")
    success = fix_database()
    if success:
        print("🎉 Database fix completed successfully!")
    else:
        print("💥 Database fix failed!")