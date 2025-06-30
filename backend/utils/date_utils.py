"""
Date utility functions for handling European date format (DD.MM.YYYY)
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def is_valid_european_date(date_string: str) -> bool:
    """
    Validates if a string contains a valid European date format (DD.MM.YYYY)

    Args:
        date_string: Date string to validate

    Returns:
        bool: True if valid European date format found, False otherwise
    """
    if not date_string or not isinstance(date_string, str):
        return False

    # Find European date pattern in the string
    european_date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
    match = re.search(european_date_pattern, date_string.strip())

    if not match:
        return False

    # Extract components
    day, month, year = match.groups()
    day_num = int(day)
    month_num = int(month)
    year_num = int(year)

    # Basic validation
    if year_num < 1900 or year_num > 2100:
        return False
    if month_num < 1 or month_num > 12:
        return False
    if day_num < 1 or day_num > 31:
        return False

    # Check for valid days in month
    try:
        # Create date to validate day exists in month
        datetime(year_num, month_num, day_num)
        return True
    except ValueError:
        return False


def european_to_iso_date(date_string: str) -> Optional[str]:
    """
    Converts European date format (DD.MM.YYYY) to ISO date format (YYYY-MM-DD)
    Uses regex to find the date component in strings that may contain additional text

    Args:
        date_string: String containing date in DD.MM.YYYY format

    Returns:
        str: Date in YYYY-MM-DD format or None if invalid
    """
    if not date_string:
        return None

    # Find European date pattern in the string
    european_date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
    match = re.search(european_date_pattern, date_string.strip())

    if not match:
        return None

    day, month, year = match.groups()

    # Validate the extracted date
    try:
        day_num = int(day)
        month_num = int(month)
        year_num = int(year)

        # Basic validation
        if year_num < 1900 or year_num > 2100:
            return None
        if month_num < 1 or month_num > 12:
            return None
        if day_num < 1 or day_num > 31:
            return None

        # Create date to validate day exists in month
        datetime(year_num, month_num, day_num)

        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except ValueError:
        return None


def iso_to_european_date(iso_date: str) -> Optional[str]:
    """
    Converts ISO date format (YYYY-MM-DD) to European date format (DD.MM.YYYY)

    Args:
        iso_date: Date in YYYY-MM-DD format

    Returns:
        str: Date in DD.MM.YYYY format or None if invalid
    """
    if not iso_date:
        return None

    try:
        date_obj = datetime.fromisoformat(iso_date)
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return None


def parse_european_date_components(date_string: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse European date string into day, month, year components

    Args:
        date_string: Date in DD.MM.YYYY format

    Returns:
        Tuple[int, int, int]: (day, month, year) or None if invalid
    """
    if not is_valid_european_date(date_string):
        return None

    european_date_pattern = r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$'
    match = re.match(european_date_pattern, date_string.strip())

    if not match:
        return None

    day, month, year = match.groups()
    return int(day), int(month), int(year)


def format_date_for_display(date_string: str) -> str:
    """
    Formats a date string for display, handling both European and ISO formats

    Args:
        date_string: Date string in various formats

    Returns:
        str: Formatted date string or original if parsing fails
    """
    if not date_string:
        return "N/A"

    # Handle European date format (DD.MM.YYYY)
    if is_valid_european_date(date_string):
        iso_date = european_to_iso_date(date_string)
        if iso_date:
            try:
                date_obj = datetime.fromisoformat(iso_date)
                return date_obj.strftime("%d.%m.%Y")
            except ValueError:
                pass

    # Fallback: try to parse as ISO date
    try:
        date_obj = datetime.fromisoformat(date_string)
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return date_string  # Return original string if parsing fails


def get_current_date_european() -> str:
    """
    Gets the current date in European format

    Returns:
        str: Current date in DD.MM.YYYY format
    """
    return datetime.now().strftime("%d.%m.%Y")


def compare_european_dates(date1: str, date2: str) -> int:
    """
    Compares two dates in European format

    Args:
        date1: First date in DD.MM.YYYY format
        date2: Second date in DD.MM.YYYY format

    Returns:
        int: -1 if date1 < date2, 0 if equal, 1 if date1 > date2
    """
    iso1 = european_to_iso_date(date1)
    iso2 = european_to_iso_date(date2)

    if not iso1 or not iso2:
        return 0

    try:
        d1 = datetime.fromisoformat(iso1)
        d2 = datetime.fromisoformat(iso2)

        if d1 < d2:
            return -1
        elif d1 > d2:
            return 1
        else:
            return 0
    except ValueError:
        return 0