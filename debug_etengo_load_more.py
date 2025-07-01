#!/usr/bin/env python3
"""
Debug script to test Etengo load more functionality specifically.
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

async def debug_etengo_load_more():
    """Debug Etengo load more functionality."""

    print("=== Debugging Etengo Load More ===")

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
    driver = None

    try:
        driver = scraper.setup_driver()
        site_url = etengo_config["level1_search"]["site_url"]
        project_list_selector = etengo_config["level1_search"]["project-list-selector"]
        project_entry_selector = etengo_config["level1_search"]["project-entry-selector"]
        next_page_selector = etengo_config["level1_search"]["next-page-selector"]

        print(f"Navigating to: {site_url}")
        driver.get(site_url)

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))

        # Test load more functionality for a few iterations
        for iteration in range(5):
            print(f"\n--- Iteration {iteration + 1} ---")

            # Get current project count
            project_elements = driver.find_elements(By.CSS_SELECTOR, project_entry_selector)
            current_count = len(project_elements)
            print(f"Current project count: {current_count}")

            # Check if load more button exists
            try:
                load_more_button = driver.find_element(By.CSS_SELECTOR, next_page_selector)
                print(f"Load more button found: {load_more_button.text}")
                print(f"Button enabled: {load_more_button.is_enabled()}")
                print(f"Button displayed: {load_more_button.is_displayed()}")

                # Click the button
                print("Clicking load more button...")
                driver.execute_script("arguments[0].click();", load_more_button)

                # Wait a bit for content to load
                time.sleep(3)

                # Get new project count
                new_project_elements = driver.find_elements(By.CSS_SELECTOR, project_entry_selector)
                new_count = len(new_project_elements)
                print(f"New project count: {new_count}")

                if new_count > current_count:
                    print(f"SUCCESS: Loaded {new_count - current_count} new projects")
                elif new_count == current_count:
                    print("WARNING: No new projects loaded - this should trigger termination")
                    break
                else:
                    print(f"ERROR: Project count decreased from {current_count} to {new_count}")
                    break

            except Exception as e:
                print(f"Error with load more button: {e}")
                break

    except Exception as e:
        print(f"Error during debug: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    asyncio.run(debug_etengo_load_more())