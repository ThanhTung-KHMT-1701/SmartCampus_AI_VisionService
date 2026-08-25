# FIT4110 Lab05 - Run 18 test cases via Postman CLI
# Generates individual evidence files in reports/evidence/ for each test case.
# Also outputs a JSON summary at the end.
#
# Usage:
#   .\scripts\run-18-test-cases.ps1
#
# Prerequisites:
#   - Docker container running:  docker compose up -d
#   - Postman CLI (postman) installed and in PATH:  https://www.postman.com/downloads/
#   - Postman CLI login:  postman login --with-api-key <YOUR_API_KEY>

$ErrorActionPreference = "Continue"
$BASE    = "http://127.0.0.1:8000"
$TOKEN   = "local-dev-token-vision"
$CAM_BASE = "http://192.168.137.115:8001"
$CAM_TOKEN = "lab-token-camera"

# Resolve project root (parent of scripts/)
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$EV_DIR = Join-Path $PROJECT_ROOT "reports\evidence"
$REPORTS_DIR = Join-Path $PROJECT_ROOT "reports"

New-Item -ItemType Directory -Force -Path $EV_DIR | Out-Null

# Clean empty leftover json files
Get-ChildItem $EV_DIR -Filter "*.json" -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -eq 0 } | Remove-Item -Force

$results = New-Object System.Collections.Generic.List[object]

function Run-Case {
    param(
        [string]$Id,
        [string]$Title,
        [string]$Method,
        [string]$Url,
        [string]$BodyPath = $null,
        [int]$ExpectedStatus,
        [string]$EvidenceTag,
        [string[]]$Headers = @()
    )

    $argList = [System.Collections.Generic.List[string]]::new()
    $argList.Add("request")
    $argList.Add($Method)
    $argList.Add($Url)
    foreach ($h in $Headers) {
        $argList.Add("-H")
        $argList.Add($h)
    }
    if ($BodyPath -and (Test-Path $BodyPath)) {
        $argList.Add("-d")
        $argList.Add("@$BodyPath")
    }

    $stdoutRaw = & postman @argList 2>&1
    $exitCode  = $LASTEXITCODE
    $cleanStdout = ($stdoutRaw | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] }) -join "`n"

    # Extract HTTP status code from postman output
    $code = $null
    $firstLine = ($cleanStdout -split "`n" | Select-Object -First 5) -join " | "
    if ($firstLine -match "(\d{3})\s+(OK|Unauthorized|Forbidden|Not Found|Unprocessable Entity|Bad Request|Request Timeout|Payload Too Large|Too Many Requests|Internal Server Error|Service Unavailable|Created)") {
        $code = [int]$Matches[1]
    }

    $body = ($cleanStdout -split "`n" | Where-Object { $_ -match '^\s*\{' } | Select-Object -First 1) -replace '^\s+', '' -replace '\s+$', ''
    $evidencePath = "$EV_DIR\$Id.stdout.txt"
    $cleanStdout | Out-File -FilePath $evidencePath -Encoding UTF8

    $marker = if ($code -eq $ExpectedStatus) { "PASS" } else { "FAIL" }
    Write-Host "$Id [$marker] $Title -> code=$code (expected=$ExpectedStatus)"

    $results.Add([PSCustomObject]@{
        Id             = $Id
        Title          = $Title
        Method         = $Method
        Url            = $Url
        ExpectedStatus = $ExpectedStatus
        ActualStatus   = $code
        Body           = $body
        Result         = $marker
        Evidence       = $evidencePath
    })
}

$H_JSON       = @("Authorization:Bearer $TOKEN", "Content-Type:application/json")
$H_JSON_ONLY  = @("Content-Type:application/json")
$H_AUTH_ONLY  = @("Authorization:Bearer $TOKEN")
$H_BAD_TOKEN  = @("Authorization:Bearer invalid-token-xyz", "Content-Type:application/json")
$H_CAM_JSON   = @("Authorization:Bearer $CAM_TOKEN", "Content-Type:application/json")

Write-Host "###################################################################"
Write-Host "# Running 18 test cases via Postman CLI"
Write-Host "# Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "# Target: $BASE"
Write-Host "###################################################################"

