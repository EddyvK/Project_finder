"""Database initialization script for Project Finder."""

import asyncio
import logging
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db
from backend.models.core_models import Project, Employee, AppState, Skill
from backend.logger_config import setup_logging
from backend.tfidf_service import tfidf_service
from datetime import datetime

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def create_test_data(db: Session) -> None:
    """Create test data for development."""
    import json
    try:
        # Check if test data already exists
        existing_projects = db.query(Project).filter(
            Project.tenderer == "Test"
        ).count()

        if existing_projects > 0:
            logger.info("Test data already exists, skipping creation")
            return

        # Get today's date in DD.MM.YYYY format
        today_str = datetime.now().strftime("%d.%m.%Y")

        # Create test projects
        test_projects = [
            {
                "title": "Full-Stack Web Development",
                "description": "Development of a modern web application using React and Node.js",
                "release_date": today_str,
                "start_date": "01.01.2025",
                "location": "Berlin",
                "tenderer": "Test",
                "project_id": "TEST-001",
                "requirements_tf": {"React": 3, "Node.js": 2, "TypeScript": 2, "MongoDB": 1},
                "rate": "85€/h",
                "url": "https://example.com/project1",
                "budget": "50000€",
                "duration": "6 months"
            },
            {
                "title": "Data Science Project",
                "description": "Machine learning project for customer behavior analysis",
                "release_date": today_str,
                "start_date": "15.01.2025",
                "location": "Remote",
                "tenderer": "Test",
                "project_id": "TEST-002",
                "requirements_tf": {"Python": 4, "Machine Learning": 3, "Pandas": 2, "Scikit-learn": 2},
                "rate": "95€/h",
                "url": "https://example.com/project2",
                "budget": "75000€",
                "duration": "8 months"
            },
            {
                "title": "DevOps Infrastructure",
                "description": "Setting up CI/CD pipelines and cloud infrastructure",
                "release_date": today_str,
                "start_date": "20.01.2025",
                "location": "Munich",
                "tenderer": "Test",
                "project_id": "TEST-003",
                "requirements_tf": {"Docker": 3, "Kubernetes": 2, "AWS": 2, "Jenkins": 1},
                "rate": "90€/h",
                "url": "https://example.com/project3",
                "budget": "60000€",
                "duration": "4 months"
            },
            {
                "title": "Mobile App Development",
                "description": "Cross-platform mobile application using Flutter",
                "release_date": today_str,
                "start_date": "10.01.2025",
                "location": "Hamburg",
                "tenderer": "Test",
                "project_id": "TEST-004",
                "requirements_tf": {"Flutter": 3, "Dart": 2, "Firebase": 2, "Mobile Development": 1},
                "rate": "80€/h",
                "url": "https://example.com/project4",
                "budget": "45000€",
                "duration": "5 months"
            }
        ]

        for project_data in test_projects:
            project = Project(
                title=project_data["title"],
                description=project_data["description"],
                release_date=project_data["release_date"],
                start_date=project_data["start_date"],
                location=project_data["location"],
                tenderer=project_data["tenderer"],
                project_id=project_data["project_id"],
                rate=project_data["rate"],
                url=project_data["url"],
                budget=project_data["budget"],
                duration=project_data["duration"]
            )
            project.set_requirements_tf(project_data["requirements_tf"])
            db.add(project)

        # Create test employees
        test_employees = [
            {
                "name": "John Smith",
                "skill_list": ["React", "Node.js", "JavaScript", "MongoDB"],
                "experience_years": 5
            },
            {
                "name": "Sarah Johnson",
                "skill_list": ["Python", "Machine Learning", "Data Analysis", "Pandas"],
                "experience_years": 7
            },
            {
                "name": "Michael Brown",
                "skill_list": ["Docker", "Kubernetes", "AWS", "Linux"],
                "experience_years": 4
            },
            {
                "name": "Emily Davis",
                "skill_list": ["Flutter", "Dart", "Mobile Development", "Firebase"],
                "experience_years": 3
            }
        ]

        for employee_data in test_employees:
            employee = Employee(
                name=employee_data["name"],
                experience_years=employee_data["experience_years"]
            )
            employee.set_skill_list(employee_data["skill_list"])
            db.add(employee)

        db.commit()
        logger.info("Test data created successfully")

        # --- NEW: Populate the skills table and update IDF factors ---
        # Collect all unique skills from projects and employees
        unique_skills = set()
        for project_data in test_projects:
            unique_skills.update(project_data["requirements_tf"].keys())
        for employee_data in test_employees:
            unique_skills.update(employee_data["skill_list"])
        # Add skills to the Skill table if missing
        for skill_name in unique_skills:
            skill = db.query(Skill).filter(Skill.skill_name == skill_name).first()
            if not skill:
                # Create skill with placeholder embedding - will be filled by rebuild process
                # or when first used in matching
                db.add(Skill(skill_name=skill_name, embedding="[]", idf_factor=None))
        db.commit()

        # Update IDF factors for all skills
        tfidf_service.update_skills_idf_factors(db)
        db.commit()
        logger.info("Skills table populated and IDF factors updated.")

        # Note: Embeddings will be generated when the rebuild embeddings API is called
        # or when skills are first used in matching

    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        db.rollback()
        raise


def main():
    """Main function to initialize database."""
    try:
        logger.info("Initializing database...")

        # Initialize database tables
        init_db()

        # Create test data
        db = SessionLocal()
        try:
            create_test_data(db)
        finally:
            db.close()

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()