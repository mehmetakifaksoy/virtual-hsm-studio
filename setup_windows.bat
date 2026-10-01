@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON=py -3.11
) else (
  set PYTHON=python
)

if not exist .venv (
  %PYTHON% -m venv .venv || goto :error
)

.venv\Scripts\python.exe -m pip install --upgrade pip || goto :error
.venv\Scripts\python.exe -m pip install -e . || goto :error

echo.
echo SoftHSM Studio setup completed.
echo Run run.bat to start the application.
exit /b 0

:error
echo.
echo Setup failed. Review the error above.
exit /b 1
