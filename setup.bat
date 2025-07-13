@echo off
echo Setting up ITS Example Templates project...

REM Check if virtual environment already exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python is installed and try running as administrator
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists, skipping creation
)

echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    exit /b 1
)

echo Installing project dependencies...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo.
echo =====================================================
echo Setup complete!
echo.
echo To use the project:
echo   1. Activate environment: venv\Scripts\activate
echo   2. Run compiler: python compile_all_templates.py
echo =====================================================
