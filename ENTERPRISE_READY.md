# Enterprise Ready Blueprint

This guide covers deploying the Connect SRE Agent safely into a corporate AWS Landing Zone — VPC constraints, IAM boundaries, container image management, progressive feature enablement, and the path from developer mode to production.

---

## Architecture modes

### Developer mode (current default)

The CloudFormation template provisions a **VPC with public subnets and no NAT Gateway** to minimise cost for solo operators. The ALB ingress is locked to a single `AllowedAdminCIDR` (your home IP). ECS tasks run in those public subnets with a public IP — internet-accessible only from your IP, but not fully private.

This is the right topology for development and demos. Do not use it for production.

### Enterprise mode (Landing Zone)

For a corporate Landing Zone deployment:

| Component | Change required |
|---|---|
| VPC | Use pre-existing shared VPC with private subnets and Transit Gateway / VPC endpoints |
| ALB | Internal ALB (or remove ALB entirely if accessed via VPN/Direct Connect) |
| ECS | Remove `AssignPublicIp: ENABLED`; route egress through NAT Gateway |
| ECR | Push image to your own ECR in the target account |
| IAM | Replace `connect-sre-agent-runtime` IAM user with ECS task role |
| Secrets | Move `GEMINI_API_KEY` to AWS Secrets Manager; inject via ECS secrets |
| KMS | A KMS key is provisioned by the template — ensure your key policy allows the task role |

---

## CloudFormation parameters

All deployment decisions are controlled via CloudFormation parameters. No code changes are required to promote between environments.

| Parameter | Default | Purpose |
|---|---|---|
| `EnvironmentName` | `dev` | Prefix for all resource names (`dev-connect-sre-*`) |
| `PrimaryConnectInstanceId` | *(empty)* | If set, creates a CloudWatch Logs subscription filter for contact flow error ingestion |
| `EnableConnectWriteActions` | `false` | Master switch — must be `true` for any remediation to execute |
| `EnableAutonomousActions` | `false` | Allows `AUTO_APPROVED` actions to execute without UI sign-off |

**Production recommendation:** keep both feature flags `false` until you have validated incident triage quality over at least 30 days. Enable `EnableConnectWriteActions` with human approval only first; never enable `EnableAutonomousActions` in production without a formal change control review.

---

## Deploying to a new environment

### 1. Build and push the container image

```bash
# Build
./build.sh

# Tag and push to your ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --profile connect-sre-dev)
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/connect-sre-agent"

aws ecr get-login-password --region us-west-2 --profile connect-sre-dev \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"

docker tag connect-sre-agent-runtime:latest "${ECR_REPO}:latest"
docker push "${ECR_REPO}:latest"

# Or use the provided script
./infra/scripts/build_and_push.sh
```

### 2. Deploy the CloudFormation stack

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/connect-sre-agent-platform.yaml \
  --stack-name prod-connect-sre-platform \
  --parameter-overrides \
      EnvironmentName=prod \
      PrimaryConnectInstanceId=<your-connect-instance-uuid> \
      EnableConnectWriteActions=false \
      EnableAutonomousActions=false \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile connect-sre-dev
```

### 3. Seed the database

```bash
# Populate policies, tool registry, journeys, runbooks
./infra/scripts/run_seeds.sh

# Populate the topology graph
./infra/scripts/test_topology_scanner.sh
# or:
CONNECT_INSTANCE_IDS=<uuid> python infra/src/topology_scanner.py
```

### 4. Upload runbooks

```bash
RUNBOOK_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name prod-connect-sre-platform \
  --query "Stacks[0].Outputs[?OutputKey=='RunbookBucketName'].OutputValue" \
  --output text --profile connect-sre-dev)

