#!/bin/bash
set -e

REGION="us-west-2"
TOOL_TABLE="dev-connect-sre-tool-registry"
POLICY_TABLE="dev-connect-sre-policy-config"
ACTION_TYPE="connect_toggle_emergency_routing"

echo "Seeding Tool Registry table..."
aws dynamodb put-item \
    --table-name "$TOOL_TABLE" \
    --region "$REGION" \
    --item '{
        "toolId": {"S": "'"$ACTION_TYPE"'"},
        "enabled": {"BOOL": true},
        "description": {"S": "Toggles emergency routing mode for Amazon Connect flows."}
    }'

echo "Seeding Policy Config table..."
aws dynamodb put-item \
    --table-name "$POLICY_TABLE" \
    --region "$REGION" \
    --item '{
        "policyId": {"S": "'"$ACTION_TYPE"'"},
        "riskLevel": {"S": "high"},
        "requiresApproval": {"BOOL": true}
    }'

echo "Successfully seeded tool registry and policy tables for '$ACTION_TYPE'."
