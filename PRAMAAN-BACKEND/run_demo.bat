@echo off
TITLE PRAMAAN Demo Flow
color 0B
echo.
echo =====================================================
echo   PRAMAAN Demo Flow -- SIH PS 26190
echo   Upload -> Hash -> Verify -> Tamper -> Alert -> Audit
echo =====================================================
echo.
echo Make sure server is running (start_server.bat) first!
echo.
python -X utf8 demo_flow.py
echo.
pause
