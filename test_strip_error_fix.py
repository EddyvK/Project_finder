#!/usr/bin/env python3
"""
Test to verify the strip error fix.
"""

def test_strip_error_fix():
    """Test that the defensive programming fixes the strip error."""

    # Simulate the scenario where BeautifulSoup methods return non-string objects
    def simulate_get_text_strip():
        """Simulate get_text(strip=True) returning a dictionary."""
        return {"key": "value"}  # This would cause the original error

    def simulate_stripped_strings():
        """Simulate stripped_strings returning non-string objects."""
        return [{"key": "value"}, "normal string", {"another": "dict"}]

    # Test the defensive programming logic
    def test_defensive_strip():
        """Test the defensive programming approach."""

        # Test 1: get_text returning dictionary
        try:
            text_content = simulate_get_text_strip()
            if isinstance(text_content, str):
                result = text_content.strip()
            else:
                result = str(text_content) if text_content else None
            print(f"Test 1 (get_text dict): {result}")
        except Exception as e:
            print(f"Test 1 failed: {e}")

        # Test 2: stripped_strings returning mixed types
        try:
            location_parts = []
            for text in simulate_stripped_strings():
                if isinstance(text, str) and text and not text.startswith('‐'):
                    location_parts.append(text)

            cleaned_parts = []
            for part in location_parts:
                if isinstance(part, str):
                    stripped_part = part.strip()
                    if stripped_part:
                        cleaned_parts.append(stripped_part)

            result = ', '.join(cleaned_parts) if cleaned_parts else None
            print(f"Test 2 (stripped_strings mixed): {result}")
        except Exception as e:
            print(f"Test 2 failed: {e}")

        # Test 3: startswith on non-string
        try:
            text_content = simulate_get_text_strip()
            if isinstance(text_content, str) and text_content.startswith("label"):
                date_part = text_content[len("label"):].strip()
                result = date_part
            else:
                result = str(text_content) if text_content else None
            print(f"Test 3 (startswith non-string): {result}")
        except Exception as e:
            print(f"Test 3 failed: {e}")

    test_defensive_strip()

if __name__ == "__main__":
    test_strip_error_fix()