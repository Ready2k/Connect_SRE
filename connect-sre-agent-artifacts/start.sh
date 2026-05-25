#!/usr/bin/env bash
set -e

echo "Connect SRE Agent Runtime"
echo "-------------------------"

# Prompt for Gemini API key (hidden input)
read -rsp "Enter GEMINI_API_KEY: " GEMINI_API_KEY
echo

if [[ -z "$GEMINI_API_KEY" ]]; then
  echo "Error: GEMINI_API_KEY cannot be empty."
  exit 1
fi

# Stop any existing container
EXISTING=$(docker ps -q --filter ancestor=connect-sre-agent-runtime:latest)
if [[ -n "$EXISTING" ]]; then
  echo "Stopping existing container..."
  docker stop "$EXISTING" > /dev/null
fi

echo "Starting Connect SRE Agent Runtime..."

docker run -d \
  -p 8000:8000 \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_PROFILE=connect-sre-runtime \
  -e AWS_REGION=us-west-2 \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  connect-sre-agent-runtime:latest

echo "Runtime available at http://localhost:8000"
