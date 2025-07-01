"""Debug script to test pagination selectors for Freelancermap."""

import asyncio
import logging
from backend.web_scraper import WebScraper
from backend.config_manager import config_manager
from backend.logger_config import setup_logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def debug_pagination():
    """Debug the pagination selector for Freelancermap."""
    try:
        scraper = WebScraper()
        websites = config_manager.get_websites()

        if not websites:
            print("No websites configured")
            return

        # Find Freelancermap config
        freelancermap_config = None
        for website in websites:
            if website['level1_search']['name'] == 'Freelancermap':
                freelancermap_config = website
                break

        if not freelancermap_config:
            print("Freelancermap config not found")
            return

        print("🔍 Debugging Freelancermap pagination...")
        print(f"Site URL: {freelancermap_config['level1_search']['site_url']}")
        print(f"Project list selector: {freelancermap_config['level1_search']['project-list-selector']}")
        print(f"Next page selector: {freelancermap_config['level1_search']['next-page-selector']}")
        print()

        # Setup driver and get page
        driver = scraper.setup_driver()
        driver.get(freelancermap_config['level1_search']['site_url'])

        # Wait for page to load
        wait = webdriver.support.ui.WebDriverWait(driver, 10)
        project_list_selector = freelancermap_config['level1_search']['project-list-selector']
        wait.until(webdriver.support.expected_conditions.presence_of_element_located(
            (webdriver.common.by.By.CSS_SELECTOR, project_list_selector)
        ))

        time.sleep(3)  # Additional wait for dynamic content

        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Save HTML for inspection
        with open('debug_freelancermap_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)

        print("✅ HTML saved to debug_freelancermap_page.html")
        print()

        # Test project list selector
        project_grid = soup.select_one(project_list_selector)
        if project_grid:
            print(f"✅ Found project grid with selector: {project_list_selector}")
            project_cards = project_grid.select(freelancermap_config['level1_search']['project-entry-selector'])
            print(f"   Found {len(project_cards)} project cards")
        else:
            print(f"❌ No project grid found with selector: {project_list_selector}")
            print("   Available elements with similar names:")
            for element in soup.find_all(class_=lambda x: x and 'project' in x.lower()):
                print(f"   - {element.name}.{element.get('class', [])}")

        print()

        # Test next page selector
        next_page_selector = freelancermap_config['level1_search']['next-page-selector']
        print(f"🔍 Testing next page selector: {next_page_selector}")

        # Search in entire page
        next_page_element = soup.select_one(next_page_selector)
        if next_page_element:
            print(f"✅ Found next page element: {next_page_element.name}")
            print(f"   Text: {next_page_element.get_text(strip=True)}")
            print(f"   Href: {next_page_element.get('href', 'N/A')}")
            print(f"   Classes: {next_page_element.get('class', [])}")
        else:
            print(f"❌ No next page element found with selector: {next_page_selector}")

            # Look for pagination-related elements
            print("   Looking for pagination-related elements:")
            pagination_keywords = ['pagination', 'paginator', 'next', 'page', 'nav']
            for keyword in pagination_keywords:
                elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
                for element in elements[:3]:  # Show first 3 matches
                    print(f"   - {element.name}.{element.get('class', [])}: {element.get_text(strip=True)[:50]}...")

            # Also look for elements with 'next' in text
            print("   Looking for elements with 'next' in text:")
            for element in soup.find_all(text=lambda text: text and 'next' in text.lower()):
                parent = element.parent
                if parent:
                    print(f"   - {parent.name}.{parent.get('class', [])}: {element.strip()}")

        print()

        # Test if selector works when searching within project grid
        if project_grid:
            print("🔍 Testing next page selector within project grid scope:")
            next_page_in_grid = project_grid.select_one(next_page_selector)
            if next_page_in_grid:
                print(f"✅ Found next page element within project grid")
            else:
                print(f"❌ No next page element found within project grid scope")
                print("   This confirms the pagination controls are outside the project list!")

        driver.quit()

    except Exception as e:
        logger.error(f"Error debugging pagination: {e}")
        if 'driver' in locals():
            driver.quit()


if __name__ == "__main__":
    asyncio.run(debug_pagination())