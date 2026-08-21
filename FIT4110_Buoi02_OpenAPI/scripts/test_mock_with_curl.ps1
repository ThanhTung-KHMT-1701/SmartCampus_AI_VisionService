$ErrorActionPreference = "Stop"

$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:4010" }
$AuthHeader = "Authorization: Bearer test-token"

Write-Host "[Lab02] Testing Prism mock server at $BaseUrl"
Write-Host ""

Write-Host "[1/5] Happy path: GET /health"
curl.exe -i "$BaseUrl/health"
Write-Host "`n---"

Write-Host "[2/5] Happy path: GET /alerts/recent"
curl.exe -i "$BaseUrl/alerts/recent" -H $AuthHeader
Write-Host "`n---"

Write-Host "[3/5] Happy path: POST /alerts"
$payload = '{
  "sourceService": "core-business",
  "alertType": "UNAUTHORIZED_ACCESS",
  "severity": "HIGH",
  "message": "Phat hien truy cap trai phep tai cong chinh",
  "relatedEventId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc"
}'
curl.exe -i -X POST "$BaseUrl/alerts" -H $AuthHeader -H "Content-Type: application/json" -d $payload
Write-Host "`n---"

Write-Host "[4/5] Error case: GET /alerts/recent without token"
curl.exe -i "$BaseUrl/alerts/recent"
Write-Host "`n---"

Write-Host "[5/5] Error case: POST /alerts invalid payload"
curl.exe -i -X POST "$BaseUrl/alerts" -H $AuthHeader -H "Content-Type: application/json" -d '{ "alertType": 12345 }'
Write-Host ""
