#!/usr/bin/env python3
"""
Simple test to verify Etengo pagination with load more functionality.
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

async def test_etengo_pagination():
    """Test Etengo pagination with load more functionality."""

    print("=== Testing Etengo Pagination with Load More ===")

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

    # Create web scraper
    scraper = WebScraper()

    # Track processed projects and pages
    processed_projects = []
    page_count = 0
    start_time = time.time()

    try:
        # Use a longer time range (30 days) to ensure we get projects
        async for project_data in scraper.scan_website_stream(etengo_config, time_range=30, existing_project_data={}, scan_id="pagination_test"):
            processed_projects.append(project_data)
            print(f"Processed project: {project_data.get('title', 'Unknown')}")

            # Limit to prevent infinite loop in case the fix doesn't work
            if len(processed_projects) > 50:
                print("WARNING: Reached 50 projects, stopping test to prevent infinite loop")
                break

            # Check if we've been running too long (more than 10 minutes)
            if time.time() - start_time > 600:
                print("WARNING: Test running for more than 10 minutes, stopping to prevent infinite loop")
                break

    except Exception as e:
        print(f"Error during scan: {e}")

    elapsed_time = time.time() - start_time
    print(f"\n=== Etengo Pagination Test Results ===")
    print(f"Total projects processed: {len(processed_projects)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Projects found:")
    for i, project in enumerate(processed_projects, 1):
        print(f"  {i}. {project.get('title', 'Unknown')} (Date: {project.get('release_date', 'Unknown')})")

    # Test passed if we processed some projects and didn't get stuck in infinite loop
    success = len(processed_projects) > 0 and elapsed_time < 600
    print(f"Test {'PASSED' if success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(test_etengo_pagination())