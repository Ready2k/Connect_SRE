# Amazon Connect Contact Flow Regression Triage

## Overview
This runbook describes the standard operating procedures for triaging and remediating Contact Flow execution errors, high drop rates, and telephony degradation inside Amazon Connect.

---

## Symptoms & Alarms
* **Alarm**: `Connect-Contact-Flow-Fatal-Errors-Alert` (Spike in `ContactFlowErrors` or `ContactFlowFatalErrors` metrics).
* **Symptom**: Customers experience silent drops, disconnected calls immediately after routing, or generic error prompts ("An error has occurred...").

---

## Step-by-Step Diagnostics

### 1. Check Lambda Integrations
Connect flows often rely heavily on AWS Lambda for data dips (e.g., fetching customer profiles, validating balances). 
* Check if a recent Lambda update introduced syntax errors, timed out (> 8 seconds, which is Connect's hard timeout limit), or exceeded concurrency limits.
* **Verification Command**:
  ```bash
  aws lambda get-function-configuration --function-name <Function-Name> --region us-west-2
  ```

### 2. Verify Prompt & Queue Configuration
Ensure all prompt IDs and queue ARNs referenced in the flow actually exist in the environment. Flow imports from other environments (e.g., Staging to Prod) frequently carry hardcoded IDs that fail in the target environment.

### 3. Analyze Telephony Limits
* Telephony limits like Max Concurrent Calls or telephony port capacity may be exhausted.
* Check CloudWatch metrics for `ConcurrentCalls` and `CallsDropped` to determine if capacity boundaries have been exceeded.

---

## Remediation Actions

### Action A: Rollback Flow to Previous Version
If a recent deployment caused the regression, roll back to the previously active flow version:
1. In the Amazon Connect Admin Console, navigate to **Routing > Contact Flows**.
2. Select the affected flow.
3. Click the **Versions** tab.
4. Select the last known-good version and click **Publish**.

### Action B: Disable Non-Critical Data Dips
If a third-party API or Lambda integration is down:
1. Edit the contact flow.
2. Route the **Error** output of the affected **Invoke AWS Lambda Function** block to a backup prompt and standard queue rather than dropping the call.
3. Click **Save** and **Publish**.
