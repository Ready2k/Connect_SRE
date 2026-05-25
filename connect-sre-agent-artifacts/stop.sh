#!/usr/bin/env bash
set -e

EXISTING=$(docker ps -q --filter ancestor=connect-sre-agent-runtime:latest)

if [[ -z "$EXISTING" ]]; then
  echo "No running container found."
  exit 0
fi

echo "Stopping Connect SRE Agent Runtime..."
docker stop "$EXISTING" > /dev/null
echo "Stopped."
