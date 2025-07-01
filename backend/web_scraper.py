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

# Suppress noisy logging from external libraries
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.ERROR)

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

        # Suppress DevTools and TensorFlow warnings
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")  # Only fatal errors
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Suppress DevTools listening messages
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

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

            # Check if load more button exists and is visible
            try:
                load_more_button = driver.find_element(By.CSS_SELECTOR, next_page_selector)
                if not load_more_button.is_displayed():
                    logger.info("Load more button is not visible, no more projects to load")
                    return False
            except Exception:
                logger.info("Load more button not found, no more projects to load")
                return False

            # Get current project count
            project_entry_selector = website_config["level1_search"]["project-entry-selector"]
            current_count = len(driver.find_elements(By.CSS_SELECTOR, project_entry_selector))

            # Click the button
            driver.execute_script("arguments[0].click();", load_more_button)
            logger.info("Clicked load more button")

            # Wait for new content to load (wait for more projects to appear)
            try:
                wait = WebDriverWait(driver, 10)
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

    async def level3_scan(self, project_url: str, scan_id: str = None, website_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Take a single URL, return requirements using Mistral AI."""
        if not self.mistral_handler:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.warning("Mistral handler not available for Level 3 scan")
            return {"requirements": []}

        # Check if this is a Randstad project that needs external URL extraction
        if website_config and website_config.get("level3_search"):
            try:
                external_url = await self._extract_external_url(project_url, website_config, scan_id)
                if external_url:
                    # Use the external URL for the actual level3 scan
                    return await self._extract_project_data_with_mistral(external_url, scan_id)
                else:
                    # Fallback to original URL if external URL extraction fails
                    if scan_id:
                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                    else:
                        scraper_logger = logging.getLogger(__name__)
                    scraper_logger.warning(f"Failed to extract external URL from {project_url}, using original URL")
                    return await self._extract_project_data_with_mistral(project_url, scan_id)
            except Exception as e:
                if scan_id:
                    scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                else:
                    scraper_logger = logging.getLogger(__name__)
                scraper_logger.error(f"Error extracting external URL: {e}, using original URL")
                return await self._extract_project_data_with_mistral(project_url, scan_id)

        # Default behavior for other websites
        return await self._extract_project_data_with_mistral(project_url, scan_id)

    async def _extract_external_url(self, project_url: str, website_config: Dict[str, Any], scan_id: str = None) -> str:
        """Extract the external project URL from the project detail page."""
        try:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)

            scraper_logger.info(f"Extracting external URL from project detail page: {project_url}")

            # Load the project detail page
            driver = self.setup_driver()
            driver.get(project_url)

            # Wait for page to load
            time.sleep(3)

            # Get the page source
            page_source = driver.page_source
            driver.quit()

            # Parse the HTML
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find the external URL link using the selector from config
            level3_config = website_config["level3_search"]
            external_url_selector = level3_config.get("external-url-selector")
            external_url_param = level3_config.get("external-url-param", "project_url")

            if not external_url_selector:
                scraper_logger.warning("No external URL selector configured")
                return None

            # Find the link element
            link_element = soup.select_one(external_url_selector)
            if not link_element:
                scraper_logger.warning(f"No external URL link found with selector: {external_url_selector}")
                return None

            # Extract the href attribute
            href = link_element.get('href')
            if not href:
                scraper_logger.warning("No href attribute found in external URL link")
                return None

            # Parse the URL to extract the project_url parameter
            from urllib.parse import urlparse, parse_qs, unquote

            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)

            if external_url_param not in query_params:
                scraper_logger.warning(f"Parameter '{external_url_param}' not found in URL: {href}")
                return None

            # Get and decode the external URL
            encoded_external_url = query_params[external_url_param][0]
            external_url = unquote(encoded_external_url)

            scraper_logger.info(f"Successfully extracted external URL: {external_url}")
            return external_url

        except Exception as e:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.error(f"Error extracting external URL: {e}")
            return None

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

    async def quick_level3_scan(self, project_url: str, scan_id: str = None, website_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Quick level3 scan to get just the release date for filtering."""
        if not self.mistral_handler:
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.warning("Mistral handler not available for quick Level 3 scan")
            return {"release_date": None}

        try:
            # Check if this is a Randstad project that needs external URL extraction
            if website_config and website_config.get("level3_search"):
                try:
                    external_url = await self._extract_external_url(project_url, website_config, scan_id)
                    if external_url:
                        # Use the external URL for the quick level3 scan
                        project_url = external_url
                    else:
                        # Fallback to original URL if external URL extraction fails
                        if scan_id:
                            scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                        else:
                            scraper_logger = logging.getLogger(__name__)
                        scraper_logger.warning(f"Failed to extract external URL from {project_url} for quick scan, using original URL")
                except Exception as e:
                    if scan_id:
                        scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
                    else:
                        scraper_logger = logging.getLogger(__name__)
                    scraper_logger.error(f"Error extracting external URL for quick scan: {e}, using original URL")

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

    def _consolidate_data(self, level2_data: Dict[str, Any], level3_data: Dict[str, Any], scan_id: str = None) -> Dict[str, Any]:
        l2d = ensure_parsed_json(level2_data)
        l3d = ensure_parsed_json(level3_data)
        consolidated = {}
        consolidated.update(l2d)

        # Handle requirements with term frequency (new format)
        # Check for both old "requirements" and new "requirements_tf" fields
        l2_requirements = l2d.get("requirements_tf", l2d.get("requirements", {}))
        l3_requirements = l3d.get("requirements_tf", l3d.get("requirements", {}))

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

        # Store as requirements_tf (new format)
        consolidated["requirements_tf"] = merged_requirements

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

        # Add fallback for start_date if missing or invalid
        if not consolidated.get('start_date') or consolidated.get('start_date') == 'N/A' or consolidated.get('start_date') == 'Invalid Date':
            from backend.utils.date_utils import get_current_date_european
            current_date = get_current_date_european()
            consolidated['start_date'] = current_date
            if scan_id:
                scraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
            else:
                scraper_logger = logging.getLogger(__name__)
            scraper_logger.info(f"Using current date as fallback for start_date: {current_date}")

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

        # Initialize current_url with the site URL
        current_url = website_config["level1_search"]["site_url"]
        page_count = 0
        total_projects_processed = 0
        driver = None
        processed_project_urls = set()

        try:
            # Initialize driver for the entire scanning session
            driver = self.setup_driver()
            wait = WebDriverWait(driver, 10)
            project_list_selector = website_config["level1_search"]["project-list-selector"]
            stop_pagination = False

            # Second loop: Loop through each page with pagination support
            while not stop_pagination:
                # Navigate to current page at the beginning of the loop
                scraper_logger.info(f"Starting iteration with URL: {current_url}")
                driver.get(current_url)

                # Wait for project list to load
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, project_list_selector)))

                if website_config['level1_search']['next-page-selector'] == "N/A":
                    stop_pagination = True
                    scraper_logger.info("Pagination disabled (N/A), stopping after current page")

                # Debug: Check if load-more-selector exists in config
                scraper_logger.info(f"Checking for load-more-selector in config: {'load-more-selector' in website_config['level1_search']}")
                if "load-more-selector" in website_config['level1_search']:
                    scraper_logger.info(f"Load-more-selector found: {website_config['level1_search']['load-more-selector']}")

                # Download all projects available with load more button
                if "load-more-selector" in website_config['level1_search']:
                    scraper_logger.info("Downloading all projects with load more button")
                    load_more_selector = website_config['level1_search']['load-more-selector']

                    # Keep clicking load more until no more projects can be loaded
                    load_more_attempts = 0
                    max_load_more_attempts = 50  # Prevent infinite loops

                    while load_more_attempts < max_load_more_attempts:
                        try:
                            # Get current project count before clicking
                            current_soup = BeautifulSoup(driver.page_source, 'html.parser')
                            current_project_grid = current_soup.select_one(project_list_selector)
                            current_project_count = len(current_project_grid.select(website_config["level1_search"]["project-entry-selector"])) if current_project_grid else 0

                            scraper_logger.info(f"Current project count: {current_project_count}")

                            # Debug: Check if load more button exists in the HTML
                            load_more_elements = current_soup.select(load_more_selector)
                            scraper_logger.info(f"Found {len(load_more_elements)} load more elements with selector: {load_more_selector}")

                            if len(load_more_elements) == 0:
                                scraper_logger.info("No load more button found in HTML, all projects loaded")
                                break

                            # Try to find and click the load more button using Selenium
                            try:
                                load_more_button = driver.find_element(By.CSS_SELECTOR, load_more_selector)
                                scraper_logger.info(f"Found load more button: {load_more_button.text}")

                                if not load_more_button.is_displayed():
                                    scraper_logger.info("Load more button is not visible, all projects loaded")
                                    break

                                # Click the load more button
                                driver.execute_script("arguments[0].click();", load_more_button)
                                scraper_logger.info(f"Clicked load more button (attempt {load_more_attempts + 1})")

                            except Exception as button_error:
                                scraper_logger.warning(f"Error finding/clicking load more button: {button_error}")
                                # Try alternative approach - find by text content
                                try:
                                    buttons = driver.find_elements(By.TAG_NAME, "button")
                                    load_more_button = None
                                    for button in buttons:
                                        if "weitere Projekte laden" in button.text or "load more" in button.text.lower():
                                            load_more_button = button
                                            break

                                    if load_more_button and load_more_button.is_displayed():
                                        driver.execute_script("arguments[0].click();", load_more_button)
                                        scraper_logger.info(f"Clicked load more button by text (attempt {load_more_attempts + 1})")
                                    else:
                                        scraper_logger.info("No load more button found by text, all projects loaded")
                                        break
                                except Exception as text_error:
                                    scraper_logger.warning(f"Error with text-based button search: {text_error}")
                                    break

                            # Wait for new content to load
                            time.sleep(3)

                            # Check if new projects were loaded
                            new_soup = BeautifulSoup(driver.page_source, 'html.parser')
                            new_project_grid = new_soup.select_one(project_list_selector)
                            new_project_count = len(new_project_grid.select(website_config["level1_search"]["project-entry-selector"])) if new_project_grid else 0

                            scraper_logger.info(f"New project count: {new_project_count}")

                            if new_project_count <= current_project_count:
                                scraper_logger.info(f"No new projects loaded (prev: {current_project_count}, new: {new_project_count}), stopping load more")
                                break
                            else:
                                scraper_logger.info(f"Successfully loaded {new_project_count - current_project_count} new projects")

                            load_more_attempts += 1

                        except Exception as e:
                            scraper_logger.warning(f"Error during load more attempt {load_more_attempts + 1}: {e}")
                            break

                    scraper_logger.info(f"Load more process completed after {load_more_attempts} attempts")

                page_count += 1
                scraper_logger.info(f"Scanning page/load {page_count}")

                # Get current page content
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                project_grid = soup.select_one(project_list_selector)

                try:
                    project_cards = project_grid.select(website_config["level1_search"]["project-entry-selector"])
                    scraper_logger.info(f"Found {len(project_cards)} project cards on current page")
                except Exception as e:
                    scraper_logger.error(f"Error finding project cards: {e}")
                    stop_pagination = True
                    break

                # Third (inner) loop: Process each project card on the current page
                for project_index, project_card in enumerate(project_cards, 1):
                    try:
                        # Extract level 2 data
                        project_level_2_data = await self.level2_scan(project_card, website_config, scan_id)

                        # Check, based on the project_level_2_data, whether this project is already in the database
                        # Do this BEFORE any level3 scans to avoid unnecessary AI calls
                        if existing_project_data:
                            project_url = project_level_2_data.get('url')
                            if project_url and project_url in existing_project_data:
                                db_project = existing_project_data[project_url]
                                scraper_logger.info(f"Page {page_count}, Project {project_index}: {db_project['title']} already in database, skipping further processing")
                                continue  # Skip this project but continue with the next one

                        # Check if we have release_date from level2, if not we'll need level3
                        release_date = project_level_2_data.get('release_date')
                        title = project_level_2_data.get('title', 'Unknown')

                        if release_date: # If we have a release date and its outside the time range, we can spare the level3 scan
                            if not self._is_within_time_range(release_date, time_range):
                                # Skip date-based filtering for top projects
                                if self._is_top_project(project_card):
                                    scraper_logger.info(f"Page {page_count}, Project {project_index}: Found top project outside time range: {title} (release date: {release_date}) - including anyway")
                                else:
                                    scraper_logger.info(f"Page {page_count}, Project {project_index}: Non-top project outside time range found: {title} (release date: {release_date}) - stopping pagination")
                                    stop_pagination = True
                                    break  # Break out of the project loop immediately

                        scraper_logger.info(f"Page {page_count}, Project {project_index}: Checking project: {title} with release date: {release_date}")

                        # Project passed filtering - now do the full level3 scan for all detailed data
                        project_url = project_level_2_data.get('url')
                        if project_url:
                            project_level_3_data = await self.level3_scan(project_url, scan_id, website_config)
                        else:
                            project_level_3_data = {"requirements_tf": {}}

                        # Consolidate all data (level2 + full level3)
                        consolidated_data = self._consolidate_data(project_level_2_data, project_level_3_data, scan_id)
                        if "url" not in consolidated_data and project_level_2_data.get('url'):
                            consolidated_data["url"] = project_level_2_data['url']

                        total_projects_processed += 1
                        scraper_logger.info(f"Page {page_count}, Project {project_index}: Processed project {total_projects_processed}: {consolidated_data.get('title', 'Unknown')}")

                        yield consolidated_data

                    except Exception as e:
                        scraper_logger.error(f"Page {page_count}, Project {project_index}: Error processing project card: {e}")
                        continue

                # Check if we need to stop pagination due to time range filtering
                if stop_pagination:
                    scraper_logger.info(f"Stopping pagination due to non-top project outside time range found on page {page_count}")
                    break



                # Check for next page or load more functionality
                next_page_selector = website_config["level1_search"].get("next-page-selector")
                if not next_page_selector:
                    scraper_logger.info("No next page selector configured, stopping")
                    break

                # Get fresh soup for pagination check
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Special handling for Freelancermap pagination
                if website_config['level1_search']['name'] == 'Freelancermap':
                    # Find all pagination links and get the next page
                    pagination_links = soup.select(next_page_selector)
                    next_page_element = None
                    current_page_num = 1

                    # Try to extract current page number from URL
                    current_url = driver.current_url
                    if 'pagenr=' in current_url:
                        try:
                            current_page_num = int(current_url.split('pagenr=')[1].split('&')[0])
                        except (ValueError, IndexError):
                            current_page_num = 1

                    # Find the link to the next page
                    for link in pagination_links:
                        href = link.get('href', '')
                        if 'pagenr=' in href:
                            try:
                                page_num = int(href.split('pagenr=')[1].split('&')[0])
                                if page_num == current_page_num + 1:
                                    next_page_element = link
                                    break
                            except (ValueError, IndexError):
                                continue

                    scraper_logger.info(f"Freelancermap pagination: current page {current_page_num}, found {len(pagination_links)} pagination links")

                    # If no next page found, try alternative approach
                    if not next_page_element:
                        scraper_logger.info("No next page found with current logic, trying alternative approach")
                        # Look for any link with a higher page number
                        for link in pagination_links:
                            href = link.get('href', '')
                            if 'pagenr=' in href:
                                try:
                                    page_num = int(href.split('pagenr=')[1].split('&')[0])
                                    if page_num > current_page_num:
                                        next_page_element = link
                                        scraper_logger.info(f"Found alternative next page: {page_num}")
                                        break
                                except (ValueError, IndexError):
                                    continue
                else:
                    # Standard pagination handling for other websites
                    next_page_element = soup.select_one(next_page_selector)

                # Debug pagination
                if next_page_element:
                    scraper_logger.info(f"Found next page element: {next_page_element.name}, href: {next_page_element.get('href', 'None')}")
                else:
                    scraper_logger.info(f"No next page element found with selector: {next_page_selector}")

                # Determine pagination type and handle accordingly
                if next_page_element and next_page_element.name == 'button':
                    # LOAD MORE PAGINATION: Projects are appended to the same page
                    # Need session duplicate tracking to avoid reprocessing
                    scraper_logger.info("Detected LOAD MORE pagination")

                    prev_project_count = len(project_cards)

                    # Check if load more button is still visible and clickable
                    try:
                        load_more_button = driver.find_element(By.CSS_SELECTOR, next_page_selector)
                        if not load_more_button.is_displayed():
                            scraper_logger.info("Load more button is not visible, stopping pagination")
                            break
                    except Exception:
                        scraper_logger.info("Load more button not found, stopping pagination")
                        break

                    # Try to load more projects
                    if await self._load_more_projects(website_config, driver):
                        # Add a small delay after loading more content
                        time.sleep(2)
                        # Get new project count and updated project list
                        soup_after = BeautifulSoup(driver.page_source, 'html.parser')
                        project_grid_after = soup_after.select_one(project_list_selector)
                        project_cards_after = project_grid_after.select(website_config["level1_search"]["project-entry-selector"]) if project_grid_after else []
                        new_project_count = len(project_cards_after)

                        # Check if we actually got new projects
                        if new_project_count <= prev_project_count:
                            scraper_logger.info(f"No new projects loaded after clicking load more (prev: {prev_project_count}, new: {new_project_count}), stopping scan to prevent infinite loop.")
                            break
                        else:
                            scraper_logger.info(f"Successfully loaded {new_project_count - prev_project_count} new projects (prev: {prev_project_count}, new: {new_project_count})")
                            # Update the project_cards list to include the newly loaded projects
                            project_cards = project_cards_after
                            # Continue the outer while loop to process the newly loaded projects
                            # Session duplicate tracking will handle skipping already processed projects
                            continue
                    else:
                        scraper_logger.info("Load more button not found or not clickable, stopping")
                        break

                elif next_page_element and (next_page_element.name == 'link' or next_page_element.name == 'a'):
                    # NEXT PAGE PAGINATION: Projects are on separate pages
                    # No session duplicate tracking needed since we're on a new page
                    scraper_logger.info("Detected NEXT PAGE pagination")

                    next_page_url = next_page_element.get('href')
                    if next_page_url:
                        if not next_page_url.startswith('http'):
                            next_page_url = urljoin(driver.current_url, next_page_url)

                        scraper_logger.info(f"Next page URL determined: {next_page_url}")
                        # Update current_url for next iteration
                        current_url = next_page_url
                        # Add a small delay to ensure page is fully loaded
                        time.sleep(2)
                        # Break out of the inner loop to continue with the new URL in the outer loop
                        scraper_logger.info("Breaking inner loop to continue with new URL in outer loop")
                        scraper_logger.info(f"Will continue with URL: {current_url}")
                        break
                    else:
                        scraper_logger.info("No next page URL found, stopping pagination")
                        break
                else:
                    scraper_logger.info("No next page element found, stopping pagination")
                    scraper_logger.info(f"Current URL: {driver.current_url}")
                    scraper_logger.info(f"Available pagination links: {[link.get('href', 'None') for link in soup.select(next_page_selector)]}")
                    break

            scraper_logger.info(f"Completed scanning {page_count} pages/loads, processed {total_projects_processed} projects")
            scraper_logger.info(f"Final stop_pagination value: {stop_pagination}")

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