@echo off
echo Starting Project Finder Backend...
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause