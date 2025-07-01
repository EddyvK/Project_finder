#!/usr/bin/env python3
"""Check IDF factors in the database."""

from backend.database import SessionLocal
from backend.models.core_models import Skill, Project

def check_idf_factors():
    session = SessionLocal()

    try:
        # Check skills with IDF factors
        skills_with_idf = session.query(Skill).filter(Skill.idf_factor.isnot(None)).limit(10).all()
        skills_without_idf = session.query(Skill).filter(Skill.idf_factor.is_(None)).all()

        print("=== Skills with IDF factors ===")
        for skill in skills_with_idf:
            print(f"{skill.skill_name}: {skill.idf_factor}")

        print(f"\n=== ALL Skills without IDF factors ({len(skills_without_idf)} found) ===")
        for skill in skills_without_idf:
            print(f"{skill.skill_name}: {skill.idf_factor}")

        # Check if these skills appear in any project requirements
        print(f"\n=== Checking if skills without IDF appear in project requirements ===")
        all_projects = session.query(Project).filter(Project.requirements_tf.isnot(None)).all()

        for skill in skills_without_idf:
            skill_name = skill.skill_name
            found_in_projects = []

            for project in all_projects:
                requirements_tf = project.get_requirements_tf()
                if requirements_tf and skill_name in requirements_tf:
                    found_in_projects.append(f"Project {project.id}: {project.title}")

            if found_in_projects:
                print(f"'{skill_name}' found in {len(found_in_projects)} projects:")
                for project_info in found_in_projects[:3]:  # Show first 3
                    print(f"  - {project_info}")
                if len(found_in_projects) > 3:
                    print(f"  ... and {len(found_in_projects) - 3} more")
            else:
                print(f"'{skill_name}' NOT found in any project requirements")

        # Check total counts
        total_skills = session.query(Skill).count()
        skills_with_idf_count = session.query(Skill).filter(Skill.idf_factor.isnot(None)).count()
        total_projects = session.query(Project).count()
        projects_with_tf_count = session.query(Project).filter(Project.requirements_tf.isnot(None)).count()

        print(f"\n=== Summary ===")
        print(f"Total skills: {total_skills}")
        print(f"Skills with IDF factors: {skills_with_idf_count}")
        print(f"Skills without IDF factors: {len(skills_without_idf)}")
        print(f"Total projects: {total_projects}")
        print(f"Projects with requirements_tf: {projects_with_tf_count}")

    finally:
        session.close()

if __name__ == "__main__":
    check_idf_factors()