#!/bin/bash
set -e

REGION="us-west-2"
LAMBDA_NAME="dev-connect-sre-topology-scanner"
PROFILE_ARG=${AWS_PROFILE:+--profile "$AWS_PROFILE"}

echo "Invoking Topology Scanner Lambda (Full Scan)..."

# Empty payload triggers a full scan
PAYLOAD=$(cat <<EOF
{}
EOF
)

# Convert payload to base64 for AWS CLI v2
PAYLOAD_B64=$(echo -n "$PAYLOAD" | base64)

aws lambda invoke \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION" \
    --payload "$PAYLOAD_B64" \
    $PROFILE_ARG \
    response.json

echo "Lambda Response:"
cat response.json
echo ""

rm response.json
