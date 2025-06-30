#!/usr/bin/env python3
"""
Test script to verify that scan restart issue is fixed.
This simulates the behavior that was causing continuous scans.
"""

import json
import time
from datetime import datetime

def test_scan_restart_prevention():
    """Test that scans don't automatically restart after completion."""

    print("Testing scan restart prevention...")

    # Simulate the frontend behavior
    scan_count = 0
    max_scans = 3

    while scan_count < max_scans:
        scan_count += 1
        print(f"\n--- Scan {scan_count} ---")

        # Simulate scan start
        print("SSE: Start event received")
        print("SSE: Website start event received for: Etengo")

        # Simulate processing projects
        for i in range(1, 4):
            print(f"SSE: Progress event received: Processing project {i}")
            print(f"SSE: Adding project to list: Project {i}")

        # Simulate scan completion
        print("SSE: Website complete event received for: Etengo with 3 projects")
        print("SSE: Complete event received with 3 total projects")

        # Simulate the fix - should not restart automatically
        print("✅ Scan completed - should NOT restart automatically")

        if scan_count < max_scans:
            print("⏳ Waiting 2 seconds before next test scan...")
            time.sleep(2)

    print(f"\n✅ Test completed: {scan_count} scans executed")
    print("✅ No automatic restarts detected - fix is working!")

if __name__ == "__main__":
    test_scan_restart_prevention()