# Amazon Connect SRE Agent Architecture

The Connect SRE Agent is designed as a hybrid, event-driven multi-agent platform using AWS and the Google Antigravity SDK.

## High-Level Flow
1. **Ingestion**: Amazon EventBridge captures native AWS signals (CloudWatch Alarms, Connect Flow Logs, CloudTrail).
2. **Normalization**: The `normalizer.py` Lambda standardizes the event into a standard JSON payload and saves it to DynamoDB.
3. **Trigger**: EventBridge (or SQS) POSTs the standardized incident to the ADK Runtime via the Application Load Balancer.
4. **Investigation**: The FastAPI application receives the incident and kicks off the `Agent.chat()` session in the background.
5. **Dynamic Subagents**: The Supervisor agent evaluates the incident, dynamically spawns required sub-agents, uses custom tools to query DynamoDB and S3, and investigates the outage.
6. **Remediation**: The agent proposes a remediation action by writing to the Approval DynamoDB table.
7. **Control Plane Execution**: Once approved via the UI, the `action_dispatcher.py` Lambda safely executes the remediation via SSM or native Connect APIs.

## Infrastructure Map (AWS Option 2 - Developer Mode)
The infrastructure uses a VPC with Public subnets to avoid NAT Gateway charges while remaining highly secure.

* **ALB**: Locks inbound port 80/443 traffic specifically to the developer's home IP using the `AllowedAdminCIDR`.
* **ECS Fargate**: Runs the FastAPI / Antigravity Python container in isolated compute.
* **DynamoDB Tables**:
  - `dev-connect-sre-topology`: Real-time mapped dependency graph of the Connect instance.
  - `dev-connect-sre-incidents`: Historical records of alarms and configurations.
  - `dev-connect-sre-approvals`: Pending/Completed LLM actions requiring human sign-off.
