# Policy Model

The Connect SRE Agent enforces two independent layers of policy: **agent-time gates** evaluated inside `propose_remediation` before an approval record is written, and **dispatch-time gates** enforced by `action_dispatcher.py` before any AWS API write occurs.

---

## Layer 1 — Agent-time gates (`runtime/tools.py`)

When the supervisor calls `propose_remediation`, four policy checks run in order against the `dev-connect-sre-policy-config` table. Each check matches by exact `policyName` string — the names below must be preserved verbatim in DynamoDB.

### Check 1 — Out-of-hours block
**Policy name:** `Block Out-of-hours Deployments`  
**policyId:** `POL-007`  
**Default:** enabled

Blocks any write action between **22:00 and 06:00 UTC**. Evaluated before blast radius, so a change proposed at 23:00 is blocked even if the blast radius is zero.

```python
if current_hour >= 22 or current_hour < 6:
    blocked_reason = "Blocked by Policy: Out-of-hours Deployments (22:00-06:00 UTC)"
```

### Check 2 — Blast radius cap
**Policy name:** `Max Blast Radius: 20%`  
**policyId:** `POL-005`  
**Default:** enabled

If `params` contains a `targetNodeId`, `propose_remediation` runs `calculate_blast_radius(targetNodeId, max_depth=3, direction="upstream")` and blocks if the impacted node count exceeds 20 % of instance volume (currently: `impacted_count / 100.0 > 0.20`).

The blast radius data is always attached to the approval record regardless of whether the policy blocks, so operators can review it in the UI.

### Check 3 — Lambda approval requirement
**Policy name:** `Require Approval for Lambda Updates`  
**policyId:** `POL-008`  
**Default:** enabled

If `action_type` or `params` contain the string `"lambda"` (case-insensitive), the `lambda_requires_approval` flag is set. This suppresses the SEV4 auto-approve path (Check 4), forcing a human review even for low-severity incidents.

### Check 4 — SEV4 auto-approve
**Policy name:** `Auto-approve SEV4 Changes`  
**policyId:** `POL-009`  
**Default:** **disabled**

If enabled, and if `"sev4"` appears in the justification text or `params.severity == "SEV4"`, and no other gate has blocked the action, the approval record is written with `status = "AUTO_APPROVED"` rather than `"PENDING"`. Has no effect when the Lambda policy is triggered.

### Outcome values

| Status | Meaning |
|---|---|
| `BLOCKED` | A policy gate fired — no approval record written, action dead-ends |
| `PENDING` | Approval record created, awaiting human review in `/approvals` |
| `AUTO_APPROVED` | SEV4 policy fired — Action Dispatcher may execute without UI interaction |

---

## Layer 2 — Dispatch-time gates (`infra/src/action_dispatcher.py`)

Four independent rules evaluated after the operator approves in the UI and the Action Dispatcher Lambda is invoked. All four must pass or execution is denied and the approval record is updated to `BLOCKED`.

### Rule A — Feature flag: write actions enabled
```
ENABLE_CONNECT_WRITE_ACTIONS environment variable must be "true"
```
This is a CloudFormation parameter (default: `false`). With it false the Lambda runs in read-only mode — the evaluation logic exists but no AWS write is ever reached.

### Rule B — High-risk actions need an approval ticket
```
If riskLevel == "high" in policy record and no approvalId → deny
```
The `riskLevel` field on each policy record in `dev-connect-sre-policy-config` drives this. The seeded policies do not include `riskLevel` — add it to records where you need extra gates.

### Rule C — Feature flag: autonomous actions enabled
```
ENABLE_AUTONOMOUS_ACTIONS must be "true" when operator == "system"
```
Blocks the `AUTO_APPROVED` path from silently executing in production. Both CloudFormation parameters default to `false`, so the system is read-only and human-gated out of the box.

### Rule D — Approval ticket must be `APPROVED`
```
approval record status must == "APPROVED"
```
Prevents replay attacks and race conditions where a ticket is approved, recalled, then replayed. The Action Dispatcher reads the current record state at dispatch time.

---

## Seeded policies

Run `./infra/scripts/run_seeds.sh` (or `python infra/src/seed_policies.py`) to populate `dev-connect-sre-policy-config` with the default set:

| policyId | policyName | Default state | Purpose |
|---|---|---|---|
| `POL-001` | Require Human Approval for Remediations | **enabled** | Documents the baseline human-in-the-loop requirement |
| `POL-002` | Allow Connect Routing Profile Modification | disabled | Routing profile write access |
| `POL-003` | Allow Connect Prompt Creation | **enabled** | Emergency IVR prompt creation |
| `POL-004` | Allow Lex Bot Alias Rollbacks | **enabled** | Lex alias rollback permission |
| `POL-005` | Max Blast Radius: 20% | **enabled** | Caps automatic blast radius at 20 % |
| `POL-006` | Allow Emergency Call Callback Activation | disabled | Priority queue callback activation |
| `POL-007` | Block Out-of-hours Deployments | **enabled** | Blocks writes 22:00–06:00 UTC |
| `POL-008` | Require Approval for Lambda Updates | **enabled** | Forces human review for Lambda actions |
| `POL-009` | Auto-approve SEV4 Changes | disabled | Allows autonomous SEV4 remediations |
| `AgentToolConfig` | *(internal)* | **enabled** | Default log group, time window, CTR S3 location for tool calls — not shown in Policy UI |

---

## Adding a new policy

1. Add a record to `dev-connect-sre-policy-config` with a unique `policyId` and a `policyName` string.
2. If the policy should gate `propose_remediation`, add a check in `tools.py` that matches by `policyName` exactly — the match is case-sensitive.
3. If the policy should gate dispatch, add logic to `evaluate_policy_gates()` in `action_dispatcher.py`.
4. Add the new policy to `infra/src/seed_policies.py` so fresh environments get it automatically.

---

## Execution path after approval

```
Operator clicks Approve in /approvals
  → FastAPI PATCH /api/approvals/{id}/action
  → DynamoDB approval record → status: APPROVED
  → (MVP: manually invoke action_dispatcher.py Lambda with approvalId)
  → Rule A: ENABLE_CONNECT_WRITE_ACTIONS?
  → Rule B: high risk needs approvalId?
  → Rule C: ENABLE_AUTONOMOUS_ACTIONS if system operator?
  → Rule D: approvalId record == APPROVED?
  → execute_remediation(action_type, parameters)
  → SSM Automation Document: SRE-Connect-{action_type}
  → (if document missing in dev: simulated execution ID returned)
  → approval record → status: EXECUTED
  → incident record → status: Recovering
```

SSM Automation Documents follow the naming convention `SRE-Connect-{action_type}`. In MVP these are not yet provisioned — the dispatcher simulates execution and logs `ssm_document_missing_simulated`.
