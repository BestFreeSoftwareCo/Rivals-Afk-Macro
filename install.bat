@echo off
setlocal EnableExtensions
net session >nul 2>&1
if not %errorlevel%==0 (
  echo Please run install.bat as Administrator.
  pause
  exit /b 1
)
echo Rivals AFK Macro installer
echo.
set ROOT=%~dp0
if not exist "%ROOT%app" mkdir "%ROOT%app" >nul 2>&1
if not exist "%ROOT%autoit" mkdir "%ROOT%autoit" >nul 2>&1
if not exist "%ROOT%config" mkdir "%ROOT%config" >nul 2>&1
if not exist "%ROOT%logs" mkdir "%ROOT%logs" >nul 2>&1
echo Checking Python...
set PY_CMD=
where py >nul 2>&1
if %errorlevel%==0 (
  set PY_CMD=py -3
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set PY_CMD=python
  )
)

if "%PY_CMD%"=="" (
  echo Python was not found on PATH. Please install Python 3.12 and re-run.
  pause
  exit /b 1
)

%PY_CMD% --version
if not %errorlevel%==0 (
  echo Python was not found on PATH. Please install Python 3.12 and re-run.
  pause
  exit /b 1
)

echo Installing required Python packages...
%PY_CMD% -m pip install --upgrade pip
if exist "%ROOT%requirements.txt" (
  %PY_CMD% -m pip install -r "%ROOT%requirements.txt"
) else (
  %PY_CMD% -m pip install keyboard
)
if not %errorlevel%==0 (
  echo Failed to install Python packages.
  pause
  exit /b 1
)
echo.
echo AutoIt v3 must be installed for this macro.
echo If it is not installed, install it from https://www.autoitscript.com/site/autoit/downloads/
echo.
echo Placeholder GitHub download step:
echo - Set REPO_ZIP_URL to your repo zip, then implement download/unzip.
echo.
set REPO_ZIP_URL=https://example.com/placeholder.zip
echo REPO_ZIP_URL=%REPO_ZIP_URL%
echo.
echo Setup complete.
echo Run Launch-Rivals-AFK.bat to launch.
pause
