#!/usr/bin/env python3
"""
Test script to verify duplicate project handling in the frontend.
This simulates the SSE events that would be sent during a scan.
"""

import json
import time
from datetime import datetime

def simulate_sse_events():
    """Simulate SSE events that would be sent during a scan."""

    # Sample project data
    sample_projects = [
        {
            "id": 146,
            "title": "IT Software Einkäufer (f/m/d)",
            "description": "Für unseren Kunden aus der Textilbranche...",
            "release_date": "26.06.2025",
            "start_date": "18.08.2025",
            "location": "Remote option 2 days on site: 2 days",
            "tenderer": "etengo",
            "project_id": "ca-98655",
            "requirements": ["Google Workspace", "SirionOne", "IT Infrastruktur"],
            "rate": "Not specified",
            "url": "https://www.etengo.de/it-projektsuche/98655/",
            "budget": "Not specified",
            "duration": "5 months",
            "workload": "4 day(s) per week"
        },
        {
            "id": 147,
            "title": "Experte (w/m/d) DefectDojo",
            "description": "Einführung des Produkts DefectDojo...",
            "release_date": "26.06.2025",
            "start_date": "ab sofort",
            "location": "Remote",
            "tenderer": "etengo",
            "project_id": "ca-98653",
            "requirements": ["DefectDojo", "Schwachstellenmanagement", "Sicherheitsstandards"],
            "rate": "N/A",
            "url": "https://www.etengo.de/it-projektsuche/98653/",
            "budget": "N/A",
            "duration": "5 Monate",
            "workload": "5 Tage pro Woche"
        }
    ]

    print("Simulating SSE events for duplicate handling test...")
    print("=" * 60)

    # Simulate start event
    start_event = {
        "type": "start",
        "message": "Scan started"
    }
    print(f"SSE Event: {json.dumps(start_event, ensure_ascii=False)}")

    # Simulate website start
    website_start = {
        "type": "website_start",
        "website": "Etengo"
    }
    print(f"SSE Event: {json.dumps(website_start, ensure_ascii=False)}")

    # Simulate project events (including duplicates)
    for i, project in enumerate(sample_projects):
        # Progress event
        progress_event = {
            "type": "progress",
            "message": f"Processing project {i+1}"
        }
        print(f"SSE Event: {json.dumps(progress_event, ensure_ascii=False)}")

        # Project event
        project_event = {
            "type": "project",
            "data": project
        }
        print(f"SSE Event: {json.dumps(project_event, ensure_ascii=False)}")

        # Simulate duplicate project event (same ID)
        print(f"SSE Event: {json.dumps(project_event, ensure_ascii=False)} (DUPLICATE)")

    # Simulate website complete
    website_complete = {
        "type": "website_complete",
        "website": "Etengo",
        "projects": len(sample_projects)
    }
    print(f"SSE Event: {json.dumps(website_complete, ensure_ascii=False)}")

    # Simulate complete event
    complete_event = {
        "type": "complete",
        "total_projects": len(sample_projects),
        "errors": [],
        "deduplication": {
            "total_removed": 0,
            "duplicate_groups_processed": 0,
            "removed_details": [],
            "message": "No duplicates found"
        }
    }
    print(f"SSE Event: {json.dumps(complete_event, ensure_ascii=False)}")

    print("=" * 60)
    print("Expected behavior:")
    print("- Each project should be added only once")
    print("- Duplicate events should be logged as 'already processed'")
    print("- processedProjectIds should prevent duplicate processing")

if __name__ == "__main__":
    simulate_sse_events()