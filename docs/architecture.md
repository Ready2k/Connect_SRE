# Amazon Connect SRE Agent — Architecture

This document describes the system architecture at four C4 levels: Context, Containers, Components, and key Code flows.

---

## Level 1 — System Context

Who uses the system and what external systems does it depend on?

```mermaid
graph TB
    OPS["🧑‍💻 SRE Operator\nReviews incidents, approves\nremediations, monitors health"]

    subgraph SRE ["Connect SRE Agent"]
        CORE["Detects, investigates, and\nrecommends remediations for\nAmazon Connect operational incidents"]
    end

    subgraph AWS_Ext ["AWS (monitored)"]
        CONN["Amazon Connect\nFlows · queues · routing · agents"]
        LEX["Amazon Lex V2\nNLU bot for Connect flows"]
        QC["Amazon Q in Connect\nAI agent orchestration\n(ORCHESTRATION type agents)"]
        CW["CloudWatch\nAlarms · Logs · Metrics"]
        CT["CloudTrail\nAPI mutation events"]
    end

    subgraph LLM ["LLM Providers (selectable at start)"]
        BEDROCK["AWS Bedrock\nClaude Haiku / Sonnet / Opus"]
        GEMINI["Google Gemini\ngemini-3.5-flash / 2.5-pro"]
    end

    OPS -->|"Browser / HTTPS"| SRE
    SRE -->|"connect: / lexv2: / qconnect: / cloudwatch: SDK"| AWS_Ext
    CT -->|"EventBridge rule"| SRE
    CW -->|"Alarm state changes\nFlow log errors"| SRE
    SRE -->|"Bedrock path"| BEDROCK
    SRE -->|"Gemini path"| GEMINI
```

---

## Level 2 — Containers

The major deployable units and how they communicate.

```mermaid
graph TB
    OPS["SRE Operator\n(Browser)"]

    subgraph VPC ["VPC — Public Subnets"]
        UI["SRE Console\nReact 19 + Vite\n(served from ECS :8000)"]
        API["Agent Runtime\nFastAPI + Python 3.11\nECS Fargate :8000"]
    end

    subgraph Lambdas ["Lambda Functions"]
        NL["Normalizer\nnormalizer.py\nEventBridge → DynamoDB → API"]
        SC["Topology Scanner\ntopology_scanner.py\nSchedule + SQS"]
        AD["Action Dispatcher\naction_dispatcher.py\nPolicy gates + Connect writes"]
    end

    subgraph Storage ["State (DynamoDB + S3)"]
        DDB[("DynamoDB\n9 tables")]
        S3[("S3\nRunbook Bucket")]
    end

    subgraph Events ["Event Bus"]
        EB["EventBridge\nCloudWatch Alarms\nCloudTrail mutations\nConnect flow logs"]
    end

    OPS -->|HTTPS| UI
    UI -->|"/api/* (same origin)"| API
    API --> DDB
    API --> S3
    EB --> NL
    NL --> DDB
    NL -->|"POST /api/incidents"| API
    EB --> SC
    SC --> DDB
    API -.->|"approved remediation"| AD
    AD --> DDB
```

### Demo vs Live mode

Every `GET` endpoint accepts `?mode=demo|live`. In demo mode the backend returns hardcoded mock data and never calls AWS APIs. The UI header toggle sets this globally — safe for demonstrations without a populated environment.

---

## Level 3 — Components

### 3.1 Agent Runtime (`runtime/`)

