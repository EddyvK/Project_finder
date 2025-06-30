#!/usr/bin/env python3
"""
Script to check date formats in the database.
"""

from backend.database import SessionLocal
from backend.models.core_models import Project
from datetime import datetime

def check_dates():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Checking Date Formats in Database")
        print("=" * 60)

        # Check all projects
        print("\nAll Projects with Release Dates:")
        projects = db.query(Project).all()
        for p in projects:
            print(f"  Project {p.id}: {p.title}")
            print(f"    Release Date: '{p.release_date}' (type: {type(p.release_date)})")
            print(f"    Start Date: '{p.start_date}' (type: {type(p.start_date)})")
            print(f"    Tenderer: {p.tenderer}")
            print()

        # Check test projects specifically
        print("\nTest Projects (Tenderer = 'Test'):")
        test_projects = db.query(Project).filter(Project.tenderer == "Test").all()
        for p in test_projects:
            print(f"  Project {p.id}: {p.title}")
            print(f"    Release Date: '{p.release_date}' (type: {type(p.release_date)})")
            print(f"    Start Date: '{p.start_date}' (type: {type(p.start_date)})")
            print()

        # Check non-test projects
        print("\nNon-Test Projects:")
        non_test_projects = db.query(Project).filter(Project.tenderer != "Test").all()
        for p in non_test_projects:
            print(f"  Project {p.id}: {p.title}")
            print(f"    Release Date: '{p.release_date}' (type: {type(p.release_date)})")
            print(f"    Start Date: '{p.start_date}' (type: {type(p.start_date)})")
            print(f"    Tenderer: {p.tenderer}")
            print()

    finally:
        db.close()

if __name__ == "__main__":
    check_dates()