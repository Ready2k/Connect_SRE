# Amazon Connect SRE Agent Architecture

The Connect SRE Agent is designed as a hybrid, event-driven multi-agent platform using AWS and a provider-selectable inference runtime. Two inference paths are supported and selected at container start via the `MODEL_PROVIDER` environment variable:

- **`gemini`** — Google ADK (`google.antigravity`) with dynamic subagent spawning
- **`bedrock`** — AWS Strands SDK with 10 statically-registered specialist agents as supervisor tools

`./start.sh` prompts for provider and model interactively. `./stop.sh` stops the running container.

## High-Level Flow
1. **Ingestion**: Amazon EventBridge captures native AWS signals (CloudWatch Alarms, Connect Flow Logs, CloudTrail).
2. **Normalization**: The `normalizer.py` Lambda standardizes the event into a standard JSON payload and saves it to DynamoDB.
3. **Trigger**: EventBridge (or SQS) POSTs the standardized incident to the Agent Runtime via the Application Load Balancer.
4. **Investigation**: The FastAPI application receives the incident and kicks off `investigate_incident_background()` as an async background task.
5. **Multi-Agent Investigation**: The Supervisor agent picks up the incident. On the **Gemini path**, it dynamically spawns specialist subagents via ADK. On the **Bedrock path**, it calls 10 specialist agents registered as Strands tools — each scoped to read-only tooling. All paths query DynamoDB topology, CloudWatch, and S3 evidence stores.
6. **Remediation**: The Supervisor proposes a remediation action by writing an approval record to the DynamoDB approvals table via the `propose_remediation` tool (supervisor-only).
7. **Control Plane Execution**: Once approved via the UI, the `action_dispatcher.py` Lambda enforces policy gates and safely executes the remediation via SSM or native Connect APIs.

## Demo vs Live Operation
To facilitate demonstrations and safe exploration without requiring a fully populated AWS Connect environment, the system supports two operational modes:
* **Live Mode**: The FastAPI backend routes all requests to the underlying DynamoDB tables (`dev-connect-sre-incidents`, `dev-connect-sre-approvals`, etc.) and real AWS APIs.
* **Demo Mode**: The frontend appends `?mode=demo` to API requests. The backend intercepts these requests and immediately returns robust, hardcoded mock data for incidents, traces, agent status, and approvals, completely bypassing the AWS control plane.

## Infrastructure Map (AWS Option 2 - Developer Mode)
The infrastructure uses a VPC with Public subnets to avoid NAT Gateway charges while remaining highly secure.

* **ALB**: Locks inbound port 80/443 traffic specifically to the developer's home IP using the `AllowedAdminCIDR`.
* **ECS Fargate**: Runs the FastAPI / Antigravity Python container in isolated compute.
* **DynamoDB Tables**:
  - `dev-connect-sre-topology`: Real-time mapped dependency graph of the Connect instance.
  - `dev-connect-sre-incidents`: Historical records of alarms and configurations.
  - `dev-connect-sre-approvals`: Pending/Completed LLM actions requiring human sign-off.

## Enterprise Portability

Because the AWS Control Plane (EventBridge, Lambda, DynamoDB) strictly isolates the state and execution layer from the LLM reasoning layer, this architecture avoids vendor lock-in.

### Current: AWS Strands + Bedrock (supported today)

Switch to the Bedrock inference path by running `./start.sh` and selecting option 2. All data stays within the AWS perimeter. The Strands supervisor calls the same `tools.py` functions as the Gemini path — no tool changes required.

Supported Bedrock models (us-west-2 geo-inference):

| Model | ID |
|---|---|
| Claude Sonnet 4.6 (recommended) | `us.anthropic.claude-sonnet-4-6` |
| Claude Opus 4.7 | `us.anthropic.claude-opus-4-7` |
| Claude Haiku 4.5 (fastest) | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |

### Future: Managed Amazon Bedrock Agents

For Landing Zones that cannot run custom Docker containers at all:
- Replace the ECS Fargate cluster and FastAPI app with a managed **Amazon Bedrock Agent** as Supervisor.
- Wrap custom tools (`query_topology`, `fetch_runbook`, etc.) in Lambda functions attached as "Action Groups".
- Use Bedrock's native Multi-Agent Collaboration feature to replicate specialist orchestration.
