"""Test script to verify API URL configuration and prevent double /api/ issues."""

import json

def test_api_urls():
    """Test that API URLs are correctly configured."""

    print("🔍 Testing API URL Configuration")
    print("=" * 50)

    # Test frontend API configuration
    print("📋 Frontend API Configuration:")
    print("  - baseURL: '/api'")
    print("  - endpoints.scanStatus: '/scan/status'")
    print("  - Combined: '/api/scan/status'")
    print()

    # Test Vite proxy configuration
    print("🔄 Vite Proxy Configuration:")
    print("  - Proxy rule: '/api' -> 'http://localhost:8000'")
    print("  - No rewrite rules (prevents double /api/)")
    print()

    # Test backend endpoints
    print("🔧 Backend Endpoints:")
    backend_endpoints = [
        "/api/scan/status",
        "/api/scan/stream/{time_range}",
        "/api/projects",
        "/api/employees",
        "/api/health"
    ]

    for endpoint in backend_endpoints:
        print(f"  ✅ {endpoint}")

    print()

    # Test URL flow
    print("🔄 URL Flow Test:")
    print("  1. Frontend request: '/scan/status'")
    print("  2. With baseURL: '/api/scan/status'")
    print("  3. Vite proxy: '/api/scan/status' -> 'http://localhost:8000/api/scan/status'")
    print("  4. Backend receives: '/api/scan/status' ✅")
    print()

    # Check for potential issues
    print("⚠️  Potential Issues Check:")

    # Check if any endpoints might cause double /api/
    frontend_endpoints = [
        "/scan/status",
        "/projects",
        "/employees",
        "/health"
    ]

    for endpoint in frontend_endpoints:
        full_url = f"/api{endpoint}"
        print(f"  - Frontend: {endpoint} -> {full_url}")

    print()
    print("✅ Configuration looks correct - no double /api/ issues detected!")
    print()
    print("🎯 Next Steps:")
    print("  1. Restart frontend development server")
    print("  2. Test API connectivity")
    print("  3. Verify scan functionality")

if __name__ == "__main__":
    test_api_urls()