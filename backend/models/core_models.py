"""Core SQLAlchemy models for the Project Finder application."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Any, Dict
import json

Base = declarative_base()


class Project(Base):
    """Database model for project information."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    release_date = Column(String(20), nullable=True)
    start_date = Column(String(20), nullable=True)
    location = Column(String(200), nullable=True)
    tenderer = Column(String(200), nullable=True)
    project_id = Column(String(100), nullable=True, index=True)
    requirements_tf = Column(Text, nullable=True)  # JSON string of requirements with term frequency
    rate = Column(String(100), nullable=True)
    url = Column(String(1000), nullable=True)
    budget = Column(String(100), nullable=True)
    duration = Column(String(100), nullable=True)
    workload = Column(String(100), nullable=True)  # Workload in hours per week
    sort_order = Column(Integer, nullable=True, index=True)  # For efficient ordering by release date
    last_scan = Column(DateTime(timezone=True), server_default=func.now())

    def get_requirements_list(self) -> List[str]:
        """Get requirements as a list of strings from requirements_tf."""
        requirements_tf = self.get_requirements_tf()
        return list(requirements_tf.keys()) if requirements_tf else []

    def get_requirements_tf(self) -> Dict[str, int]:
        """Get requirements with term frequency as a dictionary."""
        if not self.requirements_tf:
            return {}
        try:
            return json.loads(self.requirements_tf)
        except json.JSONDecodeError:
            return {}

    def set_requirements_tf(self, requirements_tf: Dict[str, int]) -> None:
        """Set requirements with term frequency from a dictionary."""
        self.requirements_tf = json.dumps(requirements_tf, ensure_ascii=False)


class Skill(Base):
    """Database model for skill embeddings."""

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(200), nullable=False, unique=True, index=True)
    embedding = Column(Text, nullable=False)  # JSON string of embedding vector
    idf_factor = Column(Float, nullable=True)  # Inverse Document Frequency factor
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def get_embedding(self) -> List[float]:
        """Get embedding as a list of floats."""
        try:
            return json.loads(self.embedding)
        except json.JSONDecodeError:
            return []

    def set_embedding(self, embedding: List[float]) -> None:
        """Set embedding from a list of floats."""
        self.embedding = json.dumps(embedding, ensure_ascii=False)


class Employee(Base):
    """Database model for employee information."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    skill_list = Column(Text, nullable=True)  # JSON string of skills
    experience_years = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def get_skill_list(self) -> List[str]:
        """Get skills as a list of strings."""
        if not self.skill_list:
            return []
        try:
            return json.loads(self.skill_list)
        except json.JSONDecodeError:
            return []

    def set_skill_list(self, skills: List[str]) -> None:
        """Set skills from a list of strings, removing duplicates (case-insensitive, preserving first occurrence)."""
        seen = set()
        deduped_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                deduped_skills.append(skill)
        self.skill_list = json.dumps(deduped_skills, ensure_ascii=False)


class AppState(Base):
    """Database model for application state."""

    __tablename__ = "app_state"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def get_value(self) -> Any:
        """Get value as JSON."""
        if not self.value:
            return None
        try:
            return json.loads(self.value)
        except json.JSONDecodeError:
            return self.value

    def set_value(self, value: Any) -> None:
        """Set value as JSON."""
        if isinstance(value, (dict, list)):
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)