# Builder Prompt: Connect SRE Agent

## Role

You are a senior AWS platform engineer, Amazon Connect engineer, and AI agent engineer building a domain-specific **Connect SRE Agent**.

Build from `SPEC.md`.

The product is **not** a generic AWS SRE Agent. Generic AWS monitoring is only the substrate. The value is Amazon Connect operational intelligence across customer journeys, contact flows, modules, queues, routing, agents, Lex bots, Lambda integrations, Contact Lens, Q in Connect, and AI agent integrations.

Use:

- Google ADK Python for multi-agent orchestration
- AWS for eventing, telemetry, storage, audit, and controlled remediation
- A pluggable model router supporting Gemini, Bedrock, OpenAI-compatible endpoints, and mock/test providers
- CloudFormation for repeatable AWS deployment
- A management interface for supervisor control

Do not build a model with broad AWS write permissions. That is not engineering. That is gambling with JSON.

---

## Non-Negotiables

1. The project must be named and structured as `connect-sre-agent`.
2. The primary domain must be Amazon Connect reliability.
3. Implement the supervisor pattern with specialist agents.
4. Use Google ADK-compatible agent modules.
5. Implement a pluggable model router from day one.
6. Do not hard-code one LLM provider.
7. Do not let any model or agent directly execute Connect or AWS write actions.
8. All executable actions must go through:
   - Tool registry
   - Policy engine
   - Approval state if required
   - Action dispatcher
9. Default operating mode must be `recommend_only`.
10. MVP must be read-only for Connect configuration changes.
11. All incidents, topology scans, model calls, tool calls, approvals, policy decisions, and action results must be audited.
12. Customer-sensitive data must be redacted or hashed before being passed to external model providers.

---

## Target Repository Structure

Create this structure:

```text
connect-sre-agent/
  README.md
  SPEC.md
  BUILDER_PROMPT.md
  docs/
    architecture.md
    connect-topology.md
    runbook-authoring.md
    policy-model.md
    model-routing.md
    threat-model.md
  infra/
    cloudformation/
      connect-sre-agent-platform.yaml
      nested/
        security.yaml
        eventing.yaml
        state.yaml
        compute.yaml
        connect-observability.yaml
        management-ui.yaml
  agent/
    pyproject.toml
    src/
      connect_sre_agent/
        main.py
        agents/
          supervisor.py
          flow_health.py
          module_dependency.py
          queue_routing.py
          lex_bot.py
          ai_assist.py
          change_correlation.py
          customer_impact.py
          runbook.py
          risk_policy.py
          verification.py
        models/
          router.py
          providers/
            base.py
            gemini.py
            bedrock.py
            openai_compatible.py
            mock.py
        tools/
          connect_read.py
          connect_metrics.py
          connect_flow_logs.py
          connect_topology.py
          cloudtrail.py
          lex.py
          lambda_signals.py
          contact_lens.py
          notifications.py
          ticketing.py
        policy/
          engine.py
          models.py
        schemas/
          connect_event.py
          topology.py
          journey.py
          incident.py
          approval.py
          tool_registry.py
          model_config.py
        services/
          incident_store.py
          topology_store.py
          evidence_store.py
          audit_log.py
  normalizer/
    src/
      handler.py
  topology-scanner/
    src/
      handler.py
  action-dispatcher/
    src/
      handler.py
  ui/
    package.json
    src/
      pages/
      components/
      api/
  runbooks/
    flow-regression.yaml
    module-rollback-checklist.yaml
    queue-degradation.yaml
    lex-fallback-spike.yaml
    ai-assist-fallback.yaml
  tests/
    unit/
    integration/
    simulations/
```

---

## Build Order

### Step 1: Foundation

Create:

- Python package under `agent/`
- Pydantic schemas for:
  - Normalized Connect incident event
  - Connect resource node
  - Connect topology edge
  - Business journey
  - Incident state
  - Tool registry entry
  - Approval
  - Model config
  - Agent run record
- Basic FastAPI service:
  - `GET /health`
  - `POST /events/connect`
  - `GET /incidents`
  - `GET /incidents/{incidentId}`
  - `GET /topology`
  - `POST /topology/scan`

Use in-memory stores only as a temporary local fallback. Keep storage behind service classes.

### Step 2: Model Router

Implement model abstraction:

