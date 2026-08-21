$ErrorActionPreference = "Continue"
$BASE = "http://127.0.0.1:8000"
$TOKEN = "local-dev-token-vision"
$REPO = "E:\dnu.khmt.1701.1771040029@gmail.com\GithubClassroom\DichVuKetNoiVaCongNgheNenTang_1771040029\FIT4110_Buoi03_Postman_Mock_Testing"
$EV_DIR = Join-Path $REPO "reports\evidence"
New-Item -ItemType Directory -Force -Path $EV_DIR | Out-Null

# Clean leftover empty files
Get-ChildItem $EV_DIR -Filter "*.json" -ErrorAction SilentlyContinue | Where-Object { $_.Length -eq 0 } | Remove-Item -Force

$results = New-Object System.Collections.Generic.List[object]

function Run-Case {
    param(
        [string]$Id,
        [string]$Title,
        [string]$Method,
        [string]$Url,
        [string]$BodyPath,
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
    if ($BodyPath) {
        $argList.Add("-d")
        $argList.Add("@$BodyPath")
    }

    $stdoutRaw = & postman @argList 2>&1
    $exitCode = $LASTEXITCODE
    $cleanStdout = ($stdoutRaw | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] }) -join "`n"

    # Extract status code from the line "200 OK" or "401 Unauthorized" or "422 Unprocessable Entity"
    $code = $null
    $firstLine = ($cleanStdout -split "`n" | Select-Object -First 5) -join " | "
    if ($firstLine -match "(\d{3})\s+(OK|Unauthorized|Forbidden|Not Found|Unprocessable Entity|Bad Request|Request Timeout|Payload Too Large|Too Many Requests|Internal Server Error|Service Unavailable|Created)") {
        $code = [int]$Matches[1]
    }

    $body = ($cleanStdout -split "`n" | Where-Object { $_ -match "^\s*\{" } | Select-Object -First 1) -replace '^\s+', '' -replace '\s+$', ''
    $evidencePath = "$EV_DIR\$Id.stdout.txt"
    $cleanStdout | Out-File -FilePath $evidencePath -Encoding UTF8

    $marker = if ($code -eq $ExpectedStatus) { "PASS" } else { "FAIL" }
    Write-Host "$Id [$marker] $Title -> code=$code (expected=$ExpectedStatus)"

    $results.Add([PSCustomObject]@{
        Id = $Id
        Title = $Title
        Method = $Method
        Url = $Url
        ExpectedStatus = $ExpectedStatus
        ActualStatus = $code
        Body = $body
        Result = $marker
        Evidence = $evidencePath
    })
}

$H_JSON = @("Authorization:Bearer $TOKEN", "Content-Type:application/json")
$H_JSON_ONLY = @("Content-Type:application/json")
$H_AUTH_ONLY = @("Authorization:Bearer $TOKEN")
$H_BAD = @("Authorization:Bearer invalid-token-xyz", "Content-Type:application/json")
$H_CAM = @("Authorization:Bearer lab-token-camera", "Content-Type:application/json")

Write-Host "############################################################"
Write-Host "# Running 15 test-cases via Postman CLI v1.46.0"
Write-Host "############################################################"

# TC01
Run-Case "TC01" "Health check returns 200 + status=ok" "GET" "$BASE/health" $null 200 "GET /health"

# TC02
$body02 = '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-13T07:30:00Z","confidence_threshold":0.6}'
$body02 | Out-File -FilePath "$EV_DIR\TC02.body.json" -Encoding UTF8
Run-Case "TC02" "POST /vision/detect with image_url -> 200" "POST" "$BASE/vision/detect" "$EV_DIR\TC02.body.json" 200 "POST /vision/detect (image_url)" $H_JSON

# TC03
$body03 = '{"camera_id":"cam-library-02","image_base64":"aGVsbG8td29ybGQ=","timestamp":"2026-08-13T07:31:00Z"}'
$body03 | Out-File -FilePath "$EV_DIR\TC03.body.json" -Encoding UTF8
Run-Case "TC03" "POST /vision/detect with image_base64 -> 200" "POST" "$BASE/vision/detect" "$EV_DIR\TC03.body.json" 200 "POST /vision/detect (image_base64)" $H_JSON

# TC04 - boundary
$body04 = '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-13T07:30:00Z","confidence_threshold":1.0}'
$body04 | Out-File -FilePath "$EV_DIR\TC04.body.json" -Encoding UTF8
Run-Case "TC04" "POST /vision/detect confidence_threshold=1.0 (max) -> 200" "POST" "$BASE/vision/detect" "$EV_DIR\TC04.body.json" 200 "POST /vision/detect (boundary max)" $H_JSON

