#!/usr/bin/env python3
"""Migration script to add workload column to projects table."""

import sqlite3
import os
import sys

def migrate_add_workload_field():
    """Add workload column to projects table."""
    # Use database file in root directory
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'project_finder.db')

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
        print(f"❌ Error during migration: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Starting migration: Add workload field to projects table")
    success = migrate_add_workload_field()
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)