"""Debug script to examine individual project page structure."""

import asyncio
import logging
from web_scraper import WebScraper
from config_manager import config_manager
from logger_config import setup_logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def debug_project_page():
    """Debug the structure of an individual project page."""
    try:
        scraper = WebScraper()
        websites = config_manager.get_websites()

        if not websites:
            print("No websites configured")
            return

        website_config = websites[0]

        # Get a project URL first
        project_urls = await scraper.level1_scan(website_config)
        if not project_urls:
            print("No project URLs found")
            return

        test_url = project_urls[0]
        print(f"Debugging project page: {test_url}")

        # Setup driver and get page
        driver = scraper.setup_driver()
        driver.get(test_url)
        time.sleep(3)

        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Save HTML for inspection
        with open('debug_project_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)

        print("HTML saved to debug_project_page.html")

        # Look for the specific elements we need
        print("\n=== Looking for project data ===")

        # Look for box-50 elements
        boxes = soup.find_all('div', class_='box-50')
        print(f"Found {len(boxes)} box-50 elements")

        for i, box in enumerate(boxes):
            small = box.find('small')
            span = box.find('span')
            if small and span:
                print(f"Box {i+1}: {small.get_text(strip=True)} = {span.get_text(strip=True)}")

        # Look for title
        title_element = soup.find('h3', class_='headline-4')
        if title_element:
            print(f"Title: {title_element.get_text(strip=True)}")

        driver.quit()

    except Exception as e:
        logger.error(f"Error debugging project page: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(debug_project_page())