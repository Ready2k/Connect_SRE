#!/bin/bash
set -e

REGION="us-west-2"
LAMBDA_NAME="dev-connect-sre-action-dispatcher"

echo "Seeding Mock Approval Ticket into DynamoDB..."
aws dynamodb put-item \
    --table-name "dev-connect-sre-approvals" \
    --region "$REGION" \
    --item '{
        "approvalId": {"S": "mock-approval-123"},
        "status": {"S": "APPROVED"},
        "actionType": {"S": "connect_toggle_emergency_routing"},
        "incidentId": {"S": "INC-MOCK-123"}
    }' > /dev/null

echo "Invoking Action Dispatcher Lambda with mock approval..."

PAYLOAD=$(cat <<EOF
{
  "approvalId": "mock-approval-123",
  "actionType": "connect_toggle_emergency_routing",
  "parameters": {
    "InstanceId": "8dc186bb-1a4b-42ab-b91b-d8acd52f00fc",
    "ContactFlowId": "mock-flow-12345",
    "TargetState": "EMERGENCY_ON"
  },
  "operator": "jamescregeen",
  "incidentId": "INC-MOCK-123"
}
EOF
)

# Convert payload to base64 for AWS CLI v2
PAYLOAD_B64=$(echo -n "$PAYLOAD" | base64)

aws lambda invoke \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION" \
    --payload "$PAYLOAD_B64" \
    response.json

echo "Lambda Response:"
cat response.json
echo ""

rm response.json
