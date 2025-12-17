@echo off
setlocal
pushd "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -c "import customtkinter" >nul 2>nul
    if not %errorlevel%==0 (
        echo Installing dependencies...
        py -m pip install -r requirements.txt
    )
    py -m app.main
) else (
    python -c "import customtkinter" >nul 2>nul
    if not %errorlevel%==0 (
        echo Installing dependencies...
        python -m pip install -r requirements.txt
    )
    python -m app.main
)

if not %errorlevel%==0 (
    echo.
    echo App exited with error %errorlevel%.
    pause
)

popd
endlocal