```python
class ModelProvider:
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...

    async def stream(self, request: ModelRequest):
        ...

    def supports_tools(self) -> bool:
        ...

    def supports_json_mode(self) -> bool:
        ...

    def provider_name(self) -> str:
        ...
```

Providers:

- `MockModelProvider`
- `GeminiModelProvider`
- `BedrockModelProvider`
- `OpenAICompatibleModelProvider`

The mock provider must be deterministic for tests.

Config example:

```yaml
defaultProvider: bedrock
defaultModel: anthropic.claude-3-7-sonnet
agents:
  connect_supervisor:
    provider: bedrock
    model: anthropic.claude-3-7-sonnet
  flow_health:
    provider: bedrock
    model: amazon.nova-pro
  module_dependency:
    provider: gemini
    model: gemini-2.5-pro
fallback:
  enabled: true
  orderedProviders:
    - bedrock
    - gemini
    - openai_compatible
```

### Step 3: Specialist Agents

Create ADK-compatible agent modules:

- `supervisor.py`
- `flow_health.py`
- `module_dependency.py`
- `queue_routing.py`
- `lex_bot.py`
- `ai_assist.py`
- `change_correlation.py`
- `customer_impact.py`
- `runbook.py`
- `risk_policy.py`
- `verification.py`

Supervisor flow:

1. Accept normalized Connect event.
2. Create/update incident.
3. Run Flow/Queue/Lex/AI/change-specific agents depending on event type.
4. Query topology graph.
5. Collect evidence.
6. Estimate customer impact.
7. Retrieve runbook.
8. Request policy decision.
9. If denied, mark blocked.
10. If approval required, create approval.
11. If allowed, call action dispatcher.
12. Verify.
13. Write audit trail.

### Step 4: Connect Topology Scanner

Implement `topology-scanner`.

It must inventory, where permissions allow:

- Connect instances
- Contact flows
- Contact flow modules
- Queues
- Routing profiles
- Users
- Agent statuses where available
- Hours of operation
- Phone numbers
- Quick connects
- Security profiles
- Prompts
- Lex bot integrations
- Lambda references in contact flow content
- Flow-module references
- Queue references inside flow content

Store graph records in `connect-sre-topology`.

Represent nodes and edges.

Minimum node schema:

```json
{
  "nodeId": "connect-flow:instance-id:flow-id",
  "nodeType": "contact_flow",
  "displayName": "Customer Authentication",
  "arn": "...",
  "instanceId": "...",
  "metadata": {},
  "lastSeenAt": "..."
}
```

Minimum edge schema:

```json
{
  "sourceNodeId": "journey:customer-authentication",
  "edgeType": "USES_FLOW",
  "targetNodeId": "connect-flow:instance-id:flow-id",
  "confidence": 1.0,
  "evidence": "manual-map|flow-json|api|tag"
}
```

### Step 5: Connect Read Tools

Implement wrappers for:

- Connect list/describe APIs
- Contact flow content retrieval
- Contact flow module retrieval
- Queue/routing/user inventory
- CloudWatch Connect metrics
- CloudWatch Logs Insights for flow logs
- CloudTrail lookup for Connect changes
- Lex bot/alias metadata
- Lambda integration health
- Contact Lens / Q in Connect placeholders where APIs are not yet wired

All tools must:

- Be read-only in MVP.
- Return structured JSON.
- Redact sensitive data.
- Log request metadata.
- Handle AWS errors gracefully.
- Be individually unit-testable.

### Step 6: Normalizer Lambda

Create `normalizer/src/handler.py`.

Normalize:

- CloudWatch alarm state changes for Connect metrics
- CloudTrail Connect API changes
- CloudTrail Lex API changes
- CloudTrail Lambda changes affecting flow integrations
- Scheduled proactive health checks
- Scheduled topology scan trigger events

Output common event schema:

```json
{
  "schemaVersion": "1.0",
  "incidentId": "conn-inc-...",
  "dedupeKey": "connect:...",
  "source": "aws.connect.cloudwatch",
  "accountId": "...",
  "region": "...",
  "eventTime": "...",
  "severityHint": "...",
  "connect": {
    "instanceId": "...",
    "businessJourney": "...",
    "contactFlowId": "...",
    "contactFlowModuleId": "...",
    "queueId": "...",
    "routingProfileId": "...",
    "lexBotAlias": "...",
    "lambdaFunctionArn": "..."
  },
  "signal": {},
  "rawEventS3Uri": "...",
  "correlation": {}
}
```

