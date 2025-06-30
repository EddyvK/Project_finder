"""Scan service for handling project scanning operations.

This file is now considered STABLE and should not be changed unless explicitly requested.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.config_manager import config_manager
from backend.models.core_models import Project, AppState
from backend.models.schemas import ProjectResponse
from backend.web_scraper import WebScraper
from backend.deduplication_service import deduplication_service
from backend.tfidf_service import tfidf_service

logger = logging.getLogger(__name__)


class ScanService:
    """Service for scanning projects from configured websites."""

    def __init__(self):
        self.web_scraper = WebScraper()
        self.active_scans = {}  # Track active scans by scan_id
        self._scan_lock = False  # Global lock to prevent multiple scans

    def cancel_scan(self, scan_id: str) -> bool:
        """Cancel an active scan by its ID."""
        if scan_id in self.active_scans:
            self.active_scans[scan_id] = True  # Mark as cancelled
            logger.info(f"Scan {scan_id} marked for cancellation")
            return True
        return False

    def is_scan_cancelled(self, scan_id: str) -> bool:
        """Check if a scan has been cancelled."""
        return self.active_scans.get(scan_id, False)

    def _register_scan(self, scan_id: str) -> None:
        """Register a new scan as active."""
        self.active_scans[scan_id] = False

    def _unregister_scan(self, scan_id: str) -> None:
        """Unregister a scan when it's complete."""
        if scan_id in self.active_scans:
            del self.active_scans[scan_id]

    def is_scan_active(self) -> bool:
        """Check if any scan is currently active."""
        return self._scan_lock or len(self.active_scans) > 0

    def _acquire_scan_lock(self) -> bool:
        """Try to acquire the scan lock. Returns True if successful, False if already locked."""
        if self._scan_lock:
            return False
        self._scan_lock = True
        return True

    def _release_scan_lock(self) -> None:
        """Release the scan lock."""
        self._scan_lock = False

    async def scan_projects(self, time_range: int, db: Session) -> Dict[str, Any]:
        """Scan for new projects using the traditional approach."""
        # Check if a scan is already active
        if not self._acquire_scan_lock():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another scan is already in progress. Please wait for it to complete."
            )

        # Generate unique scan ID for correlation
        scan_id = str(uuid.uuid4())[:8]  # e.g., "a1b2c3d4"
        scan_logger = logging.getLogger(f"scan.{scan_id}")

        try:
            # Register this scan as active
            self._register_scan(scan_id)
            scan_logger.info(f"Starting project scan with time_range: {time_range}")

            # Collect existing projects data once at the beginning
            existing_projects = db.query(Project).all()
            existing_project_data = {
                project.url: {
                    'id': project.id,
                    'title': project.title,
                    'url': project.url,
                    'release_date': project.release_date,
                    'start_date': project.start_date,
                    'duration': project.duration,
                    'location': project.location,
                    'tenderer': project.tenderer,
                    'rate': project.rate,
                    'description': project.description,
                    'project_id': project.project_id,
                    'budget': project.budget,
                    'workload': project.workload
                } for project in existing_projects
            }

            # Get website configurations
            websites = config_manager.get_websites()
            if not websites:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No websites configured for scanning"
                )

            total_projects = 0
            errors = []

            # Scan each website
            for website_config in websites:
                try:
                    website_name = website_config['level1_search']['name']
                    website_logger = logging.getLogger(f"scan.{scan_id}.website.{website_name}")

                    website_logger.info(f"Scanning website: {website_name}")
                    projects = await self.web_scraper.scan_website(website_config, time_range, existing_project_data, scan_id)

                    # Save projects to database
                    for project_data in projects:
                        try:
                            project = Project(
                                title=project_data.get("title", ""),
                                description=project_data.get("description"),
                                release_date=project_data.get("release_date"),
                                start_date=project_data.get("start_date"),
                                location=project_data.get("location"),
                                tenderer=project_data.get("tenderer"),
                                project_id=project_data.get("project_id"),
                                rate=project_data.get("rate"),
                                url=project_data.get("url"),
                                budget=project_data.get("budget"),
                                duration=project_data.get("duration"),
                                workload=project_data.get("workload")
                            )

                            if project_data.get("requirements"):
                                # Handle requirements format with term frequency
                                requirements_data = project_data["requirements"]
                                if isinstance(requirements_data, dict):
                                    # Store term frequency data
                                    project.set_requirements_tf(requirements_data)
                                else:
                                    # Fallback for old format (list of strings) - convert to TF format
                                    requirements_dict = {req: 1 for req in requirements_data}
                                    project.set_requirements_tf(requirements_dict)

                            db.add(project)
                            total_projects += 1

                        except Exception as e:
                            website_logger.error(f"Error saving project: {str(e)}")
                            errors.append(f"Failed to save project: {str(e)}")

                    db.commit()
                    website_logger.info(f"Scanned {len(projects)} projects from website")

                except Exception as e:
                    error_msg = f"Error scanning website: {str(e)}"
                    website_logger.error(error_msg)
                    errors.append(error_msg)

            # Update last scan timestamp
            self._update_last_scan_timestamp(db)

            # Call deduplication service only if projects were found
            if total_projects > 0:
                deduplication_result = deduplication_service.run_deduplication(db)
                scan_logger.info(f"Deduplication result: {deduplication_result}")

                # Calculate and update IDF factors after deduplication
                try:
                    scan_logger.info("Starting TF/IDF calculation...")
                    idf_factors = tfidf_service.update_skills_idf_factors(db)
                    scan_logger.info(f"TF/IDF calculation completed. Updated {len(idf_factors)} skills with IDF factors")
                except Exception as e:
                    scan_logger.error(f"Error during TF/IDF calculation: {str(e)}")
                    errors.append(f"TF/IDF calculation failed: {str(e)}")
            else:
                deduplication_result = {
                    "total_removed": 0,
                    "duplicate_groups_processed": 0,
                    "removed_details": [],
                    "message": "No projects found to deduplicate"
                }
                scan_logger.info("No projects found, skipping deduplication")

            # Send deduplication message
            dedup_message = f"data: {json.dumps({'type': 'deduplication', 'result': deduplication_result}, ensure_ascii=False)}\n\n"
            scan_logger.info(f"Sending deduplication message: {dedup_message.strip()}")

            return {
                "message": f"Scan completed successfully. Found {total_projects} projects.",
                "projects_found": total_projects,
                "projects_processed": total_projects,
                "errors": errors,
                "deduplication": deduplication_result
            }

        except HTTPException:
            raise
        except Exception as e:
            scan_logger.error(f"Error during project scan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to scan projects"
            )
        finally:
            # Always unregister the scan and release the lock when done
            self._unregister_scan(scan_id)
            self._release_scan_lock()

    async def scan_projects_stream(self, time_range: int, db: Session) -> AsyncGenerator[str, None]:
        """Scan for new projects and stream results using Server-Sent Events."""
        # Check if a scan is already active
        if not self._acquire_scan_lock():
            error_message = f"data: {json.dumps({'type': 'error', 'message': 'Another scan is already in progress. Please wait for it to complete.'}, ensure_ascii=False)}\n\n"
            yield error_message
            return

        # Generate unique scan ID for correlation
        scan_id = str(uuid.uuid4())[:8]  # e.g., "a1b2c3d4"
        scan_logger = logging.getLogger(f"scan.{scan_id}")

        try:
            # Register this scan as active
            self._register_scan(scan_id)
            scan_logger.info(f"Starting streaming project scan with time_range: {time_range}")

            # Collect existing projects data once at the beginning
            existing_projects = db.query(Project).all()
            existing_project_data = {
                project.url: {
                    'id': project.id,
                    'title': project.title,
                    'url': project.url,
                    'release_date': project.release_date,
                    'start_date': project.start_date,
                    'duration': project.duration,
                    'location': project.location,
                    'tenderer': project.tenderer,
                    'rate': project.rate,
                    'description': project.description,
                    'project_id': project.project_id,
                    'budget': project.budget,
                    'workload': project.workload
                } for project in existing_projects
            }

            # Get website configurations
            websites = config_manager.get_websites()
            if not websites:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No websites configured for scanning"
                )

            total_projects = 0
            errors = []

            # Send start message
            start_message = f"data: {json.dumps({'type': 'start', 'message': 'Scan started', 'scan_id': scan_id}, ensure_ascii=False)}\n\n"
            scan_logger.info(f"Sending start message: {start_message.strip()}")
            yield start_message

            # Outer loop: Scan each website using streaming web scraper logic
            for website_config in websites:
                # Check for cancellation before starting each website
                if self.is_scan_cancelled(scan_id):
                    scan_logger.info(f"Scan {scan_id} was cancelled, stopping")
                    yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Scan was cancelled by user'}, ensure_ascii=False)}\n\n"
                    return

                try:
                    website_name = website_config['level1_search']['name']
                    website_logger = logging.getLogger(f"scan.{scan_id}.website.{website_name}")

                    website_logger.info("=========================================================================")
                    website_logger.info(f"Started processing website: {website_name}")
                    website_logger.info("=========================================================================")

                    # Send website start message
                    website_start_msg = f"data: {json.dumps({'type': 'website_start', 'website': website_name}, ensure_ascii=False)}\n\n"
                    website_logger.info(f"Sending website start message: {website_start_msg.strip()}")
                    yield website_start_msg

                    # Use streaming web scraper logic
                    website_logger.info("Calling streaming web scraper...")
                    project_count = 0
                    async for project_data in self.web_scraper.scan_website_stream(
                        website_config,
                        time_range,
                        existing_project_data,
                        scan_id  # Pass scan_id for cancellation checks
                    ):
                        # Check for cancellation before processing each project
                        if self.is_scan_cancelled(scan_id):
                            scan_logger.info(f"Scan {scan_id} was cancelled during project processing, stopping")
                            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Scan was cancelled by user'}, ensure_ascii=False)}\n\n"
                            return

                        try:
                            project_count += 1
                            project_logger = logging.getLogger(f"scan.{scan_id}.project.{project_count}")
                            # Send progress update immediately
                            progress_msg = f"data: {json.dumps({'type': 'progress', 'message': f'Processing project {project_count}'}, ensure_ascii=False)}\n\n"
                            project_logger.info(f"Sending progress message: {progress_msg.strip()}")
                            yield progress_msg

                            # Create project using existing logic
                            project = Project(
                                title=project_data.get("title", ""),
                                description=project_data.get("description"),
                                release_date=project_data.get("release_date"),
                                start_date=project_data.get("start_date"),
                                location=project_data.get("location"),
                                tenderer=project_data.get("tenderer"),
                                project_id=project_data.get("project_id"),
                                rate=project_data.get("rate"),
                                url=project_data.get("url"),
                                budget=project_data.get("budget"),
                                duration=project_data.get("duration"),
                                workload=project_data.get("workload")
                            )

                            if project_data.get("requirements"):
                                # Handle requirements format with term frequency
                                requirements_data = project_data["requirements"]
                                if isinstance(requirements_data, dict):
                                    # Store term frequency data
                                    project.set_requirements_tf(requirements_data)
                                else:
                                    # Fallback for old format (list of strings) - convert to TF format
                                    requirements_dict = {req: 1 for req in requirements_data}
                                    project.set_requirements_tf(requirements_dict)

                            db.add(project)
                            db.flush()  # Get the ID without committing
                            total_projects += 1

                            # Send project data immediately - include full data to avoid API calls
                            project_display_data = {
                                'id': project.id,
                                'title': project.title,
                                'description': project.description,
                                'release_date': project.release_date,
                                'start_date': project.start_date,
                                'location': project.location,
                                'tenderer': project.tenderer,
                                'project_id': project.project_id,
                                'requirements': project.get_requirements_list(),
                                'rate': project.rate,
                                'url': project.url,
                                'budget': project.budget,
                                'duration': project.duration,
                                'workload': project.workload
                            }

                            project_message = f"data: {json.dumps({'type': 'project', 'data': project_display_data}, ensure_ascii=False)}\n\n"
                            project_logger.info("Sending project message.}")
                            yield project_message

                            # Commit each project immediately to ensure it's saved
                            db.commit()

                        except Exception as e:
                            logger.error(f"Error saving project: {str(e)}")
                            errors.append(f"Failed to save project: {str(e)}")
                            error_message = f"data: {json.dumps({'type': 'error', 'message': f'Error saving project: {str(e)}'}, ensure_ascii=False)}\n\n"
                            project_logger.info(f"Sending error message: {error_message.strip()}")
                            yield error_message

                    website_logger.info(f"Web scraper processed {project_count} projects")

                    # Send immediate feedback about found projects
                    if project_count > 0:
                        info_message = f"data: {json.dumps({'type': 'info', 'message': f'Found {project_count} projects, processing...'}, ensure_ascii=False)}\n\n"
                        project_logger.info(f"Sending info message: {info_message.strip()}")
                        yield info_message

                    # No need for final commit since we commit after each project
                    yield f"data: {json.dumps({'type': 'website_complete', 'website': website_name, 'projects': project_count}, ensure_ascii=False)}\n\n"

                except Exception as e:
                    error_msg = f"Error scanning website: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    error_message = f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                    scan_logger.info(f"Sending error message: {error_message.strip()}")
                    yield error_message

            # Check for cancellation before final steps
            if self.is_scan_cancelled(scan_id):
                scan_logger.info(f"Scan {scan_id} was cancelled before final steps")
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Scan was cancelled by user'}, ensure_ascii=False)}\n\n"
                return

            # Update last scan timestamp
            self._update_last_scan_timestamp(db)

            # Call deduplication service only if projects were found
            if total_projects > 0:
                deduplication_result = deduplication_service.run_deduplication(db)
                logger.info(f"Deduplication result: {deduplication_result}")

                # Calculate and update IDF factors after deduplication
                try:
                    scan_logger.info("Starting TF/IDF calculation...")
                    idf_factors = tfidf_service.update_skills_idf_factors(db)
                    scan_logger.info(f"TF/IDF calculation completed. Updated {len(idf_factors)} skills with IDF factors")

                    # Send TF/IDF completion message
                    tfidf_message = f"data: {json.dumps({'type': 'tfidf_complete', 'skills_updated': len(idf_factors)}, ensure_ascii=False)}\n\n"
                    scan_logger.info(f"Sending TF/IDF completion message: {tfidf_message.strip()}")
                    yield tfidf_message
                except Exception as e:
                    scan_logger.error(f"Error during TF/IDF calculation: {str(e)}")
                    errors.append(f"TF/IDF calculation failed: {str(e)}")
                    error_message = f"data: {json.dumps({'type': 'error', 'message': f'TF/IDF calculation failed: {str(e)}'}, ensure_ascii=False)}\n\n"
                    yield error_message
            else:
                deduplication_result = {
                    "total_removed": 0,
                    "duplicate_groups_processed": 0,
                    "removed_details": [],
                    "message": "No projects found to deduplicate"
                }
                logger.info("No projects found, skipping deduplication")

            # Send deduplication message
            dedup_message = f"data: {json.dumps({'type': 'deduplication', 'result': deduplication_result}, ensure_ascii=False)}\n\n"
            scan_logger.info(f"Sending deduplication message: {dedup_message.strip()}")
            yield dedup_message

            # Send completion message
            complete_message = f"data: {json.dumps({'type': 'complete', 'total_projects': total_projects, 'errors': errors, 'deduplication': deduplication_result}, ensure_ascii=False)}\n\n"
            scan_logger.info(f"Sending complete message: {complete_message.strip()}")
            yield complete_message

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during streaming project scan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to scan projects"
            )
        finally:
            # Always unregister the scan and release the lock when done
            self._unregister_scan(scan_id)
            self._release_scan_lock()

    def _update_last_scan_timestamp(self, db: Session) -> None:
        """Update the last scan timestamp in the database."""
        try:
            last_scan_state = db.query(AppState).filter(AppState.key == "last_scan").first()
            if last_scan_state:
                last_scan_state.set_value(datetime.now().isoformat())
                db.commit()
        except Exception as e:
            logger.error(f"Error updating last scan timestamp: {str(e)}")


# Global scan service instance
scan_service = ScanService()