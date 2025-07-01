"""
Mistral services for intelligently extracting project data from raw html.

This file is now considered STABLE and should not be changed unless explicitly requested.
"""

from mistralai import Mistral
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)

class MistralHandler:
    """Handler for Mistral AI API interactions."""

    def __init__(self, api_key: str):
        """Initialize the Mistral handler with API key."""
        try:
            self.client = Mistral(api_key=api_key)
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Error initializing Mistral client: {e}")
            self.logger.error("Please ensure your API key is valid.")
            raise

    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean and normalize JSON string to handle common formatting issues.

        Args:
            json_str (str): Raw JSON string

        Returns:
            str: Cleaned JSON string
        """
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Remove any leading/trailing whitespace
        json_str = json_str.strip()

        return json_str

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from various response formats including markdown code blocks.

        Args:
            response_text (str): The raw response text from Mistral API

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None if parsing fails
        """
        if not response_text or not isinstance(response_text, str):
            return None

        # Clean the response text
        text = response_text.strip()

        # Try to extract JSON from markdown code blocks
        # Pattern for ```json ... ``` or ``` ... ```
        json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_block_pattern, text, re.DOTALL)

        if match:
            json_str = match.group(1)
            json_str = self._clean_json_string(json_str)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON from code block: {e}")

        # Try to find JSON object directly in the text
        # Look for content that starts with { and ends with }
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            match = self._clean_json_string(match)
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # If no JSON found, try to parse the entire text as JSON
        text = self._clean_json_string(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            self.logger.warning("No valid JSON found in response")
            return None

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better requirement extraction."""
        if not text:
            return ""

        # Remove common prefixes and suffixes
        prefixes = ["required", "requirement", "must have", "should have", "needs"]
        suffixes = ["experience", "knowledge", "skills", "required", "preferred"]

        text = text.lower().strip()

        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()

        # Remove extra whitespace and normalize
        text = " ".join(text.split())
        return text

    def extract_clean_text(self, html: str) -> str:
        """
        Extracts and returns clean, visible text from raw HTML content.

        Args:
            html (str): Raw HTML as a string.

        Returns:
            str: Cleaned, visible text content.
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, and meta tags
        for element in soup(['script', 'style', 'meta', 'noscript', 'iframe']):
            element.decompose()

        # Get visible text and clean whitespace
        text = soup.get_text(separator=' ', strip=True)
        clean_text = ' '.join(text.split())
        return clean_text

    async def extract_project_details(self, text: str, scan_id: str = None) -> Dict[str, Any]:
        """Extract requirements from text using Mistral AI."""
        # Create structured logger for this scan
        if scan_id:
            mistral_logger = logging.getLogger(f"scan.{scan_id}.mistral")
        else:
            mistral_logger = self.logger

        try:
            if not text:
                return {}

            # Preprocess the text
            processed_text = self.preprocess_text(self.extract_clean_text(text))

            messages = [
                {
                    "role": "system",
                    "content": """You are a precise data extraction assistant. Extract project details from the provided text
                    and return them in a specific JSON format. IMPORTANT: Return ONLY the JSON object without any markdown formatting,
                    code blocks, or additional text. Do not wrap the response in ```json or ``` blocks. Preserve all German characters
                    (umlauts, etc.) exactly as they appear. Do not add any commentary or explanation, just return the JSON object.
                    The JSON must include these exact fields:
                    - title (string) - description (string)
                    - release_date (string in format DD.MM.YYYY)
                    - start_date  (string in format DD.MM.YYYY)
                    - location (string)
                    - tenderer (string)
                    - project_id (string)
                    - requirements_tf(dictionary of strings (requirement) and integers (Number of occurences on project-specific
                        web-page including title and description))
                    - workload (string)
                    - rate (string or number)
                    - duration (string)
                    - budget (string or number)"""
                },
                {
                    "role": "user",
                    "content": f"""Extract the following project details from this text:
                    - title i.e. the  title of the project
                    - Summary description of the project in no more than 60 words, focussing on details not mentioned
                        in the title or other fields.
                    - release_date, i.e. the date on which the project was published. This will most likely be written in the format
                       DD.MM.YYYY.
                    - start_date, i.e. the date on which the project is expected to start. This will most likely be written in the format
                       DD.MM.YYYY.
                    - location, i.e. the location where the project is to be fulfilled, possibly 'Remote' or 'Hybrid' or
                        'On-site' or 'Berlin' or another geographical designation
                    - tenderer, i.e. the company that is offering the project
                    - project_id, i.e anbieter-spezifischer-id for the project (string)
                    - requirements_tf, i.e. the skills ('Anforderungen', 'Qualifikationen', 'Fähigkeiten' or similar) required for
                        the project; If no requirements are mentioned explicitly, determine them from the project description
                        or from the project title. Requirements are to consist of two core words maximum e.g. 'Schreiben von
                        Dokumentation' is shortened to 'Dokumentation', 'Zielbild' instead of 'Entwicklung eines Zielbildes',
                        'marktverfügbare Systeme' instead of 'Kenntnis der auf dem Markt verfügbaren Systeme'. Please return
                        the requirements in the format of a dictionary with the requirement as the key and the number of
                        occurences on the project-specific web-page including title and description as the value.
                    - Workload, i.e. the workload of the project in hours per week ("Auslastung" in German). This will most likely be written in the format
                    - rate, i.e. the payment rate of the project in €/h or €/day or €/month or €/year
                    - duration, i.e. the duration of the project (e.g., "3 months", "6 weeks", "ongoing")
                    - budget, i.e. the total budget for the project in €
                    and return them in the specified JSON format. Preserve all German characters exactly as they appear.
                    \n\n{processed_text}"""
                }
            ]

            try:
                response = self.client.chat.complete(
                    model="mistral-large-latest",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2000
                )
                project_data = response.choices[0].message.content
            except Exception as e:
                mistral_logger.error(f"Error calling Mistral API: {str(e)}")
                return {}

            parsed_data = self._extract_json_from_response(project_data)
            if parsed_data:
                mistral_logger.info("Successfully parsed project data.")
                return parsed_data
            else:
                mistral_logger.warning("Could not extract valid JSON from response, returning fallback")
                return {}

        except Exception as e:
            mistral_logger.error(f"Error extracting project details with Mistral: {str(e)}")
            return {}

    async def extract_release_date(self, text: str, scan_id: str = None) -> Dict[str, Any]:
        """Extract release date from text using Mistral AI."""
        # Create structured logger for this scan
        if scan_id:
            mistral_logger = logging.getLogger(f"scan.{scan_id}.mistral")
        else:
            mistral_logger = self.logger

        try:
            if not text:
                return {}

            processed_text = self.extract_clean_text(text)

            messages = [
                {
                    "role": "system",
                    "content": """You are a precise data extraction assistant. Extract ONLY the release date from the provided text
                    and return it in a specific JSON format. IMPORTANT: Return ONLY the JSON object without any markdown formatting,
                    code blocks, or additional text. Do not wrap the response in ```json or ``` blocks. Preserve all German characters
                    (umlauts, etc.) exactly as they appear. Do not add any commentary or explanation, just return the JSON object.
                    The JSON must include only this field:
                    - release_date (string in format DD.MM.YYYY)"""
                },
                {
                    "role": "user",
                    "content": f"""Extract ONLY the release date from this text. The release date is the date on which the project was published.
                    This will most likely be written in the format DD.MM.YYYY. If no release date is found, return an empty object {{}}.
                    Preserve all German characters exactly as they appear.
                    \n\n{processed_text}"""
                }
            ]

            try:
                response = self.client.chat.complete(
                    model="mistral-large-latest",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500
                )
                release_date_data = response.choices[0].message.content
            except Exception as e:
                mistral_logger.error(f"Error calling Mistral API: {str(e)}")
                return {}

            parsed_data = self._extract_json_from_response(release_date_data)
            if parsed_data:
                return parsed_data
            else:
                return {}

        except Exception as e:
            mistral_logger.error(f"Error extracting release date with Mistral: {str(e)}")
            return {}