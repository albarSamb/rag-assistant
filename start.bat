@echo off
echo Starting DocuBot...
echo.
echo [Backend] Starting on http://localhost:8000
start "DocuBot Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"
timeout /t 3 /noq > nul
echo [Frontend] Starting on http://localhost:3000
start "DocuBot Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 4 /noq > nul
start http://localhost:3000
echo.
echo DocuBot is running! Close the terminal windows to stop.
pause
