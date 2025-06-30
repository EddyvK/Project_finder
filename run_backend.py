#!/usr/bin/env python3
"""
Simple script to run the Project Finder backend application.
This script changes to the backend directory and runs the FastAPI app.
"""

import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, 'backend')

    # Change to backend directory
    os.chdir(backend_dir)

    # Run the uvicorn server
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'main:app',
        '--reload',
        '--host', '0.0.0.0',
        '--port', '8000'
    ]

    print(f"Starting Project Finder backend from: {backend_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("Press Ctrl+C to stop the server")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {e}")

if __name__ == "__main__":
    main()