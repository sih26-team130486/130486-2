@echo off
TITLE PRAMAAN Backend Server
color 0A
echo.
echo =====================================================
echo   PRAMAAN Backend -- SIH PS 26190
echo   Django + DRF + SQLite + JWT + SHA-256
echo =====================================================
echo.
echo [1/3] Running migrations...
python manage.py migrate --run-syncdb
echo.
echo [2/3] Seeding demo users...
python manage.py seed_demo
echo.
echo [3/3] Starting development server...
echo.
echo   API Base URL : http://127.0.0.1:8000/api/v1/
echo   Admin Panel  : http://127.0.0.1:8000/admin/
echo.
echo   Demo Credentials:
echo     ADMIN : admin              / Admin@1234
echo     IO    : inspector_sharma   / IO@12345
echo     COURT : court_user         / Court@1234
echo.
echo =====================================================
echo.
python manage.py runserver
pause
