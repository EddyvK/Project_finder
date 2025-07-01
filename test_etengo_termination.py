#!/usr/bin/env python3
"""
Test script to verify Etengo scan termination when load more doesn't add new projects.
"""

import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.web_scraper import WebScraper
from backend.config_manager import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_etengo_termination():
    """Test that Etengo scan terminates when load more doesn't add new projects."""

    print("Testing Etengo scan termination...")

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
    page_count = 0

    try:
        async for project_data in scraper.scan_website_stream(etengo_config, time_range=1, existing_project_data={}, scan_id="test"):
            processed_projects.append(project_data)
            print(f"Processed project: {project_data.get('title', 'Unknown')}")

            # Limit to prevent infinite loop in case the fix doesn't work
            if len(processed_projects) > 50:
                print("WARNING: Reached 50 projects, stopping test to prevent infinite loop")
                break

    except Exception as e:
        print(f"Error during scan: {e}")

    print(f"\nTest completed!")
    print(f"Total projects processed: {len(processed_projects)}")
    print(f"Projects found:")
    for i, project in enumerate(processed_projects, 1):
        print(f"  {i}. {project.get('title', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_etengo_termination())