# TC01 - Health check
Run-Case "TC01" "GET /health returns 200 + status=ok" "GET" "$BASE/health" $null 200 "GET /health"

# TC02 - Detect with image_url
$body02 = '{"camera_id":"cam-lab05-gate","image_url":"http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest","timestamp":"2026-08-25T08:00:00Z","confidence_threshold":0.6}'
$body02 | Out-File -FilePath "$EV_DIR\TC02.body.json" -Encoding UTF8
Run-Case "TC02" "POST /vision/detect (image_url) -> 200" "POST" "$BASE/vision/detect" "$EV_DIR\TC02.body.json" 200 "POST /vision/detect (image_url)" $H_JSON

# TC03 - Detect with image_base64
$body03 = '{"camera_id":"cam-lab05-library","image_base64":"aGVsbG8td29ybGQtaW1hZ2U=","timestamp":"2026-08-25T08:05:00Z"}'
$body03 | Out-File -FilePath "$EV_DIR\TC03.body.json" -Encoding UTF8
Run-Case "TC03" "POST /vision/detect (image_base64) -> 200" "POST" "$BASE/vision/detect" "$EV_DIR\TC03.body.json" 200 "POST /vision/detect (image_base64)" $H_JSON

# TC04 - confidence_threshold=0.0 boundary
$body04 = '{"camera_id":"cam-lab05-gate","image_url":"http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest","timestamp":"2026-08-25T08:20:00Z","confidence_threshold":0.0}'
$body04 | Out-File -FilePath "$EV_DIR\TC04.body.json" -Encoding UTF8
Run-Case "TC04" "POST /vision/detect confidence=0.0 (min) -> 200" "POST" "$BASE/vision/detect" "$EV_DIR\TC04.body.json" 200 "POST /vision/detect (boundary min)" $H_JSON

