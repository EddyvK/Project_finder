"""Web scraper for project data extraction."""

import logging
from typing import List, Dict, Any, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
from urllib.parse import urlparse, urljoin
# Try to import from backend first, then fall back to direct import
try:
    from backend.config_manager import config_manager
except ImportError:
    from config_manager import config_manager
from backend.mistral_handler import MistralHandler
from bs4 import BeautifulSoup
from backend.utils.date_utils import european_to_iso_date, compare_european_dates
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def ensure_parsed_json(input_data: Union[str, dict]) -> dict:
    if isinstance(input_data, dict):
        return input_data
    elif isinstance(input_data, str):
        import json
        return json.loads(input_data)
    else:
        raise TypeError(f"Unsupported input type: {type(input_data)}")

class WebScraper:
    def __init__(self):
        self.config = config_manager.get_websites()
        self.mistral_handler = None
        api_keys = config_manager.get_api_keys()
        if api_keys.get("mistral"):
            self.mistral_handler = MistralHandler(api_keys["mistral"])
        self.logger = logging.getLogger(__name__)

    def setup_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    def _get_time_range_date(self, time_range: int) -> datetime:
        """Calculate the cutoff date based on time range."""
        today = datetime.now()
        # time_range directly represents the number of days to go back
        cutoff_date = today - timedelta(days=time_range)
        return cutoff_date

    def _is_within_time_range(self, start_date_str: str, time_range: int) -> bool:
        """Check if a project's start date is within the specified time range."""
        if not start_date_str:
            return True  # If no date, include it

        # Convert European date to ISO format
        iso_date = european_to_iso_date(start_date_str)
        if not iso_date:
            logger.warning(f"Could not parse date: {start_date_str}, including project")
            return True  # If date parsing fails, include it

        try:
            project_date = datetime.fromisoformat(iso_date)
            cutoff_date = self._get_time_range_date(time_range)

            # Normalize to date only (remove time component)
            project_date = project_date.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Only include projects that start on or after the cutoff date
            is_within_range = project_date >= cutoff_date

            if not is_within_range:
                logger.info(f"Excluding project with release date {start_date_str} (before cutoff {cutoff_date.strftime('%d.%m.%Y')})")

            return is_within_range

        except ValueError as e:
            logger.warning(f"Error parsing date {start_date_str}: {e}, including project")
            return True  # If date parsing fails, include it

    def _is_top_project(self, project_card) -> bool:
        """Check if a project card is a top project (should be excluded from cutoff date logic)."""
        # Check for top-project class
        if project_card.get('class') and 'top-project' in project_card.get('class'):
            return True

        # Check for top-project-badge
        top_badge = project_card.select_one('.top-project-badge')
        if top_badge:
            return True

        return False

    def _is_on_cutoff_date(self, release_date_str: str, time_range: int) -> bool:
        """Check if a project is exactly on the cutoff date."""
        if not release_date_str:
            return False

        # Convert European date to ISO format
        iso_date = european_to_iso_date(release_date_str)
        if not iso_date:
            return False

        try:
            project_date = datetime.fromisoformat(iso_date)
            cutoff_date = self._get_time_range_date(time_range)

            # Normalize to date only (remove time component)
            project_date = project_date.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Check if project is exactly on the cutoff date
            is_on_cutoff = project_date == cutoff_date

            return is_on_cutoff

        except ValueError:
            return False

    def _is_significantly_outside_range(self, release_date_str: str, time_range: int) -> bool:
        """Check if a project is significantly outside the time range (more than 2x the time range)."""
        if not release_date_str:
            return False

        # Convert European date to ISO format
        iso_date = european_to_iso_date(release_date_str)
        if not iso_date:
            logger.warning(f"Could not parse date: {release_date_str}, excluding project")
            return False

        try:
            project_date = datetime.fromisoformat(iso_date)
            cutoff_date = self._get_time_range_date(time_range)

            # Normalize to date only (remove time component)
            project_date = project_date.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # Calculate extended cutoff (2x the original time range)
            extended_cutoff = cutoff_date - timedelta(days=time_range)

            # Check if project is significantly outside range
            is_significantly_outside = project_date < extended_cutoff

            if is_significantly_outside:
                logger.info(f"Project significantly outside range: {release_date_str} (before extended cutoff {extended_cutoff.strftime('%d.%m.%Y')})")

            return is_significantly_outside

        except ValueError:
            return False

    async def _scan_page_with_pagination(self, website_config: Dict[str, Any], time_range: int, current_url: str = None):
        """Scan a single page and return project cards, along with next page URL if available."""
        driver = None
        try:
            driver = self.setup_driver()
            if current_url is None:
                current_url = website_config["level1_search"]["site_url"]

            project_list_selector = website_config["level1_search"]["project-list-selector"]
            project_entry_selector = website_config["level1_search"]["project-entry-selector"]
            next_page_selector = website_config["level1_search"].get("next-page-selector")

            driver.get(current_url)
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            project_grid = soup.select_one(project_list_selector)

            if not project_grid:
                logger.error(f"No project grid found on {current_url} with selector: {project_list_selector}")
                return [], None, False

            project_cards = project_grid.select(project_entry_selector)
            logger.info(f"Found {len(project_cards)} project cards on current page")

            # Check for next page or load more button
            next_page_url = None
            has_load_more = False

            if next_page_selector:
                # Check if it's a load more button (button element)
                load_more_button = soup.select_one(next_page_selector)
                if load_more_button and load_more_button.name == 'button':
                    has_load_more = True
                    logger.info("Found load more button")
                else:
                    # Traditional pagination link
                    next_page_element = soup.select_one(next_page_selector)
                    if next_page_element and next_page_element.get('href'):
                        next_page_url = next_page_element.get('href')
                        if not next_page_url.startswith('http'):
                            # Handle relative URLs
                            base_url = driver.current_url
                            next_page_url = urljoin(base_url, next_page_url)
                        logger.info(f"Found next page URL: {next_page_url}")

            return project_cards, next_page_url, has_load_more

        except Exception as e:
            self.logger.error(f"Error scanning page: {e}")
            return [], None, False
        finally:
            if driver:
                driver.quit()

    async def _load_more_projects(self, website_config: Dict[str, Any], driver: webdriver.Chrome) -> bool:
        """Click the load more button and wait for new content to load."""
        try:
            next_page_selector = website_config["level1_search"].get("next-page-selector")
            if not next_page_selector:
                return False

            # Find and click the load more button
            wait = WebDriverWait(driver, 10)
            load_more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_page_selector)))

            # Get current project count
            project_entry_selector = website_config["level1_search"]["project-entry-selector"]
            current_count = len(driver.find_elements(By.CSS_SELECTOR, project_entry_selector))

            # Click the button
            driver.execute_script("arguments[0].click();", load_more_button)
            logger.info("Clicked load more button")

            # Wait for new content to load (wait for more projects to appear)
            try:
                wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, project_entry_selector)) > current_count)
                logger.info("New projects loaded successfully")
                return True
            except TimeoutException:
                logger.info("No new projects loaded after clicking load more")
                return False

        except Exception as e:
            logger.error(f"Error clicking load more button: {e}")
            return False

    async def level1_scan(self, website_config: Dict[str, Any]):
        """Return a list of project card elements from the main page (BeautifulSoup objects)."""
        driver = None
        try:
            driver = self.setup_driver()
            site_url = website_config["level1_search"]["site_url"]
            project_list_selector = website_config["level1_search"]["project-list-selector"]
            project_entry_selector = website_config["level1_search"]["project-entry-selector"]

            driver.get(site_url)
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            project_grid = soup.select_one(project_list_selector)
            if not project_grid:
                logger.error(f"No project grid found on {site_url} with selector: {project_list_selector}")
                return []
            project_cards = project_grid.select(project_entry_selector)
            logger.info(f"Found {len(project_cards)} project cards")
            return project_cards
        except Exception as e:
            self.logger.error(f"Level 1 scan error: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    async def level2_scan(self, project_card, website_config: Dict[str, Any], scan_id: str = None) -> Dict[str, Any]:
        """Extract project data from a single card element using config, return project dict."""
        # Check for cancellation at the start of level2 scan
        if scan_id:
            from backend.scan_service import scan_service
            if scan_service.is_scan_cancelled(scan_id):
                raise Exception("Scan was cancelled during level2 scan")

        level2_config = website_config["level2_search"]
        data = {}
        try:
            # Extract title and URL
            title_selector = level2_config.get("title-selector")
            url_selector = level2_config.get("url-selector")
            if title_selector:
                title_element = project_card.select_one(title_selector)
                if title_element:
                    data['title'] = title_element.get_text(strip=True)
            if url_selector:
                url_element = project_card.select_one(url_selector)
                if url_element:
                    data['url'] = url_element.get('href')
                    if data['url'] and not data['url'].startswith('http'):
                        # Handle relative URLs using base URL from config
                        base_url = website_config["level1_search"]["site_url"]
                        parsed_url = urlparse(base_url)
                        data['url'] = f"{parsed_url.scheme}://{parsed_url.netloc}{data['url']}"

            # Check for cancellation after basic extraction
            if scan_id:
                from backend.scan_service import scan_service
                if scan_service.is_scan_cancelled(scan_id):
                    raise Exception("Scan was cancelled during level2 scan")

            # Extract all possible fields from config
            field_mappings = {
                "project-id-selector": "project_id",
                "location-selector": "location",
                "duration-selector": "duration",
                "start-date-selector": "start_date",
                "release-date-selector": "release_date",
                "industry-selector": "industry",
                "tenderer-selector": "tenderer"
            }

            for selector_key, data_key in field_mappings.items():
                selector = level2_config.get(selector_key)
                if selector:
                    # For fields that might share the same selector, we need to find the right element
                    label = level2_config.get(f"{selector_key.replace('-selector', '-label')}", "")

                    if label:
                        # Find all elements with this selector and look for the one with the matching label
                        elements = project_card.select(selector)
                        found_element = None

                        for element in elements:
                            # Check if this element or its parent contains the label
                            parent = element.parent
                            if parent:
                                # Look for the label in the parent element (usually in a <small> tag)
                                label_element = parent.find('small')
                                try:
                                    if label_element and isinstance(label_element.get_text(strip=True), str) and label_element.get_text(strip=True) == label:
                                        found_element = element
                                        break
                                except Exception as e:
                                    if scan_id:
                                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                                    else:
                                        scraper_logger = logging.getLogger(__name__)
                                    scraper_logger.warning(f"Error processing label_element: {e}")

                        if found_element:
                            try:
                                text_content = found_element.get_text(strip=True)
                                if isinstance(text_content, str):
                                    data[data_key] = text_content
                                else:
                                    data[data_key] = str(text_content) if text_content else None
                            except Exception as e:
                                if scan_id:
                                    scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                                else:
                                    scraper_logger = logging.getLogger(__name__)
                                scraper_logger.warning(f"Error processing found_element for {data_key}: {e}")
                        elif selector_key == "release-date-selector":
                            # Special handling for release date with label
                            element = project_card.select_one(selector)
                            if element:
                                try:
                                    text_content = element.get_text(strip=True)
                                    if isinstance(text_content, str):
                                        if label and text_content.startswith(label):
                                            # Extract date part after the label
                                            date_part = text_content[len(label):].strip()
                                            data[data_key] = date_part
                                        else:
                                            data[data_key] = text_content
                                    else:
                                        data[data_key] = str(text_content) if text_content else None
                                except Exception as e:
                                    if scan_id:
                                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                                    else:
                                        scraper_logger = logging.getLogger(__name__)
                                    scraper_logger.warning(f"Error processing release-date element: {e}")
                        # If not found, don't set any value - this prevents fallback to incorrect values
                        # This ensures that missing fields remain None instead of getting incorrect values
                    else:
                        # No label specified, handle special cases
                        if selector_key == "industry-selector":
                            # For industry/keywords, collect all matching elements
                            elements = project_card.select(selector)
                            keywords = []
                            for element in elements:
                                try:
                                    keyword = element.get_text(strip=True)
                                    if isinstance(keyword, str) and keyword and not keyword.startswith('+'):
                                        keywords.append(keyword)
                                except Exception as e:
                                    if scan_id:
                                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                                    else:
                                        scraper_logger = logging.getLogger(__name__)
                                    scraper_logger.warning(f"Error processing keyword element: {e}")
                            if keywords:
                                data[data_key] = ', '.join(keywords)
                        elif selector_key == "location-selector":
                            # For location, get the full text content
                            element = project_card.select_one(selector)
                            if element:
                                # Extract location text, handling nested elements
                                location_parts = []
                                try:
                                    for text in element.stripped_strings:
                                        # Ensure text is actually a string before calling strip()
                                        if isinstance(text, str) and text and not text.startswith('‐'):
                                            location_parts.append(text)
                                except Exception as e:
                                    if scan_id:
                                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                                    else:
                                        scraper_logger = logging.getLogger(__name__)
                                    scraper_logger.warning(f"Error processing stripped_strings: {e}")
                                    # Fallback: try get_text instead
                                    try:
                                        text_content = element.get_text(strip=True)
                                        if isinstance(text_content, str) and text_content:
                                            location_parts = [text_content]
                                    except Exception as e2:
                                        scraper_logger.warning(f"Fallback get_text also failed: {e2}")

                                if location_parts:
                                    # Clean up the location text by removing empty parts
                                    cleaned_parts = []
                                    for part in location_parts:
                                        if isinstance(part, str):
                                            stripped_part = part.strip()
                                            if stripped_part:
                                                cleaned_parts.append(stripped_part)
                                    if cleaned_parts:
                                        data[data_key] = ', '.join(cleaned_parts)
                        elif selector_key == "release-date-selector":
                            # For release date, handle label-based extraction
                            element = project_card.select_one(selector)
                            if element:
                                text_content = element.get_text(strip=True)
                                if label and text_content.startswith(label):
                                    # Extract date part after the label
                                    if isinstance(text_content, str):
                                        date_part = text_content[len(label):].strip()
                                        data[data_key] = date_part
                                    else:
                                        data[data_key] = text_content
                                else:
                                    data[data_key] = text_content
                        else:
                            # Default behavior for other fields
                            element = project_card.select_one(selector)
                            if element:
                                try:
                                    text_content = element.get_text(strip=True)
                                    if isinstance(text_content, str):
                                        data[data_key] = text_content
                                    else:
                                        # If not a string, convert to string or skip
                                        data[data_key] = str(text_content) if text_content else None
                                except Exception as e:
                                    if scan_id:
                                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                                    else:
                                        scraper_logger = logging.getLogger(__name__)
                                    scraper_logger.warning(f"Error processing element for {data_key}: {e}")

            # Set default values
            if 'tenderer' not in data:
                data['tenderer'] = level2_config.get("tenderer", "Unknown")
            data['rate'] = level2_config.get("rate", "N/A")

            # Log extracted data
            title = data.get('title', 'Unknown')
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.info(f"Level2 scan extracted data for '{title}':")
            # logger.info(f"  - Title: {data.get('title', 'N/A')}")
            # logger.info(f"  - URL: {data.get('url', 'N/A')}")
            # logger.info(f"  - Project ID: {data.get('project_id', 'N/A')}")
            # logger.info(f"  - Release Date: {data.get('release_date', 'N/A')}")
            # logger.info(f"  - Start Date: {data.get('start_date', 'N/A')}")
            # logger.info(f"  - Location: {data.get('location', 'N/A')}")
            # logger.info(f"  - Duration: {data.get('duration', 'N/A')}")
            # logger.info(f"  - Industry/Skills: {data.get('industry', 'N/A')}")
            # logger.info(f"  - Tenderer: {data.get('tenderer', 'N/A')}")
            # logger.info(f"  - Rate: {data.get('rate', 'N/A')}")

        except Exception as e:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.debug(f"Error extracting card: {e}")
        return data

    async def level3_scan(self, project_url: str, scan_id: str = None) -> Dict[str, Any]:
        """Take a single URL, return requirements using Mistral AI."""
        if not self.mistral_handler:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.warning("Mistral handler not available for Level 3 scan")
            return {"requirements": []}
        return await self._extract_project_data_with_mistral(project_url, scan_id)

    async def _extract_project_data_with_mistral(self, project_url: str, scan_id: str = None) -> Dict[str, Any]:
        """Extract project data using Mistral AI from a project URL."""
        try:
            # Get the page content
            driver = self.setup_driver()
            driver.get(project_url)

            # Wait for page to load
            time.sleep(2)

            # Get the page source
            page_source = driver.page_source

            # Close the driver
            driver.quit()

            # Extract project details using Mistral
            project_data = await self.mistral_handler.extract_project_details(page_source, scan_id)

            # Add the URL to the project data
            project_data['url'] = project_url

            return project_data

        except Exception as e:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.error(f"Error extracting project data with Mistral: {e}")
            return {"requirements": [], "url": project_url}

    async def quick_level3_scan(self, project_url: str, scan_id: str = None) -> Dict[str, Any]:
        """Quick level3 scan to get just the release date for filtering."""
        if not self.mistral_handler:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.warning("Mistral handler not available for quick Level 3 scan")
            return {"release_date": None}

        try:
            # Get the page content
            driver = self.setup_driver()
            driver.get(project_url)

            # Wait for page to load
            time.sleep(2)

            # Get the page source
            page_source = driver.page_source

            # Close the driver
            driver.quit()

            # Extract just the release date using Mistral
            release_date = await self.mistral_handler.extract_release_date(page_source, scan_id)

            return {"release_date": release_date}

        except Exception as e:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.error(f"Error in quick level3 scan: {e}")
            return {"release_date": None}

    def _is_valid_project_url(self, url: str) -> bool:
        if not url:
            return False
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)

    def _consolidate_data(self, level2_data: Dict[str, Any], level3_data: Dict[str, Any]) -> Dict[str, Any]:
        l2d = ensure_parsed_json(level2_data)
        l3d = ensure_parsed_json(level3_data)
        consolidated = {}
        consolidated.update(l2d)

        # Handle requirements with term frequency (new format)
        l2_requirements = l2d.get("requirements", {})
        l3_requirements = l3d.get("requirements", {})

        # Convert to dictionaries if they're not already
        if not isinstance(l2_requirements, dict):
            l2_requirements = {}
        if not isinstance(l3_requirements, dict):
            l3_requirements = {}

        # Merge requirements dictionaries, adding term frequencies
        merged_requirements = {}
        for skill, count in l2_requirements.items():
            merged_requirements[skill] = count
        for skill, count in l3_requirements.items():
            if skill in merged_requirements:
                merged_requirements[skill] += count
            else:
                merged_requirements[skill] = count

        consolidated["requirements"] = merged_requirements

        # Also create a list of requirements for backward compatibility
        consolidated["requirements_list"] = list(merged_requirements.keys())

        for key, value in l3d.items():
            if key != "requirements":
                if value and str(value).strip():
                    if consolidated.get(key) == "n/a":
                        consolidated[key] = value
                    elif consolidated.get(key) != value:
                        consolidated[key] = value
        # Ensure specific fields are included from level3 data if available
        for field in ["workload", "duration", "budget"]:
            if l3d.get(field) and str(l3d[field]).strip():
                consolidated[field] = l3d[field]
        return consolidated

    async def scan_website_stream(self, website_config: Dict[str, Any], time_range: int = 1, existing_project_data=None, scan_id: str = None):
        """
        Scan a specific website for projects and yield results as they are found.

        Args:
            website_config (dict): Configuration for the website to scan
            time_range (int, optional): Number of days to look back for projects
            existing_project_data (dict): Pre-collected existing projects data
            scan_id (str, optional): Scan ID for cancellation checks

        Yields:
            dict: Project data as it is found
        """
        # Create structured logger for this scan
        if website_config['level1_search']['name']:
            scraper_logger = logging.getLogger(f"scan.{website_config['level1_search']['name']}.webscraper")
        else:
            scraper_logger = logging.getLogger(__name__)
        scraper_logger.info(f"Scanning website {website_config['level1_search']['site_url']}")

        current_url = website_config["level1_search"]["site_url"]
        page_count = 0
        total_projects_processed = 0
        driver = None

        try:
            # Initialize driver for the entire scanning session
            driver = self.setup_driver()
            driver.get(current_url)

            # Wait for initial page to load
            project_list_selector = website_config["level1_search"]["project-list-selector"]
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))

            # Second loop: Loop through each page with pagination support
            while True:
                page_count += 1
                scraper_logger.info(f"Scanning page/load {page_count}")

                # Get current page content
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                project_grid = soup.select_one(project_list_selector)

                if not project_grid:
                    scraper_logger.info(f"No project list found on page {page_count}")
                    break

                project_cards = project_grid.select(website_config["level1_search"]["project-entry-selector"])
                scraper_logger.info(f"Found {len(project_cards)} project cards on current page")

                if not project_cards:
                    scraper_logger.info(f"No project cards found on page {page_count}")
                    break

                # Process each project card on the current page
                projects_outside_range = 0
                projects_on_cutoff_date = 0
                cutoff_date_reached = False

                # Third (inner) loop: Process each project card on the current page
                for project_card in project_cards:
                    try:
                        # Extract level 2 data
                        project_level_2_data = await self.level2_scan(project_card, website_config, scan_id)

                        # Check, based on the project_level_2_data, whether this project is already in the database
                        if existing_project_data:
                            project_url = project_level_2_data.get('url')
                            if project_url and project_url in existing_project_data:
                                db_project = existing_project_data[project_url]
                                scraper_logger.info("=========================================================================")
                                scraper_logger.info(f"Project {db_project['title']} already in database, skipping further processing")
                                scraper_logger.info("=========================================================================")
                                # Continue scanning to ensure time range coverage - don't stop pagination
                                continue  # Skip this project but continue with the next one

                        # Check if we have release_date from level2, if not we'll need level3
                        release_date = project_level_2_data.get('release_date')
                        title = project_level_2_data.get('title', 'Unknown')

                        # If no release_date from level2, we need to do a quick level3 scan to get it for filtering
                        if not release_date:
                            scraper_logger.info(f"No release_date from level2, doing quick level3 scan for filtering: {title}")
                            project_url = project_level_2_data.get('url')
                            if project_url:
                                # Quick level3 scan just for release_date
                                quick_level3_data = await self.quick_level3_scan(project_url, scan_id)
                                # Get release_date from level3 - extract the string value from the dictionary
                                release_date = quick_level3_data.get('release_date')
                                if isinstance(release_date, dict):
                                    release_date = release_date.get('release_date')
                            else:
                                release_date = None

                        scraper_logger.info(f"Checking project: {title} with release date: {release_date}")

                        # Check if project is significantly outside range (immediate stop condition)
                        if self._is_significantly_outside_range(release_date, time_range):
                            # Skip date-based stopping for top projects
                            if self._is_top_project(project_card):
                                scraper_logger.info(f"Found top project significantly outside time range: {title} (release date: {release_date}) - ignoring for scan stop")
                            else:
                                scraper_logger.info(f"Stopping scan: Found project significantly outside time range: {title} (release date: {release_date})")
                                return  # Exit the entire scanning process

                        # Check if project is on the cutoff date (signal to stop pagination after this page)
                        if self._is_on_cutoff_date(release_date, time_range):
                            # Skip cutoff date logic for top projects
                            if self._is_top_project(project_card):
                                scraper_logger.info(f"Found top project on cutoff date: {title} (release date: {release_date}) - ignoring for pagination stop")
                            else:
                                scraper_logger.info(f"Found project on cutoff date: {title} (release date: {release_date}) - will stop pagination after this page")
                                projects_on_cutoff_date += 1
                                cutoff_date_reached = True

                        # Check if project is outside time range (should trigger cutoff date logic)
                        if not self._is_within_time_range(release_date, time_range):
                            # Skip date-based filtering for top projects
                            if self._is_top_project(project_card):
                                scraper_logger.info(f"Found top project outside time range: {title} (release date: {release_date}) - including anyway")
                            else:
                                scraper_logger.info(f"Project outside time range found: {title} (release date: {release_date})")
                                projects_outside_range += 1
                                # Don't continue processing this project, but don't stop pagination yet
                                # The cutoff date logic will handle stopping pagination after this page
                                continue

                        # Project passed filtering - now do the full level3 scan for all detailed data
                        project_url = project_level_2_data.get('url')
                        if project_url:
                            project_level_3_data = await self.level3_scan(project_url, scan_id)
                        else:
                            project_level_3_data = {"requirements": []}

                        # Consolidate all data (level2 + full level3)
                        consolidated_data = self._consolidate_data(project_level_2_data, project_level_3_data)
                        if "url" not in consolidated_data and project_level_2_data.get('url'):
                            consolidated_data["url"] = project_level_2_data['url']

                        total_projects_processed += 1
                        scraper_logger.info(f"Processed project {total_projects_processed}: {consolidated_data.get('title', 'Unknown')}")

                        yield consolidated_data

                    except Exception as e:
                        scraper_logger.error(f"Error processing project card: {e}")
                        continue

                # If we found projects on the cutoff date, stop pagination
                if cutoff_date_reached:
                    scraper_logger.info(f"Stopping pagination: Found {projects_on_cutoff_date} projects on cutoff date")
                    break

                # If most projects on this page are outside the time range, stop scanning
                if projects_outside_range > 0 and projects_outside_range >= len(project_cards) * 0.7:  # 70% threshold
                    scraper_logger.info(f"Stopping scan: {projects_outside_range}/{len(project_cards)} projects on this page are outside time range")
                    break

                # Check for next page or load more functionality
                next_page_selector = website_config["level1_search"].get("next-page-selector")
                if not next_page_selector:
                    scraper_logger.info("No next page selector configured, stopping")
                    break

                # Check if it's a load more button
                load_more_button = soup.select_one(next_page_selector)
                if load_more_button and load_more_button.name == 'button':
                    # Handle load more button
                    if await self._load_more_projects(website_config, driver):
                        # Add a small delay after loading more content
                        time.sleep(2)
                        continue
                    else:
                        scraper_logger.info("No more projects to load, stopping")
                        break
                else:
                    # Handle traditional pagination
                    if load_more_button and load_more_button.get('href'):
                        next_page_url = load_more_button.get('href')
                        if not next_page_url.startswith('http'):
                            next_page_url = urljoin(driver.current_url, next_page_url)

                        # Navigate to next page
                        driver.get(next_page_url)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))
                        time.sleep(2)  # Small delay between pages
                        continue
                    else:
                        scraper_logger.info("No next page found, stopping pagination")
                        break

            scraper_logger.info(f"Completed scanning {page_count} pages/loads, processed {total_projects_processed} projects")

        except Exception as e:
            scraper_logger.error(f"Error during scanning: {e}")
        finally:
            if driver:
                driver.quit()

    async def scan_website(self, website_config: Dict[str, Any], time_range: int = 1, existing_project_data=None, scan_id: str = None) -> List[Dict[str, Any]]:
        """Scan website with pagination support, returning a list of all projects within time range."""
        projects = []
        async for project_data in self.scan_website_stream(website_config, time_range, existing_project_data, scan_id):
            projects.append(project_data)
        return projects

    async def scan_projects_stream(self, time_range=None):
        """
        Scan all configured websites for projects and yield results as they are found.

        Args:
            time_range (int, optional): Number of days to look back for projects.
                                      If None, all projects are included.

        Yields:
            dict: Project data as it is found
        """
        try:
            # Collect projects table content once at the beginning
            from backend.models.core_models import Project
            from backend.database import DatabaseHandler

            db_handler = DatabaseHandler()
            with db_handler.get_session() as session:
                existing_projects = session.query(Project).all()
                existing_project_data = {
                    project.url: {
                        'id': project.id,
                        'title': project.title,
                        'url': project.url,
                        'release_date': project.release_date,
                        'start_date': project.start_date,
                        'duration': project.duration,
                        'location': project.location,
                        'tenderer': project.tenderer,
                        'rate': project.rate,
                        'description': project.description,
                        'project_id': project.project_id,
                        'budget': project.budget,
                        'workload': project.workload
                    } for project in existing_projects
                }

            for website_config in self.config['websites']:
                try:
                    async for project_data in self.scan_website_stream(website_config, time_range, existing_project_data):
                        yield project_data
                except Exception as e:
                    logger.error(f"Error scanning website {website_config['level1_search']['name']}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in scan_projects_stream: {str(e)}")
            raise