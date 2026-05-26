# EventBridge Rule Failures and DLQ Alerts Triage

## Overview
This runbook covers diagnostics and immediate remediation actions for EventBridge failed invocations, rule triggers, and redriving messages stuck in SQS Dead Letter Queues (DLQs).

---

## Symptoms & Alarms
* **Alarm**: `EventBridge-FailedInvocations-Spike` (Failed invocations on Connect alarm routing rules).
* **Alarm**: `SQS-DLQ-VisibleMessages-Spike` (Messages accumulated in `dev-connect-sre-dlq` or similar queues).

---

## Step-by-Step Diagnostics

### 1. Inspect EventBridge Rule Target Configuration
If EventBridge cannot invoke a target (e.g. SQS queue or Lambda function):
* Check if target permissions are correct. For SQS, the queue policy must allow the EventBridge service principal (`events.amazonaws.com`) to run `sqs:SendMessage`.
* Check rule target details:
  ```bash
  aws events list-targets-by-rule \
    --rule <Rule-Name> \
    --region us-west-2
  ```

### 2. Check SQS Queue Policy
Verify that the SQS queue policy has the correct SID allowing EventBridge to push events.

---

## Remediation Actions

### Action A: Fix SQS Queue Policy Permissions
If the queue policy is blocking EventBridge:
1. Apply a corrected SQS queue policy that allows EventBridge rule execution:
   ```json
   {
     "Sid": "AllowEventBridgePublish",
     "Effect": "Allow",
     "Principal": {
       "Service": "events.amazonaws.com"
     },
     "Action": "sqs:SendMessage",
     "Resource": "arn:aws:sqs:us-west-2:388660028061:dev-connect-sre-topology-refresh"
   }
   ```

### Action B: Redrive Messages from DLQ
If EventBridge failed and dumped messages to the Dead Letter Queue:
1. Troubleshoot and fix the primary queue or Lambda downstream.
2. Once the target is healthy, trigger an SQS message redrive task in the AWS SQS Console or via script to push the accumulated DLQ payloads back into the primary SQS queue for processing.
