#!/usr/bin/env bash
set -euo pipefail

mkdir -p evidence/buoi-02/mock-screenshots

echo "[Lab02] Collecting tool versions..."
{
  echo "# Tool versions"
  echo
  echo "## Node"
  node --version || true
  echo
  echo "## npm"
  npm --version || true
  echo
  echo "## Spectral"
  spectral --version || true
  echo
  echo "## Prism"
  prism --version || true
} > evidence/buoi-02/tool-versions.txt

echo "[Lab02] Running Spectral lint..."
set +e
spectral lint openapi.yaml --ruleset campus-spectral.yaml --format text > evidence/buoi-02/spectral-report.txt
LINT_EXIT=$?
set -e

echo "[Lab02] Collecting git log..."
git log --oneline -n 10 > evidence/buoi-02/git-log.txt || true

if [ "$LINT_EXIT" -ne 0 ]; then
  echo "[Lab02] Spectral found errors/warnings. Check evidence/buoi-02/spectral-report.txt"
  exit "$LINT_EXIT"
fi

echo "[Lab02] Done. Evidence saved to evidence/buoi-02/"
