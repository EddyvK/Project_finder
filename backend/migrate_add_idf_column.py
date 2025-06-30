#!/usr/bin/env python3
"""
Migration script to add idf_factor column to skills table for TF/IDF implementation.
"""

import sqlite3
import os
from pathlib import Path

def migrate_add_idf_column():
    """Add idf_factor column to skills table."""

    # Get the database path
    db_path = Path("project_finder.db")

    if not db_path.exists():
        print("Database file not found. Creating new database...")
        return

    print("=" * 60)
    print("Migration: Adding idf_factor column to skills table")
    print("=" * 60)

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(skills)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'idf_factor' not in columns:
            print("Adding idf_factor column...")
            cursor.execute("ALTER TABLE skills ADD COLUMN idf_factor REAL")
            print("✅ idf_factor column added successfully")
        else:
            print("✅ idf_factor column already exists")

        # Commit the changes
        conn.commit()

        # Verify the changes
        cursor.execute("PRAGMA table_info(skills)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"\nUpdated skills table columns: {columns}")

        conn.close()
        print("\n✅ Migration completed successfully")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_add_idf_column()