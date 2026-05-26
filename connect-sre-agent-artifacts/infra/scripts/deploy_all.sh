#!/bin/bash
set -e

# Configuration
REGION=${AWS_REGION:-"us-west-2"}
ENVIRONMENT=${ENVIRONMENT_NAME:-"dev"}
STACK_NAME="${ENVIRONMENT}-connect-sre-agent-platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE_FILE="$ROOT_DIR/infra/cloudformation/connect-sre-agent-platform.yaml"

echo "=========================================================="
echo " Deploying Connect SRE Agent Platform"
echo " Environment: $ENVIRONMENT"
echo " Region: $REGION"
echo "=========================================================="
echo ""

# Step 1: Deploy CloudFormation (The Infrastructure Shell)
echo "[1/3] Deploying Infrastructure Shell via CloudFormation..."
aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --parameter-overrides EnvironmentName="$ENVIRONMENT"

echo ""

# Step 2: Deploy Business Logic (The Python Code)
echo "[2/3] Deploying Business Logic to Lambdas..."
"$SCRIPT_DIR/deploy_normalizer.sh"
"$SCRIPT_DIR/deploy_topology_scanner.sh"
"$SCRIPT_DIR/deploy_action_dispatcher.sh"

echo ""

# Step 3: Fix Action Dispatcher KMS permissions
echo "[3/3] Attaching KMS permissions to Action Dispatcher..."
# We run the fix script we created earlier to ensure the role has KMS access
"$SCRIPT_DIR/fix_action_dispatcher_kms.sh"

echo ""
echo "=========================================================="
echo " Deployment Complete!"
echo " Your AWS account now has the full Connect SRE Agent backend deployed."
echo "=========================================================="
