"""Debug script to examine UTF-8 encoding issues in the database."""

import json
import logging
from backend.database import SessionLocal
from backend.models.core_models import Project, Employee, Skill, AppState
from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def debug_employee_data():
    """Debug employee data to understand UTF-8 issues."""
    db = SessionLocal()
    try:
        logger.info("=== DEBUGGING EMPLOYEE DATA ===")

        employees = db.query(Employee).all()
        for employee in employees:
            logger.info(f"\nEmployee {employee.id}: {employee.name}")
            logger.info(f"Raw skill_list: {employee.skill_list}")

            if employee.skill_list:
                try:
                    # Try to parse the JSON
                    parsed_skills = json.loads(employee.skill_list)
                    logger.info(f"Parsed skills: {parsed_skills}")

                    # Check if any skills have escaped characters
                    for i, skill in enumerate(parsed_skills):
                        if '\\u' in skill:
                            logger.info(f"  Skill {i} has escaped Unicode: {skill}")
                            # Try to decode it
                            try:
                                decoded = skill.encode().decode('unicode_escape')
                                logger.info(f"  Decoded: {decoded}")
                            except Exception as e:
                                logger.error(f"  Error decoding: {e}")
                        else:
                            logger.info(f"  Skill {i}: {skill}")

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing skills: {e}")

    except Exception as e:
        logger.error(f"Error debugging employee data: {e}")
    finally:
        db.close()


def fix_employee_skills_aggressive():
    """Aggressively fix employee skills by decoding escaped Unicode."""
    db = SessionLocal()
    try:
        logger.info("=== AGGRESSIVELY FIXING EMPLOYEE SKILLS ===")

        employees = db.query(Employee).all()
        fixed_count = 0

        for employee in employees:
            if employee.skill_list:
                try:
                    # Parse the current skills
                    current_skills = json.loads(employee.skill_list)
                    fixed_skills = []

                    for skill in current_skills:
                        if '\\u' in skill:
                            # This skill has escaped Unicode characters
                            try:
                                # Remove extra quotes and decode
                                clean_skill = skill.strip('"')
                                decoded_skill = clean_skill.encode().decode('unicode_escape')
                                fixed_skills.append(decoded_skill)
                                logger.info(f"Fixed skill: '{skill}' -> '{decoded_skill}'")
                            except Exception as e:
                                logger.error(f"Error fixing skill '{skill}': {e}")
                                fixed_skills.append(skill)
                        else:
                            # Remove extra quotes if present
                            clean_skill = skill.strip('"')
                            fixed_skills.append(clean_skill)

                    # Re-save with proper UTF-8 encoding
                    employee.set_skill_list(fixed_skills)
                    fixed_count += 1
                    logger.info(f"Fixed skills for employee {employee.id}: {employee.name}")
                    logger.info(f"New skills: {fixed_skills}")

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing skills for employee {employee.id}: {e}")

        if fixed_count > 0:
            db.commit()
            logger.info(f"Fixed UTF-8 encoding for {fixed_count} employees")
        else:
            logger.info("No employee skills needed fixing")

    except Exception as e:
        logger.error(f"Error fixing employee skills: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function to debug and fix UTF-8 issues."""
    try:
        logger.info("Starting UTF-8 debugging and fixing...")

        # First, debug the current state
        debug_employee_data()

        # Then, aggressively fix the issues
        fix_employee_skills_aggressive()

        # Debug again to see the results
        debug_employee_data()

        logger.info("UTF-8 debugging and fixing completed")

    except Exception as e:
        logger.error(f"UTF-8 debugging and fixing failed: {e}")
        raise


if __name__ == "__main__":
    main()