#!/usr/bin/env python3
"""
Script to check current project and skill data to debug TF-IDF issues.
"""

from backend.database import SessionLocal
from backend.models.core_models import Project, Skill
from backend.tfidf_service import tfidf_service

def check_data():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Checking Project and Skill Data")
        print("=" * 60)

        # Check projects
        print("\nProjects:")
        projects = db.query(Project).all()
        for p in projects:
            print(f"  {p.id}: {p.title}")
            print(f"    Requirements TF: {p.get_requirements_tf()}")
            print(f"    Requirements List: {p.get_requirements_list()}")
            print()

        # Check skills
        print("\nSkills:")
        skills = db.query(Skill).all()
        for s in skills:
            print(f"  {s.skill_name}: IDF={s.idf_factor}")

        # Check IDF factors for specific skills
        print("\nIDF Factors for Project Requirements:")
        for p in projects:
            print(f"\nProject {p.id} ({p.title}):")
            requirements_tf = p.get_requirements_tf()
            for req, tf in requirements_tf.items():
                idf = tfidf_service.get_skill_idf_factor(req, db)
                tfidf_weight = tf * idf
                print(f"  {req}: TF={tf}, IDF={idf:.4f}, TF-IDF={tfidf_weight:.4f}")

        # Calculate total weights
        print("\nTotal TF-IDF Weights per Project:")
        for p in projects:
            requirements_tf = p.get_requirements_tf()
            total_weight = 0
            for req, tf in requirements_tf.items():
                idf = tfidf_service.get_skill_idf_factor(req, db)
                total_weight += tf * idf
            print(f"  Project {p.id}: {total_weight:.4f}")

    finally:
        db.close()

if __name__ == "__main__":
    check_data()