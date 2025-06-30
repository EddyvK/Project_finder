"""Main FastAPI application for Project Finder."""

import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import logging
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import local modules
from backend.database import get_db, init_db
from backend.logger_config import setup_logging
from backend.config_manager import config_manager
from backend.models.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    SkillCreate, SkillResponse,
    AppStateCreate, AppStateUpdate, AppStateResponse,
    ScanResponse, EmployeeMatchResponse
)
from backend.models.core_models import Project, Employee, AppState
from backend.web_scraper import WebScraper
from backend.matching_service import MatchingService
from backend.scan_service import scan_service
from backend.utils.date_utils import european_to_iso_date
from backend.matching_service import MatchingService
from backend.tfidf_service import TFIDFService
from backend.openai_handler import OpenAIHandler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Create FastAPI app
app = FastAPI(
    title="Project Finder API",
    description="API for matching employees with projects based on skill compatibility",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize services
web_scraper = WebScraper()
matching_service = MatchingService()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Project Finder API starting up")

    # Validate configuration
    if not config_manager.validate_config():
        logger.warning("Configuration validation failed")

    logger.info("Project Finder API startup complete")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Project Finder API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Project Finder API is running"}


# Project endpoints
@app.get("/api/projects", response_model=List[ProjectResponse])
async def get_projects(
    time_range: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all projects, optionally filtered by time range."""
    try:
        query = db.query(Project)

        # Filter by time range if specified
        if time_range:
            # Calculate cutoff date based on time range
            today = datetime.now()
            cutoff_date = today - timedelta(days=time_range)

            # Get all projects and filter by release date
            all_projects = query.all()
            filtered_projects = []

            for project in all_projects:
                if not project.release_date:
                    # If no release date, include the project
                    filtered_projects.append(project)
                    continue

                # Convert European date to ISO format for comparison
                iso_date = european_to_iso_date(project.release_date)
                if not iso_date:
                    # If date parsing fails, include the project
                    filtered_projects.append(project)
                    continue

                try:
                    project_date = datetime.fromisoformat(iso_date)
                    # Normalize to date only (remove time component)
                    project_date = project_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    cutoff_date_normalized = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

                    # Include projects that are on or after the cutoff date
                    if project_date >= cutoff_date_normalized:
                        filtered_projects.append(project)
                except ValueError:
                    # If date parsing fails, include the project
                    filtered_projects.append(project)

            # Use sort_order if available, otherwise sort by release date
            if any(p.sort_order is not None for p in filtered_projects):
                # Use the pre-computed sort_order for efficient ordering
                projects = sorted(filtered_projects, key=lambda p: p.sort_order if p.sort_order is not None else float('inf'))
            else:
                # Fallback to release date sorting
                def get_sort_key(project):
                    if not project.release_date:
                        return datetime.min  # Put projects with no date at the end
                    iso_date = european_to_iso_date(project.release_date)
                    if not iso_date:
                        return datetime.min  # Put unparseable dates at the end
                    try:
                        return datetime.fromisoformat(iso_date)
                    except ValueError:
                        return datetime.min

                projects = sorted(filtered_projects, key=get_sort_key, reverse=True)
        else:
            # No time range filter - use sort_order for efficient ordering
            if db.query(Project).filter(Project.sort_order.isnot(None)).first():
                # Use sort_order if it exists
                projects = query.order_by(Project.sort_order).all()
            else:
                # Fallback to release date sorting
                projects = query.all()
                def get_sort_key(project):
                    if not project.release_date:
                        return datetime.min
                    iso_date = european_to_iso_date(project.release_date)
                    if not iso_date:
                        return datetime.min
                    try:
                        return datetime.fromisoformat(iso_date)
                    except ValueError:
                        return datetime.min

                projects = sorted(projects, key=get_sort_key, reverse=True)

        # Convert to response models with proper field conversion
        response_projects = []
        for project in projects:
            # Convert datetime to ISO string for JSON serialization
            last_scan_str = project.last_scan.isoformat() if project.last_scan else None

            response_project = ProjectResponse(
                id=project.id,
                title=project.title,
                description=project.description,
                release_date=project.release_date,
                start_date=project.start_date,
                location=project.location,
                tenderer=project.tenderer,
                project_id=project.project_id,
                requirements_tf=project.get_requirements_tf(),  # Include term frequency data
                rate=project.rate,
                url=project.url,
                budget=project.budget,
                duration=project.duration,
                workload=project.workload,
                last_scan=last_scan_str
            )
            response_projects.append(response_project)

        return response_projects

    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Convert to response model with proper field conversion
        # Convert datetime to ISO string for JSON serialization
        last_scan_str = project.last_scan.isoformat() if project.last_scan else None

        response_project = ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            release_date=project.release_date,
            start_date=project.start_date,
            location=project.location,
            tenderer=project.tenderer,
            project_id=project.project_id,
            requirements_tf=project.get_requirements_tf(),  # Include term frequency data
            rate=project.rate,
            url=project.url,
            budget=project.budget,
            duration=project.duration,
            workload=project.workload,
            last_scan=last_scan_str
        )

        return response_project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Update fields
        update_data = project_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "requirements_tf" and value is not None:
                project.set_requirements_tf(value)
            else:
                setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error updating project {project_id}: {str(e)}\nTraceback:\n{tb}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}\nTraceback:\n{tb}"
        )


# Employee endpoints
@app.get("/api/employees", response_model=List[EmployeeResponse])
async def get_employees(db: Session = Depends(get_db)):
    """Get all employees."""
    try:
        employees = db.query(Employee).all()

        # Convert to response models with proper field conversion
        response_employees = []
        for employee in employees:
            response_employee = EmployeeResponse(
                id=employee.id,
                name=employee.name,
                skill_list=employee.get_skill_list(),
                experience_years=employee.experience_years,
                created_at=employee.created_at,
                updated_at=employee.updated_at
            )
            response_employees.append(response_employee)

        return response_employees

    except Exception as e:
        logger.error(f"Error getting employees: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employees"
        )


@app.post("/api/employees", response_model=EmployeeResponse)
async def create_employee(
    employee_create: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """Create a new employee."""
    try:
        employee = Employee(
            name=employee_create.name,
            experience_years=employee_create.experience_years
        )

        if employee_create.skill_list:
            employee.set_skill_list(employee_create.skill_list)

        db.add(employee)
        db.commit()
        db.refresh(employee)

        logger.info(f"Created employee: {employee.name}")

        # Convert to response model with proper field conversion
        response_employee = EmployeeResponse(
            id=employee.id,
            name=employee.name,
            skill_list=employee.get_skill_list(),
            experience_years=employee.experience_years,
            created_at=employee.created_at,
            updated_at=employee.updated_at
        )

        return response_employee

    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee"
        )


@app.put("/api/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """Update an employee."""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        # Update fields
        update_data = employee_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "skill_list" and value is not None:
                # Get old skills for comparison
                old_skills = set(employee.get_skill_list())
                new_skills = set(value)

                # Find new skills that need processing
                new_skills_to_process = new_skills - old_skills

                # Update the employee's skill list immediately
                employee.set_skill_list(value)

                # Process new skills asynchronously (non-blocking)
                if new_skills_to_process:
                    logger.info(f"Processing {len(new_skills_to_process)} new skills for employee {employee.name}")

                    # Start async processing in background
                    asyncio.create_task(process_new_skills_async(new_skills_to_process, db))
            else:
                setattr(employee, field, value)

        db.commit()
        db.refresh(employee)

        logger.info(f"Updated employee: {employee.name}")

        # Convert to response model with proper field conversion
        response_employee = EmployeeResponse(
            id=employee.id,
            name=employee.name,
            skill_list=employee.get_skill_list(),
            experience_years=employee.experience_years,
            created_at=employee.created_at,
            updated_at=employee.updated_at
        )

        return response_employee

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee {employee_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee"
        )

async def process_new_skills_async(new_skills: set, db: Session):
    """Process new skills asynchronously without blocking the API response."""
    try:
        # Initialize services if needed
        api_keys = config_manager.get_api_keys()
        openai_handler = None
        if api_keys.get("openai"):
            try:
                openai_handler = OpenAIHandler(api_keys["openai"])
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI handler: {str(e)}")

        if openai_handler:
            tfidf_service = TFIDFService()

            for skill in new_skills:
                try:
                    # Check if skill already exists in skills table
                    existing_skill = db.query(Skill).filter(
                        Skill.skill_name == skill
                    ).first()

                    if not existing_skill:
                        # Create new skill with embedding (with timeout)
                        try:
                            embedding = await asyncio.wait_for(
                                openai_handler.get_embedding(skill),
                                timeout=10.0  # 10 second timeout per embedding
                            )
                            if embedding:
                                # Store in skills table
                                skill_record = Skill(skill_name=skill)
                                skill_record.set_embedding(embedding)
                                db.add(skill_record)
                                logger.info(f"Created embedding for new skill: {skill}")
                        except asyncio.TimeoutError:
                            logger.warning(f"Timeout creating embedding for skill: {skill}")
                        except Exception as e:
                            logger.error(f"Error creating embedding for skill '{skill}': {str(e)}")
                    else:
                        # Check if existing skill has empty embedding
                        existing_embedding = existing_skill.get_embedding()
                        if not existing_embedding or len(existing_embedding) == 0:
                            try:
                                embedding = await asyncio.wait_for(
                                    openai_handler.get_embedding(skill),
                                    timeout=10.0
                                )
                                if embedding:
                                    existing_skill.set_embedding(embedding)
                                    logger.info(f"Updated embedding for existing skill: {skill}")
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout updating embedding for skill: {skill}")
                            except Exception as e:
                                logger.error(f"Error updating embedding for skill '{skill}': {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing skill '{skill}': {str(e)}")

            # Only recalculate IDF factors if we processed a significant number of skills
            if len(new_skills) > 5:
                try:
                    tfidf_service.recalculate_idf_factors(db)
                    logger.info("Recalculated IDF factors after skill update")
                except Exception as e:
                    logger.error(f"Error recalculating IDF factors: {str(e)}")
            else:
                logger.info(f"Skipping IDF recalculation for {len(new_skills)} new skills")
        else:
            logger.warning("OpenAI handler not available - new skills will not have embeddings")
    except Exception as e:
        logger.error(f"Error in async skill processing: {str(e)}")


@app.delete("/api/employees/{employee_id}")
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Delete an employee."""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        db.delete(employee)
        db.commit()

        logger.info(f"Deleted employee: {employee.name}")
        return {"message": "Employee deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting employee {employee_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete employee"
        )


# Scanning endpoints
@app.post("/api/scan/{time_range}", response_model=ScanResponse)
async def scan_projects(
    time_range: int,
    db: Session = Depends(get_db)
):
    """Scan for new projects."""
    try:
        result = await scan_service.scan_projects(time_range, db)
        return ScanResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during project scan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan projects"
        )


@app.delete("/api/projects")
async def clear_projects(db: Session = Depends(get_db)):
    """Clear all projects from database."""
    try:
        count = db.query(Project).count()
        db.query(Project).delete()
        db.commit()

        logger.info(f"Cleared {count} projects from database")
        return {"message": f"Cleared {count} projects from database"}

    except Exception as e:
        logger.error(f"Error clearing projects: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear projects"
        )


@app.post("/api/deduplication")
async def run_deduplication(db: Session = Depends(get_db)):
    """Run deduplication to remove redundant projects from database."""
    try:
        from backend.deduplication_service import deduplication_service
        result = deduplication_service.run_deduplication(db)

        logger.info(f"Deduplication completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error running deduplication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run deduplication"
        )


# Matching endpoints
@app.get("/api/matches/{employee_id}", response_model=EmployeeMatchResponse)
async def get_matches(employee_id: int, db: Session = Depends(get_db)):
    """Get project matches for an employee."""
    try:
        result = await matching_service.match_employee_to_projects(db, employee_id)
        return EmployeeMatchResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting matches for employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get matches"
        )


