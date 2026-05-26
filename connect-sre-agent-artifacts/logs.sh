#!/usr/bin/env bash
set -e

FOLLOW=false
TAIL_LINES=100

usage() {
  echo "Usage: $0 [-f] [-n <lines>]"
  echo "  -f          Follow log output (tail -f mode)"
  echo "  -n <lines>  Number of tail lines to show (default: 100)"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--follow) FOLLOW=true; shift ;;
    -n|--lines)  TAIL_LINES="$2"; shift 2 ;;
    -h|--help)   usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

CONTAINER=$(docker ps -q --filter publish=8000)
if [[ -z "$CONTAINER" ]]; then
  CONTAINER=$(docker ps -q --filter ancestor=connect-sre-agent-runtime:latest)
fi

if [[ -z "$CONTAINER" ]]; then
  echo "No running container found."
  exit 1
fi

DOCKER_ARGS=(--tail "$TAIL_LINES")
if [[ "$FOLLOW" == "true" ]]; then
  DOCKER_ARGS+=(-f)
fi

docker logs "${DOCKER_ARGS[@]}" "$CONTAINER"
