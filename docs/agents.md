# SRE Agent Personas & Orchestration

The SRE platform runs a **Supervisor + 10 Specialist** multi-agent system. The provider (Gemini or Bedrock/Strands) is selected at container start — no code changes required.

---

## Provider paths

### Google ADK (Gemini) — `MODEL_PROVIDER=gemini`

The Supervisor is a `google.antigravity.Agent` with `enable_subagents=True`. When an incident arrives, the Supervisor reads its system instructions (`SUPERVISOR_SYSTEM_INSTRUCTION` in `prompts.py`) and dynamically spawns specialist sub-agents. The ADK manages spawning, tool registration, and result aggregation automatically.

### AWS Strands (Bedrock) — `MODEL_PROVIDER=bedrock`

`build_strands_supervisor()` in `agents_bedrock.py` creates all 10 specialist `Agent` instances as closures, wraps each in a Strands `@tool`, and passes them to the Supervisor. The Supervisor calls specialists as explicit tool invocations; Strands handles JSON schema generation from type hints and docstrings. Strands is synchronous — `_BedrockSupervisor.chat()` runs in a thread-pool executor so FastAPI's async event loop is never blocked.

Both paths call the same underlying `tools.py` functions. The `@tool` decorator is applied in `agents_bedrock.py` only, keeping `tools.py` provider-agnostic.

---

## The Supervisor

Receives the normalised incident payload and decides which specialists to invoke. On the Strands path it is the only agent that may call `propose_remediation` — all specialists are intentionally read-only.

System prompt: `SUPERVISOR_STRANDS_INSTRUCTION` (Bedrock) / `SUPERVISOR_SYSTEM_INSTRUCTION` (Gemini).

---

## The 10 Specialist Agents

### 1. FLOW — Flow Health Agent
**Prompt:** `FLOW_HEALTH_PROMPT`  
**Tools:** `query_topology`, `query_connect_metrics`, `query_cloudwatch_flow_logs`

Investigates Amazon Connect Contact Flow errors. Queries CloudWatch Logs Insights for `ContactFlowFatalErrors` and `ContactFlowErrors`, maps dependent modules using the topology graph, and correlates error spikes with flow-level metrics.

### 2. MODULE — Module Dependency Agent
**Prompt:** `MODULE_DEPENDENCY_PROMPT`  
**Tools:** `query_topology`, `calculate_blast_radius`

Evaluates shared Contact Flow Modules. When a module fails, traverses `REQUIRED_BY` edges upstream to find all parent flows and entry points affected, sizing the blast radius.

### 3. QUEUE — Queue and Routing Agent
**Prompt:** `QUEUE_ROUTING_PROMPT`  
**Tools:** `query_topology`, `query_connect_metrics`, `query_connect_ctrs`, `query_contact_lens`, `query_agent_events`

Evaluates queue health, routing profile assignments, and live agent state. Reads historical metrics via `GetMetricDataV2`, individual contact records via `DescribeContact`, Contact Lens evaluation data, and real-time agent occupancy via `GetCurrentUserData`.

### 4. LEXA — Lex Bot Agent
**Prompt:** `LEX_BOT_PROMPT`  
**Tools:** `query_topology`, `query_lex_bot_health`, `query_connect_metrics`

Checks Lex V2 bot alias status (`lexv2-models:DescribeBotAlias`), CloudWatch `MissedUtteranceCount` and `RuntimePollingRequests`, and downstream Connect flow error rates. Identifies NLU degradation and alias/version mismatches.

### 5. AIA — AI Assist Agent
**Prompt:** `AI_ASSIST_PROMPT`  
**Tools:** `query_topology`, `query_ai_agent_health`

Investigates Amazon Q Connect AI Agents (ORCHESTRATION type). Calls `query_ai_agent_health()` to fetch agent config, prompt model, Bedrock invocation error rate, and Lex runtime errors. Flags:
- `status != ACTIVE` or `visibilityStatus != PUBLISHED` — configuration issue
- Bedrock `errorRatePct > 5%` — model invocation failure
- Lex `RuntimeUserErrors > 0` — conversation runtime error

Then maps affected contact flows via `query_topology`.

### 6. CHANGE — Change Correlation Agent
**Prompt:** `CHANGE_CORRELATION_PROMPT`  
**Tools:** `query_recent_mutations`

