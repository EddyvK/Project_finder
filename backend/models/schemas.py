"""Pydantic schemas for API validation and serialization."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProjectBase(BaseModel):
    """Base schema for project data."""

    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    release_date: Optional[str] = Field(None, max_length=20)
    start_date: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=200)
    tenderer: Optional[str] = Field(None, max_length=200)
    project_id: Optional[str] = Field(None, max_length=100)
    requirements_tf: Optional[Dict[str, int]] = None
    rate: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=1000)
    budget: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    workload: Optional[str] = Field(None, max_length=100)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    release_date: Optional[str] = Field(None, max_length=20)
    start_date: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=200)
    tenderer: Optional[str] = Field(None, max_length=200)
    project_id: Optional[str] = Field(None, max_length=100)
    requirements_tf: Optional[Dict[str, int]] = None
    rate: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=1000)
    budget: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    workload: Optional[str] = Field(None, max_length=100)


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: int
    last_scan: Optional[str] = None

    @validator('requirements_tf', pre=True)
    def parse_requirements_tf(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v

    @validator('last_scan', pre=True)
    def parse_last_scan(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v
        try:
            return v.isoformat()
        except Exception:
            return str(v)

    class Config:
        from_attributes = True


class SkillBase(BaseModel):
    """Base schema for skill data."""

    skill_name: str = Field(..., max_length=200)
    embedding: Optional[List[float]] = None
    idf_factor: Optional[float] = None


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""

    skill_name: Optional[str] = Field(None, max_length=200)
    embedding: Optional[List[float]] = None
    idf_factor: Optional[float] = None


class SkillResponse(SkillBase):
    """Schema for skill response."""

    id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeBase(BaseModel):
    """Base schema for employee data."""

    name: str = Field(..., max_length=200)
    skill_list: Optional[List[str]] = None
    experience_years: Optional[int] = None


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee."""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""

    name: Optional[str] = Field(None, max_length=200)
    skill_list: Optional[List[str]] = None
    experience_years: Optional[int] = None


class EmployeeResponse(EmployeeBase):
    """Schema for employee response."""

    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v
        try:
            return v.isoformat()
        except Exception:
            return str(v)

    class Config:
        from_attributes = True


class AppStateBase(BaseModel):
    """Base schema for app state data."""

    key: str = Field(..., max_length=100)
    value: Optional[Any] = None


class AppStateCreate(AppStateBase):
    """Schema for creating app state."""
    pass


class AppStateUpdate(BaseModel):
    """Schema for updating app state."""

    key: Optional[str] = Field(None, max_length=100)
    value: Optional[Any] = None


class AppStateResponse(AppStateBase):
    """Schema for app state response."""

    id: int
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    """Schema for scan response."""

    status: str
    projects_found: int
    projects_processed: int
    errors: List[str]
    duration: float


class MatchResult(BaseModel):
    """Schema for match result."""

    project_id: int
    project_title: str
    match_percentage: float
    matching_skills: List[str]
    missing_skills: List[str]


class EmployeeMatchResponse(BaseModel):
    """Schema for employee match response."""

    employee_id: int
    employee_name: str
    matches: List[MatchResult]
    missing_skills_summary: List[str]
    total_projects_checked: int


class ScanResult(BaseModel):
    """Schema for scan result."""

    success: bool
    message: str
    projects_scanned: int
    errors: List[str] = []