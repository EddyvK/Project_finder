#!/usr/bin/env python3
"""
Script to debug the matching logic for Michael Brown and see why permissive matches occur, including similarity scores.
"""

from backend.database import SessionLocal
from backend.models.core_models import Project, Employee
from backend.matching_service import MatchingService, config_manager
import asyncio

async def debug_matching_logic():
    db = SessionLocal()
    matching_service = MatchingService()

    try:
        # Get Michael Brown
        employee = db.query(Employee).filter(Employee.name == "Michael Brown").first()
        if not employee:
            print("Michael Brown not found")
            return
        print(f"Testing with employee: {employee.name}")
        print(f"Employee skills: {employee.get_skill_list()}")

        # Get all projects
        projects = db.query(Project).all()
        threshold = config_manager.get_matching_threshold()
        print(f"\nUsing similarity threshold: {threshold}")

        for project in projects[:3]:  # Limit to first 3 projects for brevity
            print(f"\nProject: {project.title}")
            requirements = project.get_requirements_list()
            print(f"Requirements: {requirements}")

            # Get embeddings
            project_embeddings = await matching_service._get_project_embeddings(db, project)
            employee_embeddings = await matching_service._get_employee_embeddings(db, employee)

            for req in requirements:
                req_embedding = project_embeddings.get(req)
                if not req_embedding:
                    continue
                best_match_score = 0.0
                best_match_skill = None
                for emp_skill, emp_embedding in employee_embeddings.items():
                    if not emp_embedding:
                        continue
                    distance_model = config_manager.get_distance_model().lower()
                    if distance_model == "cosine":
                        similarity = matching_service._cosine_similarity(req_embedding, emp_embedding)
                    else:
                        distance = matching_service.openai_handler.calculate_distance(req_embedding, emp_embedding)
                        similarity = max(0, 1 - (distance / 0.3))
                    if similarity > best_match_score:
                        best_match_score = similarity
                        best_match_skill = emp_skill
                if best_match_score >= threshold:
                    print(f"  [MATCH] {req} <-> {best_match_skill} | similarity: {best_match_score:.3f} (ABOVE threshold)")
                else:
                    print(f"  [NO MATCH] {req} | best similarity: {best_match_score:.3f}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_matching_logic())