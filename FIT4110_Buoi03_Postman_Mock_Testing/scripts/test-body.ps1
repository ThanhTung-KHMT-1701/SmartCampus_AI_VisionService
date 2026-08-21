$argList = @("request", "POST", "http://127.0.0.1:8000/vision/detect",
    "-H", "Authorization:Bearer local-dev-token-vision",
    "-H", "Content-Type:application/json",
    "-d", '{"camera_id":"cam-gate-01","image_url":"http://storage.campus.local/images/frame-001.jpg","timestamp":"2026-08-13T07:30:00Z","confidence_threshold":0.6}'
)
$stdoutRaw = & postman @argList 2>&1 | Out-String
Write-Host "==RAW=="
Write-Host $stdoutRaw
