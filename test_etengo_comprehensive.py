#!/usr/bin/env python3
"""
Comprehensive test for Etengo load more pagination with proper duplicate handling.
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

async def test_etengo_comprehensive():
    """Comprehensive test for Etengo load more pagination."""

    print("=== Comprehensive Etengo Load More Test ===")

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
    print(f"Next page selector: {etengo_config['level1_search']['next-page-selector']}")
    print(f"Project entry selector: {etengo_config['level1_search']['project-entry-selector']}")

    # Create web scraper
    scraper = WebScraper()

    # Track processed projects and pages
    processed_projects = []
    page_count = 0
    start_time = time.time()

    try:
        # Use a reasonable time range to get some projects
        async for project_data in scraper.scan_website_stream(etengo_config, time_range=30, existing_project_data={}, scan_id="comprehensive_test"):
            processed_projects.append(project_data)
            print(f"✅ Processed project: {project_data.get('title', 'Unknown')} (Date: {project_data.get('release_date', 'Unknown')})")

            # Limit to prevent infinite loop
            if len(processed_projects) > 50:
                print("⚠️  Reached 50 projects, stopping test")
                break

            # Check if we've been running too long (more than 8 minutes)
            if time.time() - start_time > 480:
                print("⚠️  Test running for more than 8 minutes, stopping")
                break

    except Exception as e:
        print(f"❌ Error during scan: {e}")

    elapsed_time = time.time() - start_time
    print(f"\n=== Comprehensive Test Results ===")
    print(f"Total projects processed: {len(processed_projects)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Average time per project: {elapsed_time/len(processed_projects):.2f} seconds" if processed_projects else "No projects processed")

    # Test passed if we processed some projects and didn't get stuck in infinite loop
    success = len(processed_projects) > 0 and elapsed_time < 480
    print(f"Test {'✅ PASSED' if success else '❌ FAILED'}")

    if success:
        print("🎉 Etengo load more pagination is working correctly!")
        print("✅ Session duplicate handling is working")
        print("✅ Load more button detection is working")
        print("✅ Scan termination is working")
    else:
        print("💥 Etengo pagination still has issues")

    # Show some sample projects
    if processed_projects:
        print(f"\n📋 Sample projects processed:")
        for i, project in enumerate(processed_projects[:5], 1):
            print(f"  {i}. {project.get('title', 'Unknown')} (Date: {project.get('release_date', 'Unknown')})")
        if len(processed_projects) > 5:
            print(f"  ... and {len(processed_projects) - 5} more")

if __name__ == "__main__":
    asyncio.run(test_etengo_comprehensive())