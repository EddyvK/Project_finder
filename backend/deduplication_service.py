"""Deduplication service for removing redundant projects from the database."""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from backend.models.core_models import Project
from backend.utils.date_utils import european_to_iso_date
from datetime import datetime

logger = logging.getLogger(__name__)


class DeduplicationService:
    """Service for identifying and removing redundant projects."""

    def __init__(self):
        """Initialize the deduplication service."""
        self.logger = logging.getLogger(__name__)

    def _get_sort_key(self, project: Project) -> datetime:
        """
        Get sort key for a project based on release date.
        Projects with no release date or unparseable dates go to the end.
        """
        if not project.release_date:
            return datetime.min

        iso_date = european_to_iso_date(project.release_date)
        if not iso_date:
            return datetime.min

        try:
            return datetime.fromisoformat(iso_date)
        except ValueError:
            return datetime.min

    def find_duplicate_projects(self, db: Session) -> List[Tuple[Project, List[Project]]]:
        """
        Find duplicate projects based on multiple criteria.
        Projects are first sorted by release date (newest first) for efficiency.

        Returns:
            List of tuples containing (original_project, [duplicate_projects])
        """
        try:
            self.logger.info("Starting duplicate project detection...")

            # Get all projects and sort by release date (newest first)
            all_projects = db.query(Project).all()
            self.logger.info(f"Analyzing {len(all_projects)} projects for duplicates")

            # Sort projects by release date (newest first) for efficient deduplication
            sorted_projects = sorted(all_projects, key=self._get_sort_key, reverse=True)
            self.logger.info("Projects sorted by release date (newest first)")

            duplicates = []
            processed_ids = set()

            for i, project in enumerate(sorted_projects):
                if project.id in processed_ids:
                    continue

                # Find duplicates for this project (only check subsequent projects since they're sorted)
                duplicate_group = self._find_duplicates_for_project_efficient(project, sorted_projects[i+1:])

                if duplicate_group:
                    # Keep the newest project (first in sorted list) as original
                    original = project  # Since we're iterating in sorted order, this is the newest
                    duplicates_list = duplicate_group

                    if duplicates_list:
                        duplicates.append((original, duplicates_list))
                        # Mark all projects in this group as processed
                        processed_ids.add(original.id)
                        for p in duplicates_list:
                            processed_ids.add(p.id)

            self.logger.info(f"Found {len(duplicates)} groups of duplicate projects")
            return duplicates

        except Exception as e:
            self.logger.error(f"Error finding duplicate projects: {str(e)}")
            return []

    def _find_duplicates_for_project_efficient(self, project: Project, subsequent_projects: List[Project]) -> List[Project]:
        """
        Find duplicates for a specific project efficiently by only checking subsequent projects.
        Since projects are sorted by release date, duplicates will be adjacent.

        Args:
            project: The project to find duplicates for
            subsequent_projects: List of projects that come after this one (sorted by release date)

        Returns:
            List of projects that are duplicates (excluding the original)
        """
        duplicates = []

        for other_project in subsequent_projects:
            if self._are_projects_duplicates(project, other_project):
                duplicates.append(other_project)

        return duplicates

    def _find_duplicates_for_project(self, db: Session, project: Project, all_projects: List[Project]) -> List[Project]:
        """
        Find duplicates for a specific project based on multiple criteria.

        Args:
            db: Database session
            project: The project to find duplicates for
            all_projects: List of all projects to search through

        Returns:
            List of projects that are duplicates (including the original)
        """
        duplicates = [project]

        for other_project in all_projects:
            if other_project.id == project.id:
                continue

            if self._are_projects_duplicates(project, other_project):
                duplicates.append(other_project)

        return duplicates if len(duplicates) > 1 else []

    def _are_projects_duplicates(self, project1: Project, project2: Project) -> bool:
        """
        Check if two projects are duplicates based on multiple criteria.

        Args:
            project1: First project to compare
            project2: Second project to compare

        Returns:
            True if projects are considered duplicates
        """
        # Criterion 1: Same project_id (most reliable)
        if (project1.project_id and project2.project_id and
            project1.project_id.strip() == project2.project_id.strip()):
            return True

        # Criterion 2: Same URL (very reliable)
        if (project1.url and project2.url and
            project1.url.strip() == project2.url.strip()):
            return True

        # Criterion 3: Same title and tenderer (moderately reliable)
        if (project1.title and project2.title and
            project1.tenderer and project2.tenderer and
            project1.title.strip().lower() == project2.title.strip().lower() and
            project1.tenderer.strip().lower() == project2.tenderer.strip().lower()):
            return True

        # Criterion 4: Same title, location, and start_date (more specific)
        if (project1.title and project2.title and
            project1.location and project2.location and
            project1.start_date and project2.start_date and
            project1.title.strip().lower() == project2.title.strip().lower() and
            project1.location.strip().lower() == project2.location.strip().lower() and
            project1.start_date.strip() == project2.start_date.strip()):
            return True

        return False

    def reorder_projects_by_release_date(self, db: Session) -> Dict[str, Any]:
        """
        Reorder projects in the database by release date (newest first).
        Projects without release dates or with unparseable dates are placed at the end.

        Args:
            db: Database session

        Returns:
            Dictionary with reordering statistics
        """
        try:
            self.logger.info("Starting project reordering by release date...")

            # Get all projects
            all_projects = db.query(Project).all()
            self.logger.info(f"Reordering {len(all_projects)} projects")

            # Sort projects by release date (newest first)
            sorted_projects = sorted(all_projects, key=self._get_sort_key, reverse=True)

            # Create a new ordering based on the sorted list
            # We'll use a temporary column to store the new order
            for i, project in enumerate(sorted_projects):
                # Store the new position in a temporary way
                # Since SQLite doesn't support reordering directly, we'll use a workaround
                pass

            # For SQLite, we need to recreate the table with the new order
            # This is a more complex operation, so we'll use a simpler approach:
            # Update the projects with a temporary sort_order field

            # First, add a temporary sort_order column if it doesn't exist
            try:
                db.execute(text("ALTER TABLE projects ADD COLUMN sort_order INTEGER"))
                self.logger.info("Added temporary sort_order column")
            except Exception:
                # Column might already exist
                pass

            # Update sort_order for all projects
            for i, project in enumerate(sorted_projects):
                project.sort_order = i
                db.add(project)

            db.commit()
            self.logger.info("Updated sort_order for all projects")

            # Now we can query projects in the correct order
            # The frontend will automatically get them in the right order when using ORDER BY sort_order

            result = {
                'total_reordered': len(sorted_projects),
                'message': f'Successfully reordered {len(sorted_projects)} projects by release date'
            }

            self.logger.info(f"Project reordering completed: {result['message']}")
            return result

        except Exception as e:
            self.logger.error(f"Error reordering projects: {str(e)}")
            db.rollback()
            return {
                'total_reordered': 0,
                'error': str(e),
                'message': f'Project reordering failed: {str(e)}'
            }

    def remove_duplicate_projects(self, db: Session, duplicates: List[Tuple[Project, List[Project]]]) -> Dict[str, Any]:
        """
        Remove duplicate projects from the database.

        Args:
            db: Database session
            duplicates: List of tuples containing (original_project, [duplicate_projects])

        Returns:
            Dictionary with removal statistics
        """
        try:
            self.logger.info("Starting duplicate project removal...")

            total_removed = 0
            removed_details = []

            for original, duplicate_list in duplicates:
                self.logger.info(f"Removing {len(duplicate_list)} duplicates for project '{original.title}' (ID: {original.id})")

                for duplicate in duplicate_list:
                    try:
                        # Log what we're removing
                        removed_info = {
                            'id': duplicate.id,
                            'title': duplicate.title,
                            'project_id': duplicate.project_id,
                            'url': duplicate.url,
                            'reason': f"Duplicate of project ID {original.id}"
                        }
                        removed_details.append(removed_info)

                        # Remove the duplicate
                        db.delete(duplicate)
                        total_removed += 1

                        self.logger.debug(f"Removed duplicate project ID {duplicate.id}: {duplicate.title}")

                    except Exception as e:
                        self.logger.error(f"Error removing duplicate project {duplicate.id}: {str(e)}")

            # Commit all changes
            db.commit()

            result = {
                'total_removed': total_removed,
                'duplicate_groups_processed': len(duplicates),
                'removed_details': removed_details
            }

            self.logger.info(f"Successfully removed {total_removed} duplicate projects")
            return result

        except Exception as e:
            self.logger.error(f"Error removing duplicate projects: {str(e)}")
            db.rollback()
            return {
                'total_removed': 0,
                'duplicate_groups_processed': 0,
                'removed_details': [],
                'error': str(e)
            }

    def run_deduplication(self, db: Session) -> Dict[str, Any]:
        """
        Run the complete deduplication process with optimized sorting.

        Args:
            db: Database session

        Returns:
            Dictionary with deduplication results
        """
        try:
            self.logger.info("Starting optimized project deduplication process...")

            # Step 1: Find duplicates (now with sorting for efficiency)
            duplicates = self.find_duplicate_projects(db)

            if not duplicates:
                self.logger.info("No duplicate projects found")
                # Still reorder projects even if no duplicates found
                reorder_result = self.reorder_projects_by_release_date(db)
                return {
                    'total_removed': 0,
                    'duplicate_groups_processed': 0,
                    'removed_details': [],
                    'reordering': reorder_result,
                    'message': 'No duplicate projects found, but projects have been reordered by release date'
                }

            # Step 2: Remove duplicates
            dedup_result = self.remove_duplicate_projects(db, duplicates)

            # Step 3: Reorder remaining projects by release date
            reorder_result = self.reorder_projects_by_release_date(db)

            # Combine results
            result = {
                'total_removed': dedup_result['total_removed'],
                'duplicate_groups_processed': dedup_result['duplicate_groups_processed'],
                'removed_details': dedup_result['removed_details'],
                'reordering': reorder_result,
                'message': f"Removed {dedup_result['total_removed']} duplicate projects and reordered remaining projects by release date"
            }

            self.logger.info(f"Optimized deduplication completed: {result['message']}")
            return result

        except Exception as e:
            self.logger.error(f"Error in optimized deduplication process: {str(e)}")
            return {
                'total_removed': 0,
                'duplicate_groups_processed': 0,
                'removed_details': [],
                'reordering': {'total_reordered': 0, 'error': str(e)},
                'error': str(e),
                'message': f'Optimized deduplication failed: {str(e)}'
            }


# Global deduplication service instance
deduplication_service = DeduplicationService()