@app.post("/api/embeddings/rebuild")
async def rebuild_embeddings(db: Session = Depends(get_db)):
    """Rebuild all embeddings for projects and employees."""
    try:
        result = await matching_service.rebuild_all_embeddings(db)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rebuilding embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rebuild embeddings"
        )


# App state endpoints
@app.get("/api/state/{key}")
async def get_app_state(key: str, db: Session = Depends(get_db)):
    """Get application state value."""
    try:
        state = db.query(AppState).filter(AppState.key == key).first()
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="State key not found"
            )
        return {"key": key, "value": state.get_value()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting app state {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get app state"
        )


@app.put("/api/state/{key}")
async def update_app_state(
    key: str,
    value: Any,
    db: Session = Depends(get_db)
):
    """Update application state value."""
    try:
        state = db.query(AppState).filter(AppState.key == key).first()
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="State key not found"
            )

        state.set_value(value)
        db.commit()

        logger.info(f"Updated app state {key}: {value}")
        return {"key": key, "value": state.get_value()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating app state {key}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update app state"
        )


# Database inspection endpoints
@app.get("/api/database/tables")
async def get_database_tables(db: Session = Depends(get_db)):
    """Get list of all tables in the database."""
    try:
        # Get table names from SQLAlchemy metadata
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()

        return {"tables": tables}
    except Exception as e:
        logger.error(f"Error getting database tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get database tables"
        )


