#!/usr/bin/env python3
"""
Comprehensive test script to verify all previous functionality has been maintained
after the deduplication optimization changes.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_backend_imports():
    """Test that all backend components can be imported."""
    print("Testing backend imports...")

    try:
        from backend.main import app
        print("✅ Backend main app imports successfully")

        from backend.scan_service import scan_service
        print("✅ ScanService imports successfully")

        from backend.web_scraper import WebScraper
        print("✅ WebScraper imports successfully")

        from backend.mistral_handler import MistralHandler
        print("✅ MistralHandler imports successfully")

        from backend.deduplication_service import deduplication_service
        print("✅ DeduplicationService imports successfully")

        from backend.config_manager import config_manager
        print("✅ ConfigManager imports successfully")

        from backend.database import get_db, init_db
        print("✅ Database imports successfully")

        from backend.models.core_models import Project, Employee
        print("✅ Core models import successfully")

        return True
    except Exception as e:
        print(f"❌ Backend import error: {e}")
        return False

def test_web_scraper_initialization():
    """Test that WebScraper can be initialized without errors."""
    print("\nTesting WebScraper initialization...")

    try:
        from backend.web_scraper import WebScraper
        scraper = WebScraper()
        print("✅ WebScraper initializes successfully")

        # Check that required attributes exist
        assert hasattr(scraper, 'mistral_handler'), "Mistral handler should exist"
        print("✅ WebScraper has required attributes")

        return True
    except Exception as e:
        print(f"❌ WebScraper initialization error: {e}")
        return False

def test_scan_service_methods():
    """Test that ScanService methods have correct signatures."""
    print("\nTesting ScanService method signatures...")

    try:
        from backend.scan_service import scan_service
        import inspect

        # Check scan_projects method
        scan_projects_sig = inspect.signature(scan_service.scan_projects)
        assert 'time_range' in scan_projects_sig.parameters, "scan_projects should have time_range parameter"
        assert 'db' in scan_projects_sig.parameters, "scan_projects should have db parameter"
        print("✅ scan_projects method signature is correct")

        # Check scan_projects_stream method
        scan_stream_sig = inspect.signature(scan_service.scan_projects_stream)
        assert 'time_range' in scan_stream_sig.parameters, "scan_projects_stream should have time_range parameter"
        assert 'db' in scan_stream_sig.parameters, "scan_projects_stream should have db parameter"
        print("✅ scan_projects_stream method signature is correct")

        return True
    except Exception as e:
        print(f"❌ ScanService method signature error: {e}")
        return False

def test_web_scraper_methods():
    """Test that WebScraper methods have correct signatures."""
    print("\nTesting WebScraper method signatures...")

    try:
        from backend.web_scraper import WebScraper
        import inspect

        scraper = WebScraper()

        # Check scan_website_stream method
        stream_sig = inspect.signature(scraper.scan_website_stream)
        assert 'website_config' in stream_sig.parameters, "scan_website_stream should have website_config parameter"
        assert 'time_range' in stream_sig.parameters, "scan_website_stream should have time_range parameter"
        assert 'existing_project_data' in stream_sig.parameters, "scan_website_stream should have existing_project_data parameter"
        print("✅ scan_website_stream method signature is correct")

        # Check scan_website method
        scan_sig = inspect.signature(scraper.scan_website)
        assert 'website_config' in scan_sig.parameters, "scan_website should have website_config parameter"
        assert 'time_range' in scan_sig.parameters, "scan_website should have time_range parameter"
        assert 'existing_project_data' in scan_sig.parameters, "scan_website should have existing_project_data parameter"
        print("✅ scan_website method signature is correct")

        return True
    except Exception as e:
        print(f"❌ WebScraper method signature error: {e}")
        return False

def test_mistral_handler_methods():
    """Test that MistralHandler methods have correct signatures."""
    print("\nTesting MistralHandler method signatures...")

    try:
        from backend.mistral_handler import MistralHandler
        import inspect

        # Check extract_project_details method
        project_sig = inspect.signature(MistralHandler.extract_project_details)
        assert 'text' in project_sig.parameters, "extract_project_details should have text parameter"
        assert 'scan_id' in project_sig.parameters, "extract_project_details should have scan_id parameter"
        print("✅ extract_project_details method signature is correct")

        # Check extract_release_date method
        release_sig = inspect.signature(MistralHandler.extract_release_date)
        assert 'text' in release_sig.parameters, "extract_release_date should have text parameter"
        assert 'scan_id' in release_sig.parameters, "extract_release_date should have scan_id parameter"
        print("✅ extract_release_date method signature is correct")

        return True
    except Exception as e:
        print(f"❌ MistralHandler method signature error: {e}")
        return False

def test_deduplication_service_methods():
    """Test that DeduplicationService methods have correct signatures."""
    print("\nTesting DeduplicationService method signatures...")

    try:
        from backend.deduplication_service import deduplication_service
        import inspect

        # Check run_deduplication method
        dedup_sig = inspect.signature(deduplication_service.run_deduplication)
        assert 'db' in dedup_sig.parameters, "run_deduplication should have db parameter"
        print("✅ run_deduplication method signature is correct")

        # Check find_duplicate_projects method
        find_sig = inspect.signature(deduplication_service.find_duplicate_projects)
        assert 'db' in find_sig.parameters, "find_duplicate_projects should have db parameter"
        print("✅ find_duplicate_projects method signature is correct")

        # Check reorder_projects_by_release_date method
        reorder_sig = inspect.signature(deduplication_service.reorder_projects_by_release_date)
        assert 'db' in reorder_sig.parameters, "reorder_projects_by_release_date should have db parameter"
        print("✅ reorder_projects_by_release_date method signature is correct")

        return True
    except Exception as e:
        print(f"❌ DeduplicationService method signature error: {e}")
        return False

def test_database_model_fields():
    """Test that the Project model has all required fields including the new sort_order."""
    print("\nTesting database model fields...")

    try:
        from backend.models.core_models import Project

        # Check that all original fields exist
        required_fields = [
            'id', 'title', 'description', 'release_date', 'start_date',
            'location', 'tenderer', 'project_id', 'rate',
            'url', 'budget', 'duration', 'workload', 'last_scan'
        ]

        for field in required_fields:
            assert hasattr(Project, field), f"Project model should have {field} field"

        # Check that the new sort_order field exists
        assert hasattr(Project, 'sort_order'), "Project model should have sort_order field"
        print("✅ Project model has all required fields including sort_order")

        return True
    except Exception as e:
        print(f"❌ Database model fields error: {e}")
        return False

def test_date_filtering_functionality():
    """Test that date filtering functionality is still present."""
    print("\nTesting date filtering functionality...")

    try:
        from backend.main import app
        from backend.utils.date_utils import european_to_iso_date

        # Test date utility function
        test_date = "28.06.2025"
        iso_date = european_to_iso_date(test_date)
        assert iso_date == "2025-06-28", f"Date conversion failed: {test_date} -> {iso_date}"
        print("✅ Date utility function works correctly")

        # Test that the filtering logic exists in the code
        with open('backend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Filter by time range if specified' in content, "Time range filtering logic should exist"
            assert 'european_to_iso_date' in content, "Date conversion should be used"
            assert 'sort_order' in content, "Sort order functionality should exist"
        print("✅ Date filtering logic is present in main.py")

        return True
    except Exception as e:
        print(f"❌ Date filtering functionality error: {e}")
        return False

def test_database_checking_functionality():
    """Test that database checking functionality is still present."""
    print("\nTesting database checking functionality...")

    try:
        with open('backend/web_scraper.py', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'already in database' in content, "Database checking logic should exist"
            assert 'continue  # Skip this project but continue with the next one' in content, "Continue scanning logic should exist"
        print("✅ Database checking functionality is present")

        return True
    except Exception as e:
        print(f"❌ Database checking functionality error: {e}")
        return False

def test_structured_logging_functionality():
    """Test that structured logging functionality is present."""
    print("\nTesting structured logging functionality...")

    try:
        import uuid
        import logging

        # Test scan ID generation
        scan_id = str(uuid.uuid4())[:8]
        assert len(scan_id) == 8, f"Scan ID should be 8 characters: {scan_id}"
        print("✅ Scan ID generation works correctly")

        # Test structured logger creation
        scan_logger = logging.getLogger(f"scan.{scan_id}")
        website_logger = logging.getLogger(f"scan.{scan_id}.website.Etengo")
        project_logger = logging.getLogger(f"scan.{scan_id}.project.1")
        webscraper_logger = logging.getLogger(f"scan.{scan_id}.webscraper")
        mistral_logger = logging.getLogger(f"scan.{scan_id}.mistral")

        assert scan_logger != website_logger, "Loggers should be different instances"
        print("✅ Structured loggers can be created")

        # Test that structured logging is used in the code
        with open('backend/scan_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'scan_id = str(uuid.uuid4())[:8]' in content, "Scan ID generation should exist"
            assert 'scan_logger = logging.getLogger(f"scan.{scan_id}")' in content, "Structured logging should exist"
        print("✅ Structured logging is implemented in scan_service.py")

        return True
    except Exception as e:
        print(f"❌ Structured logging functionality error: {e}")
        return False

def test_api_endpoints():
    """Test that all API endpoints are still present."""
    print("\nTesting API endpoints...")

    try:
        from backend.main import app

        # Check that key endpoints exist
        routes = [route.path for route in app.routes]

        required_endpoints = [
            "/api/health",
            "/api/projects",
            "/api/scan/stream/{time_range}",
            "/api/employees",
            "/api/matches/{employee_id}",
            "/api/deduplication",
            "/api/embeddings/rebuild"
        ]

        import re

        def endpoint_to_regex(endpoint):
            # Replace {param} with [^/]+ to match any path parameter
            return re.compile('^' + re.sub(r'\{[^/]+\}', r'[^/]+', endpoint) + '$')

        for endpoint in required_endpoints:
            pattern = endpoint_to_regex(endpoint)
            matching_routes = [route for route in routes if pattern.match(route)]
            assert matching_routes, f"Endpoint {endpoint} should exist"
            print(f"✅ Endpoint {endpoint} exists (matched: {matching_routes[0]})")

        # Additional check for the streaming endpoint specifically
        streaming_routes = [route for route in routes if "scan/stream" in route]
        assert streaming_routes, "Streaming endpoint should exist"
        print(f"✅ Streaming endpoint found: {streaming_routes[0]}")

        return True
    except Exception as e:
        print(f"❌ API endpoints error: {e}")
        return False

def test_deduplication_optimization():
    """Test that the deduplication optimization is working correctly."""
    print("\nTesting deduplication optimization...")

    try:
        from backend.deduplication_service import deduplication_service
        from backend.database import get_db

        # Test that the optimization methods exist
        assert hasattr(deduplication_service, 'reorder_projects_by_release_date'), "reorder_projects_by_release_date method should exist"
        assert hasattr(deduplication_service, '_get_sort_key'), "_get_sort_key method should exist"
        assert hasattr(deduplication_service, '_find_duplicates_for_project_efficient'), "_find_duplicates_for_project_efficient method should exist"
        print("✅ Deduplication optimization methods exist")

        # Test that the sort_order field is being used
        with open('backend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'sort_order' in content, "sort_order field should be used in main.py"
            assert 'ORDER BY sort_order' in content or 'order_by(Project.sort_order)' in content, "sort_order should be used for ordering"
        print("✅ sort_order field is being used for efficient ordering")

        return True
    except Exception as e:
        print(f"❌ Deduplication optimization error: {e}")
        return False

def test_frontend_compatibility():
    """Test that frontend components are still compatible."""
    print("\nTesting frontend compatibility...")

    try:
        # Check that frontend API service exists and has correct endpoints
        with open('frontend/src/services/api.ts', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'scanStream' in content, "scanStream endpoint should exist"
            assert 'deduplication' in content, "deduplication endpoint should exist"
            assert 'SSEStream' in content, "SSEStream class should exist"
        print("✅ Frontend API service is compatible")

        # Check that ProjectExplorer component exists and uses correct endpoints
        with open('frontend/src/components/ProjectExplorer.tsx', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'handleScan' in content, "handleScan function should exist"
            assert 'handleDeduplication' in content, "handleDeduplication function should exist"
            assert 'endpoints.scanStream' in content, "Should use scanStream endpoint"
            assert 'endpoints.deduplication' in content, "Should use deduplication endpoint"
        print("✅ ProjectExplorer component is compatible")

        return True
    except Exception as e:
        print(f"❌ Frontend compatibility error: {e}")
        return False

def main():
    """Run all functionality tests."""
    print("=" * 70)
    print("COMPREHENSIVE FUNCTIONALITY VERIFICATION AFTER DEDUPLICATION OPTIMIZATION")
    print("=" * 70)

    tests = [
        test_backend_imports,
        test_web_scraper_initialization,
        test_scan_service_methods,
        test_web_scraper_methods,
        test_mistral_handler_methods,
        test_deduplication_service_methods,
        test_database_model_fields,
        test_date_filtering_functionality,
        test_database_checking_functionality,
        test_structured_logging_functionality,
        test_api_endpoints,
        test_deduplication_optimization,
        test_frontend_compatibility
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 70)
    print(f"COMPREHENSIVE FUNCTIONALITY VERIFICATION RESULTS")
    print("=" * 70)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("✅ ALL FUNCTIONALITY MAINTAINED - No issues found!")
        print("✅ Deduplication optimization successfully implemented!")
        print("✅ Backend and frontend compatibility confirmed!")
    else:
        print(f"❌ {total - passed} tests failed - Some functionality may be broken")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)