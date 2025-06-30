#!/usr/bin/env python3
"""
TF/IDF calculation service for project requirements.
"""

import math
import logging
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from backend.models.core_models import Project, Skill
from backend.database import SessionLocal

logger = logging.getLogger(__name__)


class TFIDFService:
    """Service for calculating TF/IDF factors for project requirements."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_idf_factors(self, db: Session = None) -> Dict[str, float]:
        """
        Calculate IDF factors for all skills based on current project data.

        IDF = log(total_documents / documents_containing_term)

        Args:
            db: Database session (optional, will create one if not provided)

        Returns:
            Dictionary mapping skill names to their IDF factors
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            self.logger.info("Starting IDF factor calculation...")

            # Get all projects with requirements
            projects = db.query(Project).filter(Project.requirements_tf.isnot(None)).all()
            total_documents = len(projects)

            if total_documents == 0:
                self.logger.warning("No projects with requirements found for IDF calculation")
                return {}

            self.logger.info(f"Found {total_documents} projects with requirements")

            # Count documents containing each skill
            skill_document_counts: Dict[str, int] = {}

            for project in projects:
                requirements_tf = project.get_requirements_tf()
                if requirements_tf:
                    # Add each skill to the document count
                    for skill in requirements_tf.keys():
                        skill_document_counts[skill] = skill_document_counts.get(skill, 0) + 1

            self.logger.info(f"Found {len(skill_document_counts)} unique skills across all projects")

            # Calculate IDF factors
            idf_factors: Dict[str, float] = {}
            for skill, doc_count in skill_document_counts.items():
                if doc_count > 0:
                    # IDF = log(total_documents / documents_containing_term)
                    idf_factor = math.log(total_documents / doc_count)
                    idf_factors[skill] = idf_factor
                    self.logger.debug(f"Skill '{skill}': IDF = {idf_factor:.4f} (appears in {doc_count}/{total_documents} documents)")

            self.logger.info(f"Calculated IDF factors for {len(idf_factors)} skills")
            return idf_factors

        except Exception as e:
            self.logger.error(f"Error calculating IDF factors: {e}")
            raise
        finally:
            if should_close:
                db.close()

    def update_skills_idf_factors(self, db: Session = None) -> Dict[str, float]:
        """
        Calculate IDF factors and update the skills table.

        Args:
            db: Database session (optional, will create one if not provided)

        Returns:
            Dictionary mapping skill names to their IDF factors
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            self.logger.info("Updating skills table with IDF factors...")

            # Calculate IDF factors
            idf_factors = self.calculate_idf_factors(db)

            if not idf_factors:
                self.logger.warning("No IDF factors calculated, skipping skills table update")
                return {}

            # Update existing skills with IDF factors
            updated_count = 0
            for skill_name, idf_factor in idf_factors.items():
                skill = db.query(Skill).filter(Skill.skill_name == skill_name).first()
                if skill:
                    skill.idf_factor = idf_factor
                    updated_count += 1
                else:
                    # Create new skill entry if it doesn't exist
                    new_skill = Skill(
                        skill_name=skill_name,
                        embedding="[]",  # Empty embedding, will be populated later if needed
                        idf_factor=idf_factor
                    )
                    db.add(new_skill)
                    updated_count += 1

            # Commit changes
            db.commit()
            self.logger.info(f"Updated {updated_count} skills with IDF factors")

            return idf_factors

        except Exception as e:
            self.logger.error(f"Error updating skills IDF factors: {e}")
            if should_close:
                db.rollback()
            raise
        finally:
            if should_close:
                db.close()

    def get_skill_idf_factor(self, skill_name: str, db: Session = None) -> float:
        """
        Get the IDF factor for a specific skill.

        Args:
            skill_name: Name of the skill
            db: Database session (optional, will create one if not provided)

        Returns:
            IDF factor for the skill, or 0.0 if not found
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            skill = db.query(Skill).filter(Skill.skill_name == skill_name).first()
            return skill.idf_factor if skill and skill.idf_factor is not None else 0.0
        finally:
            if should_close:
                db.close()

    def calculate_tfidf_score(self, skill_name: str, term_frequency: int, db: Session = None) -> float:
        """
        Calculate TF-IDF score for a skill in a specific project.

        Args:
            skill_name: Name of the skill
            term_frequency: Term frequency (TF) in the project
            db: Database session (optional, will create one if not provided)

        Returns:
            TF-IDF score (TF * IDF)
        """
        idf_factor = self.get_skill_idf_factor(skill_name, db)
        return term_frequency * idf_factor

    def get_project_tfidf_scores(self, project: Project, db: Session = None) -> Dict[str, float]:
        """
        Calculate TF-IDF scores for all skills in a project.

        Args:
            project: Project object
            db: Database session (optional, will create one if not provided)

        Returns:
            Dictionary mapping skill names to their TF-IDF scores
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            requirements_tf = project.get_requirements_tf()
            if not requirements_tf:
                return {}

            tfidf_scores = {}
            for skill_name, term_frequency in requirements_tf.items():
                tfidf_score = self.calculate_tfidf_score(skill_name, term_frequency, db)
                tfidf_scores[skill_name] = tfidf_score

            return tfidf_scores

        finally:
            if should_close:
                db.close()


# Global instance
tfidf_service = TFIDFService()