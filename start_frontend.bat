@echo off
echo ========================================
echo   Xiangcai Workbench - Frontend Dev Server
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Checking Node.js environment...
node --version
if errorlevel 1 (
    echo [ERROR] Node.js not found, please install Node.js 18+
    pause
    exit /b 1
)

echo.
echo [2/2] Starting dev server...
echo.
echo Frontend URL:  http://localhost:5173
echo API Proxy:     /api -^> http://127.0.0.1:8090
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

npm run dev

pause