aws s3 sync runbooks/ "s3://${RUNBOOK_BUCKET}/" --include "*.md" --profile connect-sre-dev
```

---

## IAM hardening

The CloudFormation template creates Lambda execution roles and an ECS task role (`{env}-connect-sre-runtime-task-role`) with the minimum permissions required. Review and tighten before production:

| Role | Key permissions | Hardening action |
|---|---|---|
| ECS task role | `connect:Get*`, `connect:List*`, `connect:Describe*`, DynamoDB CRUD on `dev-connect-sre-*`, S3 GetObject on runbook bucket, CloudWatch Logs Insights, `bedrock:InvokeModel*` | Scope DynamoDB to specific table ARNs; scope Bedrock to specific model IDs |
| Normalizer Lambda role | EventBridge PutEvents, DynamoDB PutItem/UpdateItem on incidents table, SQS SendMessage | Remove SQS permission if not using topology refresh |
| Topology Scanner Lambda role | `connect:List*`, `connect:Describe*`, `lexv2-models:DescribeBotAlias`, DynamoDB PutItem on topology table | Already narrow — no changes needed |
| Action Dispatcher Lambda role | DynamoDB GetItem/UpdateItem on approvals/incidents/policy/tool-registry tables, SSM StartAutomationExecution | Scope SSM to specific document names (`SRE-Connect-*`) |

### IAM user `connect-sre-agent-runtime` (manually managed)

This user is used for local development and is not created by CloudFormation. For production ECS, replace it with the task role and remove static credentials. Required permissions if you keep the user for dev:

- `bedrock:InvokeModel` + `bedrock:InvokeModelWithResponseStream` on Resource `"*"` (cross-region inference requires this)
- `connect:GetCurrentMetricData`, `connect:GetMetricDataV2`
- `wisdom:ListAIAgents`, `wisdom:GetAIAgent`, `wisdom:ListAIPrompts`, `wisdom:GetAIPrompt`
- All actions on `dev-connect-sre-*` DynamoDB tables
- `logs:StartQuery`, `logs:GetQueryResults`, `logs:DescribeLogGroups`, `logs:DescribeLogStreams`

---

## Secrets management

| Secret | Development | Production |
|---|---|---|
| `GEMINI_API_KEY` | Entered interactively at `./start.sh` prompt | Store in AWS Secrets Manager; inject as ECS secret |
| AWS credentials | `~/.aws` mounted into container | ECS task role (no static credentials) |
| `QCONNECT_ASSISTANT_ID` | Hardcoded default in `main.py` | Pass as ECS environment variable override |

### ECS secrets injection (Secrets Manager)

In the CloudFormation task definition:
```yaml
Secrets:
  - Name: GEMINI_API_KEY
    ValueFrom: arn:aws:secretsmanager:us-west-2:<account>:secret:connect-sre/gemini-api-key
```

---

## Progressive feature enablement

Follow this sequence when promoting to production. Each stage requires a validation period before proceeding.

```
Stage 0: Read-only (default)
  EnableConnectWriteActions = false
  EnableAutonomousActions   = false
  → Agent investigates and proposes remediations.
    No writes ever reach Connect APIs.
    Validate: are proposals accurate? Are blast radii correct?

Stage 1: Human-approved writes
  EnableConnectWriteActions = true
  EnableAutonomousActions   = false
  → Operators review and approve in /approvals.
    Action Dispatcher executes after approval.
    All approvals require human sign-off.
    Validate: do approved actions achieve the expected outcome?

Stage 2: Autonomous low-risk writes (optional)
  EnableConnectWriteActions = true
  EnableAutonomousActions   = true
  + Enable "Auto-approve SEV4 Changes" policy (POL-009) in DynamoDB
  → SEV4 remediations execute without UI interaction.
    Lambda actions still require human approval (POL-008).
    Validate in non-production first. Requires formal change control sign-off.
```

---

## Multi-account / multi-instance

The platform supports multiple Connect instances in a single deployment:

- Set `CONNECT_INSTANCE_IDS` to a comma-separated list of instance UUIDs
- The topology scanner crawls all listed instances into the same DynamoDB table
- The normalizer extracts `connectInstanceId` from alarm dimensions — each incident is scoped to its instance
- The UI live mode allows selecting an instance via `/instances`

For full account isolation (separate AWS accounts per Connect instance), deploy a separate CloudFormation stack per account. Cross-account EventBridge forwarding can funnel events to a central SRE account.

---

## Multi-region

The platform is designed for single-region deployment (us-west-2 by default). Multi-region considerations:

- Bedrock cross-region inference IDs (`us.anthropic.*`) already route through us-east-1 when needed — no change required for model calls
- Connect instances are regional; each region needs its own stack deployment
- DynamoDB tables are not replicated by default — use Global Tables if you need cross-region agent state

---

## Operational checklist before going live

- [ ] Topology scanner has been run and table has > 0 rows (`aws dynamodb scan --select COUNT`)
- [ ] CloudWatch alarms carry `InstanceId` and `ContactFlowId`/`QueueId` dimensions
- [ ] All runbooks uploaded to S3 runbook bucket
- [ ] `EnableConnectWriteActions=false` confirmed (or Stage 1 approved by change board)
- [ ] ALB ingress CIDR restricted to corporate VPN range, not `0.0.0.0/0`
- [ ] Static IAM credentials removed from ECS task (task role used instead)
- [ ] `GEMINI_API_KEY` moved to Secrets Manager (if using Gemini path)
- [ ] Log groups have retention policies set (CloudFormation creates them without retention — set to 90 days minimum)
- [ ] Alerts on Action Dispatcher `BLOCKED` events set up (indicates policy gate violations worth reviewing)
