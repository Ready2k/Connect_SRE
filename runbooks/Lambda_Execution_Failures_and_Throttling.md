# Lambda Execution Failures and Throttling Triage

## Overview
This runbook provides triage and mitigation steps for Lambda execution errors, timeout limits, and concurrency throttling affecting Amazon Connect integration flows.

---

## Symptoms & Alarms
* **Alarm**: `Lambda-Throttling-Alert` (Spike in Lambda `Throttles` metric).
* **Alarm**: `Lambda-Error-Rate-High-Alert` (Spike in Lambda `Errors` metric).
* **Symptom**: Connect contact flow execution routes immediately to the `Error` branch of an "Invoke AWS Lambda" block.

---

## Step-by-Step Diagnostics

### 1. Diagnose Timeout Errors
Amazon Connect has a strict maximum execution limit of **8 seconds** for Lambda calls. If your Lambda function takes 8.1 seconds, Connect terminates the connection and follows the `Error` path.
* Check CloudWatch Metrics `Duration` for the function.
* Check Lambda logs for `Task timed out` messages.

### 2. Identify Throttling / Concurrency Bottlenecks
* Telephony spikes can exhaust the Lambda function's reserved concurrency or the regional concurrency limits (default 1000).
* Check CloudWatch `Throttles` metric.

---

## Remediation Actions

### Action A: Allocate Provisioned Concurrency
To eliminate cold starts and guarantee execution instances during high call volumes:
1. Run the command to put provisioned concurrency configuration:
   ```bash
   aws lambda put-provisioned-concurrency-config \
     --function-name <Function-Name> \
     --qualifier <Alias-or-Version> \
     --provisioned-concurrent-executions 50 \
     --region us-west-2
   ```

### Action B: Add Short-Circuit / Caching Logic
If downstream databases (e.g. RDS or DynamoDB) are slow:
* Enable DynamoDB DAX or ElastiCache to reduce Lambda execution duration.
* Increase the Lambda function's timeout parameter (if < 8 seconds) up to a max of **8 seconds** (aligning with Connect's limit).