# TC05 - capture detection_id from TC02 stdout file
$tc02content = Get-Content "$EV_DIR\TC02.stdout.txt" -Raw
$DET_ID = $null
if ($tc02content -match '"detection_id":"([0-9a-f-]+)"') { $DET_ID = $Matches[1] }
if (-not $DET_ID) {
    # Fallback: hit the API directly via PowerShell to grab a fresh id
    $b = $body02 | ConvertFrom-Json
    $r = Invoke-RestMethod -Uri "$BASE/vision/detect" -Method POST -Headers @{Authorization="Bearer $TOKEN"; "Content-Type"="application/json"} -Body ($body02)
    $DET_ID = $r.detection_id
}
Run-Case "TC05" "GET /vision/detections/{id} -> 200" "GET" "$BASE/vision/detections/$DET_ID" $null 200 "GET /vision/detections/$DET_ID" $H_AUTH_ONLY

# TC06
Run-Case "TC06" "GET /vision/results/recent?limit=10&camera_id=cam-gate-01 -> 200" "GET" "$BASE/vision/results/recent?limit=10&camera_id=cam-gate-01" $null 200 "GET /vision/results/recent (filter)" $H_AUTH_ONLY

# TC07
$body07 = '{"image_url":"http://storage.campus.local/images/face.jpg","reference_image_url":"http://storage.campus.local/profiles/student-001.jpg","threshold":0.75,"trace_id":"trace-20260813-001","timestamp":"2026-08-13T07:30:00Z"}'
$body07 | Out-File -FilePath "$EV_DIR\TC07.body.json" -Encoding UTF8
Run-Case "TC07" "POST /vision/face-match happy path -> 200" "POST" "$BASE/vision/face-match" "$EV_DIR\TC07.body.json" 200 "POST /vision/face-match" $H_JSON

# TC08
Run-Case "TC08" "GET /vision/models/info -> 200" "GET" "$BASE/vision/models/info" $null 200 "GET /vision/models/info" $H_AUTH_ONLY

# TC09
Run-Case "TC09" "GET /vision/detections/{random uuid} valid token -> 404 (not 401/403)" "GET" "$BASE/vision/detections/00000000-0000-0000-0000-000000000000" $null 404 "GET detection (random uuid, valid token)" $H_AUTH_ONLY

# TC10
$body10 = '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-13T07:30:00Z"}'
$body10 | Out-File -FilePath "$EV_DIR\TC10.body.json" -Encoding UTF8
Run-Case "TC10" "POST /vision/detect missing token -> 401" "POST" "$BASE/vision/detect" "$EV_DIR\TC10.body.json" 401 "POST /vision/detect (no auth)" $H_JSON_ONLY

# TC11
Run-Case "TC11" "POST /vision/detect wrong token -> 401" "POST" "$BASE/vision/detect" "$EV_DIR\TC10.body.json" 401 "POST /vision/detect (wrong token)" $H_BAD

# TC12
$body12 = '{"image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-13T07:30:00Z"}'
$body12 | Out-File -FilePath "$EV_DIR\TC12.body.json" -Encoding UTF8
Run-Case "TC12" "POST /vision/detect missing camera_id -> 422" "POST" "$BASE/vision/detect" "$EV_DIR\TC12.body.json" 422 "POST /vision/detect (no camera_id)" $H_JSON

# TC13
$body13 = '{"camera_id":"cam-gate-01","timestamp":"2026-08-13T07:30:00Z"}'
$body13 | Out-File -FilePath "$EV_DIR\TC13.body.json" -Encoding UTF8
Run-Case "TC13" "POST /vision/detect missing image -> 422" "POST" "$BASE/vision/detect" "$EV_DIR\TC13.body.json" 422 "POST /vision/detect (no image)" $H_JSON

# TC14
Run-Case "TC14" "GET /vision/detections/not-a-uuid -> 422" "GET" "$BASE/vision/detections/not-a-uuid" $null 422 "GET detection (bad uuid)" $H_AUTH_ONLY

# TC15
$body15 = '{"camera_id":"cam-gate-01","frame_url":"http://storage.campus.local/frames/frame-001.jpg","motion_detected":true,"timestamp":"2026-08-13T07:30:00Z"}'
$body15 | Out-File -FilePath "$EV_DIR\TC15.body.json" -Encoding UTF8
Run-Case "TC15" "POST /frames on Camera Stream mock -> 201" "POST" "http://127.0.0.1:4014/frames" "$EV_DIR\TC15.body.json" 201 "POST camera stream mock (consumer-side smoke)" $H_CAM

Write-Host ""
Write-Host "############################################################"
Write-Host "# Summary"
Write-Host "############################################################"
$pass = ($results | Where-Object { $_.Result -eq "PASS" }).Count
$fail = ($results | Where-Object { $_.Result -eq "FAIL" }).Count
Write-Host "Total: $($results.Count)  PASS: $pass  FAIL: $fail"

$results | Select-Object Id, Title, ExpectedStatus, ActualStatus, Result | Format-Table -AutoSize

$results | ConvertTo-Json -Depth 4 | Out-File "$EV_DIR\results.json" -Encoding UTF8
