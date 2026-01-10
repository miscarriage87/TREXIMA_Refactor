@echo off
REM =============================================================================
REM TREXIMA Windows Build Script
REM Creates standalone .exe using PyInstaller
REM =============================================================================

echo.
echo ============================================
echo   TREXIMA Windows Executable Builder
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if exist build_env rmdir /s /q build_env
python -m venv build_env
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call build_env\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements-desktop.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Building executable with PyInstaller...
pyinstaller trexima.spec --clean
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo [5/5] Cleaning up...
REM Deactivate virtual environment
call deactivate

echo.
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Executable created at: dist\TREXIMA.exe
echo.
echo You can now distribute TREXIMA.exe to users.
echo No Python installation required to run it.
echo.

REM Open the dist folder
explorer dist

pause
