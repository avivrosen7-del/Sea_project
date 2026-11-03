@echo off
REM One-click launcher: fetch fresh data and open the HTML report
cd /d "%~dp0"
"venv\Scripts\python.exe" main.py
if errorlevel 1 pause
