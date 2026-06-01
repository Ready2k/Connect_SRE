# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Connect SRE Agent — a domain-specific SRE platform for Amazon Connect. It detects contact flow regressions, correlates infrastructure changes to incidents, calculates blast radius, and recommends safe remediation actions. MVP is **read-only by default**; autonomous actions are disabled behind feature flags.

AWS profile for all infrastructure operations is `connect-sre-dev` (us-west-2). The runtime container uses `connect-sre-runtime`.

## Commands

### Runtime (Docker)

```bash
# Build the image (Dockerfile is in runtime/)
./build.sh

# Start with interactive provider selection (Gemini or Bedrock)
./start.sh

# Stop
./stop.sh

# View container logs
./logs.sh              # last 100 lines
./logs.sh -f           # follow (tail -f)
./logs.sh -n 200       # last N lines
```

`start.sh` prompts for provider choice:
- **Gemini** — asks for `GEMINI_API_KEY`, sets `MODEL_PROVIDER=gemini`
- **Bedrock** — uses the mounted `~/.aws` profile, sets `MODEL_PROVIDER=bedrock` + `BEDROCK_MODEL_ID`

### UI (React + Vite)

```bash
cd ui
npm install
npm run dev      # Vite dev server → http://localhost:5173 (proxies /api/* to :8000)
npm run build    # Production build → dist/  (built into Docker image)
npm run lint
```

The Vite proxy target is `http://127.0.0.1:8000` — the FastAPI backend must be running (in Docker or locally) for API calls to resolve in dev mode.

### Lambda deploy & test scripts

All scripts require `--profile connect-sre-dev` (already embedded). Run from repo root:

```bash
./infra/scripts/deploy_all.sh                 # deploy all Lambdas in one shot
./infra/scripts/deploy_normalizer.sh
./infra/scripts/deploy_topology_scanner.sh
./infra/scripts/deploy_action_dispatcher.sh
./infra/scripts/test_normalizer.sh            # fires synthetic CloudWatch alarm
./infra/scripts/test_topology_scanner.sh      # triggers full scan
./infra/scripts/test_action_dispatcher.sh
./infra/scripts/update_dev_ip.sh              # update security group with current public IP
./infra/scripts/build_and_push.sh             # build + push Docker image to ECR
```

### Seeding a fresh environment

Run once after deploying the stack to populate DynamoDB tables (policies, tool registry, journeys, topology stub, runbooks):

```bash
./infra/scripts/run_seeds.sh
# Then populate the topology graph for a real Connect instance:
CONNECT_INSTANCE_IDS=<uuid> python infra/src/topology_scanner.py
```

### Lambda functions (local execution)

```bash
cd infra/src
TOPOLOGY_TABLE_NAME=dev-connect-sre-topology \
CONNECT_INSTANCE_IDS=<id1>,<id2> \
python topology_scanner.py

# Same pattern for normalizer.py, action_dispatcher.py, seed_topology.py
```

### Testing the agent

```bash
# Inside the running container (tests tool signatures + Strands registry + live Bedrock call):
docker exec <container_id> python /app/test_agent.py

# Locally — runs only tool signature validation (no Strands/Bedrock required):
cd runtime && python test_agent.py
```

### CloudFormation

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/connect-sre-agent-platform.yaml \
  --stack-name dev-connect-sre-platform \
  --parameter-overrides \
      EnvironmentName=dev \
      PrimaryConnectInstanceId=<connect-instance-uuid> \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile connect-sre-dev
