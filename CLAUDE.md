# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Connect SRE Agent — a domain-specific SRE platform for Amazon Connect. It detects contact flow regressions, correlates infrastructure changes to incidents, calculates blast radius, and recommends (or dispatches) safe remediation actions. MVP is **read-only by default**; autonomous actions are disabled behind feature flags.

All code lives under `connect-sre-agent-artifacts/`.

## Commands

### UI (React + Vite)

```bash
cd connect-sre-agent-artifacts/ui
npm install
npm run dev      # Vite dev server → http://localhost:5173
npm run build    # Production build → dist/
npm run lint     # ESLint (no test runner configured yet)
npm run preview  # Serve production build locally
```

### Infrastructure

```bash
# Deploy or update the CloudFormation stack
aws cloudformation deploy \
  --template-file connect-sre-agent-artifacts/infra/cloudformation/connect-sre-agent-platform.yaml \
  --stack-name dev-connect-sre-platform \
  --parameter-overrides EnvironmentName=dev DefaultModelProvider=bedrock \
  --capabilities CAPABILITY_NAMED_IAM

# Update your developer IP in the admin security group (run from repo root)
./connect-sre-agent-artifacts/infra/scripts/update_dev_ip.sh
```

### Lambda functions (local execution)

```bash
cd connect-sre-agent-artifacts/infra/src
# Set required env vars then invoke directly:
TOPOLOGY_TABLE_NAME=dev-connect-sre-topology \
CONNECT_INSTANCE_IDS=<id1>,<id2> \
python topology_scanner.py

# Same pattern for normalizer.py, action_dispatcher.py, seed_topology.py
```

## Architecture

### Frontend (`ui/`)

Single-page React 19 app with React Router 7. Routes:

| Route | Purpose |
|---|---|
| `/` | Overview dashboard |
| `/incidents` | Incident browser |
| `/agents` | Agent management |
| `/monitoring` | Real-time metrics |
| `/topology` | Interactive React Flow graph of Connect resources |
| `/approvals` | Pending action approvals |
| `/config` | Model router + policy configuration |
| `/logs` | Audit trail |

Key libraries: `reactflow` (topology graph), Recharts (metrics charts), Lucide React (icons). Styling is vanilla CSS with CSS variables — no CSS framework.

**API integration:** Several components make `fetch` calls to `/api/*` endpoints. Vite proxies these to `http://127.0.0.1:8000` during development (`vite.config.js`). The backend API server at port 8000 is **not yet implemented** in this repo — components that call it (`Incidents`, `Agents`, `Topology`, `PendingApprovals`) will fall back to their error/loading states without it. Endpoints expected:
- `GET /api/incidents`
- `GET /api/agents/status`
- `GET /api/topology`
- `GET /api/approvals`
- `POST /api/approvals/{id}/action`

### Backend Lambda functions (`infra/src/`)

| File | Trigger | Role |
|---|---|---|
| `topology_scanner.py` | EventBridge schedule + SQS partial refresh | Crawls Connect APIs (flows, modules, queues, routing profiles, agents, Lex bots) and writes an adjacency-list graph to DynamoDB |
| `seed_topology.py` | One-shot bootstrap | Seeds business journey definitions and test topology data |
| `normalizer.py` | Event-driven | Normalizes CloudWatch metrics, correlates changes to incidents, generates deterministic incident digests |
| `action_dispatcher.py` | API/orchestrator call | Checks tool registry, policy gates, and approval state before executing any remediation; guards all writes |

### Data model (DynamoDB)

Four primary tables (names are CloudFormation parameters):

- **Topology table** — adjacency-list pattern: `nodeId` (PK) + `edgeTypeTarget` (SK). Stores both node metadata and edges in the same table.
- **Incidents table** — incident records with severity, trigger context, affected resources, and evidence.
- **Approvals table** — approval state machine for action governance (pending → approved/rejected).
- **Policy / Tool Registry tables** — what actions are allowed and under what conditions.

### Multi-agent design

The agent layer (Google ADK Python, not yet implemented in this repo) follows a **supervisor pattern**: a coordinator agent delegates to specialist agents (flow health, module dependency, queue routing, Lex bot health, AI agent/Q in Connect monitoring). The action_dispatcher enforces policy gates before any write reaches AWS.

Model provider is pluggable: Bedrock, Gemini, OpenAI-compatible, or mock — set via the `DefaultModelProvider` CloudFormation parameter.

### Feature flags

Both are CloudFormation parameters defaulting to `false`:

- `EnableConnectWriteActions` — allows the platform to modify Connect resources
- `EnableAutonomousActions` — allows changes without human approval

### Infrastructure (`infra/cloudformation/`)

`connect-sre-agent-platform.yaml` is the parent template. `sre-agent-platform.yaml` is a compatibility copy — keep them in sync. CloudFormation manages VPC networking, security groups, Lambda IAM roles, DynamoDB tables, EventBridge rules, and SQS queues.

## Key constraints (from BUILDER_PROMPT.md and SPEC.md)

- This platform is **Connect-specific**, not a generic AWS SRE tool — all detection and diagnosis logic must be grounded in Connect concepts (contact flows, modules, queues, routing profiles, Lex bots, Q in Connect).
- The topology graph is the source of truth for blast-radius analysis; always read from DynamoDB, not from live Connect APIs during incident triage.
- All remediation actions must pass through `action_dispatcher.py` policy gates — never call Connect write APIs directly from other functions.
- Retention: topology snapshots 180 days, evidence 90 days (enforced by DynamoDB TTL set in CloudFormation).
