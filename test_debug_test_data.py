#!/usr/bin/env python3
"""Debug script to test test data creation directly."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.init_db import create_test_data

def test_create_test_data():
    """Test creating test data directly."""
    print("Testing test data creation directly...")

    try:
        db = SessionLocal()

        # Check if test data already exists
        existing_projects = db.query(Project).filter(Project.tenderer == "Test").count()
        print(f"Existing test projects: {existing_projects}")

        if existing_projects > 0:
            print("Test data already exists, clearing it first...")
            db.query(Project).filter(Project.tenderer == "Test").delete()
            db.query(Employee).delete()
            db.commit()

        # Create test data
        create_test_data(db)

        # Check results
        project_count = db.query(Project).filter(Project.tenderer == "Test").count()
        employee_count = db.query(Employee).count()

        print(f"✅ Test data created successfully!")
        print(f"Projects created: {project_count}")
        print(f"Employees created: {employee_count}")

        # Show some details
        projects = db.query(Project).filter(Project.tenderer == "Test").all()
        for project in projects:
            print(f"  - {project.title}: {project.get_requirements_list()}")

        db.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create_test_data()