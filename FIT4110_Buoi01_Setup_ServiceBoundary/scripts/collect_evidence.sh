#!/usr/bin/env bash
set -u
mkdir -p evidence/buoi-01
{
  echo "# Tool versions"; date; git --version || true; docker --version || true
  docker compose version || true; node --version || true; npm --version || true
  python --version || python3 --version || true; pip --version || pip3 --version || true
} > evidence/buoi-01/tool-versions.txt 2>&1
docker --version > evidence/buoi-01/docker-version.txt 2>&1 || true
docker compose version > evidence/buoi-01/compose-version.txt 2>&1 || true
docker run --rm hello-world > evidence/buoi-01/hello-world.txt 2>&1 || true
docker image ls --format "table {{.Repository}}:{{.Tag}}	{{.ID}}	{{.Size}}" > evidence/buoi-01/image-list.txt 2>&1 || true
git log --oneline -5 > evidence/buoi-01/git-log.txt 2>&1 || true
./scripts/smoke_test.sh || true
echo "Evidence collected in evidence/buoi-01"