Queries the incidents table for CloudTrail-sourced change events on the affected resource. Identifies timing correlation between a configuration change and the alarm, the IAM principal that made the change, and whether the change is a likely root cause.

### 7. IMPACT — Customer Impact Agent
**Prompt:** `CUSTOMER_IMPACT_PROMPT`  
**Tools:** `calculate_blast_radius`, `query_topology`, `query_contact_lens`, `query_agent_events`

Calculates blast radius by traversing upstream `REQUIRED_BY` edges from the failed node. Counts affected entry points (phone numbers), flows, queues, and in-flight contacts. Assesses whether the incident is Sev1 (complete outage of an entry point) or Sev2 (partial degradation).

### 8. RUNBOOK — Runbook Agent
**Prompt:** `RUNBOOK_PROMPT`  
**Tools:** `fetch_runbook`

Searches the S3 runbook library for a matching SOP by topic. Returns the markdown runbook content for the supervisor to include in the investigation summary and proposed remediation.

Available runbooks cover: contact flow regression, Lex misrouting, Lambda failures, EventBridge failures, Q Connect latency, DynamoDB throttling, and Connect CCP/WebRTC failures.

### 9. RISK — Risk and Policy Agent
**Prompt:** `RISK_POLICY_PROMPT`  
**Tools:** `calculate_blast_radius`, `query_topology`

Evaluates the safety of a proposed remediation before the supervisor calls `propose_remediation`. Computes the blast radius of the proposed change target and cross-checks against active policies in `dev-connect-sre-policy-config`. Read-only — it informs the supervisor but cannot write approvals.

### 10. VERIFY — Verification Agent
**Prompt:** `VERIFICATION_PROMPT`  
**Tools:** `query_connect_metrics`, `query_cloudwatch_flow_logs`

After a remediation is applied, re-queries the original metric and flow log sources to confirm the alarm has cleared. Reports whether the fix was successful, partial, or ineffective.

---

## Adding a new specialist

Three coordinated changes are required:

1. **`runtime/prompts.py`** — add a `NEW_SPECIALIST_PROMPT` constant
2. **`runtime/agents_bedrock.py`** — instantiate a Strands `Agent`, wrap it with `@tool`, pass it to the supervisor's tool list in `build_strands_supervisor()`
3. **`runtime/prompts.py`** — add a persona entry in `SUPERVISOR_STRANDS_INSTRUCTION` so the supervisor knows when to delegate to the new specialist

For the Gemini path the system instruction in `SUPERVISOR_SYSTEM_INSTRUCTION` must also be updated to describe the new persona.

---

## Tool library (`runtime/tools.py`)

All 14 tools are plain Python functions — no framework decorators. The Strands `@tool` is applied in `agents_bedrock.py` at the boundary only.

| Tool | Primary AWS call | Used by |
|---|---|---|
| `query_topology` | DynamoDB scan | FLOW, MODULE, QUEUE, LEXA, AIA, IMPACT, RISK |
| `calculate_blast_radius` | DynamoDB BFS | MODULE, IMPACT, RISK |
| `query_connect_metrics` | `connect:GetMetricDataV2` | FLOW, QUEUE, LEXA, VERIFY |
| `query_connect_ctrs` | `connect:DescribeContact` | QUEUE |
| `query_contact_lens` | `connect:ListContactEvaluations` | QUEUE, IMPACT |
| `query_agent_events` | `connect:GetCurrentUserData` | QUEUE, IMPACT |
| `query_cloudwatch_flow_logs` | CloudWatch Logs Insights | FLOW, VERIFY |
| `query_lex_bot_health` | `lexv2-models:DescribeBotAlias` + `AWS/Lex` CW | LEXA |
| `query_ai_agent_health` | `qconnect:GetAIAgent` + `AWS/Bedrock` + `AWS/Lex` CW | AIA |
| `query_recent_mutations` | DynamoDB (CloudTrail-sourced incidents) | CHANGE |
| `fetch_runbook` | S3 GetObject | RUNBOOK |
| `propose_remediation` | DynamoDB `dev-connect-sre-approvals` | **Supervisor only** |
| `recall_prior_incidents` | DynamoDB `dev-connect-sre-memory` | Supervisor |
| `record_investigation_memory` | DynamoDB `dev-connect-sre-memory` | Supervisor |
