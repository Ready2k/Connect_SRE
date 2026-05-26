#!/bin/bash
set -e

REGION="us-west-2"
LAMBDA_NAME="dev-connect-sre-normalizer"
PROFILE_ARG=${AWS_PROFILE:+--profile "$AWS_PROFILE"}

echo "Invoking Normalizer Lambda with synthetic CloudWatch alarm event..."

PAYLOAD=$(cat <<EOF
{
  "source": "aws.cloudwatch",
  "detail-type": "CloudWatch Alarm State Change",
  "detail": {
    "alarmName": "Test-Connect-Fatal-Errors",
    "state": {
      "value": "ALARM",
      "reason": "Threshold Crossed: 1 out of the last 1 datapoints [5.0 (25/05/26 12:00:00)] was greater than or equal to the threshold (1.0)."
    },
    "configuration": {
      "metrics": [
        {
          "metricStat": {
            "metric": {
              "metricName": "ContactFlowFatalErrors",
              "dimensions": {
                "InstanceId": "8dc186bb-1a4b-42ab-b91b-d8acd52f00fc",
                "ContactFlowId": "mock-flow-12345"
              }
            }
          }
        }
      ]
    }
  }
}
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
