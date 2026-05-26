#!/bin/bash
set -e

# Configuration
REGION="us-west-2"
LAMBDA_NAME="dev-connect-sre-action-dispatcher"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../src"
BUILD_DIR="$SCRIPT_DIR/../build"

echo "Deploying Action Dispatcher Lambda..."

# Ensure build directory exists
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clean up old zip
rm -f action_dispatcher.zip

# Create new zip
echo "Zipping action_dispatcher.py..."
cp "$SRC_DIR/action_dispatcher.py" index.py
zip -q action_dispatcher.zip index.py

# Update Lambda function code
echo "Updating Lambda function: $LAMBDA_NAME..."
aws lambda update-function-code \
    --function-name "$LAMBDA_NAME" \
    --zip-file "fileb://action_dispatcher.zip" \
    --region "$REGION" > /dev/null

# Wait for code update to complete before changing config
echo "Waiting for code update to propagate..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION"

# Update Lambda environment variables
echo "Updating Lambda environment variables..."
aws lambda update-function-configuration \
    --function-name "$LAMBDA_NAME" \
    --environment "Variables={INCIDENT_TABLE_NAME=dev-connect-sre-incidents,APPROVAL_TABLE_NAME=dev-connect-sre-approvals,TOOL_REGISTRY_TABLE_NAME=dev-connect-sre-tool-registry,POLICY_TABLE_NAME=dev-connect-sre-policy-config,ENABLE_CONNECT_WRITE_ACTIONS=true,ENABLE_AUTONOMOUS_ACTIONS=true}" \
    --region "$REGION" > /dev/null

echo "Deployment successful."

# Clean up
rm index.py action_dispatcher.zip
cd - > /dev/null
