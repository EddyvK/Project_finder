#!/usr/bin/env python3
"""
Test to reproduce the strip error.
"""

def test_strip_error():
    """Test the strip error scenario."""

    # Simulate the Mistral response data structure
    level3_data = {
        "requirements": ["Python", "Django"],
        "title": "Test Project",
        "description": "A test project",
        "release_date": "01.01.2024",
        "start_date": "15.01.2024",
        "location": "Berlin",
        "tenderer": "Test Company",
        "project_id": "TEST-001",
        "workload": "40h/week",
        "rate": "75€/h",
        "duration": "6 months",
        "budget": "50000€",
        # This could be a nested dictionary that causes the issue
        "nested_field": {"key": "value"}
    }

    level2_data = {
        "title": "Test Project",
        "url": "https://example.com/project",
        "project_id": "TEST-001",
        "location": "Berlin",
        "duration": "6 months",
        "start_date": "15.01.2024",
        "release_date": "01.01.2024",
        "industry": "IT",
        "tenderer": "Test Company",
        "rate": "N/A"
    }

    # Simulate the _consolidate_data method
    def _consolidate_data(level2_data, level3_data):
        l2d = level2_data
        l3d = level3_data
        consolidated = {}
        consolidated.update(l2d)

        l2_requirements = l2d.get("requirements", [])
        l3_requirements = l3d.get("requirements", [])
        if not isinstance(l2_requirements, list):
            l2_requirements = []
        if not isinstance(l3_requirements, list):
            l3_requirements = []
        all_requirements = list(set(l2_requirements + l3_requirements))
        consolidated["requirements"] = all_requirements

        for key, value in l3d.items():
            if key != "requirements":
                # This is where the error might occur
                if value and str(value).strip():
                    if consolidated.get(key) == "n/a":
                        consolidated[key] = value
                    elif consolidated.get(key) != value:
                        consolidated[key] = value

        # Ensure specific fields are included from level3 data if available
        for field in ["workload", "duration", "budget"]:
            if l3d.get(field) and str(l3d[field]).strip():
                consolidated[field] = l3d[field]

        return consolidated

    try:
        result = _consolidate_data(level2_data, level3_data)
        print("Consolidation successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_strip_error()