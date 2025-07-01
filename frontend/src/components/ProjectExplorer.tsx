import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { api, endpoints, SSEStream, SSEEvent, cancellationApi } from '../services/api';
import DatabaseInspection from './DatabaseInspection';
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
  rate?: string;
  url?: string;
  budget?: string;
  duration?: string;
  workload?: string;
  last_scan?: string;
}

interface ProjectExplorerProps {
  onProjectSelect?: (project: Project) => void;
  onTestDataCreated?: () => void;  // New callback for test data creation
}

const ProjectExplorer: React.FC<ProjectExplorerProps> = ({ onProjectSelect, onTestDataCreated }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [timeRange, setTimeRange] = useState<number>(8); // Default to one week
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [showDatabaseInspection, setShowDatabaseInspection] = useState<boolean>(false);

  // SSE streaming state
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamStatus, setStreamStatus] = useState<string>('');
  const [sseStream, setSseStream] = useState<SSEStream | null>(null);
  const [currentScanId, setCurrentScanId] = useState<string | null>(null);

  // Track if this is the initial mount
  const isInitialMount = useRef(true);

  // Track processed project IDs to prevent duplicates
  const processedProjectIds = useRef<Set<number>>(new Set());

  // Track if we just completed a scan to prevent auto-restart
  const justCompletedScan = useRef(false);

  // Check scan status on mount to prevent conflicts
  useEffect(() => {
    const checkScanStatus = async () => {
      try {
        // Use a shorter timeout for status check
        const response = await axios.get('/api' + endpoints.scanStatus, {
          timeout: 5000, // 5 seconds timeout for status check
        });
        const { is_active } = response.data;

        if (is_active) {
          console.log('SSE: Another scan is already active, not starting new scan');
          setIsStreaming(true);
          setStreamStatus('Another scan is already in progress...');
        }
      } catch (error: any) {
        // Don't log timeout errors as they're expected if backend is not running
        if (error.code !== 'ECONNABORTED' && error.code !== 'ERR_NETWORK') {
          console.error('Error checking scan status:', error);
        }
      }
    };

    checkScanStatus();
  }, []);

  // Initial load - only fetch projects on mount, not on every refresh
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      fetchProjects();
    }
  }, []); // Empty dependency array - only runs on mount

  // Handle timeRange changes - only fetch if not streaming
  useEffect(() => {
    if (!isInitialMount.current && !isStreaming) {
      // Only fetch projects if we haven't just completed a scan
      // This prevents automatic restarts after scan completion
      const shouldFetch = !justCompletedScan.current;
      if (shouldFetch) {
        fetchProjects();
      }
      // Reset the flag after a short delay
      if (justCompletedScan.current) {
        setTimeout(() => {
          justCompletedScan.current = false;
        }, 2000); // Increased delay to prevent immediate re-triggering
      }
    }
  }, [timeRange]); // Remove liveMode from dependencies

  // Cleanup SSE connection on unmount
  useEffect(() => {
    return () => {
      if (sseStream) {
        sseStream.disconnect();
      }
    };
  }, [sseStream]);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`${endpoints.projects}?time_range=${timeRange}`);
      const fetchedProjects = response.data;
      setProjects(fetchedProjects);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  const handleScan = async () => {
    if (isStreaming) {
      // Stop streaming
      if (sseStream) {
        sseStream.disconnect();
        setSseStream(null);
      }

      // Send cancellation request to backend
      if (currentScanId) {
        try {
          await cancellationApi.post(endpoints.cancelScan(currentScanId));
          console.log('Scan cancellation request sent for scan ID:', currentScanId);
        } catch (error) {
          console.error('Error cancelling scan:', error);
        }
      }

      setIsStreaming(false);
      setStreamStatus('');
      setCurrentScanId(null);
      return;
    }

    // Start streaming
    setIsStreaming(true);
    setStreamStatus('Starting scan...');

    // Clear existing projects for fresh scan
    setProjects([]);
    // Clear processed project IDs for new scan
    processedProjectIds.current.clear();

    // Properly clean up any existing SSE stream first
    if (sseStream) {
      sseStream.disconnect();
      setSseStream(null);
    }

    const streamUrl = '/api' + endpoints.scanStream(timeRange);  // Add /api prefix for EventSource
    const newSseStream = new SSEStream(streamUrl, handleSSEEvent);

    // Reset the stream to allow new connections
    newSseStream.reset();

    setSseStream(newSseStream);
    newSseStream.connect();
  };

  const handleSSEEvent = (event: SSEEvent) => {
    console.log('SSE Event received:', event); // Debug logging

    switch (event.type) {
      case 'start':
        console.log('SSE: Start event received');
        setStreamStatus('Scan started...');
        setCurrentScanId(event.scan_id || null);
        break;

      case 'website_start':
        console.log('SSE: Website start event received for:', event.website);
        setStreamStatus(`Scanning ${event.website}...`);
        break;

      case 'info':
        console.log('SSE: Info event received:', event.message);
        setStreamStatus(event.message || 'Processing...');
        break;

      case 'progress':
        console.log('SSE: Progress event received:', event.message);
        setStreamStatus(event.message || 'Processing...');
        break;

      case 'project':
        console.log('SSE: Project event received:', event.data);
        if (event.data) {
          // Check if we've already processed this project ID
          if (processedProjectIds.current.has(event.data.id)) {
            console.log('SSE: Project already processed, skipping:', event.data.title, '(ID:', event.data.id, ')');
            break;
          }

          // Mark as processed immediately to prevent duplicates
          processedProjectIds.current.add(event.data.id);

          setProjects(prevProjects => {
            // Double-check if project already exists in current state
            const exists = prevProjects.some(p => p.id === event.data.id);
            if (!exists) {
              console.log('SSE: Adding project to list:', event.data.title, '(ID:', event.data.id, ')');
              return [event.data, ...prevProjects];
            }
            console.log('SSE: Project already exists in state, skipping:', event.data.title, '(ID:', event.data.id, ')');
            return prevProjects;
          });
        }
        break;

      case 'website_complete':
        console.log('SSE: Website complete event received for:', event.website, 'with', event.projects, 'projects');
        setStreamStatus(`Completed ${event.website}: ${event.projects} projects found`);
        break;

      case 'complete':
        console.log('SSE: Complete event received with', event.total_projects, 'total projects');
        setIsStreaming(false);
        setStreamStatus(`Scan completed! Total: ${event.total_projects} projects`);
        setCurrentScanId(null);
        justCompletedScan.current = true;

        // Force disconnect the SSE stream to prevent reconnection
        if (sseStream) {
          sseStream.forceDisconnect();
        }
        break;

      case 'cancelled':
        console.log('SSE: Scan cancelled event received');
        setIsStreaming(false);
        setStreamStatus('Scan was cancelled');
        setCurrentScanId(null);

        // Force disconnect the SSE stream to prevent reconnection
        if (sseStream) {
          sseStream.forceDisconnect();
        }
        break;

      case 'deduplication':
        console.log('SSE: Deduplication event received:', event.result);
        if (event.result) {
          const dedupResult = event.result;
          if (dedupResult.total_removed > 0) {
            setStreamStatus(`Deduplication: Removed ${dedupResult.total_removed} duplicate projects`);
            // Refresh the project list after deduplication
            setTimeout(() => {
              fetchProjects();
            }, 1000);
          } else {
            setStreamStatus('Deduplication: No duplicates found');
          }
        }
        break;

      case 'error':
        console.log('SSE: Error event received:', event.message);
        setStreamStatus(event.message || 'Error occurred during scan');
        // Don't stop streaming for all errors - only stop for critical ones
        if (event.message?.includes('already in progress')) {
          setIsStreaming(false);
          setCurrentScanId(null);
        }
        break;

      default:
        console.log('SSE: Unknown event type:', event.type);
        break;
    }
  };

  const handleShow = () => {
    fetchProjects();
  };

  const handleEmptyDatabase = async () => {
    if (window.confirm('Are you sure you want to clear all projects from the database?')) {
      try {
        await api.delete(endpoints.projects);
        alert('Database cleared successfully');
        fetchProjects();
      } catch (error) {
        console.error('Error clearing database:', error);
        alert('Error clearing database');
      }
    }
  };

  const handleDeduplication = async () => {
    try {
      setStreamStatus('Running deduplication...');
      const response = await api.post(endpoints.deduplication);
      const result = response.data;

      if (result.total_removed > 0) {
        setStreamStatus(`Deduplication completed: Removed ${result.total_removed} duplicate projects`);
        alert(`Deduplication completed: Removed ${result.total_removed} duplicate projects`);
        // Refresh the project list after deduplication
        fetchProjects();
      } else {
        setStreamStatus('Deduplication completed: No duplicates found');
        alert('Deduplication completed: No duplicates found');
      }
    } catch (error) {
      console.error('Error running deduplication:', error);
      setStreamStatus('Deduplication failed');
      alert('Error running deduplication');
    }
  };

  const handleRebuildEmbeddings = async () => {
    try {
      setStreamStatus('Rebuilding embeddings...');
      const response = await api.post(endpoints.rebuildEmbeddings);
      const result = response.data;

      setStreamStatus(`Embeddings rebuilt: ${result.skills_processed} skills processed`);
      alert(`Embeddings rebuilt successfully!\n\nSkills processed: ${result.skills_processed}\nEmployees processed: ${result.employees_processed}\nTotal unique skills: ${result.total_unique_skills}`);
    } catch (error) {
      console.error('Error rebuilding embeddings:', error);
      setStreamStatus('Embedding rebuild failed');
      alert('Error rebuilding embeddings. Please check if OpenAI API key is configured.');
    }
  };

  const handleCreateTestData = async () => {
    if (window.confirm('This will create test projects and employees. Continue?')) {
      try {
        setStreamStatus('Creating test data...');
        const response = await api.post(endpoints.testData);
        const result = response.data;

        setStreamStatus(`Test data created: ${result.projects_created} projects, ${result.employees_created} employees`);
        alert(`Test data created successfully!\n\nProjects created: ${result.projects_created}\nEmployees created: ${result.employees_created}`);

        // Refresh the project list to show the new test data
        fetchProjects();
      } catch (error) {
        console.error('Error creating test data:', error);
        setStreamStatus('Test data creation failed');
        alert('Error creating test data. Please try again.');
      }
    }
  };

  const handleProjectClick = useCallback(async (project: Project) => {
    console.log('Project clicked:', project);
    setSelectedProjectId(project.id);

    // If we have minimal project data from streaming, fetch the full details
    if (!project.description && !project.requirements) {
      console.log('Fetching full project details for ID:', project.id);
      try {
        const response = await api.get(endpoints.project(project.id));
        const fullProject = response.data;
        console.log('Full project details fetched:', fullProject);
        // Pass the full project data directly to avoid double API calls
        if (onProjectSelect) {
          onProjectSelect(fullProject);
        }
      } catch (error) {
        console.error('Error fetching project details:', error);
        // Fallback to minimal data if fetch fails
        if (onProjectSelect) {
          onProjectSelect(project);
        }
      }
    } else {
      // If we already have full data, use it directly
      console.log('Using existing full project data');
      if (onProjectSelect) {
        onProjectSelect(project);
      }
    }
  }, [onProjectSelect]);

  const formatDate = (dateString: string) => {
    return formatDateForDisplay(dateString);
  };

  return (
    <div className="project-explorer">
      {/* Main Header */}
      <h2>Project Explorer</h2>

      {/* Controls Section */}
      <div className="controls">
        <div className="control-group">
          <label>Time Range:</label>
          <select value={timeRange} onChange={(e) => setTimeRange(Number(e.target.value))}>
            <option value={2}>One Day</option>
            <option value={8}>One Week</option>
            <option value={32}>One Month</option>
          </select>
        </div>

        <button
          className={`btn ${isStreaming ? 'btn-danger' : 'btn-primary'}`}
          onClick={handleScan}
          disabled={loading}
        >
          {isStreaming ? 'Stop Scan' : 'Scan Projects'}
        </button>

        <button className="btn btn-outline" onClick={handleShow}>
          Show
        </button>

        <button className="btn btn-outline" onClick={handleEmptyDatabase}>
          Empty DB
        </button>

        <button className="btn btn-outline" onClick={handleCreateTestData}>
          Enter Test Data
        </button>

        <button
          className="btn btn-outline"
          onClick={() => setShowDatabaseInspection(true)}
        >
          DB Inspection
        </button>

        <button
          className="btn btn-outline"
          onClick={handleDeduplication}
        >
          Deduplicate
        </button>

        <button
          className="btn btn-outline"
          onClick={handleRebuildEmbeddings}
        >
          Rebuild Embeddings
        </button>
      </div>

      {/* Streaming Status */}
      {isStreaming && (
        <div className="streaming-status">
          <div className="status-indicator">
            <span className="pulse"></span>
            {streamStatus}
          </div>
        </div>
      )}

      {/* Projects Section */}
      <h3>Projects</h3>
      <div className="projects-list">
        {projects.length === 0 ? (
          <div className="no-projects">
            {loading ? 'Loading projects...' : 'No projects found'}
          </div>
        ) : (
          projects.map((project) => (
            <div
              key={project.id}
              className={`project-item ${selectedProjectId === project.id ? 'selected' : ''}`}
              onClick={() => handleProjectClick(project)}
            >
              <div className="project-title">{project.title}</div>
              <div className="project-meta">
                {project.release_date && (
                  <div className="project-date">{formatDate(project.release_date)}</div>
                )}
                {project.tenderer && (
                  <div className="project-tenderer">{project.tenderer}</div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Database Inspection Modal */}
      {showDatabaseInspection && (
        <DatabaseInspection
          isOpen={showDatabaseInspection}
          onClose={() => setShowDatabaseInspection(false)}
        />
      )}
    </div>
  );
};

export default ProjectExplorer;