#!/usr/bin/env python3
"""
Migration script to remove the requirements column from the projects table.
This migration removes the redundant requirements field since requirements_tf contains all necessary data.
"""

import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from config_manager import config_manager

def migrate_remove_requirements_column():
    """Remove the requirements column from the projects table."""
    try:
        # Get database URL from config
        db_url = config_manager.get_database_url()
        engine = create_engine(db_url)

        # Create inspector to check table structure
        inspector = inspect(engine)

        # Check if projects table exists
        if not inspector.has_table("projects"):
            print("❌ Projects table does not exist. Cannot perform migration.")
            return False

        # Get current columns
        columns = [col['name'] for col in inspector.get_columns("projects")]
        print(f"Current columns in projects table: {columns}")

        # Check if requirements column exists
        if 'requirements' not in columns:
            print("✅ Requirements column does not exist. Migration not needed.")
            return True

        print("Migration: Removing requirements column from projects table")

        # Create a session to perform the migration
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Remove the requirements column
            db.execute(text("ALTER TABLE projects DROP COLUMN requirements"))
            db.commit()
            print("✅ Requirements column removed successfully")

            # Verify the column was removed
            inspector = inspect(engine)
            columns_after = [col['name'] for col in inspector.get_columns("projects")]
            print(f"Columns after migration: {columns_after}")

            if 'requirements' not in columns_after:
                print("✅ Migration completed successfully!")
                return True
            else:
                print("❌ Requirements column still exists after migration")
                return False

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    success = migrate_remove_requirements_column()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("The requirements column has been removed from the projects table.")
        print("All functionality now uses the requirements_tf field.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)