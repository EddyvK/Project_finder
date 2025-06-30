#!/usr/bin/env python3
"""
Setup script for Project Finder backend environment.
This script helps users create their .env file for local development.
"""

import os
from pathlib import Path

def setup_environment():
    """Setup the environment for local development."""
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    env_example = backend_dir / "env_example.txt"

    print("Setting up Project Finder backend environment...")
    print(f"Backend directory: {backend_dir}")

    # Check if .env already exists
    if env_file.exists():
        print("✅ .env file already exists")
        return

    # Check if env_example.txt exists
    if not env_example.exists():
        print("❌ env_example.txt not found")
        return

    # Create .env file from example
    try:
        with open(env_example, 'r', encoding='utf-8') as f:
            example_content = f.read()

        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(example_content)

        print("✅ Created .env file from template")
        print("📝 Please edit backend/.env to add your API keys:")
        print("   - OPENAI_API_KEY")
        print("   - MISTRAL_API_KEY")

    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    setup_environment()