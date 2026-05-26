# Q in Connect (QinConnect) Assistant Latency and Sync Triage

## Overview
This runbook provides details on diagnosing and troubleshooting latency spikes, knowledge base out-of-sync states, and query failures for Amazon Q in Connect assistant integrations.

---

## Symptoms & Alarms
* **Alarm**: `Q-In-Connect-Latency-Limit-Exceeded` (Assistant latency > 3 seconds).
* **Symptom**: Agents experience blank panels in the CCP, delayed recommendations during live calls, or failed document retrieval notifications.

---

## Step-by-Step Diagnostics

### 1. Check Knowledge Base Sync Status
When document sync fails, Q cannot return relevant recommendations or experiences high lookup latency.
* Check the synchronization status of the Knowledge Base in the Amazon Connect console.
* **Verification Command**:
  ```bash
  aws wisdom list-knowledge-bases --region us-west-2
  ```

### 2. Verify Document Parsing and S3 Ingestion Errors
If Q in Connect is linked to an S3 bucket:
* Check for parsing failures (e.g., extremely large PDF/HTML files, malformed markup, or invalid file extensions).
* Verify that the S3 bucket's KMS Key grants read permission to the Q service principal (`wisdom.amazonaws.com`).

---

## Remediation Actions

### Action A: Trigger Knowledge Base Sync
Force a resync of the knowledge base to re-ingest any stuck S3 changes:
```bash
aws wisdom start-content-association-sync \
  --knowledge-base-id <KB-ID> \
  --association-id <Association-ID> \
  --region us-west-2
```

### Action B: CCP Cache Flush & Session Reset
If the CCP is returning stale or slow agent recommendation frames:
1. Advise agents to clear browser localStorage for the Connect instance domain.
2. Force a refresh of the CCP window to establish a fresh WebSocket session to the Wisdom streaming endpoint.
