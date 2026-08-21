$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path "evidence/buoi-01" | Out-Null
$log = "evidence/buoi-01/smoke-test-result.txt"
"" | Out-File $log
function Pass($m){ "[PASS] $m" | Tee-Object -FilePath $log -Append }
function Fail($m){ "[FAIL] $m" | Tee-Object -FilePath $log -Append }
function Warn($m){ "[WARN] $m" | Tee-Object -FilePath $log -Append }
function CheckCmd($cmd){ if(Get-Command $cmd -ErrorAction SilentlyContinue){Pass "$cmd installed"}else{Fail "$cmd missing"} }
CheckCmd git; CheckCmd docker; CheckCmd node
if(Get-Command python -ErrorAction SilentlyContinue){Pass "python installed"}else{Warn "python missing"}
docker --version *> $null; if($LASTEXITCODE -eq 0){Pass "docker CLI"}else{Fail "docker CLI"}
docker compose version *> $null; if($LASTEXITCODE -eq 0){Pass "docker compose v2"}else{Fail "docker compose v2"}
docker info *> $null; if($LASTEXITCODE -eq 0){Pass "docker daemon ready"}else{Fail "docker daemon ready"}
docker run --rm hello-world *> $null; if($LASTEXITCODE -eq 0){Pass "hello-world container"}else{Fail "hello-world container"}
docker compose -f compose/docker-compose.smoke.yml up -d *> $null
if($LASTEXITCODE -eq 0){
  Start-Sleep -Seconds 6
  try { Invoke-WebRequest -UseBasicParsing http://localhost:8081 | Out-Null; Pass "nginx reachable on localhost:8081" } catch { Fail "nginx unreachable on localhost:8081" }
  try { Invoke-WebRequest -UseBasicParsing http://localhost:5000/v2/ | Out-Null; Pass "registry reachable on localhost:5000" } catch { Fail "registry unreachable on localhost:5000" }
}else{Fail "compose mini-stack could not start; check ports 8081 and 5000"}
docker compose -f compose/docker-compose.smoke.yml down *> $null
"ALL CHECKS FINISHED" | Tee-Object -FilePath $log -Append
