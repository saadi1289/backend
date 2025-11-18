@echo off
echo ========================================
echo CorpFinity Backend - Local Development
echo ========================================
echo.

echo Checking environment...
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

echo Starting FastAPI development server...
echo.
echo API will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
