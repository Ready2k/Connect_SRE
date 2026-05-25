#!/bin/bash
# A utility script to update your AWS Security Group if your home ISP changes your public IP address.
# This re-runs the CloudFormation deploy command to update the AllowedAdminCIDR parameter cleanly.

set -e

# Change directory to the location of this script
cd "$(dirname "$0")"

STACK_NAME="dev-connect-sre-platform"
TEMPLATE_FILE="../cloudformation/connect-sre-agent-platform.yaml"

echo "Fetching your current public IP address..."
CURRENT_IP=$(curl -s http://checkip.amazonaws.com)

if [ -z "$CURRENT_IP" ]; then
    echo "Failed to fetch public IP. Check your internet connection."
    exit 1
fi

echo "Updating CloudFormation stack '$STACK_NAME' to allow traffic from $CURRENT_IP/32..."

aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --parameter-overrides EnvironmentName=dev AllowedAdminCIDR=$CURRENT_IP/32 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile connect-sre-dev

echo "Security Group successfully updated!"
