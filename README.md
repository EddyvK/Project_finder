# Project Finder Application

A comprehensive project matching system that connects employees with suitable projects based on skill compatibility. The application features a Python FastAPI backend with AI-powered matching and a modern React frontend.

## 🚀 Features

- **Project Management**: Browse and manage available projects with detailed information
- **Employee Profiles**: Manage employee profiles with skills and experience
- **AI-Powered Matching**: Intelligent matching using OpenAI and Mistral AI embeddings
- **Web Scraping**: Automated project discovery from freelancing platforms
- **Real-time Dashboard**: Overview of projects, employees, and matching statistics
- **Modern UI**: Responsive React frontend with intuitive navigation

## 🏗️ Architecture

- **Backend**: Python FastAPI with SQLAlchemy ORM
- **Database**: SQLite with automatic migrations
- **AI Integration**: OpenAI GPT-4 and Mistral AI for embeddings and matching
- **Frontend**: React 18 with TypeScript and Vite
- **Styling**: Custom CSS with utility classes
- **Icons**: Lucide React icons

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## 🛠️ Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (optional):
   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

## 🚀 Running the Application

### Start the Backend Server

From the `backend` directory:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at: `http://localhost:8000`

### Start the Frontend Development Server

From the `frontend` directory:
```bash
npm run dev
```

The frontend will be available at: `http://localhost:3000`

## 📚 API Endpoints

### Core Endpoints
- `GET /` - API information
- `GET /api/health` - Health check

### Projects
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get specific project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects` - Clear all projects

### Employees
- `GET /api/employees` - List all employees
- `POST /api/employees` - Create employee
- `PUT /api/employees/{id}` - Update employee
- `DELETE /api/employees/{id}` - Delete employee

### Matching
- `GET /api/matches/{employee_id}` - Get matches for employee

### Scanning
- `POST /api/scan/{time_range}` - Scan for new projects

### App State
- `GET /api/state/{key}` - Get app state
- `PUT /api/state/{key}` - Update app state

## 🎯 Frontend Pages

### Dashboard
- Overview statistics
- Quick actions
- Recent activity

### Projects
- Project listing with filters
- Search and filtering capabilities
- Project details and management

### Employees
- Employee profiles
- Skill management
- Matching suggestions

### Settings
- Application configuration
- API key management
- Data management tools

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key
DATABASE_URL=sqlite:///./project_finder.db
```

### API Configuration

The frontend is configured to connect to `http://localhost:8000` by default. You can modify this in `frontend/src/services/api.ts`.

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest test_main.py
```

### Frontend Testing
```bash
cd frontend
npm run build
```

## 📁 Project Structure

```
Project_Finder3/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database configuration
│   ├── models/                 # SQLAlchemy models
│   ├── services/               # Business logic
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   └── App.tsx            # Main app component
│   └── package.json           # Node.js dependencies
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions, please open an issue in the repository.

## Backend Setup and Running

### Prerequisites
- Python 3.8+
- Required packages (install with `pip install -r backend/requirements.txt`)

### Environment Setup
1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Setup environment file:**
   ```bash
   python setup_env.py
   ```
   This will create a `backend/.env` file from the template. Edit it to add your API keys:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `MISTRAL_API_KEY` - Your Mistral API key

3. **Check status (optional):**
   ```bash
   python check_status.py
   ```
   This will verify that all components are working correctly.

### Running the Backend

**Option 1: From the project root (recommended)**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2: From the backend directory**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using PowerShell script (Windows)**
```powershell
powershell -ExecutionPolicy Bypass -File run_backend.ps1
```

**Option 4: Using Python script**
```bash
python run_backend.py
```

**Option 5: Using batch file (Windows Command Prompt)**
```cmd
cmd /c run_backend.bat
```

### API Endpoints
- **Main API**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/api/health`
- **API Documentation**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### Import Structure
The application uses absolute imports (e.g., `from backend.models.core_models import Project`) which allows it to run from any directory. This follows Python best practices and ensures consistent behavior regardless of where the application is started from.