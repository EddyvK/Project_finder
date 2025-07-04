"""Test script for deduplication service."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.deduplication_service import deduplication_service
from backend.models.core_models import Project

def test_deduplication():
    """Test the deduplication service."""
    print("Testing deduplication service...")

    # Get database session
    db = SessionLocal()

    try:
        # Run deduplication
        result = deduplication_service.run_deduplication(db)

        print(f"Deduplication result: {result}")

        if result.get('error'):
            print(f"Error: {result['error']}")
            return False

        print(f"Total projects removed: {result.get('total_removed', 0)}")
        print(f"Duplicate groups processed: {result.get('duplicate_groups_processed', 0)}")

        if result.get('removed_details'):
            print("Removed projects:")
            for detail in result['removed_details']:
                print(f"  - ID {detail['id']}: {detail['title']} ({detail['reason']})")

        return True

    except Exception as e:
        print(f"Error testing deduplication: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_deduplication()
    if success:
        print("Deduplication test completed successfully!")
    else:
        print("Deduplication test failed!")
        sys.exit(1)
