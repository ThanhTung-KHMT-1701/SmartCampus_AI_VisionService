#!/usr/bin/env bash
set -euo pipefail

echo "[Lab02] Checking Node.js and npm..."
node --version
npm --version

echo "[Lab02] Installing Spectral CLI and Prism CLI..."
npm install -g @stoplight/spectral-cli@6.11.1 @stoplight/prism-cli@5.14.2

echo "[Lab02] Installed versions:"
spectral --version
prism --version
