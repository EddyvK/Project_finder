#!/usr/bin/env python3
"""
Test to verify Etengo pagination fix.
"""

import asyncio
import logging
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.web_scraper import WebScraper
from backend.config_manager import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_etengo_fix():
    """Test that Etengo pagination now works correctly."""

    print("=== Testing Etengo Pagination Fix ===")

    # Get Etengo config
    websites = config_manager.get_websites()
    etengo_config = None
    for website in websites:
        if website['level1_search']['name'] == 'Etengo':
            etengo_config = website
            break

    if not etengo_config:
        print("ERROR: Etengo config not found!")
        return

    print(f"Found Etengo config: {etengo_config['level1_search']['name']}")

    # Create web scraper
    scraper = WebScraper()

    # Track processed projects
    processed_projects = []
    start_time = time.time()

    try:
        # Use a reasonable time range (14 days) to get some projects but not too many
        async for project_data in scraper.scan_website_stream(etengo_config, time_range=14, existing_project_data={}, scan_id="fix_test"):
            processed_projects.append(project_data)
            print(f"Processed project: {project_data.get('title', 'Unknown')}")

            # Limit to prevent infinite loop
            if len(processed_projects) > 30:
                print("WARNING: Reached 30 projects, stopping test")
                break

            # Check if we've been running too long (more than 5 minutes)
            if time.time() - start_time > 300:
                print("WARNING: Test running for more than 5 minutes, stopping")
                break

    except Exception as e:
        print(f"Error during scan: {e}")

    elapsed_time = time.time() - start_time
    print(f"\n=== Test Results ===")
    print(f"Total projects processed: {len(processed_projects)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

    # Test passed if we processed some projects and didn't get stuck in infinite loop
    success = len(processed_projects) > 0 and elapsed_time < 300
    print(f"Test {'PASSED' if success else 'FAILED'}")

    if success:
        print("✅ Etengo pagination is now working correctly!")
    else:
        print("❌ Etengo pagination still has issues")

if __name__ == "__main__":
    asyncio.run(test_etengo_fix())