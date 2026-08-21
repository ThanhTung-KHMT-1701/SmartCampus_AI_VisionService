#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:4010}"
AUTH_HEADER="Authorization: Bearer test-token"

echo "[Lab02] Testing Prism mock server at $BASE_URL"
echo

echo "[1/5] Happy path: GET /health"
curl -i "$BASE_URL/health"
echo "
---"

echo "[2/5] Happy path: GET /alerts/recent"
curl -i "$BASE_URL/alerts/recent" -H "$AUTH_HEADER"
echo "
---"

echo "[3/5] Happy path: POST /alerts"
curl -i -X POST "$BASE_URL/alerts" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceService": "core-business",
    "alertType": "UNAUTHORIZED_ACCESS",
    "severity": "HIGH",
    "message": "Phat hien truy cap trai phep tai cong chinh",
    "relatedEventId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc"
  }'
echo "
---"

echo "[4/5] Error case: GET /alerts/recent without token"
curl -i "$BASE_URL/alerts/recent"
echo "
---"

echo "[5/5] Error case: POST /alerts invalid payload"
curl -i -X POST "$BASE_URL/alerts" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{ "alertType": 12345 }'
echo
