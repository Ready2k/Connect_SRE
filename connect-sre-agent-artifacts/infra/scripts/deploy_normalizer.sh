#!/bin/bash
set -e

# Configuration
REGION="us-west-2"
LAMBDA_NAME="dev-connect-sre-normalizer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../src"
BUILD_DIR="$SCRIPT_DIR/../build"

echo "Deploying Normalizer Lambda..."

# Ensure build directory exists
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clean up old zip
rm -f normalizer.zip

# Create new zip
echo "Zipping normalizer.py..."
cp "$SRC_DIR/normalizer.py" index.py
zip -q normalizer.zip index.py

# Update Lambda function code
echo "Updating Lambda function: $LAMBDA_NAME..."
aws lambda update-function-code \
    --function-name "$LAMBDA_NAME" \
    --zip-file "fileb://normalizer.zip" \
    --region "$REGION" \
    --profile connect-sre-dev > /dev/null

# Wait for code update to complete before changing config
echo "Waiting for code update to propagate..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION" \
    --profile connect-sre-dev

# Update Lambda environment variables
echo "Updating Lambda environment variables..."
aws lambda update-function-configuration \
    --function-name "$LAMBDA_NAME" \
    --environment "Variables={INCIDENT_TABLE_NAME=dev-connect-sre-incidents,EVIDENCE_BUCKET_NAME=dev-connect-sre-evidence-388660028061-us-west-2,TOPOLOGY_REFRESH_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/388660028061/dev-connect-sre-topology-refresh,AGENT_API_URL=http://localhost:8000,CONNECT_INSTANCE_ID=8dc186bb-1a4b-42ab-b91b-d8acd52f00fc,DEDUPE_WINDOW_MINUTES=30}" \
    --region "$REGION" \
    --profile connect-sre-dev > /dev/null

echo "Deployment successful."

# Clean up
rm index.py normalizer.zip
cd - > /dev/null
