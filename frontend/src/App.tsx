import React, { useState, useCallback } from 'react';
import ProjectExplorer from './components/ProjectExplorer';
import ProjectContents from './components/ProjectContents';
import EmployeeFit from './components/EmployeeFit';
import './App.css';

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
  rate?: string | number;
  url?: string;
  budget?: string | number;
  duration?: string;
  workload?: string;
}

function App() {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const handleProjectSelect = useCallback((project: Project) => {
    setSelectedProject(project);
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>Project Finder</h1>
      </header>

      {/* Main Content Area - Three Columns */}
      <main className="main-content">
        {/* Left Column: Project Explorer */}
        <div className="column">
          <ProjectExplorer onProjectSelect={handleProjectSelect} />
        </div>

        {/* Center Column: Project Contents */}
        <div className="column">
          <ProjectContents selectedProject={selectedProject} />
        </div>

        {/* Right Column: Employee Fit */}
        <div className="column">
          <EmployeeFit onProjectSelect={handleProjectSelect} />
        </div>
      </main>
    </div>
  );
}

export default App;