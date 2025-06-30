"""Script to fix UTF-8 encoding issues in existing database data."""

import json
import logging
from backend.database import SessionLocal
from backend.models.core_models import Project, Employee, Skill, AppState
from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def fix_employee_skills():
    """Fix UTF-8 encoding in employee skills."""
    db = SessionLocal()
    try:
        logger.info("Fixing UTF-8 encoding in employee skills...")

        employees = db.query(Employee).all()
        fixed_count = 0

        for employee in employees:
            if employee.skill_list:
                try:
                    # Parse the current skills (which may have escaped characters)
                    current_skills = json.loads(employee.skill_list)

                    # Re-save with proper UTF-8 encoding
                    employee.set_skill_list(current_skills)
                    fixed_count += 1
                    logger.info(f"Fixed skills for employee {employee.id}: {employee.name}")

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


def fix_project_requirements():
    """Fix UTF-8 encoding in project requirements."""
    db = SessionLocal()
    try:
        logger.info("Fixing UTF-8 encoding in project requirements...")

        projects = db.query(Project).all()
        fixed_count = 0

        for project in projects:
            if project.requirements:
                try:
                    # Parse the current requirements (which may have escaped characters)
                    current_requirements = json.loads(project.requirements)

                    # Re-save with proper UTF-8 encoding
                    project.set_requirements_list(current_requirements)
                    fixed_count += 1
                    logger.info(f"Fixed requirements for project {project.id}: {project.title}")

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing requirements for project {project.id}: {e}")

        if fixed_count > 0:
            db.commit()
            logger.info(f"Fixed UTF-8 encoding for {fixed_count} projects")
        else:
            logger.info("No project requirements needed fixing")

    except Exception as e:
        logger.error(f"Error fixing project requirements: {e}")
        db.rollback()
    finally:
        db.close()


def fix_skill_names():
    """Fix UTF-8 encoding in skill names."""
    db = SessionLocal()
    try:
        logger.info("Fixing UTF-8 encoding in skill names...")

        skills = db.query(Skill).all()
        fixed_count = 0

        for skill in skills:
            # Skill names are stored as plain strings, so they should be fine
            # But let's check if they have any encoding issues
            if skill.skill_name and '\\u' in skill.skill_name:
                # This skill name has escaped Unicode characters
                try:
                    # Decode the escaped Unicode
                    decoded_name = skill.skill_name.encode().decode('unicode_escape')
                    skill.skill_name = decoded_name
                    fixed_count += 1
                    logger.info(f"Fixed skill name: {skill.skill_name}")
                except Exception as e:
                    logger.error(f"Error fixing skill name {skill.skill_name}: {e}")

        if fixed_count > 0:
            db.commit()
            logger.info(f"Fixed UTF-8 encoding for {fixed_count} skills")
        else:
            logger.info("No skill names needed fixing")

    except Exception as e:
        logger.error(f"Error fixing skill names: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function to fix all UTF-8 encoding issues."""
    try:
        logger.info("Starting UTF-8 encoding fix...")

        fix_employee_skills()
        fix_project_requirements()
        fix_skill_names()

        logger.info("UTF-8 encoding fix completed successfully")

    except Exception as e:
        logger.error(f"UTF-8 encoding fix failed: {e}")
        raise


if __name__ == "__main__":
    main()