@app.get("/api/database/table/{table_name}")
async def get_table_data(table_name: str, db: Session = Depends(get_db)):
    """Get data from a specific table."""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.bind)

        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table '{table_name}' not found"
            )

        # Get column information
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]

        # Get row count
        row_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

        # Get table data (limit to first 100 rows for performance)
        result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
        rows = []
        for row in result:
            # Convert row to dict and handle datetime objects
            row_dict = {}
            for i, value in enumerate(row):
                if hasattr(value, 'isoformat'):  # Handle datetime objects
                    row_dict[column_names[i]] = value.isoformat()
                else:
                    row_dict[column_names[i]] = value
            rows.append(row_dict)

        response_data = {
            "table_name": table_name,
            "columns": column_names,
            "row_count": row_count,
            "column_count": len(column_names),
            "data": rows,
            "total_rows": row_count,
            "displayed_rows": len(rows)
        }
        # Use ensure_ascii=False to preserve special characters
        return JSONResponse(content=json.loads(json.dumps(response_data, ensure_ascii=False)))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table data for {table_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get table data"
        )


@app.get("/api/scan/stream/{time_range}")
async def scan_projects_stream(
    time_range: int,
    db: Session = Depends(get_db)
):
    """Scan for new projects and stream results using Server-Sent Events."""
    try:
        return StreamingResponse(
            scan_service.scan_projects_stream(time_range, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "GET",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during streaming project scan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan projects"
        )


@app.post("/api/scan/cancel/{scan_id}")
async def cancel_scan(scan_id: str):
    """Cancel an active scan by its ID."""
    try:
        success = scan_service.cancel_scan(scan_id)
        if success:
            return {"message": f"Scan {scan_id} cancelled successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id} not found or already completed"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling scan {scan_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel scan"
        )


@app.get("/api/scan/status")
async def get_scan_status():
    """Get the current scan status."""
    try:
        is_active = scan_service.is_scan_active()
        return {"is_active": is_active}
    except Exception as e:
        logger.error(f"Error getting scan status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan status"
        )


@app.post("/api/test-data")
async def create_test_data(db: Session = Depends(get_db)):
    """Create test data (projects and employees) for development/testing."""
    try:
        from backend.init_db import create_test_data
        create_test_data(db)
        project_count = db.query(Project).filter(Project.tenderer == "Test").count()
        employee_count = db.query(Employee).count()
        return {
            "message": f"Test data created successfully",
            "projects_created": project_count,
            "employees_created": employee_count
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error creating test data: {str(e)}\nTraceback:\n{tb}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test data: {str(e)}\nTraceback:\n{tb}"
        )


if __name__ == "__main__":
    import uvicorn

    server_config = config_manager.get_server_config()
    uvicorn.run(
        "main:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=True
    )