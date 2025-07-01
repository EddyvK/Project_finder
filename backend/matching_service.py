"""
Project matching service for comparing employee skills with project requirements.

This file is now considered STABLE and should not be changed unless explicitly requested.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.models.core_models import Project, Employee, Skill
from backend.openai_handler import OpenAIHandler
from backend.config_manager import config_manager
from backend.tfidf_service import tfidf_service

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service for matching employees with projects based on skill compatibility.

    This class is now considered STABLE and should not be changed unless explicitly requested.
    """

    def __init__(self):
        """
        Initialize the matching service and OpenAI handler if API key is available.
        """
        self.openai_handler = None
        self.logger = logging.getLogger(__name__)

        # Initialize OpenAI handler if API key is available
        api_keys = config_manager.get_api_keys()
        if api_keys.get("openai"):
            try:
                self.openai_handler = OpenAIHandler(api_keys["openai"])
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI handler: {str(e)}")

    # Synonym mapping for skills (expand as needed)
    SKILL_SYNONYMS = {
        "deutschkenntnisse": ["deutsch", "deutsche sprache"],
        "deutsche sprache": ["deutsch", "deutschkenntnisse"],
        "deutsch": ["deutschkenntnisse", "deutsche sprache"],
        "englischkenntnisse": ["englisch", "englische sprache"],
        "englische sprache": ["englisch", "englischkenntnisse"],
        "englisch": ["englischkenntnisse", "englische sprache"],
        # Add more as needed
    }

    # List of soft skills for strict matching (expand as needed)
    SOFT_SKILLS = [
        "kommunikation", "teamarbeit", "projektmanagement", "führung", "beratung",
        "präsentation", "moderation", "workshops", "dokumentation", "support",
        "schulung", "coaching", "mentoring", "verhandlung", "konfliktmanagement"
    ]

    # Hardcoded exceptions to prevent false matches
    HARDCODED_EXCEPTIONS = {
        ("java", "javascript"): False,  # Java should not match JavaScript
        ("javascript", "java"): False,  # JavaScript should not match Java
        # Add more exceptions as needed
    }

    def _is_synonym(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are synonyms using the SKILL_SYNONYMS mapping."""
        s1 = skill1.strip().lower()
        s2 = skill2.strip().lower()
        return (
            s2 in self.SKILL_SYNONYMS.get(s1, []) or
            s1 in self.SKILL_SYNONYMS.get(s2, [])
        )

    def _is_fuzzy_match(self, skill1: str, skill2: str) -> bool:
        """Check for strict fuzzy/substring match (for short core skills only)."""
        s1 = skill1.strip().lower()
        s2 = skill2.strip().lower()
        # Only allow substring match for short skills (<= 10 chars)
        if len(s1) <= 10 and s1 in s2:
            return True
        if len(s2) <= 10 and s2 in s1:
            return True
        return False

    def _is_soft_skill(self, skill: str) -> bool:
        return skill.lower() in self.SOFT_SKILLS

    def _is_hardcoded_exception(self, skill1: str, skill2: str) -> bool:
        """
        Check if two skills are in a hardcoded exception list that prevents matching.
        Returns True if the skills should NOT be matched (exception applies).
        """
        key = (skill1.lower(), skill2.lower())
        return self.HARDCODED_EXCEPTIONS.get(key, False)

    def _cosine_similarity(self, vec1, vec2):
        import numpy as np
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
            return 0.0
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    async def match_employee_to_projects(
        self,
        db: Session,
        employee_id: int,
        threshold: float = None  # Use config threshold if not provided
    ) -> Dict[str, Any]:
        """
        Match an employee to all available projects.
        - Prioritizes exact string matches for skills.
        - Uses embedding similarity only for non-exact matches, with a strict threshold.
        - Returns a list of compatible projects with match percentages and missing skills.
        """
        try:
            # Ensure IDF factors are up to date before matching
            tfidf_service.update_skills_idf_factors(db)

            # Use config threshold if not provided
            if threshold is None:
                threshold = config_manager.get_matching_threshold()

            self.logger.info(f"Using matching threshold: {threshold}")

            # Get employee
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise ValueError(f"Employee with ID {employee_id} not found")

            # Get all projects
            projects = db.query(Project).all()
            if not projects:
                return {
                    "employee_id": employee_id,
                    "employee_name": employee.name,
                    "matches": [],
                    "missing_skills_summary": [],
                    "total_projects_checked": 0
                }

            # Get employee skills
            employee_skills = employee.get_skill_list()
            if not employee_skills:
                return {
                    "employee_id": employee_id,
                    "employee_name": employee.name,
                    "matches": [],
                    "missing_skills_summary": ["No skills defined for employee"],
                    "total_projects_checked": len(projects)
                }

            # Get or create employee skill embeddings
            employee_embeddings = await self._get_employee_embeddings(db, employee)

            # Match against each project
            matches = []
            missing_skills_summary = {}

            for project in projects:
                self.logger.debug(f"Matching employee {employee_id} against project {project.id} ({project.title})")
                self.logger.debug(f"Employee skills: {employee_skills}")
                self.logger.debug(f"Project requirements: {project.get_requirements_list()}")

                match_result = await self._match_project(
                    db, project, employee_skills, employee_embeddings, threshold
                )

                if match_result:
                    matches.append(match_result)

                    # Track missing skills
                    for skill in match_result["missing_skills"]:
                        missing_skills_summary[skill] = missing_skills_summary.get(skill, 0) + 1

            # Sort matches by percentage (descending)
            matches.sort(key=lambda x: x["match_percentage"], reverse=True)

            # Get top missing skills
            top_missing_skills = sorted(
                missing_skills_summary.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10 missing skills

            missing_skills_list = [skill for skill, count in top_missing_skills]

            return {
                "employee_id": employee_id,
                "employee_name": employee.name,
                "matches": matches,
                "missing_skills_summary": missing_skills_list,
                "total_projects_checked": len(projects)
            }

        except Exception as e:
            self.logger.error(f"Error matching employee {employee_id}: {str(e)}")
            raise

    async def _get_employee_embeddings(
        self,
        db: Session,
        employee: Employee
    ) -> Dict[str, List[float]]:
        """
        Get embeddings for employee skills through skills table lookup.
        Always uses the normalized approach: employee skills -> skills table -> embeddings.
        """
        try:
            if not self.openai_handler:
                raise ValueError("OpenAI handler not available")

            employee_skills = employee.get_skill_list()
            embeddings = {}

            for skill in employee_skills:
                # Always try to get from skills table first
                existing_skill = db.query(Skill).filter(
                    Skill.skill_name == skill
                ).first()

                if existing_skill:
                    embeddings[skill] = existing_skill.get_embedding()
                    self.logger.debug(f"Found existing embedding for skill: {skill}")
                else:
                    # Create new embedding and store in skills table
                    embedding = await self.openai_handler.get_embedding(skill)
                    if embedding:
                        embeddings[skill] = embedding
                        # Store for reuse in skills table
                        await self._store_skill_embedding(db, skill, embedding)
                        self.logger.debug(f"Created and stored embedding for skill: {skill}")

            return embeddings

        except Exception as e:
            self.logger.error(f"Error getting employee embeddings: {str(e)}")
            return {}

    async def _store_skill_embedding(
        self,
        db: Session,
        skill_name: str,
        embedding: List[float]
    ) -> None:
        """
        Store skill embedding in database for reuse.
        """
        try:
            # Check if skill already exists
            existing_skill = db.query(Skill).filter(
                Skill.skill_name == skill_name
            ).first()

            if not existing_skill:
                skill = Skill(skill_name=skill_name)
                skill.set_embedding(embedding)
                db.add(skill)
                db.commit()
                self.logger.debug(f"Stored embedding for skill: {skill_name}")

        except Exception as e:
            self.logger.error(f"Error storing skill embedding: {str(e)}")
            db.rollback()

    async def _match_project(
        self,
        db: Session,
        project: Project,
        employee_skills: List[str],
        employee_embeddings: Dict[str, List[float]],
        threshold: float
    ) -> Optional[Dict[str, Any]]:
        """
        Match a single project against employee skills with TF-IDF weighting.
        - Checks for exact string matches (case-insensitive) first.
        - Then checks for synonym matches.
        - Then checks for strict fuzzy/substring matches (for short skills).
        - Uses embedding similarity for non-exact matches, with strict normalization.
        - Weights each match by its TF-IDF factor for more accurate scoring.
        - Returns match percentage and lists of matching/missing skills.
        """
        try:
            project_requirements = project.get_requirements_list()
            if not project_requirements:
                return None

            self.logger.debug(f"Matching project {project.id} ({project.title})")
            self.logger.debug(f"Project requirements: {project_requirements}")
            self.logger.debug(f"Employee skills: {employee_skills}")

            project_embeddings = await self._get_project_embeddings(db, project)

            # Get TF-IDF weights for each requirement
            requirements_tf = project.get_requirements_tf()
            if not requirements_tf:
                # Fallback: if no TF data, use equal weights
                requirements_tf = {req: 1 for req in project_requirements}

            matching_skills = []
            missing_skills = []
            weighted_total_score = 0.0
            total_tfidf_weight = 0.0

            for req in project_requirements:
                req_embedding = project_embeddings.get(req)
                if not req_embedding:
                    continue

                # Get TF-IDF weight for this requirement
                tf_weight = requirements_tf.get(req, 1)  # Default to 1 if not found
                idf_factor = tfidf_service.get_skill_idf_factor(req, db)
                tfidf_weight = tf_weight * idf_factor
                total_tfidf_weight += tfidf_weight

                self.logger.debug(f"Requirement '{req}': TF={tf_weight}, IDF={idf_factor:.4f}, TF-IDF weight={tfidf_weight:.4f}")

                # 1. Exact string match (case-insensitive, quote/whitespace-insensitive)
                def normalize_skill(s):
                    return s.strip().strip('"').strip("'").lower()

                exact_match = None
                for emp_skill in employee_skills:
                    if normalize_skill(req) == normalize_skill(emp_skill):
                        exact_match = emp_skill
                        break
                if exact_match:
                    if self._is_hardcoded_exception(req, exact_match):
                        self.logger.info(f"[BLOCKED] {req} <-> {exact_match} (hardcoded exception after exact match)")
                        missing_skills.append(req)
                        self.logger.info(f"[NO MATCH] {req} (blocked by hardcoded exception, weight: {tfidf_weight:.4f})")
                        continue
                    matching_skills.append(req)  # Store project requirement, not employee skill
                    weighted_total_score += 1.0 * tfidf_weight
                    self.logger.info(f"[MATCH] {req} <-> {exact_match} (type: exact, score: 1.0, weight: {tfidf_weight:.4f})")
                    continue

                # 2. Synonym match (case-insensitive, quote/whitespace-insensitive)
                synonym_match = None
                for emp_skill in employee_skills:
                    if self._is_synonym(normalize_skill(req), normalize_skill(emp_skill)):
                        synonym_match = emp_skill
                        break
                if synonym_match:
                    if self._is_hardcoded_exception(req, synonym_match):
                        self.logger.info(f"[BLOCKED] {req} <-> {synonym_match} (hardcoded exception after synonym match)")
                        missing_skills.append(req)
                        self.logger.info(f"[NO MATCH] {req} (blocked by hardcoded exception, weight: {tfidf_weight:.4f})")
                        continue
                    matching_skills.append(req)  # Store project requirement, not employee skill
                    weighted_total_score += 0.95 * tfidf_weight
                    self.logger.info(f"[MATCH] {req} <-> {synonym_match} (type: synonym, score: 0.95, weight: {tfidf_weight:.4f})")
                    continue

                # 3. For soft skills, skip embedding similarity
                if self._is_soft_skill(normalize_skill(req)):
                    missing_skills.append(req)
                    self.logger.info(f"[NO MATCH] {req} (soft skill, no embedding match allowed, weight: {tfidf_weight:.4f})")
                    continue

                # 4. Embedding similarity (configurable: euclidean or cosine)
                best_match_score = 0.0
                best_match_skill = None
                best_match_type = None
                for emp_skill, emp_embedding in employee_embeddings.items():
                    if not emp_embedding:
                        continue
                    distance_model = config_manager.get_distance_model().lower()
                    if distance_model == "cosine":
                        similarity = self._cosine_similarity(req_embedding, emp_embedding)
                    else:
                        distance = self.openai_handler.calculate_distance(req_embedding, emp_embedding)
                        similarity = max(0, 1 - (distance / 0.3))
                    if similarity > best_match_score:
                        best_match_score = similarity
                        best_match_skill = emp_skill
                        best_match_type = distance_model
                if best_match_score >= threshold and best_match_skill is not None:
                    if self._is_hardcoded_exception(req, best_match_skill):
                        self.logger.info(f"[BLOCKED] {req} <-> {best_match_skill} (hardcoded exception after embedding match)")
                        missing_skills.append(req)
                        self.logger.info(f"[NO MATCH] {req} (blocked by hardcoded exception, weight: {tfidf_weight:.4f})")
                    else:
                        matching_skills.append(req)  # Store project requirement, not employee skill
                        weighted_total_score += 1.0 * tfidf_weight
                        self.logger.info(f"[MATCH] {req} <-> {best_match_skill} (type: {best_match_type}, score: {best_match_score:.3f}, weight: {tfidf_weight:.4f})")
                else:
                    missing_skills.append(req)
                    self.logger.info(f"[NO MATCH] {req} (best score: {best_match_score:.3f}, threshold: {threshold}, weight: {tfidf_weight:.4f})")

            # Remove duplicates from matching_skills while preserving order
            seen = set()
            unique_matching_skills = []
            for skill in matching_skills:
                if skill not in seen:
                    seen.add(skill)
                    unique_matching_skills.append(skill)
            matching_skills = unique_matching_skills

            # Calculate normalized match percentage using TF-IDF weights
            if total_tfidf_weight > 0:
                match_percentage = (weighted_total_score / total_tfidf_weight) * 100
            else:
                match_percentage = 0.0

            self.logger.info(f"Project {project.id} match calculation: weighted_score={weighted_total_score:.4f}, total_weight={total_tfidf_weight:.4f}, percentage={match_percentage:.2f}%")

            return {
                "project_id": project.id,
                "project_title": project.title,
                "match_percentage": round(match_percentage, 2),
                "matching_skills": matching_skills,
                "missing_skills": missing_skills
            }
        except Exception as e:
            self.logger.error(f"Error matching project {project.id}: {str(e)}")
            return None

    async def _get_project_embeddings(
        self,
        db: Session,
        project: Project
    ) -> Dict[str, List[float]]:
        """
        Get embeddings for project requirements through skills table lookup.
        Always uses the normalized approach: requirements -> skills table -> embeddings.
        """
        try:
            if not self.openai_handler:
                raise ValueError("OpenAI handler not available")

            project_requirements = project.get_requirements_list()
            embeddings = {}

            for req in project_requirements:
                # Always try to get from skills table first
                existing_skill = db.query(Skill).filter(
                    Skill.skill_name == req
                ).first()

                if existing_skill:
                    embeddings[req] = existing_skill.get_embedding()
                    self.logger.debug(f"Found existing embedding for requirement: {req}")
                else:
                    # Create new embedding and store in skills table
                    embedding = await self.openai_handler.get_embedding(req)
                    if embedding:
                        embeddings[req] = embedding
                        # Store for reuse in skills table
                        await self._store_skill_embedding(db, req, embedding)
                        self.logger.debug(f"Created and stored embedding for requirement: {req}")

            return embeddings

        except Exception as e:
            self.logger.error(f"Error getting project embeddings: {str(e)}")
            return {}

    async def get_skill_suggestions(
        self,
        db: Session,
        employee_id: int,
        limit: int = 5
    ) -> List[str]:
        """
        Get skill suggestions for an employee based on missing skills.
        """
        try:
            # Get employee's current skills
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return []

            current_skills = set(employee.get_skill_list())

            # Get all skills from database
            all_skills = db.query(Skill).all()
            available_skills = [skill.skill_name for skill in all_skills]

            # Filter out skills the employee already has
            missing_skills = [skill for skill in available_skills if skill not in current_skills]

            # Return top missing skills (simple implementation)
            return missing_skills[:limit]

        except Exception as e:
            self.logger.error(f"Error getting skill suggestions: {str(e)}")
            return []

    async def rebuild_all_embeddings(self, db: Session) -> Dict[str, Any]:
        """
        Rebuild all embeddings for projects and employees, populating the skills table.
        """
        try:
            if not self.openai_handler:
                raise ValueError("OpenAI handler not available")

            self.logger.info("Starting to rebuild all embeddings...")

            # Get all unique skills from projects and employees
            all_skills = set()

            # Collect skills from employees
            employees = db.query(Employee).all()
            for employee in employees:
                skills = employee.get_skill_list()
                all_skills.update(skills)

            # Collect skills from projects
            projects = db.query(Project).all()
            for project in projects:
                requirements = project.get_requirements_list()
                all_skills.update(requirements)

            self.logger.info(f"Found {len(all_skills)} unique skills to process")

            # Create embeddings for all skills
            skills_processed = 0
            for skill in all_skills:
                if skill.strip():  # Skip empty skills
                    try:
                        # Check if skill already exists
                        existing_skill = db.query(Skill).filter(
                            Skill.skill_name == skill
                        ).first()

                        if not existing_skill:
                            # Create new skill with embedding
                            embedding = await self.openai_handler.get_embedding(skill)
                            if embedding:
                                await self._store_skill_embedding(db, skill, embedding)
                                skills_processed += 1
                                self.logger.debug(f"Created embedding for skill: {skill}")
                        else:
                            # Check if existing skill has empty embedding
                            existing_embedding = existing_skill.get_embedding()
                            if not existing_embedding or len(existing_embedding) == 0:
                                # Update existing skill with embedding
                                embedding = await self.openai_handler.get_embedding(skill)
                                if embedding:
                                    existing_skill.set_embedding(embedding)
                                    skills_processed += 1
                                    self.logger.debug(f"Updated embedding for existing skill: {skill}")
                    except Exception as e:
                        self.logger.error(f"Error processing skill '{skill}': {str(e)}")

            # Rebuild employee embeddings (projects no longer store embeddings)
            employees_processed = 0
            for employee in employees:
                try:
                    # Get employee embeddings through skills table lookup
                    await self._get_employee_embeddings(db, employee)
                    employees_processed += 1
                except Exception as e:
                    self.logger.error(f"Error rebuilding employee {employee.id} embeddings: {str(e)}")

            db.commit()

            result = {
                "status": "success",
                "skills_processed": skills_processed,
                "employees_processed": employees_processed,
                "total_unique_skills": len(all_skills)
            }

            self.logger.info(f"Embedding rebuild completed: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error rebuilding embeddings: {str(e)}")
            db.rollback()
            raise