```mermaid
graph TB
    subgraph FASTAPI ["FastAPI — main.py"]
        RECV["POST /api/incidents\nReceive + enqueue"]
        BG["investigate_incident_background()\nBackgroundTask"]
    end

    subgraph ROUTER ["Agent Router — agent.py"]
        ENV{"MODEL_PROVIDER\nenv var"}
        GEMINI_P["Gemini Path\n_get_gemini_agent()\ngoogle.antigravity ADK\nenable_subagents=True"]
        STRANDS_P["Strands Path\n_BedrockSupervisor\nagents_bedrock.py\nbuild_strands_supervisor()"]
    end

    subgraph SPECIALISTS ["10 Specialist Agents (Strands path)"]
        FLOW["FLOW"] 
        MODULE["MODULE"]
        QUEUE["QUEUE"]
        LEXA["LEXA"]
        AIA["AIA"]
        CHANGE["CHANGE"]
        IMPACT["IMPACT"]
        RUNBOOK["RUNBOOK"]
        RISK["RISK"]
        VERIFY["VERIFY"]
    end

    subgraph TOOLS ["Tool Library — tools.py\n(provider-agnostic plain Python)"]
        T1["query_topology\ncalculate_blast_radius"]
        T2["query_connect_metrics\nquery_connect_ctrs\nquery_contact_lens\nquery_agent_events"]
        T3["query_lex_bot_health\nquery_ai_agent_health"]
        T4["query_cloudwatch_flow_logs\nquery_recent_mutations"]
        T5["fetch_runbook\npropose_remediation\nrecall_prior_incidents\nrecord_investigation_memory"]
    end

    RECV --> BG
    BG --> ENV
    ENV -->|gemini| GEMINI_P
    ENV -->|bedrock| STRANDS_P
    STRANDS_P --> SPECIALISTS
    SPECIALISTS --> TOOLS
    GEMINI_P --> TOOLS
```

**Strands thread model:** `_BedrockSupervisor.chat()` runs Strands synchronously inside a `ThreadPoolExecutor` so FastAPI's async event loop is never blocked. Strands `@tool` wrappers are applied in `agents_bedrock.py`, not in `tools.py`, preserving provider-agnosticism.

### 3.2 Normalizer Lambda (`infra/src/normalizer.py`)

Handles five distinct event shapes from EventBridge/CloudWatch Logs:

| Trigger | Pattern | Handler |
|---|---|---|
| CloudWatch Alarm | `source=aws.cloudwatch`, `detail-type=CloudWatch Alarm State Change` | `parse_cloudwatch_alarm()` |
| Connect mutation | `source=aws.cloudtrail`, `eventSource=connect.amazonaws.com` | `parse_connect_cloudtrail()` |
| Lex mutation | `source=aws.cloudtrail`, `eventSource=lexv2.amazonaws.com` | `parse_lex_cloudtrail()` |
| Lambda mutation | `source=aws.cloudtrail`, `eventSource=lambda.amazonaws.com` | `parse_lambda_cloudtrail()` |
| Flow log errors | `awslogs` key — CW Logs subscription filter | `parse_contact_flow_log_errors()` |

After parsing: `save_incident()` deduplicates within a 30-minute window (`DEDUPE_WINDOW_MINUTES`) then writes to DynamoDB. Configuration mutations also enqueue a topology refresh via SQS. All incident types call `trigger_agent_investigation()` → `POST /api/incidents`.

**CloudWatch alarm requirement:** alarms must carry Connect resource dimensions (`InstanceId` + `ContactFlowId` or `QueueId`). A bare alarm name without dimensions gives the agent no resource IDs to investigate.

### 3.3 Topology Scanner (`infra/src/topology_scanner.py`)

Crawls Connect APIs for all configured instance IDs and builds an adjacency-list graph in `dev-connect-sre-topology`. Each DynamoDB row is either:

- **`edgeTypeTarget = "METADATA"`** — node attributes (ARN, type, name)
- **`edgeTypeTarget = "DEPENDS_ON#<target>"`** — forward dependency edge
- **`edgeTypeTarget = "REQUIRED_BY#<target>"`** — reverse dependency edge

This enables BFS traversal in both directions, used by `calculate_blast_radius()` (upstream: what depends on a failed node) and `query_topology()` (all edges for a node).

**The table is empty until the scanner runs.** FLOW, MODULE, and IMPACT specialists cannot function without it.

### 3.4 Specialist Agents — tool scoping

