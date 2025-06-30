# Database Configuration

## Database File Location

The Project Finder application uses a single SQLite database file located in the **root directory** of the project:

```
Project_Finder3/
├── project_finder.db          # Main database file (SQLite)
├── backend/
│   ├── database.py            # Database configuration
│   ├── config.json            # Database URL configuration
│   └── ...
└── ...
```

## Database Configuration

### Primary Configuration
- **File**: `backend/database.py`
- **URL**: `sqlite:///./project_finder.db` (relative to project root)
- **Environment Variable**: `DATABASE_URL` (optional override)

### Configuration Files
- **Config Manager**: `backend/config_manager.py` - Uses `sqlite:///./project_finder.db`
- **Config JSON**: `backend/config.json` - Contains database URL configuration

## Database Schema

The database contains the following tables:
- `projects` - Project information with workload field
- `employees` - Employee information
- `skills` - Skill embeddings
- `app_state` - Application state

## Migration Scripts

All migration scripts have been updated to use the root directory database:

- `backend/migrate_add_workload_field.py` - Adds workload column
- `backend/migrate_remove_embedding_fields.py` - Removes embedding fields
- `fix_database.py` - General database fixes

## Testing and Verification

### Status Check
```bash
python check_status.py
```

### API Test
```bash
# Test projects endpoint
Invoke-WebRequest -Uri "http://localhost:8000/api/projects?time_range=8" -Method GET
```

### Direct Database Access
```bash
# Check database structure
python -c "import sqlite3; conn = sqlite3.connect('project_finder.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(projects)'); print(cursor.fetchall()); conn.close()"
```

## Important Notes

1. **Single Database File**: Only one database file exists in the root directory
2. **No Backend Directory Database**: The `backend/project_finder.db` file has been removed to avoid confusion
3. **Consistent Paths**: All code references point to the root directory database
4. **Environment Override**: Can be overridden with `DATABASE_URL` environment variable

## Troubleshooting

If you encounter database issues:

1. **Check file location**: Ensure `project_finder.db` exists in the project root
2. **Verify schema**: Run `python check_status.py` to verify database integrity
3. **Check permissions**: Ensure the application has read/write access to the database file
4. **Migration issues**: Run migration scripts if schema changes are needed