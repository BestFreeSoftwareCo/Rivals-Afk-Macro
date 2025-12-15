@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "ROOT=%~dp0"

echo Launching Rivals AFK Macro...
echo.
echo ROOT: "%ROOT%"

pushd "%ROOT%" >nul 2>&1
if not "%errorlevel%"=="0" (
  echo ERROR: Failed to switch to project folder.
  echo Try moving the folder to a normal local path (not OneDrive/UNC) and re-run.
  echo.
  pause
  exit /b 1
)

if not exist "app\main.py" (
  echo ERROR: Could not find "app\main.py".
  echo This does not look like the project root.
  echo.
  dir /b
  echo.
  pause
  popd
  exit /b 1
)

set "PY_CMD="
where py >nul 2>&1
if "%errorlevel%"=="0" (
  set "PY_CMD=py -3"
) else (
  where python >nul 2>&1
  if "%errorlevel%"=="0" (
    set "PY_CMD=python"
  )
)

if "%PY_CMD%"=="" (
  echo ERROR: Python was not found.
  echo.
  echo Install Python 3.10+ (recommended 3.12) from python.org
  echo and make sure "Add python.exe to PATH" is checked.
  echo.
  pause
  popd
  exit /b 1
)

echo Using: %PY_CMD%
%PY_CMD% --version
echo.

%PY_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if not "%errorlevel%"=="0" (
  echo ERROR: Python 3.10+ is required. This project uses modern type hints.
  echo Install Python 3.12 from python.org and re-run.
  echo.
  pause
  popd
  exit /b 1
)

%PY_CMD% -c "import tkinter" >nul 2>&1
if not "%errorlevel%"=="0" (
  echo ERROR: tkinter is missing from this Python installation.
  echo Reinstall Python and make sure Tcl/Tk is included.
  echo.
  pause
  popd
  exit /b 1
)

set "PYTHONUTF8=1"

echo Starting app...
echo.
%PY_CMD% -u -m app.main
set "EXITCODE=%errorlevel%"

echo.
if not "%EXITCODE%"=="0" (
  echo ERROR: App exited with code %EXITCODE%.
  echo If you see a traceback above, copy/paste it here.
) else (
  echo App exited normally.
)
echo.
pause
popd
