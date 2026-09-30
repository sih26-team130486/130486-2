@echo off
TITLE PRAMAAN -- Launch All Services
color 0A
echo.
echo ================================================================
echo   PRAMAAN -- Secure Digital Evidence Management System (SIH PS 26190)
echo   Launching Full Stack: Django Backend + React Frontend
echo ================================================================
echo.

echo [1/3] Starting Django Backend Server on http://127.0.0.1:8000 ...
start "PRAMAAN Backend (Django)" cmd /k "cd /d %~dp0PRAMAAN-BACKEND && call start_server.bat"

echo [2/3] Starting React Frontend Server on http://localhost:5173 ...
start "PRAMAAN Frontend (Vite)" cmd /k "cd /d %~dp0PRAMAAN-FRONTEND && call start_frontend.bat"

echo [3/3] Opening Google Chrome in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5173/

echo.
echo Both servers are running!
echo Frontend: http://localhost:5173/
echo Backend : http://127.0.0.1:8000/admin/
echo.
pause