```

`PrimaryConnectInstanceId` is optional but required to activate contact flow log ingestion (subscription filter on `/aws/connect/{instanceId}`). Omit it and the subscription filter is not created.

## Architecture

### End-to-end incident flow

1. **EventBridge** captures CloudWatch Alarms, Connect flow logs, CloudTrail mutations
2. **`normalizer.py`** Lambda normalises the event → DynamoDB incident record → POSTs to FastAPI `/api/incidents`
3. **FastAPI** (`runtime/main.py`) accepts the POST and runs `investigate_incident_background()` as a background task
4. **Supervisor Agent** (`runtime/agent.py` → provider path) picks up tools, queries DynamoDB/S3/CloudWatch, writes an approval record via `propose_remediation`
5. **Operator** reviews and approves in the UI (`/approvals`)
6. **`action_dispatcher.py`** Lambda enforces policy gates then executes the remediation

### Multi-agent runtime — two provider paths

`runtime/agent.py` reads `MODEL_PROVIDER` at import time and returns the correct async context manager. `main.py` calls `async with get_supervisor_agent() as s: await s.chat(prompt)`.

| | Google ADK (Gemini) | AWS Strands (Bedrock) |
|---|---|---|
| `MODEL_PROVIDER` | `gemini` (default) | `bedrock` |
| Entry point | `_get_gemini_agent()` → `google.antigravity.Agent` | `_BedrockSupervisor.__aenter__()` |
| Specialist wiring | `enable_subagents=True` — ADK spawns dynamically | `agents_bedrock.build_strands_supervisor(model)` |
| System prompt | `SUPERVISOR_SYSTEM_INSTRUCTION` | `SUPERVISOR_STRANDS_INSTRUCTION` |
| Model default | `gemini-3.5-flash` | `us.anthropic.claude-sonnet-4-6` |

**Strands multi-agent (`agents_bedrock.py`):** `build_strands_supervisor(model)` creates 10 specialist `Agent` instances as closures, wraps each with Strands `@tool`, and passes them all to the supervisor. Only the supervisor receives `propose_remediation` — specialists are read-only. Strands is synchronous; `_BedrockSupervisor.chat()` runs it in a thread-pool executor so FastAPI's event loop is never blocked.

### The 10 specialist agents

FLOW · MODULE · QUEUE · LEXA · AIA · CHANGE · IMPACT · RUNBOOK · RISK · VERIFY

Each specialist is scoped to a subset of tools. Full system prompts are in `runtime/prompts.py`. Tool implementations are in `runtime/tools.py` — plain Python functions with type hints and docstrings (compatible with both ADK and Strands without modification).

Adding a new specialist requires three coordinated changes: a system prompt constant in `prompts.py`, an `Agent` instance + `@tool` wrapper in `agents_bedrock.py`, and a persona entry in `SUPERVISOR_STRANDS_INSTRUCTION`.

### FastAPI backend (`runtime/main.py`)

Live backend serving the UI. Key endpoints:

| Endpoint | Notes |
|---|---|
| `POST /api/incidents` | Queues agent investigation as background task |
| `GET /api/incidents`, `GET /api/incidents/{id}/traces` | Reads DynamoDB |
| `GET /api/topology?mode=demo\|live&instanceId=` | Demo: DynamoDB scan. Live: Connect API |
| `GET /api/monitoring/metrics?mode=demo\|live&instanceId=` | Demo: derived from incidents. Live: Connect real-time metrics |
| `GET /api/connect/ai-agents?mode=demo\|live` | Lists Q Connect AI Agents via `qconnect.list_ai_agents`, enriched with prompt model ID |
| `GET /api/connect/ai-agents/health?mode=demo\|live` | Bedrock invocation metrics + Lex runtime metrics for the AI agent fleet |
| `GET /api/agents/status` | Returns active model label + mock agent swarm state |
| `GET/PATCH /api/models/config` | In-memory model config (reflects `_ACTIVE_MODEL_LABEL` from env) |
| `GET /api/approvals`, `POST /api/approvals/{id}/action` | Approval state machine |

`_ACTIVE_MODEL_LABEL` is derived at startup from `MODEL_PROVIDER` + `BEDROCK_MODEL_ID` env vars and flows into traces, agent status responses, and the default model config.

Most endpoints accept `?mode=demo|live`. Demo mode returns hardcoded mock data; live mode hits real AWS APIs. The UI toggle in the header switches this globally via `AppContext`.

### Frontend (`ui/`)

Single-page React 19 app (React Router 7). Vite proxies `/api/*` → `http://127.0.0.1:8000`. Styling is vanilla CSS with CSS variables — no CSS framework. Key libraries: `reactflow` (topology), Recharts (metrics), Lucide React (icons).

Pages and their primary API dependencies:
- `/agents` — SRE agent swarm diagram (supervisor + 10 specialists), sourced from `/api/agents/status`
- `/ai-agents` — Connect AI Agent management: lists Q Connect orchestration agents with Bedrock/Lex health metrics
- `/topology` — ReactFlow graph, supports `?mode=live&instanceId=` for real Connect data
- `/monitoring` — Recharts panels, same live/demo toggle
- `/config` — loads active model config from `/api/models/config` on mount, shows provider banner

### Lambda functions (`infra/src/`)

| File | Trigger | Role |
|---|---|---|
| `topology_scanner.py` | EventBridge schedule + SQS | Crawls Connect APIs, writes adjacency-list graph to DynamoDB. Auto-discovers instances if `CONNECT_INSTANCE_IDS` is empty. |
| `normalizer.py` | EventBridge | Normalises events, deduplicates within `DEDUPE_WINDOW_MINUTES`, triggers topology refresh for mutations, POSTs to agent API |
| `action_dispatcher.py` | API/orchestrator | Policy gates + approval check before any Connect write |
| `seed_topology.py` | One-shot bootstrap | Seeds journey definitions and test topology data |

### Data model (DynamoDB)

- **Topology** (`dev-connect-sre-topology`) — adjacency-list: `nodeId` (PK) + `edgeTypeTarget` (SK). `edgeTypeTarget = "METADATA"` rows hold node attributes; edge rows use `"DEPENDS_ON#<target>"` / `"REQUIRED_BY#<target>"` prefixes for BFS traversal.
- **Incidents** (`dev-connect-sre-incidents`) — GSI `by-connect-resource-createdAt` on `connectResourceId`.
- **Approvals** (`dev-connect-sre-approvals`) — state machine: `PENDING` → `AUTO_APPROVED` / approved / rejected.
- **Policy** (`dev-connect-sre-policy-config`) — active policies evaluated by `propose_remediation` at tool-call time, not at dispatch.
- **Agent runs** (`dev-connect-sre-agent-runs`) — trace records written per agent invocation.
- **Agent steps** (`dev-connect-sre-agent-steps`) — fine-grained per-step trace data, TTL 90 days.
- **Journey map** (`dev-connect-sre-journey-map`) — customer journey definitions seeded by `seed_journeys.py`.
- **Tool registry** (`dev-connect-sre-tool-registry`) — available tool metadata seeded by `seed_tools.py`.
- **Memory** (`dev-connect-sre-memory`) — agent investigation memory for `recall_prior_incidents` / `record_investigation_memory` tools.

### Infrastructure

`infra/cloudformation/connect-sre-agent-platform.yaml` is the primary template (`sre-agent-platform.yaml` is a compatibility copy — keep in sync). CloudFormation manages VPC (public subnets, no NAT Gateway), ALB, ECS Fargate, Lambda IAM roles, DynamoDB tables (TTL: topology 180d, evidence 90d), EventBridge rules, SQS queues, and a conditional CloudWatch Logs subscription filter for contact flow error ingestion.

Feature flags (CloudFormation parameters, both default `false`):
- `EnableConnectWriteActions` — allows modifying Connect resources
- `EnableAutonomousActions` — allows changes without human approval

### Current Bedrock model IDs (us-west-2)

us-west-2 has no In-Region support for Claude 4 models — use geo inference IDs:
- `us.anthropic.claude-sonnet-4-6` — recommended default
- `us.anthropic.claude-opus-4-7` — most capable
- `us.anthropic.claude-haiku-4-5-20251001-v1:0` — fastest/cheapest; used by Q Connect AI Agents

Gemini: `gemini-3.5-flash` (GA, recommended), `gemini-2.5-pro`, `gemini-2.5-flash`

### IAM user `connect-sre-agent-runtime` (manually managed, outside CloudFormation)

Attached policy: `sre_connect_AWS_access` (customer-managed, currently at v19).  
Credentials are mounted into the ECS container via `~/.aws` at runtime.

**Bedrock**
- `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` — Resource `"*"` required; cross-region inference profiles route through us-east-1 so a region-scoped ARN will silently fail.

**DynamoDB** — all standard CRUD actions (`GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Query`, `Scan`, `BatchGetItem`, `BatchWriteItem`) on every `dev-connect-sre-*` table and its GSIs:
`topology`, `journey-map`, `incidents`, `approvals`, `agent-runs`, `policy-config`, `tool-registry`, `model-config`, `incident-digests`, `memory`, `agent-steps`

**S3** — `ListBucket`/`GetBucketLocation` + `GetObject`/`PutObject`/`DeleteObject` on the four dev buckets: `runbooks`, `evidence`, `agent-traces`, `topology`.

**Connect read** — all `List*` and `Describe*` actions for instances, flows, flow modules, queues, routing profiles, users, hierarchy groups, hours of operation, phone numbers, quick connects, security profiles, prompts, bots, and Lambda functions. These feed the topology scanner and agent tools.
- `connect:GetCurrentMetricData` — real-time queue/agent metrics (`/api/monitoring/metrics?mode=live`)
- `connect:GetMetricDataV2` — historical metrics used by the `query_connect_metrics` tool. **Separate IAM action from `GetCurrentMetricData` — both must be granted explicitly.**

**Q Connect (wisdom namespace)** — boto3 client is `qconnect`; IAM actions use `wisdom:` prefix:
- `wisdom:ListAIAgents` — list all agents for the assistant (`/api/connect/ai-agents`)
- `wisdom:GetAIAgent` — fetch full agent config including prompt ID (`/api/connect/ai-agents`)
- `wisdom:ListAIPrompts` — enumerate prompts for the assistant
- `wisdom:GetAIPrompt` — resolve the model ID and status from a prompt ID; absence of this permission causes model to show as "Unknown" in the UI and health metrics to be unqueryable
- `wisdom:ListAssistants`, `wisdom:GetAssistant` — discover/validate the Q Connect assistant

**Lex** — `ListBots`, `ListBotAliases`, `DescribeBot`, `DescribeBotAlias` — topology scanner maps Lex bots as nodes in the Connect dependency graph.

**Lambda** — `GetFunction`, `GetFunctionConfiguration`, `ListAliases`, `ListVersionsByFunction` — topology scanner maps Lambda functions attached to contact flows.

**CloudWatch**
- `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `cloudwatch:ListMetrics`, `cloudwatch:DescribeAlarms` — Bedrock invocation metrics, Lex runtime metrics, and alarm state used by the health and monitoring endpoints
- `logs:DescribeLogGroups`, `logs:DescribeLogStreams`, `logs:FilterLogEvents`, `logs:GetLogEvents`, `logs:StartQuery`, `logs:StopQuery`, `logs:GetQueryResults` — CloudWatch Logs Insights queries against Connect flow logs

**KMS** — `Encrypt`, `Decrypt`, `ReEncrypt*`, `GenerateDataKey*`, `DescribeKey` — S3 bucket encryption.

**SQS / SSM / Step Functions** — `sqs:SendMessage/ReceiveMessage/DeleteMessage/GetQueueAttributes` (topology refresh queue), `ssm:StartAutomationExecution/GetAutomationExecution`, `states:StartExecution/DescribeExecution` (remediation workflows).

### boto3 version constraint

`runtime/requirements.txt` pins `boto3>=1.37.0`. The Q Connect AI Agent APIs (`list_ai_agents`, `get_ai_agent`, `get_ai_prompt`) were added in boto3 1.35.x. Do not downgrade below 1.35.0 or these calls will fail with `AttributeError: 'QConnect' object has no attribute 'list_ai_agents'`.

### Q Connect AI Agents

The Q Connect assistant ID for the `archdemos` Connect instance is `de018ffb-f5ea-4ff4-8547-714cb0eeb736` (set via `QCONNECT_ASSISTANT_ID` env var, with this value as the default). The boto3 client name is `qconnect`; IAM actions use the `wisdom:` prefix.

There is no dedicated Q Connect CloudWatch namespace — health signals come from:
- **AWS/Bedrock** — `Invocations`, `InvocationClientErrors`, `InvocationLatency` dimensioned by `ModelId`
- **AWS/Lex** — `RuntimeRequestCount`, `RuntimeUserErrors` for the Connect bot that hosts agent conversations

### Topology scanner must be run before the agent can be useful

The agent's blast-radius, flow-health, and module-dependency specialists all read from the DynamoDB topology graph (`dev-connect-sre-topology`). This table is **empty until the topology scanner runs**. Without it, the agent cannot scope incidents to specific resources and will block on every blast-radius check.

To populate for a Connect instance:
```bash
./infra/scripts/test_topology_scanner.sh
# or manually:
cd infra/src
TOPOLOGY_TABLE_NAME=dev-connect-sre-topology CONNECT_INSTANCE_IDS=<uuid> python topology_scanner.py
```

### CloudWatch alarms must carry Connect resource dimensions

The normalizer extracts `connectInstanceId` and `connectResourceId` from alarm dimensions. A bare alarm name (e.g. `Test-Connect-Fatal-Errors`) with no `InstanceId`/`ContactFlowId` dimensions means the agent has no resource IDs to query — it will block investigation immediately. Alarms should include:
- Dimension `InstanceId`: the Connect instance UUID
- Dimension `ContactFlowId` or `QueueId`: the specific resource in alarm

## Key constraints

- **Connect-specific** — all detection and diagnosis must be grounded in Connect concepts (flows, modules, queues, routing profiles, Lex bots, Q in Connect). Not a generic AWS SRE tool.
- **Topology graph is source of truth** during triage — read from DynamoDB, not live Connect APIs.
- **All writes go through `action_dispatcher.py`** — never call Connect write APIs directly from other Lambdas or the agent tools.
- **`propose_remediation` is supervisor-only** in the Strands path — specialist agents are intentionally read-only.
- Adding a new specialist agent requires: a system prompt in `prompts.py`, an `Agent` instance + `@tool` wrapper in `agents_bedrock.py`, and a corresponding persona description update in `SUPERVISOR_STRANDS_INSTRUCTION`.
