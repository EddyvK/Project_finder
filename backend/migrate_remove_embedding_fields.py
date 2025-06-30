"""
Migration script to remove embedding_fields column from projects table
and normalize the database structure to use skills table as lookup.
"""

import sqlite3
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to the path for direct execution
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from database import SessionLocal, engine
    from logger_config import setup_logging
else:
    # When imported as a module
    from backend.database import SessionLocal, engine
    from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def migrate_database():
    """Remove embedding_fields column from projects table."""
    try:
        # Connect to the database
        db_path = Path("project_finder.db")
        if not db_path.exists():
            logger.warning("Database file not found. Creating new database.")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Starting migration to remove embedding_fields column...")

        # Check if embedding_fields column exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'embedding_fields' not in columns:
            logger.info("embedding_fields column does not exist. Migration not needed.")
            return

        # Create a backup of the current table
        logger.info("Creating backup of projects table...")
        cursor.execute("""
            CREATE TABLE projects_backup AS
            SELECT id, title, description, release_date, start_date, location,
                   tenderer, project_id, requirements, rate, url, budget, duration, last_scan
            FROM projects
        """)

        # Drop the original table
        cursor.execute("DROP TABLE projects")

        # Create the new table without embedding_fields
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                release_date VARCHAR(20),
                start_date VARCHAR(20),
                location VARCHAR(200),
                tenderer VARCHAR(200),
                project_id VARCHAR(100),
                requirements TEXT,
                rate VARCHAR(100),
                url VARCHAR(1000),
                budget VARCHAR(100),
                duration VARCHAR(100),
                last_scan DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX ix_projects_id ON projects (id)")
        cursor.execute("CREATE INDEX ix_projects_title ON projects (title)")
        cursor.execute("CREATE INDEX ix_projects_project_id ON projects (project_id)")

        # Copy data back
        cursor.execute("""
            INSERT INTO projects (id, title, description, release_date, start_date,
                                location, tenderer, project_id, requirements, rate,
                                url, budget, duration, last_scan)
            SELECT id, title, description, release_date, start_date, location,
                   tenderer, project_id, requirements, rate, url, budget, duration, last_scan
            FROM projects_backup
        """)

        # Drop backup table
        cursor.execute("DROP TABLE projects_backup")

        # Commit changes
        conn.commit()

        logger.info("Migration completed successfully!")
        logger.info("embedding_fields column has been removed from projects table.")
        logger.info("Project requirement vectors will now be obtained through skills table lookup.")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def migrate_remove_embedding_fields():
    """Remove embedding_fields column from employees table."""
    db = SessionLocal()
    try:
        logger.info("Starting migration to remove embedding_fields column...")

        # Check if the column exists
        result = db.execute(text("""
            SELECT name FROM pragma_table_info('employees')
            WHERE name = 'embedding_fields'
        """))

        if result.fetchone():
            logger.info("Found embedding_fields column, removing it...")

            # Remove the column (SQLite doesn't support DROP COLUMN directly, so we recreate the table)
            db.execute(text("""
                CREATE TABLE employees_new (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    skill_list TEXT,
                    experience_years INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """))

            # Copy data from old table to new table
            db.execute(text("""
                INSERT INTO employees_new (id, name, skill_list, experience_years, created_at, updated_at)
                SELECT id, name, skill_list, experience_years, created_at, updated_at
                FROM employees
            """))

            # Drop old table and rename new table
            db.execute(text("DROP TABLE employees"))
            db.execute(text("ALTER TABLE employees_new RENAME TO employees"))

            # Recreate indexes
            db.execute(text("CREATE INDEX ix_employees_id ON employees (id)"))
            db.execute(text("CREATE INDEX ix_employees_name ON employees (name)"))

            logger.info("Successfully removed embedding_fields column from employees table")
        else:
            logger.info("embedding_fields column does not exist, no migration needed")

        db.commit()

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database()
    migrate_remove_embedding_fields()