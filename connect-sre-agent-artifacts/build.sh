#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Connect SRE Agent — Build"
echo "-------------------------"
echo ""
echo "Building connect-sre-agent-runtime:latest..."
docker build \
  -f "$SCRIPT_DIR/runtime/Dockerfile" \
  -t connect-sre-agent-runtime:latest \
  "$SCRIPT_DIR"

echo ""
echo "Build complete."