| Specialist | Prompt constant | Tools |
|---|---|---|
| **FLOW** | `FLOW_HEALTH_PROMPT` | `query_topology`, `query_connect_metrics`, `query_cloudwatch_flow_logs` |
| **MODULE** | `MODULE_DEPENDENCY_PROMPT` | `query_topology`, `calculate_blast_radius` |
| **QUEUE** | `QUEUE_ROUTING_PROMPT` | `query_topology`, `query_connect_metrics`, `query_connect_ctrs`, `query_contact_lens`, `query_agent_events` |
| **LEXA** | `LEX_BOT_PROMPT` | `query_topology`, `query_lex_bot_health`, `query_connect_metrics` |
| **AIA** | `AI_ASSIST_PROMPT` | `query_topology`, `query_ai_agent_health` |
| **CHANGE** | `CHANGE_CORRELATION_PROMPT` | `query_recent_mutations` |
| **IMPACT** | `CUSTOMER_IMPACT_PROMPT` | `calculate_blast_radius`, `query_topology`, `query_contact_lens`, `query_agent_events` |
| **RUNBOOK** | `RUNBOOK_PROMPT` | `fetch_runbook` |
| **RISK** | `RISK_POLICY_PROMPT` | `calculate_blast_radius`, `query_topology` |
| **VERIFY** | `VERIFICATION_PROMPT` | `query_connect_metrics`, `query_cloudwatch_flow_logs` |
| **Supervisor only** | `SUPERVISOR_STRANDS_INSTRUCTION` | All above + `propose_remediation` |

### 3.5 Connect AI Agent management

Q Connect AI Agents (ORCHESTRATION type) are managed via the `qconnect` boto3 client. IAM actions use the `wisdom:` prefix despite the SDK client name.

```
GET /api/connect/ai-agents        → qconnect.list_ai_agents() + get_ai_prompt() per agent
GET /api/connect/ai-agents/health → CloudWatch AWS/Bedrock + AWS/Lex (60-min window)
```

Health signals: no dedicated Q Connect CloudWatch namespace exists. Proxy metrics:
- **`AWS/Bedrock`**, dimension `ModelId` — `Invocations`, `InvocationClientErrors`, `InvocationLatency`
- **`AWS/Lex`**, dimension `BotId` — `RuntimeRequestCount`, `RuntimeUserErrors`

The AIA specialist uses `query_ai_agent_health()` to pull all three in a single tool call during incident investigation.

---

## Level 4 — Key Code Flows

### Flow A: End-to-end incident investigation

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant NL as Normalizer Lambda
    participant DB as DynamoDB
    participant API as FastAPI
    participant SUP as Supervisor Agent
    participant SPEC as Specialist(s)
    participant TOOL as tools.py
    participant OPS as Operator

    EB->>NL: Alarm / CloudTrail / Flow Log event
    NL->>NL: Parse + deduplicate (30 min window)
    NL->>DB: Write incident record
    NL->>API: POST /api/incidents

    API->>API: investigate_incident_background() [BackgroundTask]
    API->>SUP: async with get_supervisor_agent()

    loop Investigation
        SUP->>SPEC: delegate (tool call)
        SPEC->>TOOL: query_topology / query_connect_metrics / etc.
        TOOL->>DB: Read topology / memory
        TOOL-->>SPEC: Result JSON
        SPEC-->>SUP: Finding
    end

    SUP->>TOOL: propose_remediation(action, params, justification)
    TOOL->>DB: Write PENDING approval record

    OPS->>API: GET /api/approvals → review finding
    OPS->>API: POST /api/approvals/{id}/action {decision: approved}
    API->>DB: Update → APPROVED
    Note over DB: Action Dispatcher Lambda reads<br/>APPROVED record, runs policy gates,<br/>executes Connect action
```

### Flow B: Q Connect AI Agent health check

```mermaid
sequenceDiagram
    participant SUP as Supervisor
    participant AIA as AIA Specialist
    participant TOOL as query_ai_agent_health()
    participant QC as qconnect API
    participant CW as CloudWatch

    SUP->>AIA: Investigate AI Agent failure agent_id=X
    AIA->>TOOL: query_ai_agent_health(agent_id="X")
    TOOL->>QC: get_ai_agent(assistantId, aiAgentId)
    QC-->>TOOL: name, status, visibilityStatus, tools, promptId
    TOOL->>QC: get_ai_prompt(promptId)
    QC-->>TOOL: modelId, promptStatus
    TOOL->>CW: AWS/Bedrock InvocationClientErrors (ModelId=<model>, 60 min)
    TOOL->>CW: AWS/Lex RuntimeUserErrors (BotId=<bot>, 60 min)
    TOOL-->>AIA: {status, errorRatePct, lexErrors, tools, locale}
    AIA-->>SUP: Failure mode + affected flows
