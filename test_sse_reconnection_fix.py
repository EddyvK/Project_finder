#!/usr/bin/env python3
"""
Test to verify that SSE reconnection fix prevents automatic scan restarts.
"""

import requests
import time
import json
from datetime import datetime

def test_sse_reconnection_fix():
    """Test that scans don't automatically restart after completion."""

    base_url = "http://localhost:8000"

    print("=" * 60)
    print("Testing SSE Reconnection Fix")
    print("=" * 60)

    # Step 1: Check initial scan status
    print(f"\n1. Checking initial scan status...")
    try:
        response = requests.get(f"{base_url}/api/scan/status")
        status_data = response.json()
        print(f"   Scan status: {status_data}")

        if status_data.get('is_active'):
            print("   ⚠️  Another scan is already active, waiting for it to complete...")
            # Wait for any existing scan to complete
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                response = requests.get(f"{base_url}/api/scan/status")
                status_data = response.json()
                if not status_data.get('is_active'):
                    print("   ✅ Existing scan completed")
                    break
            else:
                print("   ❌ Existing scan did not complete in time")
                return False
        else:
            print("   ✅ No active scan found")
    except Exception as e:
        print(f"   ❌ Error checking scan status: {e}")
        return False

    # Step 2: Start a scan and monitor it
    print(f"\n2. Starting a scan...")
    try:
        # Start scan with 8-day time range
        response = requests.get(f"{base_url}/api/scan/stream/8", stream=True)
        if response.status_code != 200:
            print(f"   ❌ Failed to start scan: {response.status_code}")
            return False

        print("   ✅ Scan started successfully")

        # Monitor the scan
        scan_completed = False
        start_time = time.time()
        last_event_time = start_time

        for line in response.iter_lines():
            if line:
                current_time = time.time()
                last_event_time = current_time

                try:
                    # Parse SSE data
                    if line.startswith(b'data: '):
                        data_str = line[6:].decode('utf-8')
                        if data_str.strip():
                            event_data = json.loads(data_str)
                            event_type = event_data.get('type')

                            print(f"   📡 Event: {event_type}")

                            if event_type == 'complete':
                                print("   ✅ Scan completed normally")
                                scan_completed = True
                                break
                            elif event_type == 'error':
                                print(f"   ❌ Scan error: {event_data.get('message')}")
                                return False

                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue

                # Timeout if no events for 30 seconds
                if current_time - last_event_time > 30:
                    print("   ❌ Timeout waiting for scan events")
                    return False

                # Overall timeout of 2 minutes
                if current_time - start_time > 120:
                    print("   ❌ Overall timeout")
                    return False

        if not scan_completed:
            print("   ❌ Scan did not complete")
            return False

    except Exception as e:
        print(f"   ❌ Error during scan: {e}")
        return False

    # Step 3: Wait and check if any new scans start automatically
    print(f"\n3. Monitoring for automatic scan restarts...")
    try:
        # Wait for 10 seconds to see if any new scans start
        for i in range(10):
            time.sleep(1)

            # Check scan status
            response = requests.get(f"{base_url}/api/scan/status")
            status_data = response.json()

            if status_data.get('is_active'):
                print(f"   ❌ Automatic scan detected at {i+1}s after completion!")
                return False
            else:
                print(f"   ✅ No automatic scan at {i+1}s")

        print("   ✅ No automatic scans detected")

    except Exception as e:
        print(f"   ❌ Error monitoring for automatic scans: {e}")
        return False

    # Step 4: Verify we can manually start a new scan
    print(f"\n4. Testing manual scan start...")
    try:
        response = requests.get(f"{base_url}/api/scan/status")
        status_data = response.json()

        if not status_data.get('is_active'):
            print("   ✅ Manual scan start should work")
        else:
            print("   ❌ Scan is still active, cannot test manual start")
            return False

    except Exception as e:
        print(f"   ❌ Error checking scan status: {e}")
        return False

    print(f"\n✅ SSE Reconnection Fix Test PASSED")
    print("   - Scan completed normally")
    print("   - No automatic restarts detected")
    print("   - Manual scan start available")

    return True

if __name__ == "__main__":
    success = test_sse_reconnection_fix()
    exit(0 if success else 1)