$ErrorActionPreference = "Continue"
$images = @("hello-world:latest","python:3.11-slim","node:20-alpine","nginx:alpine","redis:7-alpine","registry:2")
New-Item -ItemType Directory -Force -Path "evidence/buoi-01" | Out-Null
$log = "evidence/buoi-01/pull-core-result.txt"
"" | Out-File $log
foreach ($img in $images) {
  "==> Pulling $img" | Tee-Object -FilePath $log -Append
  docker pull $img 2>&1 | Tee-Object -FilePath $log -Append
  if ($LASTEXITCODE -eq 0) { "[PASS] $img" | Tee-Object -FilePath $log -Append }
  else { "[WARN] $img" | Tee-Object -FilePath $log -Append }
}
