# DocsAgent Multi-Tenant Database Migration
# PowerShell script for Windows users

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DocsAgent Multi-Tenant Migration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker not found. Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Detect docker-compose or docker compose
$dockerComposeCmd = "docker-compose"
try {
    docker-compose version | Out-Null
} catch {
    $dockerComposeCmd = "docker compose"
}

Write-Host "[OK] Docker found: $dockerComposeCmd" -ForegroundColor Green
Write-Host ""

# Check if services are running
Write-Host "[2/4] Checking containers..." -ForegroundColor Yellow
$backendRunning = & $dockerComposeCmd ps backend | Select-String "running"
if (-not $backendRunning) {
    Write-Host "[ERROR] Backend container not running" -ForegroundColor Red
    Write-Host "Please start: $dockerComposeCmd up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Backend container is running" -ForegroundColor Green
Write-Host ""

# Run migration
Write-Host "[3/4] Running migration..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

# Method 1: Try bash script
Write-Host "Attempting method 1: bash script..." -ForegroundColor Gray
$result = & $dockerComposeCmd exec backend bash /app/run_migration.sh 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Bash script failed, trying Python..." -ForegroundColor Yellow
    Write-Host ""

    # Method 2: Try Python script
    Write-Host "Attempting method 2: Python script..." -ForegroundColor Gray
    $result = & $dockerComposeCmd exec backend python init_db.py 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Migration failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please try manually:" -ForegroundColor Yellow
        Write-Host "  $dockerComposeCmd exec backend bash" -ForegroundColor Cyan
        Write-Host "  cd /app && python init_db.py" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
}

Write-Host "[OK] Migration completed" -ForegroundColor Green
Write-Host ""

# Verify
Write-Host "[4/4] Verifying..." -ForegroundColor Yellow
& $dockerComposeCmd exec postgres psql -U docsagent -d docsagent -c "SELECT COUNT(*) as tenant_count FROM tenants;"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "SUCCESS! Migration completed" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  2. Read guide: MULTI_TENANT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