### Step 7: Policy Engine

Implement deterministic policy decisions.

Inputs:

- Environment
- Business journey criticality
- Customer impact estimate
- Resource type
- Action type
- Tool registry entry
- Model/provider policy
- Approval state
- Change freeze state
- Business hours
- Blast radius

Rules:

- Deny unregistered tools.
- Deny destructive actions in MVP.
- Deny production Connect write actions without approval.
- Require two-person approval for critical journey write actions.
- Deny actions without rollback plan.
- Deny actions without verification method.
- Deny external model use for unredacted customer-sensitive evidence.
- Deny direct model-generated flow JSON updates.

### Step 8: Action Dispatcher

Create `action-dispatcher/src/handler.py`.

It must:

1. Receive approved execution request.
2. Re-check policy.
3. Validate tool registry entry.
4. Validate parameters.
5. Execute only approved action type.
6. Record execution result.
7. Emit event for verification.

MVP should support only:

- Notify/ticket actions
- Diagnostic workflow trigger
- Topology scan trigger
- Recommendation/checklist creation

Do not implement direct Connect config mutation in MVP.

### Step 9: Management UI

Build React + TypeScript UI.

Screens:

- Dashboard
- Incident list
- Incident detail
- Connect topology
- Business journeys
- Approvals
- Agent control
- Model configuration
- Tool registry
- Policy management
- Runbooks
- Audit

Required API routes:

```text
GET    /health
GET    /incidents
GET    /incidents/{incidentId}
POST   /incidents/{incidentId}/replay

GET    /topology
POST   /topology/scan
GET    /topology/resources/{resourceId}
GET    /journeys
GET    /journeys/{journeyId}

GET    /approvals
POST   /approvals/{approvalId}/approve
POST   /approvals/{approvalId}/reject

GET    /agents/status
POST   /agents/mode
POST   /agents/pause
POST   /agents/resume

GET    /models/config
PATCH  /models/config

GET    /tools
PATCH  /tools/{toolId}

GET    /policies
PATCH  /policies/{policyId}

GET    /runbooks
POST   /runbooks/validate

GET    /audit
```

### Step 10: CloudFormation

Create parent template:

```text
infra/cloudformation/connect-sre-agent-platform.yaml
```

It should create or prepare:

- EventBridge bus
- CloudWatch alarm rule
- CloudTrail Connect change rule
- Scheduled topology scan rule
- Scheduled proactive check rule
- SQS DLQ
- DynamoDB state tables
- S3 evidence bucket
- S3 runbook bucket
- S3 topology snapshot bucket
- KMS key
- IAM roles
- Normalizer Lambda placeholder
- Topology scanner Lambda placeholder
- Action dispatcher Lambda placeholder
- CloudWatch log groups

Use least-privilege read permissions for Connect inventory and telemetry.

### Step 11: Tests

Add unit tests for:

- Connect event normalization
- CloudWatch Connect alarm mapping
- CloudTrail Connect change mapping
- Topology node/edge generation
- Model router provider selection
- Policy decisions
- Tool registry validation
- Approval state transitions
- Incident state transitions

Add simulations:

- Flow fatal error spike
- Contact flow module regression
- Queue wait time degradation
- Lex fallback spike
- Recent Connect change correlated to flow errors
- Production write action denied without approval
- External model denied for unredacted customer-sensitive evidence


---

## Critical Engineering Bottlenecks To Implement Explicitly

### A. Live Connect State Graph

Do not make the LLM infer topology from disconnected logs.

Implement a topology graph service with:

- Nodes for journeys, instances, phone numbers, flows, modules, queues, routing profiles, users, Lex bots, Lambda functions, Q/AI assist components, runbooks, and owners.
- Edges for flow/module/queue/routing/Lex/Lambda dependencies.
- Upstream, downstream, blast-radius, and journey-path traversal functions.
- Freshness metadata and stale topology warnings.

Required internal service methods:

