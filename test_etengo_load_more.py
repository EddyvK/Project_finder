#!/usr/bin/env python3
"""
Test script to investigate Etengo load more functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import logging
from web_scraper import WebScraper
from config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_etengo_load_more():
    """Test Etengo load more functionality to see project processing patterns."""

    # Initialize scraper and config
    config_manager = ConfigManager()
    scraper = WebScraper()

    # Get Etengo config
    websites = config_manager.config['websites']
    etengo_config = None
    for website in websites:
        if website['level1_search']['name'] == 'Etengo':
            etengo_config = website
            break

    if not etengo_config:
        print("Etengo config not found!")
        return

    print("=== Testing Etengo Load More Functionality ===")
    print(f"Site URL: {etengo_config['level1_search']['site_url']}")
    print(f"Project list selector: {etengo_config['level1_search']['project-list-selector']}")
    print(f"Project entry selector: {etengo_config['level1_search']['project-entry-selector']}")
    print(f"Next page selector: {etengo_config['level1_search']['next-page-selector']}")
    print()

    # Test the load more functionality
    driver = scraper.setup_driver()
    try:
        # Navigate to Etengo
        driver.get(etengo_config['level1_search']['site_url'])

        # Wait for initial page to load
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(driver, 10)
        project_list_selector = etengo_config['level1_search']['project-list-selector']
        project_entry_selector = etengo_config['level1_search']['project-entry-selector']

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))

        # Test multiple load more iterations
        for iteration in range(1, 6):  # Test up to 5 iterations
            print(f"\n--- Iteration {iteration} ---")

            # Get current project count
            project_elements = driver.find_elements(By.CSS_SELECTOR, project_entry_selector)
            print(f"Current project count: {len(project_elements)}")

            # Show first few project titles
            print("First 3 project titles:")
            for i, element in enumerate(project_elements[:3]):
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, "h3.headline-4 a")
                    title = title_element.text
                    print(f"  {i+1}. {title}")
                except:
                    print(f"  {i+1}. [Could not extract title]")

            # Try to find and click load more button
            next_page_selector = etengo_config['level1_search']['next-page-selector']
            try:
                load_more_button = driver.find_element(By.CSS_SELECTOR, next_page_selector)
                if load_more_button.is_displayed() and load_more_button.is_enabled():
                    print(f"Load more button found and clickable")

                    # Click the button
                    driver.execute_script("arguments[0].click();", load_more_button)
                    print("Clicked load more button")

                    # Wait for new content
                    import time
                    time.sleep(3)

                    # Check if more projects were loaded
                    new_project_elements = driver.find_elements(By.CSS_SELECTOR, project_entry_selector)
                    print(f"New project count: {len(new_project_elements)}")

                    if len(new_project_elements) > len(project_elements):
                        print(f"✓ Successfully loaded {len(new_project_elements) - len(project_elements)} more projects")
                    else:
                        print("✗ No new projects loaded")
                        break
                else:
                    print("Load more button not clickable, stopping")
                    break
            except Exception as e:
                print(f"Error with load more button: {e}")
                break

    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(test_etengo_load_more())