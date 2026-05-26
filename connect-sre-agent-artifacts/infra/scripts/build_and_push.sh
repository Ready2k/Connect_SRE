#!/bin/bash
# Builds the runtime Docker image and pushes it to ECR.
# Reads the ECR repository URI from the CloudFormation stack output so no
# hard-coded account IDs are needed.
set -e

REGION=${AWS_REGION:-"us-west-2"}
ENVIRONMENT=${ENVIRONMENT_NAME:-"dev"}
STACK_NAME="${ENVIRONMENT}-connect-sre-agent-platform"
PROFILE=${AWS_PROFILE:-"connect-sre-dev"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

IMAGE_TAG=${IMAGE_TAG:-"latest"}

echo "=========================================================="
echo " Connect SRE Agent — Build & Push"
echo " Environment : $ENVIRONMENT"
echo " Region      : $REGION"
echo " Profile     : $PROFILE"
echo " Tag         : $IMAGE_TAG"
echo "=========================================================="
echo ""

# 1. Resolve ECR URI from CloudFormation
echo "[1/4] Resolving ECR repository URI from CloudFormation stack '$STACK_NAME'..."
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='AgentECRRepositoryUri'].OutputValue" \
  --output text)

if [ -z "$ECR_URI" ] || [ "$ECR_URI" = "None" ]; then
  echo "ERROR: Could not find AgentECRRepositoryUri output in stack $STACK_NAME."
  echo "       Deploy the CloudFormation stack first:"
  echo "         bash $SCRIPT_DIR/deploy_all.sh"
  exit 1
fi

echo "       ECR URI: $ECR_URI"
echo ""

# Extract the registry host (account.dkr.ecr.region.amazonaws.com)
REGISTRY=$(echo "$ECR_URI" | cut -d'/' -f1)

# 2. Authenticate Docker with ECR
echo "[2/4] Authenticating Docker with ECR ($REGISTRY)..."
aws ecr get-login-password \
  --region "$REGION" \
  --profile "$PROFILE" \
  | docker login --username AWS --password-stdin "$REGISTRY"
echo ""

# 3. Build the image
echo "[3/4] Building Docker image from $ROOT_DIR/runtime/Dockerfile..."
docker build \
  --platform linux/amd64 \
  -t "connect-sre-agent-runtime:$IMAGE_TAG" \
  -f "$ROOT_DIR/runtime/Dockerfile" \
  "$ROOT_DIR"
echo ""

# 4. Tag and push
echo "[4/4] Tagging and pushing to ECR..."
docker tag "connect-sre-agent-runtime:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:$IMAGE_TAG"
echo ""

echo "=========================================================="
echo " Build & Push Complete!"
echo ""
echo " Image pushed to: $ECR_URI:$IMAGE_TAG"
echo ""
echo " To deploy: update the ECS service to force a new deployment:"
echo "   CLUSTER=\$(aws cloudformation describe-stacks --stack-name $STACK_NAME"
echo "     --query \"Stacks[0].Outputs[?OutputKey=='AgentClusterName'].OutputValue\""
echo "     --output text --region $REGION --profile $PROFILE)"
echo "   aws ecs update-service --cluster \$CLUSTER --service connect-sre-agent"
echo "     --force-new-deployment --region $REGION --profile $PROFILE"
echo "=========================================================="
