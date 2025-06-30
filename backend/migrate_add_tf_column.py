#!/usr/bin/env python3
"""
Migration script to add requirements_tf column and empty the database for TF/IDF implementation.
"""

import sqlite3
import os
from pathlib import Path

def migrate_add_tf_column():
    """Add requirements_tf column and empty the database."""

    # Get the database path
    db_path = Path("project_finder.db")

    if not db_path.exists():
        print("Database file not found. Creating new database...")
        return

    print("=" * 60)
    print("Migration: Adding requirements_tf column and emptying database")
    print("=" * 60)

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'requirements_tf' not in columns:
            print("Adding requirements_tf column...")
            cursor.execute("ALTER TABLE projects ADD COLUMN requirements_tf TEXT")
            print("✅ requirements_tf column added successfully")
        else:
            print("✅ requirements_tf column already exists")

        # Empty the database as requested
        print("\nEmptying the database...")

        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys=OFF")

        # Empty each table
        for table in tables:
            if table != 'sqlite_sequence':  # Skip the sequence table
                cursor.execute(f"DELETE FROM {table}")
                print(f"   Emptied table: {table}")

        # Reset auto-increment counters
        try:
            cursor.execute("DELETE FROM sqlite_sequence")
        except sqlite3.OperationalError:
            # sqlite_sequence table doesn't exist, which is fine
            print("   sqlite_sequence table doesn't exist, skipping")

        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")

        # Commit the changes
        conn.commit()
        print("✅ Database emptied successfully")

        # Verify the changes
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"\nUpdated projects table columns: {columns}")

        # Check that tables are empty
        for table in tables:
            if table != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   Table {table}: {count} rows")

        conn.close()
        print("\n✅ Migration completed successfully")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_add_tf_column()