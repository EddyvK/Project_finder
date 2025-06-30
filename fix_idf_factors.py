#!/usr/bin/env python3
"""
Script to fix IDF factors by recalculating and storing them properly.
"""

from backend.database import SessionLocal
from backend.models.core_models import Project, Skill
from backend.tfidf_service import tfidf_service
import math

def fix_idf_factors():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Fixing IDF Factors")
        print("=" * 60)

        # Step 1: Calculate IDF factors manually
        print("\n1. Calculating IDF factors...")

        # Get all projects with requirements
        projects = db.query(Project).filter(Project.requirements_tf.isnot(None)).all()
        total_documents = len(projects)

        print(f"   Total documents: {total_documents}")

        if total_documents == 0:
            print("   No projects found!")
            return

        # Count documents containing each skill
        skill_document_counts = {}

        for project in projects:
            requirements_tf = project.get_requirements_tf()
            if requirements_tf:
                for skill in requirements_tf.keys():
                    skill_document_counts[skill] = skill_document_counts.get(skill, 0) + 1

        print(f"   Found {len(skill_document_counts)} unique skills")

        # Calculate IDF factors
        idf_factors = {}
        for skill, doc_count in skill_document_counts.items():
            if doc_count > 0:
                # IDF = log(total_documents / documents_containing_term)
                idf_factor = math.log(total_documents / doc_count)
                idf_factors[skill] = idf_factor
                print(f"   {skill}: appears in {doc_count}/{total_documents} documents, IDF = {idf_factor:.4f}")

        # Step 2: Update skills table
        print(f"\n2. Updating skills table...")

        updated_count = 0
        for skill_name, idf_factor in idf_factors.items():
            skill = db.query(Skill).filter(Skill.skill_name == skill_name).first()
            if skill:
                skill.idf_factor = idf_factor
                updated_count += 1
                print(f"   Updated {skill_name}: IDF = {idf_factor:.4f}")
            else:
                # Create new skill entry if it doesn't exist
                new_skill = Skill(
                    skill_name=skill_name,
                    embedding="[]",  # Empty embedding, will be populated later if needed
                    idf_factor=idf_factor
                )
                db.add(new_skill)
                updated_count += 1
                print(f"   Created {skill_name}: IDF = {idf_factor:.4f}")

        # Commit changes
        db.commit()
        print(f"   ✅ Updated {updated_count} skills with IDF factors")

        # Step 3: Verify the fix
        print(f"\n3. Verifying the fix...")

        for p in projects:
            print(f"\nProject {p.id} ({p.title}):")
            requirements_tf = p.get_requirements_tf()
            total_weight = 0
            for req, tf in requirements_tf.items():
                idf = tfidf_service.get_skill_idf_factor(req, db)
                tfidf_weight = tf * idf
                total_weight += tfidf_weight
                print(f"  {req}: TF={tf}, IDF={idf:.4f}, TF-IDF={tfidf_weight:.4f}")
            print(f"  Total weight: {total_weight:.4f}")

        print(f"\n✅ IDF factors fixed successfully!")

    except Exception as e:
        print(f"❌ Error fixing IDF factors: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_idf_factors()