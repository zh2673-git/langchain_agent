@echo off
setlocal enabledelayedexpansion

echo LangChain Agent Docker Launcher
echo ==================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running, please start Docker first
    pause
    exit /b 1
)

echo Choose startup mode:
echo 1. OpenWebUI + LangChain Backend (Production)
echo 2. Gradio + LangChain Backend (Production)
echo 3. LangChain Backend Only (Production)
echo 4. Development Mode (Code Hot Reload)
echo 5. Fast Build Mode (China Mirror)
echo 6. Stop All Services
echo 7. View Service Status
echo 8. View Logs

set /p choice="Please choose (1-8): "

if "%choice%"=="1" goto option1
if "%choice%"=="2" goto option2
if "%choice%"=="3" goto option3
if "%choice%"=="4" goto option4
if "%choice%"=="5" goto option5
if "%choice%"=="6" goto option6
if "%choice%"=="7" goto option7
if "%choice%"=="8" goto option8
goto invalid

:option1
echo Starting OpenWebUI + LangChain Backend (Production)...
docker-compose up -d
echo Services started successfully
echo OpenWebUI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
goto end

:option2
echo Starting Gradio + LangChain Backend (Production)...
docker-compose --profile gradio up -d
echo Services started successfully
echo Gradio: http://localhost:7860
echo API Docs: http://localhost:8000/docs
goto end

:option3
echo Starting LangChain Backend Only (Production)...
docker-compose up -d langchain-backend
echo Backend service started successfully
echo API Docs: http://localhost:8000/docs
goto end

:option4
echo Starting Development Mode (Code Hot Reload)...
echo Building development containers...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
echo Development services started successfully
echo OpenWebUI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo 🔥 Development Mode Features:
echo   ✅ Code hot reload enabled
echo   ✅ Edit backend/ or main/ files to see changes instantly
echo   ✅ No need to rebuild containers
echo   ✅ Enhanced debugging support
goto end

:option5
echo Starting Fast Build Mode (China Mirror)...
docker-compose -f docker-compose.fast.yml up -d --build
echo Fast build services started successfully
echo OpenWebUI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo Note: Using China mirrors for faster build
goto end

:option6
echo Stopping all services...
docker-compose down
docker-compose -f docker-compose.fast.yml down
echo All services stopped
goto end

:option7
echo Service Status:
docker-compose ps
docker-compose -f docker-compose.fast.yml ps
goto end

:option8
echo Service Logs:
docker-compose logs -f
goto end

:invalid
echo Invalid choice
pause
exit /b 1

:end

pause
