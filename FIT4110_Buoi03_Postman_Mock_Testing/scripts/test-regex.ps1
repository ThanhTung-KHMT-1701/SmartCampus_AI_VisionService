$argList = @("request", "GET", "http://127.0.0.1:8000/health")
$stdoutRaw = & postman @argList 2>&1 | Out-String
Write-Host "==RAW=="
Write-Host $stdoutRaw
Write-Host "==SPLIT=="
$stdoutRaw -split "`n" | ForEach-Object { Write-Host "[$_]" }
Write-Host "==REGEX=="
$firstLine = ($stdoutRaw -split "`n" | Select-Object -First 5) -join " | "
Write-Host "First5: $firstLine"
if ($firstLine -match "(\d{3})\s+(OK|Unauthorized|Forbidden|Not Found|Unprocessable Entity|Bad Request|Request Timeout|Payload Too Large|Too Many Requests|Internal Server Error|Service Unavailable|Created)") {
    Write-Host "MATCH: code=$($Matches[1])"
} else {
    Write-Host "NO MATCH"
}
