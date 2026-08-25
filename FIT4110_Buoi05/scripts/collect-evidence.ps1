# FIT4110 Lab05 - Collect Newman evidence via Postman CLI + newman
# Generates HTML and JUnit XML reports from the full collection.
#
# Usage:
#   .\scripts\collect-evidence.ps1
#
# Prerequisites:
#   - Docker container running:  docker compose up -d
#   - Newman CLI:  npm install -g newman
#   - Postman CLI: https://www.postman.com/downloads/
#   - postman login (for private collections)

$ErrorActionPreference = "Continue"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$REPORTS_DIR = Join-Path $PROJECT_ROOT "reports"
$EV_DIR = Join-Path $REPORTS_DIR "evidence"

$COLLECTION = Join-Path $PROJECT_ROOT "postman\collections\FIT4110_lab05_ai_vision_real.postman_collection.json"
$ENVIRONMENT = Join-Path $PROJECT_ROOT "postman\environments\FIT4110_lab05_docker_local.postman_environment.json"

New-Item -ItemType Directory -Force -Path $EV_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $REPORTS_DIR | Out-Null

$TODAY = Get-Date -Format "yyyy-MM-dd-HHmmss"
$HTML_REPORT = Join-Path $REPORTS_DIR "vision-lab05-newman-docker-$TODAY.html"
$XML_REPORT  = Join-Path $REPORTS_DIR "vision-lab05-newman-docker-$TODAY.xml"
$STDOUT_REPORT = Join-Path $REPORTS_DIR "vision-lab05-newman-docker-$TODAY.stdout.txt"

Write-Host "###################################################################"
Write-Host "# FIT4110 Lab05 - Newman Evidence Collection"
Write-Host "# Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "# Collection: $COLLECTION"
Write-Host "# Environment: $ENVIRONMENT"
Write-Host "###################################################################"

if (-not (Test-Path $COLLECTION)) {
    Write-Host "[ERROR] Collection not found: $COLLECTION"
    exit 1
}
if (-not (Test-Path $ENVIRONMENT)) {
    Write-Host "[ERROR] Environment not found: $ENVIRONMENT"
    exit 1
}

# Check if Docker container is running
Write-Host ""
Write-Host "Checking AI Vision Docker service at http://127.0.0.1:8000..."
try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "[OK] AI Vision service is healthy: $($health.StatusCode)"
} catch {
    Write-Host "[WARN] AI Vision service not reachable: $_"
    Write-Host "[WARN] Make sure Docker container is running: docker compose up -d"
}

# Run Newman with HTML reporter
Write-Host ""
Write-Host "Running Newman (HTML report)..."
newman run "$COLLECTION" `
    --environment "$ENVIRONMENT" `
    --reporters cli,html,junit `
    --reporter-html-export "$HTML_REPORT" `
    --reporter-junit-export "$XML_REPORT" `
    --timeout-request 10000 `
    --iteration-count 1 2>&1 | Tee-Object -Variable newmanOutput | Out-Null

$newmanExit = $LASTEXITCODE

$newmanOutput | Out-File -FilePath $STDOUT_REPORT -Encoding UTF8
Write-Host ""
Write-Host "Reports generated:"
Write-Host "  HTML: $HTML_REPORT"
Write-Host "  JUnit: $XML_REPORT"
Write-Host "  Stdout: $STDOUT_REPORT"

# Copy latest as stable-named files for easy reference
Copy-Item -Force $HTML_REPORT (Join-Path $REPORTS_DIR "vision-newman-report-docker-latest.html") -ErrorAction SilentlyContinue
Copy-Item -Force $XML_REPORT  (Join-Path $REPORTS_DIR "vision-newman-report-docker-latest.xml")  -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Newman exit code: $newmanExit"
if ($newmanExit -eq 0) {
    Write-Host "[PASS] All Newman tests passed"
} else {
    Write-Host "[WARN] Some Newman tests failed — check the HTML report"
}

Write-Host ""
Write-Host "###################################################################"
Write-Host "# Evidence collection complete"
Write-Host "###################################################################"
