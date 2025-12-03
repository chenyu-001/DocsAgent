@echo off
REM DocsAgent Multi-Tenant Database Migration (Windows)
REM Usage: Double-click or run in CMD

echo ==========================================
echo DocsAgent Multi-Tenant Migration
echo ==========================================
echo.

REM Check Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker command not found
    echo Please install Docker Desktop
    pause
    exit /b 1
)

echo [1/4] Checking Docker service...
docker-compose ps >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    docker compose ps >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Docker Compose not running
        echo Please start: docker-compose up -d
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo [OK] Docker service is running
echo.

echo [2/4] Checking backend container...
%DOCKER_COMPOSE_CMD% ps backend | findstr "running" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend container not running
    echo Please start: %DOCKER_COMPOSE_CMD% up -d backend
    pause
    exit /b 1
)

echo [OK] Backend container is running
echo.

echo [3/4] Running database migration...
echo This may take a few minutes...
echo.

%DOCKER_COMPOSE_CMD% exec backend bash /app/run_migration.sh
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Migration failed
    echo.
    echo Alternative methods:
    echo   1. Manual: %DOCKER_COMPOSE_CMD% exec backend bash
    echo      Then run: bash /app/run_migration.sh
    echo.
    echo   2. Python: %DOCKER_COMPOSE_CMD% exec backend python init_db.py
    echo.
    echo   3. Direct SQL:
    echo      docker exec -i docsagent-postgres psql -U docsagent -d docsagent ^< backend/migrations/002_add_multi_tenant.sql
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Verifying deployment...

%DOCKER_COMPOSE_CMD% exec postgres psql -U docsagent -d docsagent -c "SELECT id, name, slug FROM tenants LIMIT 5;"

echo.
echo ==========================================
echo Migration completed successfully!
echo ==========================================
echo.
echo Next steps:
echo   1. Visit API: http://localhost:8000/docs
echo   2. Read guide: MULTI_TENANT_GUIDE.md
echo   3. Test tenant API
echo.
echo For details see: DOCKER_SETUP.md
echo.
pause
