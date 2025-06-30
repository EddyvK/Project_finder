# PowerShell script to run the Project Finder backend application

Write-Host "Starting Project Finder Backend..." -ForegroundColor Green
Write-Host ""

# Run the uvicorn server from project root
try {
    python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
}
catch {
    Write-Host "Error running server: $_" -ForegroundColor Red
}
finally {
    Write-Host "`nServer stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
}