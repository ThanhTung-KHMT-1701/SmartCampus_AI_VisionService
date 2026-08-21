#!/usr/bin/env bash
set -euo pipefail

spectral lint openapi.yaml --ruleset campus-spectral.yaml