```python
class TopologyService:
    async def get_upstream(self, resource_id: str, max_depth: int = 5) -> TopologyTraversal: ...
    async def get_downstream(self, resource_id: str, max_depth: int = 5) -> TopologyTraversal: ...
    async def get_blast_radius(self, resource_id: str) -> BlastRadius: ...
    async def get_journey_path(self, journey_id: str) -> JourneyPath: ...
    async def upsert_node(self, node: TopologyNode) -> None: ...
    async def upsert_edge(self, edge: TopologyEdge) -> None: ...
```

Agents must use topology traversal before producing blast-radius or remediation recommendations.

### B. Deterministic Incident Digest Layer

Do not pass raw high-volume CloudWatch logs to an LLM.

Implement an incident digest builder.

Required service:

```python
class IncidentDigestService:
    async def build_digest(self, incident: ConnectIncident, window_minutes: int) -> IncidentDigest: ...
    async def get_latest_digest(self, incident_id: str) -> IncidentDigest | None: ...
```

Digest builder must:

- Query bounded time windows.
- Aggregate logs by error type, flow, module, queue, Lex bot, Lambda, time bucket.
- Include representative redacted samples only.
- Preserve counts, rates, first-seen, last-seen, affected resources, topology paths.
- Store raw evidence in S3.
- Store compressed digest in DynamoDB/S3.
- Pass only the digest to the agents.

Add tests that prove raw log lines are not blindly stuffed into prompts.

### C. Strict Safe Remediation Schema

Implement safe actions as schemas, not prose.

Every proposed action must validate against:

```python
class SafeAction(BaseModel):
    action_id: str
    action_class: str
    risk_level: Literal["low", "medium", "high", "critical"]
    requires_approval: bool
    environment: str
    target: ActionTarget
    parameters: dict
    preconditions: list[str]
    rollback: RollbackPlan
    verification: VerificationPlan
```

The action dispatcher must reject:

- Unknown actions
- Disabled tools
- Invalid parameters
- Missing approval
- Expired approval
- Missing rollback
- Missing verification
- Targets not found in topology
- Production writes without approval
- Model-generated flow JSON
- Any direct Connect write in MVP

Add explicit action schemas for later phases:

- `connect_toggle_emergency_routing`
- `connect_switch_entry_point_to_fallback_flow`
- `connect_rollback_contact_flow`
- `connect_rollback_contact_flow_module`
- `lex_repoint_alias_to_previous_version`
- `connect_disable_ai_assist_feature_flag`
- `lambda_alias_rollback_for_connect_integration`

In MVP, these must exist as disabled or recommendation-only registry entries unless explicitly enabled.


---

## Additional Engineering Requirements From Review

### 1. Topology Traversal Must Not Be Naive

DynamoDB adjacency lists are acceptable for MVP storage, but do not implement recursive traversal as slow sequential reads.

Implement `TopologyService` with:

- Parallel async expansion by depth layer
- Deduplication of nodes and edges
- Max concurrency controls
- Optional in-memory graph cache
- Cache refresh after full scan
- Cache invalidation after partial scan
- Stale topology warnings

Required methods:

```python
async def get_blast_radius(resource_id: str, max_depth: int = 5) -> BlastRadius:
    ...

async def refresh_cache() -> TopologyCacheMetadata:
    ...

async def invalidate_subgraph(resource_id: str) -> None:
    ...
```

Tests must simulate depth-5 traversal and prove it does not perform one blocking read at a time.

### 2. CloudTrail Mutations Must Trigger Partial Topology Refresh

Scheduled scans are not enough.

When the normalizer sees a CloudTrail mutation event affecting Connect, Lex, Lambda, routing, queue, flow, module, phone number, or hours of operation, it must emit a partial topology refresh request.

Implement:

```python
class TopologyRefreshRequest(BaseModel):
    event_type: Literal["topology_partial_refresh_requested"]
    source_event_id: str
    resource_type: str
    resource_id: str
    instance_id: str | None
    reason: str
    observed_at: datetime
```

The topology scanner must support:

```python
async def run_full_scan() -> TopologyScanResult:
    ...

async def run_partial_scan(request: TopologyRefreshRequest) -> TopologyScanResult:
    ...
```

If an incident occurs within 60 minutes of a mutation event, the Change Correlation Agent must verify the topology cache includes the mutation. If not, request a partial scan before final diagnosis.

### 3. Supervisor Must Dispatch Agents Concurrently

Do not run every specialist agent sequentially.

Use async orchestration so independent agents run in parallel.

Example:

