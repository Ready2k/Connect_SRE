# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Connect SRE Agent — a domain-specific SRE platform for Amazon Connect. It detects contact flow regressions, correlates infrastructure changes to incidents, calculates blast radius, and recommends safe remediation actions. MVP is **read-only by default**; autonomous actions are disabled behind feature flags.

All code lives under `connect-sre-agent-artifacts/`. AWS profile for all infrastructure operations is `connect-sre-dev` (us-west-2). The runtime container uses `connect-sre-runtime`.

## Commands

### Runtime (Docker)

```bash
cd connect-sre-agent-artifacts

# Build the image (run from connect-sre-agent-artifacts/ — the Dockerfile is in runtime/)
docker build -t connect-sre-agent-runtime:latest -f runtime/Dockerfile .

# Start with interactive provider selection (Gemini or Bedrock)
./start.sh

# Stop
./stop.sh
```

`start.sh` prompts for provider choice:
- **Gemini** — asks for `GEMINI_API_KEY`, sets `MODEL_PROVIDER=gemini`
- **Bedrock** — uses the mounted `~/.aws` profile, sets `MODEL_PROVIDER=bedrock` + `BEDROCK_MODEL_ID`

### UI (React + Vite)

```bash
cd connect-sre-agent-artifacts/ui
npm install
npm run dev      # Vite dev server → http://localhost:5173 (proxies /api/* to :8000)
npm run build    # Production build → dist/  (built into Docker image)
npm run lint
```

### Lambda deploy & test scripts

All scripts require `--profile connect-sre-dev` (already embedded). Run from repo root:

```bash
./connect-sre-agent-artifacts/infra/scripts/deploy_normalizer.sh
./connect-sre-agent-artifacts/infra/scripts/deploy_topology_scanner.sh
./connect-sre-agent-artifacts/infra/scripts/test_normalizer.sh       # fires synthetic CloudWatch alarm
./connect-sre-agent-artifacts/infra/scripts/test_topology_scanner.sh # triggers full scan
./connect-sre-agent-artifacts/infra/scripts/update_dev_ip.sh         # update security group with current public IP
```

### Lambda functions (local execution)

```bash
cd connect-sre-agent-artifacts/infra/src
TOPOLOGY_TABLE_NAME=dev-connect-sre-topology \
CONNECT_INSTANCE_IDS=<id1>,<id2> \
python topology_scanner.py

# Same pattern for normalizer.py, action_dispatcher.py, seed_topology.py
```

### CloudFormation

```bash
aws cloudformation deploy \
  --template-file connect-sre-agent-artifacts/infra/cloudformation/connect-sre-agent-platform.yaml \
  --stack-name dev-connect-sre-platform \
  --parameter-overrides EnvironmentName=dev AllowedAdminCIDR=<your-ip>/32 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile connect-sre-dev
```

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

### FastAPI backend (`runtime/main.py`)

Live backend serving the UI. Key endpoints:

| Endpoint | Notes |
|---|---|
| `POST /api/incidents` | Queues agent investigation as background task |
| `GET /api/incidents`, `GET /api/incidents/{id}/traces` | Reads DynamoDB |
| `GET /api/topology?mode=demo\|live&instanceId=` | Demo: DynamoDB scan. Live: Connect API |
| `GET /api/monitoring/metrics?mode=demo\|live&instanceId=` | Demo: derived from incidents. Live: Connect real-time metrics |
| `GET /api/agents/status` | Returns active model label + mock agent swarm state |
| `GET/PATCH /api/models/config` | In-memory model config (reflects `_ACTIVE_MODEL_LABEL` from env) |
| `GET /api/approvals`, `POST /api/approvals/{id}/action` | Approval state machine |

`_ACTIVE_MODEL_LABEL` is derived at startup from `MODEL_PROVIDER` + `BEDROCK_MODEL_ID` env vars and flows into traces, agent status responses, and the default model config.

### Frontend (`ui/`)

Single-page React 19 app (React Router 7). Vite proxies `/api/*` → `http://127.0.0.1:8000`. Styling is vanilla CSS with CSS variables — no CSS framework. Key libraries: `reactflow` (topology), Recharts (metrics), Lucide React (icons).

Notable pages: `/config` loads active model config from `/api/models/config` on mount and shows an active provider banner. `/topology` supports `?mode=live&instanceId=` to fetch real Connect data. `/monitoring` same live/demo toggle.

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

### Infrastructure

`infra/cloudformation/connect-sre-agent-platform.yaml` is the primary template (`sre-agent-platform.yaml` is a compatibility copy — keep in sync). CloudFormation manages VPC (public subnets, no NAT Gateway), ALB locked to `AllowedAdminCIDR`, ECS Fargate, Lambda IAM roles, DynamoDB tables (TTL: topology 180d, evidence 90d), EventBridge rules, SQS queues.

Feature flags (CloudFormation parameters, both default `false`):
- `EnableConnectWriteActions` — allows modifying Connect resources
- `EnableAutonomousActions` — allows changes without human approval

### Current Bedrock model IDs (us-west-2)

us-west-2 has no In-Region support for Claude 4 models — use geo inference IDs:
- `us.anthropic.claude-sonnet-4-6` — recommended default
- `us.anthropic.claude-opus-4-7` — most capable
- `us.anthropic.claude-haiku-4-5-20251001-v1:0` — fastest/cheapest

Gemini: `gemini-3.5-flash` (GA, recommended), `gemini-2.5-pro`, `gemini-2.5-flash`

### IAM user `connect-sre-agent-runtime` (manually managed, outside CloudFormation)

This IAM user provides credentials to the ECS container via `~/.aws`. Required permissions:
- `bedrock:InvokeModel` + `bedrock:InvokeModelWithResponseStream` — **Resource: `"*"`** (cross-region inference routes through us-east-1, not just us-west-2)
- `connect:GetCurrentMetricData` — real-time queue/flow metrics
- `connect:GetMetricDataV2` — historical metrics used by `query_connect_metrics` tool
- All DynamoDB table actions on the `dev-connect-sre-*` tables
- CloudWatch Logs Insights (`logs:StartQuery`, `logs:GetQueryResults`, `logs:DescribeLogGroups`, `logs:DescribeLogStreams`)

When adding Connect API calls to `tools.py`, check `GetMetricDataV2` vs `GetCurrentMetricData` — they are **separate IAM actions** requiring separate grants.

### Topology scanner must be run before the agent can be useful

The agent's blast-radius, flow-health, and module-dependency specialists all read from the DynamoDB topology graph (`dev-connect-sre-topology`). This table is **empty until the topology scanner runs**. Without it, the agent cannot scope incidents to specific resources and will block on every blast-radius check.

To populate for a Connect instance:
```bash
./connect-sre-agent-artifacts/infra/scripts/test_topology_scanner.sh
# or manually:
cd connect-sre-agent-artifacts/infra/src
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
