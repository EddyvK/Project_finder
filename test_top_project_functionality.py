#!/usr/bin/env python3
"""
Test script to verify that top project functionality is working correctly.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from web_scraper import WebScraper
from bs4 import BeautifulSoup

def test_top_project_functionality():
    """Test that top projects are correctly identified and not excluded from date-based filtering."""
    print("Testing top project functionality...")

    try:
        scraper = WebScraper()

        # Test 1: Check _is_top_project method
        print("\n=== Test 1: _is_top_project method ===")

        # Create a mock project card with top-project class
        html_with_top_class = '<div class="project-container top-project"><div class="title">Test Project</div></div>'
        soup = BeautifulSoup(html_with_top_class, 'html.parser')
        project_card_with_class = soup.find('div')

        is_top = scraper._is_top_project(project_card_with_class)
        print(f"Project with 'top-project' class: {is_top}")
        assert is_top, "Project with 'top-project' class should be identified as top project"

        # Create a mock project card with top-project-badge
        html_with_badge = '<div class="project-container"><div class="top-project-badge">Top</div><div class="title">Test Project</div></div>'
        soup = BeautifulSoup(html_with_badge, 'html.parser')
        project_card_with_badge = soup.find('div')

        is_top = scraper._is_top_project(project_card_with_badge)
        print(f"Project with 'top-project-badge': {is_top}")
        assert is_top, "Project with 'top-project-badge' should be identified as top project"

        # Create a mock regular project card
        html_regular = '<div class="project-container"><div class="title">Test Project</div></div>'
        soup = BeautifulSoup(html_regular, 'html.parser')
        project_card_regular = soup.find('div')

        is_top = scraper._is_top_project(project_card_regular)
        print(f"Regular project: {is_top}")
        assert not is_top, "Regular project should not be identified as top project"

        print("✅ _is_top_project method works correctly")

        # Test 2: Check that top project logic is present in the code
        print("\n=== Test 2: Top project logic in code ===")

        with open('backend/web_scraper.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for top project exclusions in date-based logic
        assert 'Found top project significantly outside time range' in content, "Top project exclusion for significantly outside range should exist"
        assert 'Found top project on cutoff date' in content, "Top project exclusion for cutoff date should exist"
        assert 'Found top project outside time range' in content, "Top project exclusion for outside time range should exist"

        print("✅ Top project exclusions are present in date-based logic")

        # Test 3: Check that the method signature is correct
        print("\n=== Test 3: Method signature ===")

        import inspect
        sig = inspect.signature(scraper._is_top_project)
        param_count = len(sig.parameters)
        print(f"_is_top_project has {param_count} parameters: {list(sig.parameters.keys())}")
        assert param_count == 2, f"_is_top_project should have 2 parameters (self + project_card), got {param_count}"
        print("✅ _is_top_project method signature is correct")

        print("\n✅ All top project functionality tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_top_project_functionality()
    sys.exit(0 if success else 1)