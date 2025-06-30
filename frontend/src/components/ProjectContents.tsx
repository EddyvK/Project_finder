import React, { useState, useEffect } from 'react';
import { api, endpoints } from '../services/api';
import { formatDateForDisplay } from '../utils/dateUtils';

interface Project {
  id: number;
  title: string;
  description?: string;
  release_date?: string;
  start_date?: string;
  location?: string;
  tenderer?: string;
  project_id?: string;
  requirements?: string[];
  requirements_tf?: { [key: string]: number };
  rate?: string | number;
  url?: string;
  budget?: string | number;
  duration?: string;
  workload?: string;
}

interface ProjectContentsProps {
  selectedProject: Project | null;
}

const ProjectContents: React.FC<ProjectContentsProps> = ({ selectedProject }) => {
  const [projectDetails, setProjectDetails] = useState<Project | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (selectedProject) {
      // Always use the selectedProject data directly since ProjectExplorer fetches the full details
      setProjectDetails(selectedProject);
      setLoading(false);
    } else {
      setProjectDetails(null);
    }
  }, [selectedProject?.id]); // Only depend on the project ID, not the entire object

  const fetchProjectDetails = async (projectId: number) => {
    console.log('ProjectContents: Fetching details for project ID:', projectId);
    setLoading(true);
    try {
      const response = await api.get(endpoints.project(projectId));
      console.log('ProjectContents: API response:', response.data);
      setProjectDetails(response.data);
    } catch (error) {
      console.error('ProjectContents: Error fetching project details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditRequirements = () => {
    if (projectDetails) {
      alert(`Edit Project Requirements for: ${projectDetails.title}\n\nThis would open a form to edit the skill requirements for this project.`);
    }
  };

  const formatDate = (dateString: string | undefined) => {
    return formatDateForDisplay(dateString);
  };

  const formatCurrency = (amount: string | number | undefined) => {
    if (amount === undefined || amount === null) return 'N/A';
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(numAmount)) return 'N/A';
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR'
    }).format(numAmount);
  };

  return (
    <div className="project-contents">
      <h2>Project Contents</h2>

      {!selectedProject ? (
        <div className="no-selection">
          <p>Select a project to view its details.</p>
        </div>
      ) : loading ? (
        <div className="loading">Loading project details...</div>
      ) : projectDetails ? (
        <div className="project-details">
          {/* Edit Requirements Button */}
          <button
            className="btn btn-primary edit-requirements-btn"
            onClick={handleEditRequirements}
          >
            Edit Project requirements
          </button>

          {/* Project Details */}
          <div className="project-info">
            <h3 className="project-title">{projectDetails.title}</h3>

            <div className="project-summary">
              <p>{projectDetails.description}</p>
            </div>

            <div className="project-meta">
              <div className="meta-item">
                <strong>Release Date:</strong> {formatDate(projectDetails.release_date)}
              </div>
              <div className="meta-item">
                <strong>Start Date:</strong> {formatDate(projectDetails.start_date)}
              </div>
              <div className="meta-item">
                <strong>Location:</strong> {projectDetails.location || 'N/A'}
              </div>
              <div className="meta-item">
                <strong>Tenderer:</strong> {projectDetails.tenderer || 'N/A'}
              </div>
              <div className="meta-item">
                <strong>Internal Project ID:</strong> {projectDetails.project_id || 'N/A'}
              </div>
              <div className="meta-item">
                <strong>Going Rate:</strong> {formatCurrency(projectDetails.rate)}/h
              </div>
              <div className="meta-item">
                <strong>Budget:</strong> {formatCurrency(projectDetails.budget)}
              </div>
              <div className="meta-item">
                <strong>Duration:</strong> {projectDetails.duration || 'N/A'}
              </div>
              <div className="meta-item">
                <strong>Workload:</strong> {projectDetails.workload || 'N/A'}
              </div>
              {projectDetails.url && (
                <div className="meta-item">
                  <strong>URL:</strong>
                  <a href={projectDetails.url} target="_blank" rel="noopener noreferrer" className="project-url">
                    View Details
                  </a>
                </div>
              )}
            </div>

            {/* Skill Requirements */}
            {(projectDetails.requirements && projectDetails.requirements.length > 0) ||
             (projectDetails.requirements_tf && Object.keys(projectDetails.requirements_tf).length > 0) ? (
              <div className="skill-requirements">
                <h4>Skill Requirements</h4>
                <div className="skill-boxes">
                  {projectDetails.requirements && projectDetails.requirements.length > 0 ? (
                    // Use requirements list if available
                    projectDetails.requirements.map((requirement, index) => (
                      <span key={index} className="skill-box">
                        {requirement}
                      </span>
                    ))
                  ) : (
                    // Use requirements_tf keys if requirements list is not available
                    Object.keys(projectDetails.requirements_tf || {}).map((requirement, index) => (
                      <span key={index} className="skill-box">
                        {requirement}
                      </span>
                    ))
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="error">Error loading project details</div>
      )}
    </div>
  );
};

export default ProjectContents;