```

### Flow C: UI serving (dev vs production)

```
Development
  Browser :5173  →  Vite proxy /api/*  →  FastAPI :8000

Production (Docker)
  Browser :8000  →  FastAPI serves /api/* routes
                 →  FastAPI serves ui/dist/ (StaticFiles)
                 →  /{full_path} catch-all → ui/dist/index.html
```

No Nginx. The Dockerfile two-stage build copies `ui/dist` into the Python container.

---

## Infrastructure overview (AWS)

```mermaid
graph LR
    DEV["SRE Operator\n(Home IP / AllowedAdminCIDR)"]

    subgraph VPC
        ALB["ALB :80/443\nIngress locked to\nAllowedAdminCIDR"]
        ECS["ECS Fargate\nconnect-sre-runtime\n:8000"]
    end

    subgraph Compute
        NL_F["Normalizer Lambda"]
        SC_F["Topology Scanner Lambda"]
        AD_F["Action Dispatcher Lambda"]
    end

    subgraph Storage
        DDB[("DynamoDB\n9 tables\ndev-connect-sre-*")]
        S3_B[("S3\nRunbook Bucket")]
    end

    subgraph Eventing
        EB_BUS["EventBridge Bus"]
        SQS_Q["SQS\nTopologyRefreshQueue"]
        CWL["CloudWatch Logs\n/aws/connect/{instanceId}"]
    end

    subgraph ConnectEstate ["Amazon Connect Estate"]
        CONN_I["Connect Instance"]
        LEX_B["Lex V2 Bot"]
        QCA["Q Connect\nAI Agents"]
    end

    DEV --> ALB --> ECS
    ECS --> DDB
    ECS --> S3_B
    ECS -->|"SDK calls"| ConnectEstate

    EB_BUS --> NL_F
    EB_BUS -->|"schedule"| SQS_Q
    SQS_Q --> SC_F
    CWL -->|"subscription filter"| NL_F
    NL_F --> DDB
    NL_F -->|"POST /api/incidents"| ECS
    SC_F --> DDB
    SC_F -->|"list* APIs"| CONN_I
    AD_F --> DDB
    AD_F -->|"write APIs"| CONN_I

    CONN_I -->|"Alarms + CloudTrail"| EB_BUS
    LEX_B -->|"CloudTrail"| EB_BUS
```

### CloudFormation template

`infra/cloudformation/connect-sre-agent-platform.yaml` is the primary template. `sre-agent-platform.yaml` at repo root is a compatibility copy — keep both in sync. Provisions: VPC, ALB, ECS Fargate task + service, all Lambda functions, IAM roles, DynamoDB tables, EventBridge rules, SQS queues, and optionally a CloudWatch Logs subscription filter (requires `PrimaryConnectInstanceId` parameter).

Feature flags (CloudFormation parameters, both default `false`):

| Parameter | Effect |
|---|---|
| `EnableConnectWriteActions` | Allows Action Dispatcher to call Connect write APIs |
| `EnableAutonomousActions` | Allows remediations without human approval |

---

## Data model

| Table | PK | SK | Notes |
|---|---|---|---|
| `dev-connect-sre-topology` | `nodeId` | `edgeTypeTarget` | `METADATA` = attrs; `DEPENDS_ON#X` / `REQUIRED_BY#X` = edges |
| `dev-connect-sre-incidents` | `incidentId` | — | GSI on `connectResourceId + createdAt` |
| `dev-connect-sre-approvals` | `approvalId` | — | States: `PENDING → APPROVED / REJECTED / AUTO_APPROVED` |
| `dev-connect-sre-policy-config` | `policyId` | — | Evaluated by `propose_remediation` at tool-call time |
| `dev-connect-sre-agent-runs` | `runId` | — | Trace header per investigation |
| `dev-connect-sre-agent-steps` | `runId` | `stepId` | Fine-grained step trace; TTL 90 days |
| `dev-connect-sre-journey-map` | `journeyId` | — | Customer journey definitions |
| `dev-connect-sre-tool-registry` | `toolId` | — | Tool metadata + enabled flag |
| `dev-connect-sre-memory` | `memoryId` | — | Long-term investigation memory; TTL 180 days |
