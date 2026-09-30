@echo off
TITLE PRAMAAN Frontend Server (Vite)
color 0B
echo.
echo ====================================================
echo   PRAMAAN -- Secure Digital Evidence Management
echo   Starting Frontend UI on http://localhost:5173
echo ====================================================
echo.
call npm.cmd run dev
pause
