# FIT4110 Lab05 - Contract Smoke Test cho AI Vision Docker Service
# Chạy 14 requests nhanh để verify service thật đang chạy đúng.
# Dùng Invoke-WebRequest (không cần newman) — chạy được trên mọi Windows.
#
# Usage:
#   .\scripts\contract-smoke.ps1
#
# Prerequisites:
#   - Docker container dao`ng:  docker compose up -d
#   - AI Vision Service listening at 127.0.0.1:8000
#   - Camera Stream mock listening at 192.168.137.115:8001 (cho consumer-side smoke)

$ErrorActionPreference = "Continue"
$TOKEN = "local-dev-token-vision"
$BASE  = "http://127.0.0.1:8000"

function Run-Request {
    param(
        [string]$Title,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$ExpectedStatus = 0
    )
    try {
        $reqHeaders = @{}
        foreach ($k in $Headers.Keys) { $reqHeaders[$k] = $Headers[$k] }
        if (-not $reqHeaders.ContainsKey("Content-Type") -and $Body) {
            $reqHeaders["Content-Type"] = "application/json"
        }
        $params = @{ Uri = $Url; Method = $Method; Headers = $reqHeaders; UseBasicParsing = $true }
        if ($Body) { $params.Body = $Body }
        if ($PSVersionTable.PSVersion.Major -ge 7) {
            $params.SkipHttpErrorCheck = $true
        }
        $resp = Invoke-WebRequest @params
        $code = [int]$resp.StatusCode
        $text = $resp.Content
    } catch {
        $code = 0
        try { $code = [int]$_.Exception.Response.StatusCode } catch {}
        $text = ""
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $text = $reader.ReadToEnd()
        } catch {}
    }
    $marker = if ($ExpectedStatus -eq 0) { "" } elseif ($code -eq $ExpectedStatus) { " [PASS]" } else { " [FAIL expected $ExpectedStatus]" }
    Write-Host ""
    Write-Host "=== $Title$marker ==="
    Write-Host "HTTP $code"
    Write-Host $text
}

Write-Host "###################################################################"
Write-Host "# AI Vision Service - Contract Smoke Test (Docker real :8000)"
Write-Host "# $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "###################################################################"

# 1. Health check
Run-Request "1) GET /health (public -> 200)" GET "$BASE/health" @{} $null 200

# 2. Detect - valid
$body = @{
    camera_id = "cam-lab05-gate"
    image_url = "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest"
    timestamp = "2026-08-25T08:00:00Z"
    confidence_threshold = 0.6
} | ConvertTo-Json
Run-Request "2) POST /vision/detect (valid -> 200)" POST "$BASE/vision/detect" @{Authorization="Bearer $TOKEN"} $body 200

# 3. Detect - missing timestamp (422)
$body2 = @{ camera_id="cam-lab05-gate"; image_url="http://example.com/f.jpg" } | ConvertTo-Json
Run-Request "3) POST /vision/detect (missing timestamp -> 422)" POST "$BASE/vision/detect" @{Authorization="Bearer $TOKEN"} $body2 422

# 4. Detect - bad camera_id (422)
$body3 = @{ camera_id="BAD ID WITH SPACE"; image_url="http://example.com/f.jpg"; timestamp="2026-08-25T08:00:00Z" } | ConvertTo-Json
Run-Request "4) POST /vision/detect (bad camera_id -> 422)" POST "$BASE/vision/detect" @{Authorization="Bearer $TOKEN"} $body3 422

# 5. Detect - both image_url AND image_base64 (422)
$body4 = @{ camera_id="cam-lab05-01"; image_url="http://example.com/f.jpg"; image_base64="aGVsbG8="; timestamp="2026-08-25T08:00:00Z" } | ConvertTo-Json
Run-Request "5) POST /vision/detect (both images -> 422)" POST "$BASE/vision/detect" @{Authorization="Bearer $TOKEN"} $body4 422

# 6. Detect - missing token (401)
Run-Request "6) POST /vision/detect (no token -> 401)" POST "$BASE/vision/detect" @{} $body 401

# 7. Detect - wrong token (401)
Run-Request "7) POST /vision/detect (wrong token -> 401)" POST "$BASE/vision/detect" @{Authorization="Bearer wrong-token"} $body 401

# 8. Get detection by id (200) - lay detection_id tu ket qua buoc 2
$detectResp = Invoke-RestMethod -Uri "$BASE/vision/detect" -Method POST `
    -Headers @{Authorization="Bearer $TOKEN"; "Content-Type"="application/json"} `
    -Body $body
$DET_ID = $detectResp.detection_id
Run-Request "8) GET /vision/detections/$DET_ID (valid -> 200)" GET "$BASE/vision/detections/$DET_ID" @{Authorization="Bearer $TOKEN"} $null 200

# 9. Get detection - random uuid (404)
Run-Request "9) GET detection (not found -> 404)" GET "$BASE/vision/detections/00000000-0000-0000-0000-000000000000" @{Authorization="Bearer $TOKEN"} $null 404

# 10. Get detection - invalid uuid format (422)
Run-Request "10) GET detection (bad uuid -> 422)" GET "$BASE/vision/detections/not-a-uuid" @{Authorization="Bearer $TOKEN"} $null 422

# 11. GET /vision/results/recent (200)
Run-Request "11) GET /vision/results/recent?limit=5 -> 200" GET "$BASE/vision/results/recent?limit=5" @{Authorization="Bearer $TOKEN"} $null 200

# 12. Face-match - valid (200)
$bodyFM = @{
    image_url            = "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest"
    reference_image_url  = "http://192.168.137.79:8001/profiles/student-001.jpg"
    threshold            = 0.7
    trace_id             = "trace-lab05-smoke"
    timestamp            = "2026-08-25T08:00:00Z"
} | ConvertTo-Json
Run-Request "12) POST /vision/face-match (valid -> 200)" POST "$BASE/vision/face-match" @{Authorization="Bearer $TOKEN"} $bodyFM 200

# 13. Face-match - high threshold (>=0.9 -> low confidence stub returns 0.45) (200)
$bodyFM2 = @{
    image_url            = "http://192.168.137.115:8001/cameras/cam-lab05-gate/frames/latest"
    reference_image_url  = "http://192.168.137.79:8001/profiles/student-001.jpg"
    threshold            = 0.95
    timestamp            = "2026-08-25T08:00:00Z"
} | ConvertTo-Json
Run-Request "13) POST /vision/face-match (high threshold -> 200, matched=false)" POST "$BASE/vision/face-match" @{Authorization="Bearer $TOKEN"} $bodyFM2 200

# 14. GET /vision/models/info (200)
Run-Request "14) GET /vision/models/info -> 200" GET "$BASE/vision/models/info" @{Authorization="Bearer $TOKEN"} $null 200

# 15. GET /vision/results/recent limit=101 (422)
Run-Request "15) GET /vision/results/recent?limit=101 -> 422" GET "$BASE/vision/results/recent?limit=101" @{Authorization="Bearer $TOKEN"} $null 422

Write-Host ""
Write-Host "###################################################################"
Write-Host "# End of contract smoke test  ($(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))"
Write-Host "###################################################################"
