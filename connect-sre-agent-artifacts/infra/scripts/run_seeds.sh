#!/bin/bash
# Runs all seed scripts in dependency order:
#   1. Policies & tool registry (no AWS dependencies)
#   2. Journeys
#   3. Topology (seed static data, then trigger scanner if instance IDs supplied)
#   4. Runbooks (S3 upload)
set -e

REGION=${AWS_REGION:-"us-west-2"}
ENVIRONMENT=${ENVIRONMENT_NAME:-"dev"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/../src" && pwd)"
PROFILE=${AWS_PROFILE:-"connect-sre-dev"}

echo "=========================================================="
echo " Connect SRE Agent — Seed All"
echo " Environment : $ENVIRONMENT"
echo " Region      : $REGION"
echo " Profile     : $PROFILE"
echo "=========================================================="
echo ""

# Activate virtualenv if present alongside the src directory
VENV="$SRC_DIR/../venv"
if [ -d "$VENV" ]; then
  # shellcheck disable=SC1090
  source "$VENV/bin/activate"
fi

run_python() {
  local label="$1"; shift
  echo "[$label] Running $*"
  AWS_PROFILE="$PROFILE" python "$@"
  echo "[$label] Done."
  echo ""
}

# 1. Policies
run_python "1/4 policies" "$SRC_DIR/seed_policies.py"

# 2. Tool registry
run_python "2/4 tools  " "$SRC_DIR/seed_tools.py"

# 3. Journeys
run_python "3/4 journey" "$SRC_DIR/seed_journeys.py"

# 4. Topology (static seed data only — topology scanner is triggered separately
#    once real Connect instance IDs are known)
run_python "4/5 topo   " "$SRC_DIR/seed_topology.py"

# 5. Runbooks (S3 upload) — only run if the runbooks directory exists
if [ -d "$SCRIPT_DIR/../runbooks" ]; then
  echo "[5/5 runbook] Uploading runbooks to S3..."
  bash "$SCRIPT_DIR/upload_runbooks.sh"
  echo "[5/5 runbook] Done."
  echo ""
else
  echo "[5/5 runbook] Skipped — $SCRIPT_DIR/../runbooks not found."
  echo ""
fi

echo "=========================================================="
echo " All seeds complete."
echo ""
echo " Next steps:"
echo "   • If you have real Connect instance IDs, run the topology scanner:"
echo "     CONNECT_INSTANCE_IDS=<uuid> python $SRC_DIR/topology_scanner.py"
echo "   • Or trigger via the UI 'Run Discovery' button once the agent is running."
echo "=========================================================="
