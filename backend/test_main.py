"""Simplified test version of main.py to debug the issue."""

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.core_models import Project, Employee
from backend.models.schemas import ProjectResponse, EmployeeResponse

app = FastAPI()

@app.get("/test/projects")
async def test_get_projects(db: Session = Depends(get_db)):
    """Test endpoint for projects."""
    try:
        projects = db.query(Project).all()
        return {"count": len(projects), "message": "Success"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/employees")
async def test_get_employees(db: Session = Depends(get_db)):
    """Test endpoint for employees."""
    try:
        employees = db.query(Employee).all()
        return {"count": len(employees), "message": "Success"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)