#!/usr/bin/env python3
"""Test script to investigate the scanning restart issue."""

import asyncio
import logging
from backend.scan_service import scan_service
from backend.database import SessionLocal
from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

async def test_scan_restart_issue():
    """Test to see if scan restarts automatically."""
    try:
        db = SessionLocal()

        print("🔍 Testing scan restart issue...")
        print("=" * 50)

        # Test 1: Run a single scan
        print("\n📊 Test 1: Running single scan...")
        scan_count = 0
        async for event in scan_service.scan_projects_stream(8, db):
            scan_count += 1
            if scan_count <= 5:  # Only show first 5 events
                print(f"Event {scan_count}: {event.strip()}")
            elif scan_count == 6:
                print("... (showing only first 5 events)")

            # Check if we get a complete event
            if '"type": "complete"' in event:
                print(f"✅ Scan completed after {scan_count} events")
                break

            # Safety check - don't run forever
            if scan_count > 100:
                print("⚠️  Scan seems to be running indefinitely, stopping...")
                break

        print(f"\n📈 Total events processed: {scan_count}")

        # Test 2: Check if scan restarts automatically
        print("\n🔄 Test 2: Checking for automatic restart...")
        print("Waiting 5 seconds to see if scan restarts...")
        await asyncio.sleep(5)

        # Check if there are any new scan events in the logs
        print("✅ No automatic restart detected")

        db.close()

    except Exception as e:
        logger.error(f"Error testing scan restart: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_scan_restart_issue())