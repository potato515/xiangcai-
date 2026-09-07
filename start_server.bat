@echo off
echo ========================================
echo   Xiangcai Workbench - Backend Server
echo ========================================
echo.

cd /d "%~dp0server"

set PYTHON_EXE=D:\baijiahao\tools\miniconda3\python.exe

echo [1/3] Checking Python environment...
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found: %PYTHON_EXE%
    echo Please edit this file and set correct PYTHON_EXE path.
    pause
    exit /b 1
)
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo [ERROR] Python environment error
    pause
    exit /b 1
)

echo.
echo [2/3] Checking dependencies...
"%PYTHON_EXE%" -c "import fastapi, uvicorn, pydantic" 2>nul
if errorlevel 1 (
    echo [WARN] Missing dependencies, installing...
    "%PYTHON_EXE%" -m pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [WARN] Dependency install may have issues, continuing...
    )
) else (
    echo [OK] Dependencies check passed
)

echo.
echo [3/3] Starting FastAPI server...
echo.
echo Server URL:  http://127.0.0.1:9527
echo API Docs:    http://127.0.0.1:9527/docs
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

"%PYTHON_EXE%" main.py

pause
