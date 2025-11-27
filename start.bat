@echo off
echo.
echo ========================================
echo   9P Social Analytics
echo   Starting the application...
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running!
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo Docker is running...
echo.
echo Starting 9P Analytics (this may take a few minutes on first run)...
echo.

REM Start the application
docker-compose up

REM If the user presses Ctrl+C, clean shutdown
echo.
echo Application stopped.
pause
