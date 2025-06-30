#!/usr/bin/env python3
"""
Status check script for Project Finder backend.
This script verifies that all components are working correctly.
"""

import sys
from pathlib import Path

def check_status():
    """Check the status of all backend components."""
    print("🔍 Checking Project Finder backend status...")
    print("=" * 50)

    # Check 1: Import config manager
    try:
        from backend.config_manager import config_manager
        print("✅ Config manager imported successfully")

        # Check config loading
        websites = config_manager.get_websites()
        print(f"📊 Websites configured: {len(websites)}")

        db_url = config_manager.get_database_url()
        print(f"🗄️  Database URL: {db_url}")

    except Exception as e:
        print(f"❌ Config manager error: {e}")
        return False

    # Check 2: Import database
    try:
        from backend.database import get_db, init_db
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

    # Check 3: Import models
    try:
        from backend.models.core_models import Project, Employee, AppState
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Models error: {e}")
        return False

    # Check 4: Import main app
    try:
        from backend.main import app
        print("✅ FastAPI app imported successfully")
    except ImportError as e:
        if "mistralai" in str(e):
            print("⚠️  FastAPI app import failed due to mistralai dependency")
            print("   Run 'pip install -r backend/requirements.txt' to install dependencies")
        else:
            print(f"❌ FastAPI app error: {e}")
        return False
    except Exception as e:
        print(f"❌ FastAPI app error: {e}")
        return False

    # Check 5: Check if database file exists (in root directory)
    db_file = Path("project_finder.db")
    if db_file.exists():
        print(f"✅ Database file exists: {db_file.name}")
    else:
        print(f"⚠️  Database file not found: {db_file.name}")

    # Check 6: Check if config file exists
    backend_dir = Path(__file__).parent / "backend"
    config_file = backend_dir / "config.json"
    if config_file.exists():
        print(f"✅ Config file exists: {config_file.name}")
    else:
        print(f"❌ Config file not found: {config_file.name}")

    # Check 7: Check if .env file exists
    env_file = backend_dir / ".env"
    if env_file.exists():
        print(f"✅ Environment file exists: {env_file.name}")
    else:
        print(f"⚠️  Environment file not found: {env_file.name}")
        print("   Run 'python setup_env.py' to create it")

    print("=" * 50)
    print("🎉 All checks completed!")
    print("\n🚀 To start the server, run:")
    print("   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")

    return True

if __name__ == "__main__":
    success = check_status()
    sys.exit(0 if success else 1)