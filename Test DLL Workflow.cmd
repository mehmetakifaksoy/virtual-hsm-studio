@echo off
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
set "SOFTHSM_TEST_MODULE=%~dp0tools\softhsm2\SoftHSM2\lib\softhsm2-x64.dll"
"%~dp0.venv\Scripts\python.exe" -m compileall -q src tests
if errorlevel 1 goto finished
"%~dp0.venv\Scripts\python.exe" -m pytest -p no:cacheprovider
:finished
pause
