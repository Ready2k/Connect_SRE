#!/usr/bin/env bash
set -e

echo "Connect SRE Agent Runtime"
echo "-------------------------"
echo ""
echo "Select startup mode:"
echo "  1) Demo  — no API keys or AWS required, all data is mocked"
echo "  2) Live  — real AWS / AI provider (requires credentials)"
echo "  3) Both  — real AI provider, but UI can toggle between demo and live data"
read -rp "Mode [1-3, default: 1]: " MODE_CHOICE
echo ""

DOCKER_ARGS=(
  -d
  -p 8000:8000
  -v ~/.aws:/root/.aws:ro
  -e AWS_PROFILE=connect-sre-runtime
  -e AWS_REGION=us-west-2
  -e AGENT_STEPS_TABLE_NAME=dev-connect-sre-agent-steps
  -e MEMORY_TABLE_NAME=dev-connect-sre-memory
  -e RUNBOOK_BUCKET_NAME=dev-connect-sre-runbooks-388660028061-us-west-2
)

case "${MODE_CHOICE:-1}" in
  2|3)
    APP_MODE="live"
    [[ "${MODE_CHOICE}" == "3" ]] && APP_MODE="both"

    echo "Select model provider:"
    echo "  1) Gemini  (Google AI — requires GEMINI_API_KEY)"
    echo "  2) Bedrock (AWS / Anthropic Claude — uses mounted AWS profile)"
    read -rp "Choice [1-2, default: 1]: " PROVIDER_CHOICE
    echo ""

    case "${PROVIDER_CHOICE:-1}" in
      2)
        echo "Available Claude models on Bedrock:"
        echo "  a) us.anthropic.claude-sonnet-4-6  (Claude Sonnet 4.6 — recommended, geo inference)"
        echo "  b) us.anthropic.claude-opus-4-7    (Claude Opus 4.7 — most capable, geo inference)"
        echo "  c) us.anthropic.claude-haiku-4-5-20251001-v1:0  (Claude Haiku 4.5 — fastest/cheapest, geo inference)"
        echo "  Or type a full model ID to use any other."
        read -rp "Model [a-c or full ID, default: a]: " MODEL_CHOICE
        echo ""

        case "${MODEL_CHOICE:-a}" in
          a|"") BEDROCK_MODEL_ID="us.anthropic.claude-sonnet-4-6" ;;
          b)    BEDROCK_MODEL_ID="us.anthropic.claude-opus-4-7" ;;
          c)    BEDROCK_MODEL_ID="us.anthropic.claude-haiku-4-5-20251001-v1:0" ;;
          *)    BEDROCK_MODEL_ID="$MODEL_CHOICE" ;;
        esac

        echo "Mode     : $APP_MODE"
        echo "Provider : Bedrock"
        echo "Model    : $BEDROCK_MODEL_ID"
        DOCKER_ARGS+=(-e APP_MODE="$APP_MODE" -e MODEL_PROVIDER=bedrock -e BEDROCK_MODEL_ID="$BEDROCK_MODEL_ID")
        ;;

      *)
        read -rsp "Enter GEMINI_API_KEY: " GEMINI_API_KEY
        echo ""
        if [[ -z "$GEMINI_API_KEY" ]]; then
          echo "Error: GEMINI_API_KEY cannot be empty."
          exit 1
        fi
        echo "Mode     : $APP_MODE"
        echo "Provider : Gemini"
        DOCKER_ARGS+=(-e APP_MODE="$APP_MODE" -e MODEL_PROVIDER=gemini -e GEMINI_API_KEY="$GEMINI_API_KEY")
        ;;
    esac
    ;;

  *)
    echo "Mode     : demo (no API keys required)"
    DOCKER_ARGS+=(-e APP_MODE=demo -e MODEL_PROVIDER=demo)
    ;;
esac

echo ""

# Stop any existing container (find by port binding to catch stale builds)
EXISTING=$(docker ps -q --filter publish=8000)
if [[ -z "$EXISTING" ]]; then
  EXISTING=$(docker ps -q --filter ancestor=connect-sre-agent-runtime:latest)
fi
if [[ -n "$EXISTING" ]]; then
  echo "Stopping existing container..."
  docker stop "$EXISTING" > /dev/null
fi

echo "Starting Connect SRE Agent Runtime..."
docker run "${DOCKER_ARGS[@]}" connect-sre-agent-runtime:latest

echo "Runtime available at http://localhost:8000"
