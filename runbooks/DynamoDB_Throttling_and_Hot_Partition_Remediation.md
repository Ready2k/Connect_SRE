# DynamoDB Throttling and Hot Partition Remediation

## Overview
This runbook covers diagnostics and immediate remediation actions for DynamoDB capacity throttling, partition exhaustion, and GSI replica lag affecting agent-runs, policy configurations, or contact flow metadata.

---

## Symptoms & Alarms
* **Alarm**: `DynamoDB-ThrottledRequests-Alert` (Spike in `ReadThrottleEvents` or `WriteThrottleEvents` metrics).
* **Symptom**: Delayed agent screen loads, high latency on API routes (`/api/incidents`), or failure to fetch agent-runs/approvals state.

---

## Step-by-Step Diagnostics

### 1. Identify Target Table & Capacity Mode
Determine which table is being throttled and check its current Billing Mode (Provisioned vs Pay-per-Request).
* **Verification Command**:
  ```bash
  aws dynamodb describe-table --table-name dev-connect-sre-topology --region us-west-2
  ```

### 2. Check for Hot Partitions
If a GSI (Global Secondary Index) or a primary key is unevenly distributed (e.g. all transactions writing to a single `incidentId`), capacity limits on a single partition (1000 WCU or 3000 RCU) may be exceeded even if total allocated billing units are high.
* Check CloudWatch metrics for individual GSIs (`by-status-createdAt`, etc.).

---

## Remediation Actions

### Action A: Scale Up Provisioned Throughput (or Switch to On-Demand)
If the table is in `PROVISIONED` billing mode and experiencing sustained spikes:
1. Temporarily change billing mode to `PAY_PER_REQUEST` (On-Demand) to handle high elastic volumes:
   ```bash
   aws dynamodb update-table \
     --table-name <Table-Name> \
     --billing-mode PAY_PER_REQUEST \
     --region us-west-2
   ```

### Action B: Add DAX or In-Memory Caching
If hot partitions are read-heavy (e.g., fetching tool definitions or active SRE policies):
* Wire in an in-memory cache (like Redis/ElastiCache or Python's `cachetools` inside the container) to prevent repeated read sweeps on the physical DynamoDB table.
