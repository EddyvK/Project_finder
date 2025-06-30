"""Test script for the externalized scan service."""

import asyncio
import logging
from backend.scan_service import scan_service
from backend.database import SessionLocal
from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_scan_service():
    """Test the externalized scan service."""
    try:
        db = SessionLocal()

        print("Testing scan service...")

        # Test traditional scan
        print("\n=== Traditional Scan ===")
        result = await scan_service.scan_projects(8, db)  # One week
        print(f"Scan result: {result}")

        # Test streaming scan
        print("\n=== Streaming Scan ===")
        stream_count = 0
        async for event in scan_service.scan_projects_stream(8, db):  # One week
            if stream_count < 5:  # Only show first 5 events
                print(f"Event {stream_count + 1}: {event.strip()}")
            stream_count += 1

        print(f"Total streaming events: {stream_count}")

        db.close()

    except Exception as e:
        logger.error(f"Error testing scan service: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_scan_service())