"""Database configuration and session management."""

import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

# Try to import from backend first, then fall back to direct import
try:
    from backend.models.core_models import Base
except ImportError:
    from models.core_models import Base

logger = logging.getLogger(__name__)

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../project_finder.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables."""
    try:
        # Import all models to ensure they are registered
        try:
            from backend.models.core_models import Project, Skill, Employee, AppState
        except ImportError:
            from models.core_models import Project, Skill, Employee, AppState

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Initialize default app state
        db = SessionLocal()
        try:
            # Check if app state already exists
            try:
                from backend.models.core_models import AppState as AppStateModel
            except ImportError:
                from models.core_models import AppState as AppStateModel

            existing_state = db.query(AppStateModel).filter(
                AppStateModel.key == "live_mode"
            ).first()

            if not existing_state:
                # Create default app state
                default_states = [
                    AppStateModel(
                        key="live_mode",
                        value="true"
                    ),
                    AppStateModel(
                        key="overwrite",
                        value="false"
                    ),
                    AppStateModel(
                        key="last_scan",
                        value="null"
                    )
                ]

                for state in default_states:
                    db.add(state)

                db.commit()
                logger.info("Default app state initialized")

        except Exception as e:
            logger.error(f"Error initializing app state: {str(e)}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise