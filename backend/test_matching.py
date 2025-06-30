"""
Test script for the improved matching algorithm.
This file is now considered STABLE and should not be changed unless explicitly requested.
"""

import asyncio
import logging
from backend.database import SessionLocal
from backend.matching_service import MatchingService
from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_matching():
    """Test the matching algorithm with John Smith."""
    try:
        db = SessionLocal()
        matching_service = MatchingService()

        # Test matching for John Smith (ID 1)
        result = await matching_service.match_employee_to_projects(db, 1)

        print(f"\nMatching Results for {result['employee_name']}")
        print(f"Total projects checked: {result['total_projects_checked']}")
        print(f"Missing skills summary: {result['missing_skills_summary']}")

        print("\nCompatible Projects")
        for i, match in enumerate(result['matches'], 1):
            print(f"#{i}")
            print(f"{match['project_title']}")
            print(f"Match: {match['match_percentage']}%")
            print(f"Matching: {', '.join(match['matching_skills'])}")
            print(f"Missing: {', '.join(match['missing_skills']) if match['missing_skills'] else 'None'}")
            print()

        db.close()

    except Exception as e:
        logger.error(f"Error testing matching: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_matching())