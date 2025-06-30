#!/usr/bin/env python3
"""
Test script for date filtering functionality
"""

import asyncio
import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from web_scraper import WebScraper
from config_manager import config_manager

# Set up logging to see the date filtering in action
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_date_filtering():
    """Test the date filtering functionality."""
    print("Testing date filtering functionality...")

    # Initialize the web scraper
    scraper = WebScraper()

    # Get website configuration
    websites = config_manager.get_websites()
    if not websites:
        print("No websites configured!")
        return

    website_config = websites[0]  # Use the first website

    print(f"Testing with website: {website_config['level1_search']['name']}")
    print(f"Site URL: {website_config['level1_search']['site_url']}")

    # Test with different time ranges
    time_ranges = [2, 8, 32]  # 1 day, 1 week, 1 month

    for time_range in time_ranges:
        print(f"\n--- Testing time range: {time_range} ---")

        # Calculate the cutoff date for this time range
        cutoff_date = scraper._get_time_range_date(time_range)
        print(f"Cutoff date: {cutoff_date.strftime('%d.%m.%Y')}")

        try:
            # Test the streaming version with limited projects
            project_count = 0
            max_projects = 15  # Limit to first 15 projects for testing

            async for project_data in scraper.scan_website_stream(website_config, time_range, {}):
                project_count += 1
                title = project_data.get('title', 'Unknown')
                start_date = project_data.get('start_date', 'N/A')

                print(f"Project {project_count}: {title}")
                print(f"  Start Date: {start_date}")
                print(f"  Location: {project_data.get('location', 'N/A')}")
                print()

                if project_count >= max_projects:
                    print(f"Reached limit of {max_projects} projects, stopping test")
                    break

            print(f"Found {project_count} projects within time range {time_range}")

        except Exception as e:
            print(f"Error testing time range {time_range}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_date_filtering())