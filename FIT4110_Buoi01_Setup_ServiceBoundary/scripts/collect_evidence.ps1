$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path "evidence/buoi-01" | Out-Null
@("# Tool versions", (Get-Date), (git --version), (docker --version), (docker compose version), (node --version), (python --version)) | Out-File evidence/buoi-01/tool-versions.txt
docker --version | Out-File evidence/buoi-01/docker-version.txt
docker compose version | Out-File evidence/buoi-01/compose-version.txt
docker run --rm hello-world | Out-File evidence/buoi-01/hello-world.txt
docker image ls | Out-File evidence/buoi-01/image-list.txt
git log --oneline -5 | Out-File evidence/buoi-01/git-log.txt
.\scripts\smoke_test.ps1
