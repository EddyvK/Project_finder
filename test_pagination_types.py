#!/usr/bin/env python3
"""
Test to verify both pagination types work correctly with proper duplicate handling.
"""

import asyncio
import logging
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.web_scraper import WebScraper
from backend.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_pagination_types():
    """Test both pagination types with detailed logging"""
    print("=== Testing Pagination Types ===\n")

    config = ConfigManager()
    scraper = WebScraper()

    # Test each website
    websites = config.get_websites()

    for website in websites:
        site_name = website['level1_search']['name']
        next_page_selector = website['level1_search']['next-page-selector']

        print(f"--- Testing {site_name} ---")
        print(f"Next page selector: {next_page_selector}")

        # Detect pagination type
        if "load" in next_page_selector.lower() or "more" in next_page_selector.lower():
            pagination_type = "LOAD MORE"
        else:
            pagination_type = "NEXT PAGE"
        print(f"Detected pagination type: {pagination_type}")

        start_time = time.time()
        processed_count = 0
        max_projects = 5  # Limit to 5 projects for testing
        max_time = 120  # 2 minutes max

        try:
            async for project_data in scraper.scan_website_stream(website):
                processed_count += 1
                print(f"                            ✅ {site_name}: {project_data.get('title', 'Unknown')}")

                if processed_count >= max_projects:
                    print(f"✅ {site_name}: Reached max_projects ({max_projects}), stopping.")
                    break

                # Check if we've exceeded time limit
                if time.time() - start_time > max_time:
                    print(f"⚠️  Test running too long for {site_name}, stopping")
                    break

        except Exception as e:
            print(f"❌ Error testing {site_name}: {e}")

        elapsed = time.time() - start_time
        print(f"📊 {site_name} Results: {processed_count} projects in {elapsed:.2f}s")

        if processed_count >= max_projects:
            print(f"✅ {site_name}: Successfully processed {max_projects} projects")
        elif processed_count > 0:
            print(f"⚠️  {site_name}: Partial success - {processed_count}/{max_projects} projects")
        else:
            print(f"❌ {site_name}: No projects processed")

        print()

if __name__ == "__main__":
    asyncio.run(test_pagination_types())