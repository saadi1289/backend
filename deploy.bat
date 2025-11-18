@echo off
echo ========================================
echo CorpFinity Backend - Vercel Deployment
echo ========================================
echo.

echo Step 1: Checking if Vercel CLI is installed...
where vercel >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Vercel CLI not found!
    echo Please install it first: npm i -g vercel
    pause
    exit /b 1
)
echo [OK] Vercel CLI found
echo.

echo Step 2: Checking environment variables...
if not exist .env (
    echo [WARNING] .env file not found!
    echo Please create .env file with your DATABASE_URL and SECRET_KEY
    echo You can copy from .env.example
    pause
    exit /b 1
)
echo [OK] .env file exists
echo.

echo Step 3: Would you like to initialize the database? (y/n)
set /p init_db="Initialize database tables in Neon? (y/n): "
if /i "%init_db%"=="y" (
    echo Initializing database...
    python init_db.py
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Database initialization failed!
        pause
        exit /b 1
    )
    echo [OK] Database initialized
    echo.
)

echo Step 4: Deploying to Vercel...
echo.
vercel

echo.
echo ========================================
echo Deployment initiated!
echo ========================================
echo.
echo Next steps:
echo 1. Set environment variables in Vercel:
echo    vercel env add DATABASE_URL
echo    vercel env add SECRET_KEY
echo.
echo 2. Deploy to production:
echo    vercel --prod
echo.
echo 3. Update your Flutter app with the API URL
echo.
pause