# TC05 - Get detection by id (capture from TC02)
$tc02Content = Get-Content "$EV_DIR\TC02.stdout.txt" -Raw
$DET_ID = $null
if ($tc02Content -match '"detection_id":"([0-9a-f-]+)"') {
    $DET_ID = $Matches[1]
}
if (-not $DET_ID) {
    $b = $body02 | ConvertFrom-Json
    $r = Invoke-RestMethod -Uri "$BASE/vision/detect" -Method POST `
        -Headers @{Authorization="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body ($body02)
    $DET_ID = $r.detection_id
}
Run-Case "TC05" "GET /vision/detections/{id} -> 200" "GET" "$BASE/vision/detections/$DET_ID" $null 200 "GET /vision/detections/$DET_ID" $H_AUTH_ONLY

# TC06 - GET recent results with filter
Run-Case "TC06" "GET /vision/results/recent?limit=10&camera_id=cam-lab05-gate -> 200" "GET" "$BASE/vision/results/recent?limit=10&camera_id=cam-lab05-gate" $null 200 "GET /vision/results/recent (filter)" $H_AUTH_ONLY

# TC07 - Face-match happy path
$body07 = '{"image_url":"http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest","reference_image_url":"http://192.168.137.79:8001/profiles/student-001.jpg","threshold":0.75,"trace_id":"trace-lab05-001","timestamp":"2026-08-25T08:30:00Z"}'
$body07 | Out-File -FilePath "$EV_DIR\TC07.body.json" -Encoding UTF8
Run-Case "TC07" "POST /vision/face-match (threshold=0.75) -> 200" "POST" "$BASE/vision/face-match" "$EV_DIR\TC07.body.json" 200 "POST /vision/face-match" $H_JSON

# TC08 - GET models/info
Run-Case "TC08" "GET /vision/models/info -> 200" "GET" "$BASE/vision/models/info" $null 200 "GET /vision/models/info" $H_AUTH_ONLY

# TC09 - Random UUID returns 404
Run-Case "TC09" "GET /vision/detections/random-uuid valid token -> 404" "GET" "$BASE/vision/detections/00000000-0000-0000-0000-000000000000" $null 404 "GET detection (random uuid)" $H_AUTH_ONLY

# TC10 - Missing token -> 401
$body10 = '{"camera_id":"cam-lab05-gate","image_url":"http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest","timestamp":"2026-08-25T08:00:00Z"}'
$body10 | Out-File -FilePath "$EV_DIR\TC10.body.json" -Encoding UTF8
Run-Case "TC10" "POST /vision/detect (no auth) -> 401" "POST" "$BASE/vision/detect" "$EV_DIR\TC10.body.json" 401 "POST /vision/detect (no token)" $H_JSON_ONLY

# TC11 - Wrong token -> 401
Run-Case "TC11" "POST /vision/detect (wrong token) -> 401" "POST" "$BASE/vision/detect" "$EV_DIR\TC10.body.json" 401 "POST /vision/detect (wrong token)" $H_BAD_TOKEN

# TC12 - Missing camera_id -> 422
$body12 = '{"image_url":"http://example.com/f.jpg","timestamp":"2026-08-25T08:00:00Z"}'
$body12 | Out-File -FilePath "$EV_DIR\TC12.body.json" -Encoding UTF8
Run-Case "TC12" "POST /vision/detect (no camera_id) -> 422" "POST" "$BASE/vision/detect" "$EV_DIR\TC12.body.json" 422 "POST /vision/detect (no camera_id)" $H_JSON

# TC13 - Missing image -> 422
$body13 = '{"camera_id":"cam-lab05-01","timestamp":"2026-08-25T08:10:00Z"}'
$body13 | Out-File -FilePath "$EV_DIR\TC13.body.json" -Encoding UTF8
Run-Case "TC13" "POST /vision/detect (no image) -> 422" "POST" "$BASE/vision/detect" "$EV_DIR\TC13.body.json" 422 "POST /vision/detect (no image)" $H_JSON

# TC14 - Invalid UUID format -> 422
Run-Case "TC14" "GET /vision/detections/not-a-uuid -> 422" "GET" "$BASE/vision/detections/not-a-uuid" $null 422 "GET detection (bad uuid)" $H_AUTH_ONLY

# TC15 - Both images -> 422
$body15 = '{"camera_id":"cam-lab05-01","image_url":"http://example.com/f.jpg","image_base64":"aGVsbG8=","timestamp":"2026-08-25T08:15:00Z"}'
$body15 | Out-File -FilePath "$EV_DIR\TC15.body.json" -Encoding UTF8
Run-Case "TC15" "POST /vision/detect (both images) -> 422" "POST" "$BASE/vision/detect" "$EV_DIR\TC15.body.json" 422 "POST /vision/detect (both images)" $H_JSON

# TC16 - limit=101 above max -> 422
Run-Case "TC16" "GET /vision/results/recent?limit=101 -> 422" "GET" "$BASE/vision/results/recent?limit=101" $null 422 "GET recent (limit above max)" $H_AUTH_ONLY

# TC17 - Camera Stream mock POST /frames (consumer-side smoke)
$body17 = '{"camera_id":"cam-lab05-e2e","frame_url":"http://192.168.137.115:8001/cameras/cam-lab05-e2e/frames/latest","motion_detected":true,"timestamp":"2026-08-25T08:45:00Z"}'
$body17 | Out-File -FilePath "$EV_DIR\TC17.body.json" -Encoding UTF8
Run-Case "TC17" "POST Camera Stream mock /frames (consumer-side) -> 201" "POST" "$CAM_BASE/frames" "$EV_DIR\TC17.body.json" 201 "POST camera mock /frames" $H_CAM_JSON

# TC18 - Camera Stream mock health (consumer-side smoke)
Run-Case "TC18" "GET Camera Stream mock /health (consumer-side) -> 200" "GET" "$CAM_BASE/health" $null 200 "GET camera mock /health"

Write-Host ""
Write-Host "###################################################################"
Write-Host "# Summary"
Write-Host "###################################################################"
$pass = ($results | Where-Object { $_.Result -eq "PASS" }).Count
$fail = ($results | Where-Object { $_.Result -eq "FAIL" }).Count
Write-Host "Total: $($results.Count)  PASS: $pass  FAIL: $fail"

$results | Select-Object Id, Title, ExpectedStatus, ActualStatus, Result | Format-Table -AutoSize

$results | ConvertTo-Json -Depth 4 | Out-File "$EV_DIR\results.json" -Encoding UTF8
Write-Host ""
Write-Host "Evidence saved to: $EV_DIR"
Write-Host "Results summary: $EV_DIR\results.json"
