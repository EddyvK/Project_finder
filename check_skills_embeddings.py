#!/usr/bin/env python3
"""
Script to check skills table and identify skills with empty embeddings.
"""

from backend.database import SessionLocal
from backend.models.core_models import Skill
import json

def check_skills_embeddings():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Checking Skills Table for Empty Embeddings")
        print("=" * 60)

        # Get all skills
        skills = db.query(Skill).all()
        print(f"\nTotal skills in database: {len(skills)}")

        # Check for empty embeddings
        empty_embeddings = []
        valid_embeddings = []

        for skill in skills:
            if not skill.embedding or skill.embedding == '[]' or skill.embedding == 'null':
                empty_embeddings.append(skill)
            else:
                valid_embeddings.append(skill)

        print(f"\nSkills with empty embeddings: {len(empty_embeddings)}")
        print(f"Skills with valid embeddings: {len(valid_embeddings)}")

        if empty_embeddings:
            print("\nSkills with empty embeddings:")
            for skill in empty_embeddings:
                print(f"  - {skill.skill_name} (ID: {skill.id})")

        # Check a few examples of valid embeddings
        if valid_embeddings:
            print(f"\nSample valid embeddings (first 3):")
            for skill in valid_embeddings[:3]:
                try:
                    embedding_data = json.loads(skill.embedding) if skill.embedding else []
                    print(f"  - {skill.skill_name}: {len(embedding_data)} dimensions")
                except:
                    print(f"  - {skill.skill_name}: Invalid JSON format")

        # Check when skills were created/updated
        print(f"\nRecent skills (last 10):")
        recent_skills = db.query(Skill).order_by(Skill.id.desc()).limit(10).all()
        for skill in recent_skills:
            embedding_status = "Valid" if skill.embedding and skill.embedding != '[]' and skill.embedding != 'null' else "Empty"
            print(f"  - {skill.skill_name} (ID: {skill.id}): {embedding_status}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_skills_embeddings()