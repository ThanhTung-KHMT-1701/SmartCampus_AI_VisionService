#!/usr/bin/env bash
set -euo pipefail

COLLECTION="${COLLECTION:-postman/collections/FIT4110_lab03_iot_ingestion.postman_collection.json}"
ENVIRONMENT="${1:-postman/environments/FIT4110_lab03_mock.postman_environment.json}"

mkdir -p reports

npx newman run "${COLLECTION}" \
  -e "${ENVIRONMENT}" \
  --reporters cli,junit,htmlextra \
  --reporter-junit-export reports/newman-report.xml \
  --reporter-htmlextra-export reports/newman-report.html
