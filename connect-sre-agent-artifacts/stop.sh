#!/usr/bin/env bash
set -e

# Find by port binding to catch containers started from older image builds
EXISTING=$(docker ps -q --filter publish=8000)
# Fall back to ancestor filter for containers not exposing port 8000
if [[ -z "$EXISTING" ]]; then
  EXISTING=$(docker ps -q --filter ancestor=connect-sre-agent-runtime:latest)
fi

if [[ -z "$EXISTING" ]]; then
  echo "No running container found."
  exit 0
fi

echo "Stopping Connect SRE Agent Runtime..."
docker stop "$EXISTING" > /dev/null
echo "Stopped."
