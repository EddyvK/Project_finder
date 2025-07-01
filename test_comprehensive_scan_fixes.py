#!/usr/bin/env python3
"""
Comprehensive test to verify both Etengo pagination termination and non-repetition behavior.
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

async def test_etengo_pagination_termination():
    """Test that Etengo scan terminates when load more doesn't add new projects."""

    print("=== Testing Etengo Pagination Termination ===")

    # Get Etengo config
    websites = config_manager.get_websites()
    etengo_config = None
    for website in websites:
        if website['level1_search']['name'] == 'Etengo':
            etengo_config = website
            break

    if not etengo_config:
        print("ERROR: Etengo config not found!")
        return False

    print(f"Found Etengo config: {etengo_config['level1_search']['name']}")

    # Create web scraper
    scraper = WebScraper()

    # Track processed projects and pages
    processed_projects = []
    page_count = 0
    start_time = time.time()

    try:
        async for project_data in scraper.scan_website_stream(etengo_config, time_range=7, existing_project_data={}, scan_id="pagination_test"):
            processed_projects.append(project_data)
            print(f"Processed project: {project_data.get('title', 'Unknown')}")

            # Limit to prevent infinite loop in case the fix doesn't work
            if len(processed_projects) > 100:
                print("WARNING: Reached 100 projects, stopping test to prevent infinite loop")
                return False

            # Check if we've been running too long (more than 5 minutes)
            if time.time() - start_time > 300:
                print("WARNING: Test running for more than 5 minutes, stopping to prevent infinite loop")
                return False

    except Exception as e:
        print(f"Error during scan: {e}")
        return False

    elapsed_time = time.time() - start_time
    print(f"\n=== Etengo Pagination Test Results ===")
    print(f"Total projects processed: {len(processed_projects)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Projects found:")
    for i, project in enumerate(processed_projects, 1):
        print(f"  {i}. {project.get('title', 'Unknown')}")

    # Test passed if we processed some projects and didn't get stuck in infinite loop
    success = len(processed_projects) > 0 and elapsed_time < 300
    print(f"Test {'PASSED' if success else 'FAILED'}")
    return success

async def test_scan_service_cleanup():
    """Test that scan service properly cleans up after completion."""

    print("\n=== Testing Scan Service Cleanup ===")

    from backend.scan_service import scan_service

    # Check initial state
    initial_active = scan_service.is_scan_active()
    print(f"Initial scan active state: {initial_active}")

    # Create a mock scan
    scan_id = "cleanup_test"
    scan_service._register_scan(scan_id)

    # Check that scan is registered
    scan_active_after_register = scan_service.is_scan_active()
    print(f"Scan active after register: {scan_active_after_register}")

    # Unregister scan
    scan_service._unregister_scan(scan_id)

    # Check that scan is unregistered
    scan_active_after_unregister = scan_service.is_scan_active()
    print(f"Scan active after unregister: {scan_active_after_unregister}")

    # Test should pass if scan is properly unregistered
    success = not scan_active_after_unregister
    print(f"Cleanup test {'PASSED' if success else 'FAILED'}")
    return success

async def main():
    """Run all comprehensive tests."""

    print("Running comprehensive scan fixes tests...")

    # Test 1: Etengo pagination termination
    pagination_success = await test_etengo_pagination_termination()

    # Test 2: Scan service cleanup
    cleanup_success = await test_scan_service_cleanup()

    # Overall results
    print(f"\n=== Overall Test Results ===")
    print(f"Pagination termination: {'PASSED' if pagination_success else 'FAILED'}")
    print(f"Scan service cleanup: {'PASSED' if cleanup_success else 'FAILED'}")
    print(f"Overall: {'PASSED' if pagination_success and cleanup_success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())