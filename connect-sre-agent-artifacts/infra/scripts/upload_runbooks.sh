#!/bin/bash
# Uploads all runbooks from runbooks/ to the S3 runbook bucket, then creates
# normalized topic alias keys so the agent can fetch them by short names like
# "lex_bot_failure" or "flow_fatal_error".
#
# The fetch_runbook tool also does a word-overlap fallback search if an exact
# key is not found, so aliases are belt-and-braces rather than strictly required.
#
# Usage:
#   ./infra/scripts/upload_runbooks.sh                    # uses dev-connect-sre-platform stack
#   STACK_NAME=prod-connect-sre-platform ./infra/scripts/upload_runbooks.sh

set -euo pipefail

PROFILE="${AWS_PROFILE:-connect-sre-dev}"
REGION="${AWS_REGION:-us-west-2}"
STACK_NAME="${STACK_NAME:-dev-connect-sre-platform}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNBOOKS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/runbooks"

echo "Resolving runbook bucket from stack $STACK_NAME..."
BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='RunbookBucketName'].OutputValue" \
    --output text \
    --profile "$PROFILE" \
    --region "$REGION" 2>/dev/null || true)

if [ -z "$BUCKET" ] || [ "$BUCKET" = "None" ]; then
    echo "ERROR: RunbookBucketName output not found in stack $STACK_NAME."
    echo "       Run 'aws cloudformation deploy ...' first, or set BUCKET manually:"
    echo "       BUCKET=my-bucket-name ./infra/scripts/upload_runbooks.sh"
    exit 1
fi

echo "Bucket: s3://$BUCKET"
echo ""

# ---------------------------------------------------------------------------
# 1. Upload original runbook files
# ---------------------------------------------------------------------------
echo "Uploading original runbook files..."
for f in "$RUNBOOKS_DIR"/*.md; do
    key=$(basename "$f")
    echo "  $key"
    aws s3 cp "$f" "s3://$BUCKET/$key" \
        --content-type "text/markdown" \
        --profile "$PROFILE" \
        --region "$REGION"
done

# ---------------------------------------------------------------------------
# 2. Create normalized topic aliases
#    Keys on the right must match filenames uploaded above.
# ---------------------------------------------------------------------------
echo ""
echo "Creating topic aliases..."

declare -A ALIASES=(
    # Contact flow errors
    ["flow_fatal_error"]="Amazon_Connect_Flow_Regression_Triage.md"
    ["flow_regression"]="Amazon_Connect_Flow_Regression_Triage.md"
    ["contact_flow_error"]="Amazon_Connect_Flow_Regression_Triage.md"
    ["connect_flow_fatal_error"]="Amazon_Connect_Flow_Regression_Triage.md"
    ["queue_overflow"]="Amazon_Connect_Flow_Regression_Triage.md"

    # Lex / NLU failures
    ["lex_bot_failure"]="Amazon_Lex_Intent_Misrouting_and_Timeouts.md"
    ["lex_intent_misrouting"]="Amazon_Lex_Intent_Misrouting_and_Timeouts.md"
    ["lex_timeout"]="Amazon_Lex_Intent_Misrouting_and_Timeouts.md"
    ["lex_failure"]="Amazon_Lex_Intent_Misrouting_and_Timeouts.md"

    # CCP / WebRTC / agent desktop
    ["ccp_failure"]="Connect_CCP_Streams_WebRTC_and_State_Failures.md"
    ["webrtc_failure"]="Connect_CCP_Streams_WebRTC_and_State_Failures.md"
    ["ccp_streams_failure"]="Connect_CCP_Streams_WebRTC_and_State_Failures.md"
    ["agent_desktop_failure"]="Connect_CCP_Streams_WebRTC_and_State_Failures.md"

    # DynamoDB
    ["dynamodb_throttling"]="DynamoDB_Throttling_and_Hot_Partition_Remediation.md"
    ["dynamodb_hot_partition"]="DynamoDB_Throttling_and_Hot_Partition_Remediation.md"
    ["table_throttling"]="DynamoDB_Throttling_and_Hot_Partition_Remediation.md"

    # EventBridge / DLQ
    ["eventbridge_failure"]="EventBridge_Rule_Failures_and_DLQ_Alerts.md"
    ["dlq_alert"]="EventBridge_Rule_Failures_and_DLQ_Alerts.md"
    ["eventbridge_dlq"]="EventBridge_Rule_Failures_and_DLQ_Alerts.md"
    ["event_routing_failure"]="EventBridge_Rule_Failures_and_DLQ_Alerts.md"

    # Lambda
    ["lambda_failure"]="Lambda_Execution_Failures_and_Throttling.md"
    ["lambda_throttling"]="Lambda_Execution_Failures_and_Throttling.md"
    ["lambda_execution_error"]="Lambda_Execution_Failures_and_Throttling.md"
    ["lambda_error"]="Lambda_Execution_Failures_and_Throttling.md"

    # Q in Connect / AI Assist
    ["q_in_connect_failure"]="Q_In_Connect_Assistant_Latency_and_Sync.md"
    ["ai_assist_failure"]="Q_In_Connect_Assistant_Latency_and_Sync.md"
    ["amazon_q_failure"]="Q_In_Connect_Assistant_Latency_and_Sync.md"
    ["q_connect_latency"]="Q_In_Connect_Assistant_Latency_and_Sync.md"
)

for alias_key in "${!ALIASES[@]}"; do
    source_key="${ALIASES[$alias_key]}"
    echo "  ${alias_key}.md  →  $source_key"
    aws s3 cp "s3://$BUCKET/$source_key" "s3://$BUCKET/${alias_key}.md" \
        --content-type "text/markdown" \
        --profile "$PROFILE" \
        --region "$REGION"
done

echo ""
TOTAL=$(aws s3 ls "s3://$BUCKET/" --profile "$PROFILE" --region "$REGION" | wc -l | tr -d ' ')
echo "Done. $TOTAL objects now in s3://$BUCKET/"
