import React, { useState, useEffect } from 'react';
import { api, matchingApi, endpoints } from '../services/api';

interface Employee {
  id: number;
  name: string;
  skill_list: string[];
}

interface Match {
  project_id: number;
  project_title: string;
  match_percentage: number;
  matching_skills: string[];
  missing_skills: string[];
}

interface MatchResponse {
  employee_name: string;
  matches: Match[];
  missing_skills: string[];
}

interface EmployeeFitProps {
  onProjectSelect?: (project: any) => void;
}

const EmployeeFit: React.FC<EmployeeFitProps> = ({ onProjectSelect }) => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [matches, setMatches] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [showAddEmployee, setShowAddEmployee] = useState<boolean>(false);
  const [showEditSkills, setShowEditSkills] = useState<boolean>(false);
  const [newEmployeeName, setNewEmployeeName] = useState<string>('');
  const [newEmployeeSkills, setNewEmployeeSkills] = useState<string>('');
  const [editingSkills, setEditingSkills] = useState<string>('');
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await api.get(endpoints.employees);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const fetchMatches = async (employeeId: number) => {
    try {
      const response = await api.get(endpoints.matches(employeeId));
      setMatches(response.data);
    } catch (error) {
      console.error('Error fetching matches:', error);
    }
  };

  const handleEmployeeSelect = async (employeeId: number) => {
    setSelectedEmployeeId(employeeId);
    await runMatching(employeeId);
  };

  const runMatching = async (employeeId: number) => {
    setLoading(true);
    try {
      const response = await matchingApi.get(endpoints.matches(employeeId));
      setMatches(response.data);
    } catch (error: any) {
      console.error('Error running matching:', error);
      let errorMessage = 'Error running matching algorithm';
      if (error.response) {
        errorMessage = `Error: ${error.response.data?.detail || error.response.statusText}`;
      } else if (error.request) {
        errorMessage = 'No response from server. Please check if the backend is running.';
      } else {
        errorMessage = `Error: ${error.message}`;
      }
      // Only show alert for actual errors, not connection issues
      if (!errorMessage.includes('No response from server')) {
        alert(errorMessage);
      }
      setMatches(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEmployee = async () => {
    if (!newEmployeeName.trim() || !newEmployeeSkills.trim()) {
      alert('Please enter both name and skills');
      return;
    }

    try {
      const skills = newEmployeeSkills
        .split(',')
        .map(skill => skill.trim().replace(/^"|"$/g, ''));
      const response = await api.post(endpoints.employees, {
        name: newEmployeeName,
        skill_list: skills,
        email: '',
        phone: '',
        location: '',
        experience_years: 0,
        hourly_rate: 0,
        availability: '',
        notes: ''
      });

      alert('Employee added successfully!');
      setShowAddEmployee(false);
      setNewEmployeeName('');
      setNewEmployeeSkills('');
      fetchEmployees();
    } catch (error: any) {
      console.error('Error adding employee:', error);
      let errorMessage = 'Error adding employee';
      if (error.response) {
        errorMessage = `Error: ${error.response.data?.detail || error.response.statusText}`;
      } else if (error.request) {
        errorMessage = 'No response from server. Please check if the backend is running.';
      } else {
        errorMessage = `Error: ${error.message}`;
      }
      // Only show alert for actual errors, not connection issues
      if (!errorMessage.includes('No response from server')) {
        alert(errorMessage);
      }
    }
  };

  const handleEditSkills = async () => {
    if (selectedEmployeeId) {
      try {
        // Refresh the employees list to ensure we have the latest data
        await fetchEmployees();

        // Find the employee from the refreshed list
        const employee = employees.find(emp => emp.id === selectedEmployeeId);
        if (employee) {
          setEditingEmployee(employee);
          // Strip quotes from skills when displaying for editing
          const cleanSkills = employee.skill_list.map(skill => skill.replace(/^"|"$/g, ''));
          setEditingSkills(cleanSkills.join(', '));
          setShowEditSkills(true);
        } else {
          alert('Employee not found. Please try again.');
        }
      } catch (error) {
        console.error('Error refreshing employee data:', error);
        alert('Error loading employee data. Please try again.');
      }
    } else {
      alert('Please select an employee first');
    }
  };

  const handleSaveSkills = async () => {
    if (!editingEmployee || !editingSkills.trim()) {
      alert('Please enter skills');
      return;
    }

    try {
      const skills = editingSkills.split(',').map(skill => skill.trim()).filter(skill => skill.length > 0);
      console.log('Saving skills:', skills);
      console.log('Original editingSkills:', editingSkills);

      await api.put(endpoints.employee(editingEmployee.id), {
        skill_list: skills
      });

      setShowEditSkills(false);
      setEditingEmployee(null);
      setEditingSkills('');
      fetchEmployees();

      // Refresh matches if this employee is currently selected
      if (selectedEmployeeId === editingEmployee.id) {
        await runMatching(editingEmployee.id);
      }
    } catch (error: any) {
      console.error('Error updating skills:', error);
      let errorMessage = 'Error updating skills';
      if (error.response) {
        errorMessage = `Error: ${error.response.data?.detail || error.response.statusText}`;
      } else if (error.request) {
        errorMessage = 'No response from server. Please check if the backend is running.';
      } else {
        errorMessage = `Error: ${error.message}`;
      }
      // Only show alert for actual errors, not connection issues
      if (!errorMessage.includes('No response from server')) {
        alert(errorMessage);
      }
    }
  };

  const handleRefreshMatches = async () => {
    if (selectedEmployeeId) {
      setLoading(true);
      try {
        // First rebuild all embeddings
        console.log('Rebuilding embeddings...');
        const rebuildResponse = await api.post(endpoints.rebuildEmbeddings);
        console.log('Embeddings rebuild result:', rebuildResponse.data);

        // Then run matching
        await runMatching(selectedEmployeeId);
      } catch (error: any) {
        console.error('Error refreshing matches:', error);
        let errorMessage = 'Error refreshing matches';
        if (error.response) {
          errorMessage = `Error: ${error.response.data?.detail || error.response.statusText}`;
        } else if (error.request) {
          errorMessage = 'No response from server. Please check if the backend is running.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
        // Only show alert for actual errors, not connection issues
        if (!errorMessage.includes('No response from server')) {
          alert(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    } else {
      alert('Please select an employee first');
    }
  };

  const handleProjectClick = async (projectId: number) => {
    try {
      const project = await fetchProjectDetails(projectId);
      if (project) {
        // Call the parent's onProjectSelect function
        if (onProjectSelect) {
          onProjectSelect(project);
        }
      }
    } catch (error) {
      console.error('Error fetching project details:', error);
    }
  };

  const fetchProjectDetails = async (projectId: number) => {
    try {
      const response = await api.get(endpoints.project(projectId));
      return response.data;
    } catch (error) {
      console.error('Error fetching project details:', error);
      return null;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const getMostMissingSkills = (matches: Match[]): { skill: string; count: number }[] => {
    if (!matches || matches.length === 0) return [];

    // Create a dictionary to count missing skills
    const missingSkillsCount: { [key: string]: number } = {};

    // Analyze the top 20 projects instead of top 10
    const top20Matches = matches.slice(0, 20);

    // Count missing skills from each project
    top20Matches.forEach(match => {
      if (match.missing_skills) {
        match.missing_skills.forEach(skill => {
          missingSkillsCount[skill] = (missingSkillsCount[skill] || 0) + 1;
        });
      }
    });

    // Convert to array and sort by count (descending)
    const sortedMissingSkills = Object.entries(missingSkillsCount)
      .map(([skill, count]) => ({ skill, count }))
      .sort((a, b) => b.count - a.count);

    // Return top 6 most missing skills
    return sortedMissingSkills.slice(0, 6);
  };

  const handleRemoveEmployee = async () => {
    if (!selectedEmployeeId) {
      alert('Please select an employee to remove.');
      return;
    }
    const employee = employees.find(emp => emp.id === selectedEmployeeId);
    if (!employee) {
      alert('Employee not found.');
      return;
    }
    if (!window.confirm(`Are you sure you want to remove ${employee.name}? This action cannot be undone.`)) {
      return;
    }
    try {
      await api.delete(endpoints.employee(selectedEmployeeId));
      alert('Employee removed successfully!');
      setSelectedEmployeeId(null);
      setMatches(null);
      fetchEmployees();
    } catch (error: any) {
      console.error('Error removing employee:', error);
      let errorMessage = 'Error removing employee';
      if (error.response) {
        errorMessage = `Error: ${error.response.data?.detail || error.response.statusText}`;
      } else if (error.request) {
        errorMessage = 'No response from server. Please check if the backend is running.';
      } else {
        errorMessage = `Error: ${error.message}`;
      }
      if (!errorMessage.includes('No response from server')) {
        alert(errorMessage);
      }
    }
  };

  return (
    <div className="employee-fit">
      <h2>Employee fit</h2>

      {/* Employee Dropdown */}
      <div className="employee-dropdown">
        <select
          value={selectedEmployeeId || ''}
          onChange={(e) => handleEmployeeSelect(Number(e.target.value))}
          className="input"
        >
          <option value="">Select an employee.</option>
          {employees.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.name}
            </option>
          ))}
        </select>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button
          className="btn btn-primary"
          onClick={() => setShowAddEmployee(true)}
        >
          Add New Employee
        </button>
        <button
          className="btn btn-outline"
          onClick={handleEditSkills}
        >
          Edit Skills
        </button>
        <button
          className="btn btn-outline"
          onClick={handleRefreshMatches}
        >
          Refresh Matches
        </button>
        <button
          className="btn btn-danger"
          onClick={handleRemoveEmployee}
        >
          Remove Employee
        </button>
      </div>

      {/* Add Employee Modal */}
      {showAddEmployee && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Add New Employee</h3>
              <button className="close-button" onClick={() => setShowAddEmployee(false)}>
                ×
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  value={newEmployeeName}
                  onChange={(e) => setNewEmployeeName(e.target.value)}
                  className="input"
                  placeholder="Employee name"
                />
              </div>
              <div className="form-group">
                <label>Skills (comma-separated):</label>
                <input
                  type="text"
                  value={newEmployeeSkills}
                  onChange={(e) => setNewEmployeeSkills(e.target.value)}
                  className="input"
                  placeholder="JavaScript, React, Python, etc."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-primary" onClick={handleAddEmployee}>
                Add Employee
              </button>
              <button className="btn btn-outline" onClick={() => setShowAddEmployee(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Skills Modal */}
      {showEditSkills && editingEmployee && (
        <div className="modal-overlay">
          <div className="modal edit-skills-modal">
            <div className="modal-header">
              <h3>Edit Skills - {editingEmployee.name}</h3>
              <button className="close-button" onClick={() => setShowEditSkills(false)}>
                ×
              </button>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label>Edit Skills (comma-separated):</label>
                <textarea
                  value={editingSkills}
                  onChange={(e) => setEditingSkills(e.target.value)}
                  className="input"
                  placeholder="JavaScript, React, Python, etc."
                  rows={4}
                />
                <small className="help-text">
                  Separate skills with commas. You can add, remove, or modify skills.
                </small>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-primary" onClick={handleSaveSkills}>
                Save Changes
              </button>
              <button className="btn btn-outline" onClick={() => setShowEditSkills(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Matching Results */}
      <div className="matching-results">
        {loading ? (
          <div className="loading">Running matching algorithm...</div>
        ) : matches ? (
          <div>
            {/* Most Missing Skills Analysis */}
            {matches.matches && matches.matches.length > 0 && (
              <div className="most-missing-skills">
                <h4>Most Frequently Missing Skills (Top 20 Projects)</h4>
                <div className="skill-list">
                  {getMostMissingSkills(matches.matches).map((item, index) => (
                    <span key={index} className="missing-skill">
                      {item.skill} ({item.count}x)
                    </span>
                  ))}
                </div>
              </div>
            )}

            <h3>Matching Results for {matches.employee_name}</h3>

            {/* Ranked Project Matches - Top 20 Only */}
            <div className="project-matches">
              <h4>Compatible Projects (Top 20)</h4>
              {matches.matches && matches.matches.length > 0 ? (
                <div className="match-list">
                  {matches.matches.slice(0, 20).map((match, index) => (
                    <div key={index} className="match-item">
                      <div className="match-rank">#{index + 1}</div>
                      <div className="match-details">
                        <div
                          className="match-title clickable"
                          onClick={() => handleProjectClick(match.project_id)}
                          title="Click to view project details"
                        >
                          {match.project_title}
                        </div>
                        <div className="match-score">Match: {match.match_percentage}%</div>
                        <div className="match-skills">
                          <strong>Matching:</strong> {match.matching_skills.join(', ') || 'None'}
                        </div>
                        <div className="missing-skills">
                          <strong>Missing:</strong> {match.missing_skills.join(', ') || 'None'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No compatible projects found.</p>
              )}
            </div>

            {/* Missing Skills */}
            {matches.missing_skills && matches.missing_skills.length > 0 && (
              <div className="missing-skills">
                <h4>Most Often Missing Skills</h4>
                <div className="skill-list">
                  {matches.missing_skills.map((skill, index) => (
                    <span key={index} className="missing-skill">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : selectedEmployeeId ? (
          <div className="no-matches">
            <p>No matches found for the selected employee.</p>
          </div>
        ) : (
          <div className="select-employee">
            <p>Select an employee to view matching results.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployeeFit;