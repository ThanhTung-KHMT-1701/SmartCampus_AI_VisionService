#!/usr/bin/env bash
set -u
mkdir -p evidence/buoi-01
LOG=evidence/buoi-01/smoke-test-result.txt
: > "$LOG"
pass(){ printf "[PASS] %s
" "$1" | tee -a "$LOG"; }
warn(){ printf "[WARN] %s
" "$1" | tee -a "$LOG"; }
fail(){ printf "[FAIL] %s
" "$1" | tee -a "$LOG"; }
require_cmd(){ command -v "$1" >/dev/null 2>&1 && pass "$1 installed" || fail "$1 missing"; }
run_check(){ local label="$1"; shift; "$@" >>"$LOG" 2>&1 && pass "$label" || fail "$label"; }
cleanup(){ docker compose -f compose/docker-compose.smoke.yml down >>"$LOG" 2>&1 || true; }
trap cleanup EXIT

echo "== Tool checks ==" | tee -a "$LOG"
require_cmd git; require_cmd docker; require_cmd node
if command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1; then pass "python installed"; else warn "python missing"; fi

echo "== Docker checks ==" | tee -a "$LOG"
run_check "docker CLI" docker --version
run_check "docker compose v2" docker compose version
run_check "docker daemon ready" docker info
run_check "hello-world container" docker run --rm hello-world

echo "== Compose mini-stack ==" | tee -a "$LOG"
if docker compose -f compose/docker-compose.smoke.yml up -d >>"$LOG" 2>&1; then
  sleep 6
  curl -fsS http://localhost:8081 >/dev/null 2>&1 && pass "nginx reachable on localhost:8081" || fail "nginx unreachable on localhost:8081"
  curl -fsS http://localhost:5000/v2/ >/dev/null 2>&1 && pass "registry reachable on localhost:5000" || fail "registry unreachable on localhost:5000"
  docker compose -f compose/docker-compose.smoke.yml ps >>"$LOG" 2>&1 || true
else
  fail "compose mini-stack could not start; check ports 8081 and 5000"
fi

echo "ALL CHECKS FINISHED" | tee -a "$LOG"
