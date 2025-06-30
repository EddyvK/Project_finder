"""Script to clean up malformed project requirements data."""

from database import SessionLocal
from models.core_models import Project
import json
import re

def is_valid_skill(item: str) -> bool:
    # Only allow items that are 2-40 chars, mostly letters/numbers/spaces/dashes
    item = item.strip()
    if not (2 <= len(item) <= 40):
        return False
    # Exclude if it contains suspicious characters
    if re.search(r'[{}\[\]\\/:;\'\"]', item):
        return False
    # Exclude if it looks like a sentence (has more than 5 words)
    if len(item.split()) > 5:
        return False
    # Exclude if it contains only numbers or is empty
    if not re.search(r'[a-zA-Z]', item):
        return False
    return True

def clean_project_requirements():
    """Clean up malformed project requirements data."""
    db = SessionLocal()

    try:
        print("Cleaning up malformed project requirements...")

        # Get all projects
        projects = db.query(Project).all()
        cleaned_count = 0

        for project in projects:
            original_requirements = project.requirements
            cleaned_requirements = None

            # Check if requirements are malformed
            if original_requirements:
                try:
                    # Try to parse as JSON
                    requirements_list = json.loads(original_requirements)

                    # Check if it's a list of strings (valid format)
                    if isinstance(requirements_list, list):
                        cleaned_list = []
                        for item in requirements_list:
                            if isinstance(item, str):
                                cleaned_item = item.strip()
                                # Remove leading/trailing quotes and brackets
                                cleaned_item = re.sub(r'^[\"\[\]]+|[\"\[\]]+$', '', cleaned_item)
                                cleaned_item = cleaned_item.strip()
                                # Remove trailing fragments like "] or "]]
                                cleaned_item = re.sub(r'\]+$', '', cleaned_item)
                                cleaned_item = cleaned_item.strip()
                                # Remove any remaining leading/trailing punctuation
                                cleaned_item = re.sub(r'^[,;:]+|[,;:]+$', '', cleaned_item)
                                cleaned_item = cleaned_item.strip()
                                # Only keep valid skill names
                                if is_valid_skill(cleaned_item):
                                    cleaned_list.append(cleaned_item)

                        if cleaned_list != requirements_list:
                            cleaned_requirements = json.dumps(cleaned_list, ensure_ascii=False)
                            print(f"Project {project.id} ({project.title}):")
                            print(f"  Original: {original_requirements}")
                            print(f"  Cleaned: {cleaned_requirements}")
                            cleaned_count += 1

                    # If it's not a list, it's malformed
                    else:
                        print(f"Project {project.id} ({project.title}): Requirements is not a list")
                        cleaned_requirements = json.dumps([], ensure_ascii=False)
                        cleaned_count += 1

                except json.JSONDecodeError:
                    # If it's not valid JSON, clear it
                    print(f"Project {project.id} ({project.title}): Invalid JSON in requirements")
                    cleaned_requirements = json.dumps([], ensure_ascii=False)
                    cleaned_count += 1

            # Update the project if needed
            if cleaned_requirements is not None:
                project.requirements = cleaned_requirements

        # Commit changes
        if cleaned_count > 0:
            db.commit()
            print(f"\nCleaned {cleaned_count} projects with malformed requirements.")
        else:
            print("\nNo malformed requirements found.")

    except Exception as e:
        print(f"Error cleaning project requirements: {e}")
        db.rollback()
    finally:
        db.close()

def verify_cleaned_data():
    """Verify that the data has been cleaned properly."""
    db = SessionLocal()

    try:
        print("\nVerifying cleaned data...")

        # Check a few projects
        projects = db.query(Project).limit(20).all()
        for project in projects:
            print(f"\nProject {project.id}: {project.title}")
            print(f"Requirements: {project.requirements}")
            try:
                requirements_list = project.get_requirements_list()
                print(f"Parsed: {requirements_list}")
            except Exception as e:
                print(f"Parse error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    clean_project_requirements()
    verify_cleaned_data()