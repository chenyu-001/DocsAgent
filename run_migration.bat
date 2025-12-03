@echo off
REM Windows 批处理脚本 - 运行数据库迁移
REM 使用方法: 双击运行或在CMD中执行 run_migration.bat

echo ==========================================
echo DocsAgent 多租户数据库迁移 (Windows)
echo ==========================================
echo.

REM 检查Docker是否安装
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 找不到Docker命令
    echo 请确保Docker Desktop已安装并运行
    pause
    exit /b 1
)

echo [1/4] 检查Docker服务...
docker-compose ps >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    docker compose ps >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] Docker Compose服务未运行
        echo 请先启动: docker-compose up -d
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE_CMD=docker compose
) else (
    set DOCKER_COMPOSE_CMD=docker-compose
)

echo [OK] Docker服务正常
echo.

echo [2/4] 检查backend容器...
%DOCKER_COMPOSE_CMD% ps backend | findstr "running" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] backend容器未运行
    echo 请先启动: %DOCKER_COMPOSE_CMD% up -d backend
    pause
    exit /b 1
)

echo [OK] backend容器正常
echo.

echo [3/4] 执行数据库迁移...
echo 这可能需要几分钟时间...
echo.

%DOCKER_COMPOSE_CMD% exec backend bash /app/run_migration.sh
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 迁移执行失败
    echo.
    echo 可以尝试其他方法:
    echo   1. 手动进入容器: %DOCKER_COMPOSE_CMD% exec backend bash
    echo   2. 然后运行: bash /app/run_migration.sh
    echo.
    echo 或使用Python脚本:
    echo   %DOCKER_COMPOSE_CMD% exec backend python init_db.py
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] 验证部署...

%DOCKER_COMPOSE_CMD% exec postgres psql -U docsagent -d docsagent -c "SELECT id, name, slug FROM tenants LIMIT 5;"

echo.
echo ==========================================
echo 迁移完成!
echo ==========================================
echo.
echo 下一步:
echo   1. 访问API: http://localhost:8000/docs
echo   2. 查看文档: MULTI_TENANT_GUIDE.md
echo   3. 测试租户API
echo.
echo 详细说明请参考: DOCKER_SETUP.md
echo.
pause
