#!/bin/bash
set -e

# Configuration
REGION="us-west-2"
LAMBDA_NAME="dev-connect-sre-topology-scanner"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../src"
BUILD_DIR="$SCRIPT_DIR/../build"

PROFILE_ARG=${AWS_PROFILE:+--profile "$AWS_PROFILE"}

echo "Deploying Topology Scanner Lambda..."

# Ensure build directory exists
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clean up old zip
rm -f topology_scanner.zip

# Create new zip
echo "Zipping topology_scanner.py..."
cp "$SRC_DIR/topology_scanner.py" index.py
zip -q topology_scanner.zip index.py

# Update Lambda function code
echo "Updating Lambda function: $LAMBDA_NAME..."
aws lambda update-function-code \
    --function-name "$LAMBDA_NAME" \
    --zip-file "fileb://topology_scanner.zip" \
    --region "$REGION" \
    $PROFILE_ARG > /dev/null

# Wait for code update to complete before changing config
echo "Waiting for code update to propagate..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION" \
    $PROFILE_ARG

# Update Lambda environment variables
echo "Updating Lambda environment variables..."
aws lambda update-function-configuration \
    --function-name "$LAMBDA_NAME" \
    --environment "Variables={TOPOLOGY_TABLE_NAME=dev-connect-sre-topology}" \
    --region "$REGION" \
    $PROFILE_ARG > /dev/null

echo "Deployment successful."

# Clean up
rm index.py topology_scanner.zip
cd - > /dev/null
