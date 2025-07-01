#!/usr/bin/env python3
"""
Test to verify Etengo load more fix processes newly loaded projects.
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

async def test_etengo_load_more_fix():
    """Test that Etengo load more now processes newly loaded projects."""

    print("=== Testing Etengo Load More Fix ===")

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

    # Track processed projects and pages
    processed_projects = []
    start_time = time.time()

    try:
        # Use a reasonable time range to get some projects
        async for project_data in scraper.scan_website_stream(etengo_config, time_range=30, existing_project_data={}, scan_id="load_more_fix_test"):
            processed_projects.append(project_data)
            print(f"✅ Processed project: {project_data.get('title', 'Unknown')} (Date: {project_data.get('release_date', 'Unknown')})")

            # Limit to prevent infinite loop
            if len(processed_projects) > 40:
                print("⚠️  Reached 40 projects, stopping test")
                break

            # Check if we've been running too long (more than 6 minutes)
            if time.time() - start_time > 360:
                print("⚠️  Test running for more than 6 minutes, stopping")
                break

    except Exception as e:
        print(f"❌ Error during scan: {e}")

    elapsed_time = time.time() - start_time
    print(f"\n=== Load More Fix Test Results ===")
    print(f"Total projects processed: {len(processed_projects)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

    # Test passed if we processed more than 12 projects (indicating we moved past the first page)
    # and didn't get stuck in infinite loop
    success = len(processed_projects) > 12 and elapsed_time < 360
    print(f"Test {'✅ PASSED' if success else '❌ FAILED'}")

    if success:
        print("🎉 Etengo load more is now working correctly!")
        print(f"✅ Processed {len(processed_projects)} projects (more than the initial 12)")
        print("✅ Successfully moved to newly loaded projects")
        print("✅ No infinite loop detected")
    else:
        print("💥 Etengo load more still has issues")
        if len(processed_projects) <= 12:
            print("❌ Only processed first page projects - load more not working")
        if elapsed_time >= 360:
            print("❌ Test took too long - possible infinite loop")

if __name__ == "__main__":
    asyncio.run(test_etengo_load_more_fix())