```python
results = await asyncio.gather(
    flow_health_agent.run(context),
    change_correlation_agent.run(context),
    queue_routing_agent.run(context),
    lex_bot_agent.run(context),
    return_exceptions=True,
)
```

The supervisor must tolerate partial failure:

- One failed specialist agent must not fail the whole incident.
- Failed agents must be visible in the audit trace.
- Supervisor should continue with degraded confidence.

### 4. LLM and Tool Observability Is Mandatory

Every agent/model/tool step must emit trace metadata:

```python
class AgentTraceSpan(BaseModel):
    run_id: str
    incident_id: str
    agent_name: str
    span_id: str
    parent_span_id: str | None
    model_provider: str | None
    model_id: str | None
    prompt_template_version: str | None
    input_token_count: int | None
    output_token_count: int | None
    latency_ms: int
    tool_calls: list[str]
    retry_count: int
    error_type: str | None
    cache_hit: bool | None
    cost_estimate: float | None
    status: Literal["success", "failed", "partial", "skipped"]
```

Add trace output to CloudWatch Logs and summary records to the agent run table.

### 5. Missing Logs Must Be Treated As Signal

The `connect_flow_logs` tool must return structured states, not just empty arrays.

Allowed statuses:

```text
ok
no_logs_available
flow_logging_not_enabled
log_group_missing
permission_denied
query_timeout
delivery_delay_suspected
unknown_error
```

If logs are missing:

- The investigation must continue with metrics, topology, CloudTrail, and known changes.
- The agent must report the missing logs as an observability issue.
- The agent must not hallucinate log findings.
- The runbook selection must account for evidence gaps.

Add tests for:

- Flow logging not enabled
- Log group missing
- Permission denied
- Empty logs but metric alarm active

---

## Required Environment Variables

```text
ENVIRONMENT_NAME
AGENT_MODE
AWS_REGION

CONNECT_INSTANCE_IDS
CONNECT_INSTANCE_TAG_FILTER
CONNECT_TOPOLOGY_SCAN_RATE_MINUTES

INCIDENT_TABLE_NAME
APPROVAL_TABLE_NAME
AGENT_RUN_TABLE_NAME
POLICY_TABLE_NAME
TOOL_REGISTRY_TABLE_NAME
MODEL_CONFIG_TABLE_NAME
TOPOLOGY_TABLE_NAME
JOURNEY_TABLE_NAME

EVIDENCE_BUCKET_NAME
RUNBOOK_BUCKET_NAME
TOPOLOGY_SNAPSHOT_BUCKET_NAME

DEFAULT_MODEL_PROVIDER
DEFAULT_MODEL_ID
ENABLE_MODEL_FALLBACK
GEMINI_API_SECRET_ARN
BEDROCK_REGION
OPENAI_COMPATIBLE_BASE_URL
OPENAI_COMPATIBLE_SECRET_ARN

ENABLE_CONNECT_WRITE_ACTIONS
ENABLE_AUTONOMOUS_ACTIONS
REQUIRE_APPROVAL_FOR_MEDIUM_RISK
```

---

## Audit Record

Every audit record must include:

```json
{
  "auditId": "...",
  "timestamp": "...",
  "actorType": "agent|user|system",
  "actorId": "...",
  "incidentId": "...",
  "businessJourney": "...",
  "connectResourceId": "...",
  "action": "...",
  "decision": "...",
  "modelProvider": "...",
  "modelId": "...",
  "toolId": "...",
  "inputHash": "...",
  "outputHash": "..."
}
```

---

## Definition of Done for MVP

- Repo structure exists.
- CloudFormation validates syntactically.
- FastAPI runtime starts locally.
- Model router works with mock provider.
- Connect normalizer handles sample CloudWatch and CloudTrail events.
- Topology scanner creates sample nodes/edges.
- Supervisor processes a sample flow error incident.
- Flow Health Agent produces diagnosis.
- Customer Impact Agent produces basic impact summary.
- Policy engine denies unsafe Connect write actions.
- UI displays incidents and topology.
- Unit tests pass.
- README explains local run and AWS deployment path.

---

## Implementation Warning

Do not accidentally drift this back into a generic AWS SRE agent.

Generic AWS resources are supporting actors. Amazon Connect is the lead. If EC2 starts getting more screen time than contact flows, something has gone spiritually wrong.
