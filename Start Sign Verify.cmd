@echo off
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
"%~dp0.venv\Scripts\python.exe" -m softhsm_studio.sign_app
if errorlevel 1 pause
