# Runbook Authoring Guide

Runbooks are Markdown files stored in the `runbooks/` directory and uploaded to S3. The RUNBOOK specialist agent fetches them at investigation time using `fetch_runbook(topic)`. This guide explains the file format, naming convention, how the agent discovers them, and what makes a runbook effective.

---

## How `fetch_runbook` works

`fetch_runbook(topic)` in `runtime/tools.py` does the following:

1. Attempts `S3.get_object(Bucket=RUNBOOK_BUCKET_NAME, Key=f"{topic}.md")` — exact key match first.
2. If that fails with `NoSuchKey`, it calls `S3.list_objects_v2` to get all keys in the bucket, then scores each key by counting how many words from `topic` appear in the key name, and fetches the highest-scoring match.
3. If no match scores above zero, returns an error.

**Implication:** the `topic` string the RUNBOOK specialist passes is usually derived from the incident description — e.g. `"lambda_throttle"`, `"lex_intent_misrouting"`, `"contact_flow_fatal_error"`. File names should contain the keywords the agent is likely to use.

---

## File naming convention

```
runbooks/{descriptive_name}.md
```

Use underscores, not hyphens. Keep names lowercase. The agent matches on word fragments, so `Amazon_Connect_Flow_Regression_Triage.md` matches a topic of `"contact flow regression"` or `"flow fatal error"`.

**Existing runbooks:**

| File | Topic keywords |
|---|---|
| `Amazon_Connect_Flow_Regression_Triage.md` | flow, regression, fatal, error, contact |
| `Amazon_Lex_Intent_Misrouting_and_Timeouts.md` | lex, intent, misrouting, timeout, nlu |
| `Connect_CCP_Streams_WebRTC_and_State_Failures.md` | ccp, webrtc, streams, agent, state |
| `DynamoDB_Throttling_and_Hot_Partition_Remediation.md` | dynamodb, throttle, hot, partition |
| `EventBridge_Rule_Failures_and_DLQ_Alerts.md` | eventbridge, rule, dlq, dead letter |
| `Lambda_Execution_Failures_and_Throttling.md` | lambda, execution, throttle, timeout |
| `Q_In_Connect_Assistant_Latency_and_Sync.md` | q, qconnect, wisdom, latency, sync, kb |

---

## Required structure

Every runbook must have these sections. The agent reads the full markdown so well-structured headings help it extract the right information.

```markdown
# {Title}

## Overview
One paragraph describing the failure mode this runbook covers and when it applies.

---

## Symptoms & Alarms
Bullet list of CloudWatch alarm names, metric names, or observable symptoms that indicate this runbook is relevant.

---

## Step-by-Step Diagnostics
Numbered or sub-headed diagnostic steps. Include:
- What to check first
- AWS CLI commands for verification (with --region us-west-2)
- What output indicates healthy vs. degraded

---

## Remediation Actions

### Action A: {Short label}
Step-by-step instructions for the primary remediation path.

### Action B: {Short label}
Fallback or alternative remediation.
```

---

## Writing effective runbooks

**Be specific about alarm names.** The agent correlates the runbook content with the incident. If your alarm is named `Connect-Flow-Fatal-Errors-Prod`, include that string in the Symptoms section.

**Include AWS CLI verification commands.** The agent cannot execute shell commands, but it reads the commands and includes them in the justification it presents to the operator for manual verification.

**Name actions explicitly.** The RISK specialist reads the remediation actions to evaluate blast radius. Vague action descriptions ("fix the issue") produce poor risk assessments.

**Keep the blast radius visible.** State which resources are affected and at what scope — e.g. "This rollback affects all contacts currently routed through BillingFlow (~200 contacts/hour)."

**Avoid external URLs.** The agent cannot fetch external content. Self-contained runbooks produce better results.

---

## Deploying runbooks

Runbooks are loaded into the Docker container at build time (`COPY runbooks/ /app/runbooks/`) for local/dev use, and uploaded to S3 for production.

### Upload to S3

```bash
# Upload all runbooks
aws s3 sync runbooks/ s3://<RUNBOOK_BUCKET_NAME>/ \
  --profile connect-sre-dev \
  --include "*.md"

# Upload a single new runbook
aws s3 cp runbooks/My_New_Runbook.md s3://<RUNBOOK_BUCKET_NAME>/ \
  --profile connect-sre-dev
```

The bucket name is the `RUNBOOK_BUCKET_NAME` CloudFormation output (also set as an ECS task environment variable). Find it with:

```bash
aws cloudformation describe-stacks \
  --stack-name dev-connect-sre-platform \
  --query "Stacks[0].Outputs[?OutputKey=='RunbookBucketName'].OutputValue" \
  --output text \
  --profile connect-sre-dev
```

### Verify the agent can fetch a runbook

In the running container:
```bash
docker exec <container_id> python3 -c "
from tools import fetch_runbook
import json
result = json.loads(fetch_runbook('flow regression'))
print(result.get('content', result.get('message', 'error'))[:500])
"
```

---

## Example runbook

```markdown
# Q Connect AI Agent Invocation Failure

## Overview
Covers failures where a Q Connect ORCHESTRATION AI Agent stops handling
contacts — typically a Bedrock model error, a broken prompt version, or
a Lex runtime crash.

---

## Symptoms & Alarms
* Alarm: `QConnect-AI-Agent-InvocationErrors` (Bedrock InvocationClientErrors > 5/min).
* Symptom: Contacts routed to a Q Connect AI Agent channel fall silent or
  are immediately transferred to a queue without AI handling.
* AIA specialist reports: errorRatePct > 5% or Lex RuntimeUserErrors > 0.

---

## Step-by-Step Diagnostics

### 1. Check agent status and prompt version
```bash
aws qconnect list-ai-agents \
  --assistant-id <ASSISTANT_ID> \
  --region us-west-2 \
  --profile connect-sre-dev
```
Confirm `status=ACTIVE` and `visibilityStatus=PUBLISHED`.

### 2. Check Bedrock model errors
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationClientErrors \
  --dimensions Name=ModelId,Value=us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Sum \
  --region us-west-2 --profile connect-sre-dev
```

---

## Remediation Actions

### Action A: Re-publish the AI Agent
If the agent is in SAVED (draft) state or linked to a broken prompt version:
1. Open the Amazon Connect console.
2. Navigate to AI Agents under Q Connect settings.
3. Select the affected agent, verify the prompt version, and click Publish.

### Action B: Roll back to previous prompt version
1. List prompt versions: `aws qconnect list-ai-prompt-versions --assistant-id <ID> --ai-prompt-id <PROMPT_ID>`
2. Identify the last stable version.
3. Update the agent to reference the previous version and re-publish.
```
```

---

## Runbook coverage gaps

The following failure modes currently have no runbook:

- Q Connect AI Agent Bedrock invocation errors (now that AI agents are managed in the platform)
- Routing Profile queue association failures
- Contact Lens evaluation failures
- Amazon Connect Streams (CCP) WebSocket reconnection loops
- `GetCurrentMetricData` throttling during peak load

Add runbooks for these and upload to S3 to extend the agent's remediation knowledge.
