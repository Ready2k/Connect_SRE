import os
import logging
import random
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import boto3
import uuid

from agent import get_supervisor_agent, MODEL_PROVIDER, BEDROCK_MODEL_ID

# Human-readable label shown in traces and agent status responses
_ACTIVE_MODEL_LABEL = (
    BEDROCK_MODEL_ID if MODEL_PROVIDER == "bedrock" else "gemini-3.5-flash"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Amazon Connect SRE Agent Runtime")

# DynamoDB Clients
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))
connect_client = boto3.client("connect", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))
TOPOLOGY_TABLE = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
INCIDENT_TABLE = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")
JOURNEYS_TABLE = os.environ.get("JOURNEYS_TABLE_NAME", "dev-connect-sre-journey-map")
TOOLS_TABLE = os.environ.get("TOOLS_TABLE_NAME", "dev-connect-sre-tool-registry")
POLICY_TABLE = os.environ.get("POLICY_TABLE_NAME", "dev-connect-sre-policy-config")
RUNBOOKS_BUCKET = os.environ.get("RUNBOOKS_BUCKET_NAME", "dev-connect-sre-runbooks-388660028061-us-west-2")
TRACE_TABLE_NAME = os.environ.get("AGENT_RUNS_TABLE_NAME", "dev-connect-sre-agent-runs")

s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))

class IncidentPayload(BaseModel):
    incidentId: str
    source: str
    severity: str
    title: str
    details: str = ""
    metadata: Dict[str, Any] = {}

class ModelConfigPayload(BaseModel):
    agentMode: str
    primaryModel: str
    fallbackModel: str = ""

# In-memory config state (demo only — no DynamoDB config table yet)
_model_config: Dict[str, Any] = {
    "agentMode": "recommend_only",
    "primaryModel": _ACTIVE_MODEL_LABEL,
    "fallbackModel": "",
}

# In-memory cache for Connect instance list (avoid hammering the API)
_instances_cache: Dict[str, Any] = {"data": None, "fetched_at": 0}

async def investigate_incident_background(payload: IncidentPayload):
    logger.info(f"Starting investigation for incident {payload.incidentId}")
    try:
        async with get_supervisor_agent() as supervisor:
            prompt = (
                f"A new critical incident has been detected in Amazon Connect.\n"
                f"Incident ID: {payload.incidentId}\n"
                f"Source: {payload.source}\n"
                f"Severity: {payload.severity}\n"
                f"Title: {payload.title}\n"
                f"Details: {payload.details}\n"
                f"Metadata: {payload.metadata}\n\n"
                f"Please begin your investigation immediately by spawning the appropriate subagents."
            )
            response = await supervisor.chat(prompt)
            final_report = await response.text()
            logger.info(f"Investigation Complete for {payload.incidentId}. Final Report:\n{final_report}")
    except Exception as e:
        logger.error(f"Agent execution failed for incident {payload.incidentId}: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/connect/instances")
async def get_connect_instances():
    """Auto-discover all Connect instances in this AWS account. Cached 60s."""
    global _instances_cache
    now = time.time()
    if _instances_cache["data"] is not None and (now - _instances_cache["fetched_at"]) < 60:
        return {"instances": _instances_cache["data"], "cached": True}
    try:
        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))
        resp = connect_client.list_instances(MaxResults=10)
        instances = [
            {
                "instanceId": i["Id"],
                "instanceAlias": i.get("InstanceAlias", ""),
                "instanceStatus": i.get("InstanceStatus", "UNKNOWN"),
                "region": region,
                "createdTime": i.get("CreatedTime", "").isoformat() if hasattr(i.get("CreatedTime", ""), "isoformat") else str(i.get("CreatedTime", ""))
            }
            for i in resp.get("InstanceSummaryList", [])
        ]
        _instances_cache = {"data": instances, "fetched_at": now}
        return {"instances": instances, "cached": False}
    except Exception as e:
        logger.error(f"Failed to list Connect instances: {e}")
        raise HTTPException(status_code=503, detail=f"connect:ListInstances failed: {str(e)}")

@app.get("/api/instances/overview")
async def get_instances_overview():
    """Aggregated overview: all instances with their open incident counts from DynamoDB."""
    try:
        # Get instance list (uses cache)
        inst_resp = await get_connect_instances()
        instances = inst_resp.get("instances", []) if isinstance(inst_resp, dict) else []

        # Scan incidents table once
        inc_table = dynamodb.Table(INCIDENT_TABLE)
        inc_items = inc_table.scan(Limit=200).get("Items", [])

        # Count open incidents per instance (items may or may not have instanceId)
        result = []
        for inst in instances:
            iid = inst["instanceId"]
            # Filter incidents for this instance, or count all if no instanceId tag
            inst_incidents = [
                i for i in inc_items
                if i.get("instanceId", iid) == iid and i.get("status", "").lower() != "resolved"
            ]
            critical = sum(1 for i in inst_incidents if i.get("severity", "").upper() in ("SEV1", "SEV2"))
            result.append({
                **inst,
                "openIncidents": len(inst_incidents),
                "criticalIncidents": critical
            })

        return {"instances": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to build instances overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/incidents")
async def receive_incident(payload: IncidentPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(investigate_incident_background, payload)
    return {
        "status": "accepted",
        "message": f"Incident {payload.incidentId} queued for investigation.",
        "supervisor_started": True
    }

@app.get("/api/incidents")
async def get_incidents(mode: str = Query("demo")):
    if mode == "demo":
        return [
            {
                "incidentId": "INC-DEMO-001",
                "status": "Healthy",
                "createdAt": "2026-05-25T12:00:00Z",
                "source": "CloudWatch Alarm",
                "severity": "SEV1",
                "title": "Lex Bot Failure Rate High",
                "description": "High rate of fallback intents observed in Main_Routing."
            },
            {
                "incidentId": "INC-DEMO-002",
                "status": "Investigating",
                "createdAt": "2026-05-25T14:30:00Z",
                "source": "Connect Contact Lens",
                "severity": "SEV2",
                "title": "Customer Sentiment Drop",
                "description": "Average customer sentiment dropped below 0.2 in Billing."
            }
        ]
    try:
        table = dynamodb.Table(INCIDENT_TABLE)
        response = table.scan(Limit=50)
        # Sort newest first based on createdAt (mock sorting since scan doesn't order)
        items = response.get('Items', [])
        items.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        return items
    except Exception as e:
        logger.error(f"Failed to fetch incidents: {e}")
        return []

@app.post("/api/incidents/{incident_id}/trigger")
async def trigger_agent_for_incident(incident_id: str, mode: str = Query("demo")):
    if mode == "demo":
        return {"status": "success", "message": "Demo agent triggered."}
    try:
        table = dynamodb.Table(INCIDENT_TABLE)
        response = table.get_item(Key={'incidentId': incident_id})
        incident = response.get('Item')
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
            
        # Update incident status to investigating
        table.update_item(
            Key={'incidentId': incident_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'Investigating'}
        )
        
        # Write mock agent traces for demonstration
        trace_table = dynamodb.Table(TRACE_TABLE_NAME)
        now = datetime.utcnow()
        mock_traces = [
            {
                "runId": f"run-{uuid.uuid4().hex[:8]}",
                "incidentId": incident_id,
                "agentName": "SupervisorAgent",
                "startedAt": now.isoformat() + "Z",
                "latencyMs": 850,
                "modelId": _ACTIVE_MODEL_LABEL,
                "toolCalls": ["query_topology"],
                "status": "success",
                "thoughtProcess": f"I see an incident {incident_id}. I need to determine the blast radius by querying the topology graph.",
                "inputTokenCount": 1050,
                "outputTokenCount": 150,
                "costEstimate": "$0.0035"
            },
            {
                "runId": f"run-{uuid.uuid4().hex[:8]}",
                "incidentId": incident_id,
                "agentName": "FlowHealthAgent",
                "startedAt": (now + timedelta(seconds=1)).isoformat() + "Z",
                "latencyMs": 4200,
                "modelId": _ACTIVE_MODEL_LABEL,
                "toolCalls": ["query_cloudwatch_flow_logs", "query_connect_metrics"],
                "status": "success",
                "thoughtProcess": "The topology shows the issue is in the 'Main_Routing' flow. I am querying CloudWatch logs and Connect metrics to verify the error rate. Found 5 fatal errors relating to Lex bot timeout.",
                "inputTokenCount": 4500,
                "outputTokenCount": 800,
                "costEstimate": "$0.0150"
            },
            {
                "runId": f"run-{uuid.uuid4().hex[:8]}",
                "incidentId": incident_id,
                "agentName": "SupervisorAgent",
                "startedAt": (now + timedelta(seconds=6)).isoformat() + "Z",
                "latencyMs": 1200,
                "modelId": _ACTIVE_MODEL_LABEL,
                "toolCalls": ["propose_remediation"],
                "status": "success",
                "thoughtProcess": "The root cause is a Lex integration timeout. I will propose a remediation to route calls to the emergency fallback queue while Lex is recovering.",
                "inputTokenCount": 2100,
                "outputTokenCount": 200,
                "costEstimate": "$0.0080"
            }
        ]
        
        for trace in mock_traces:
            trace_table.put_item(Item=trace)

        return {"status": "success", "message": "Agent triggered."}
    except Exception as e:
        logger.error(f"Failed to trigger agent: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/incidents/{incident_id}/traces")
async def get_incident_traces(incident_id: str, mode: str = Query("demo")):
    if mode == "demo":
        return [
            {
                "runId": "run-demo-xyz",
                "incidentId": incident_id,
                "agentName": "SupervisorAgent",
                "startedAt": "2026-05-25T14:31:00Z",
                "latencyMs": 1200,
                "modelId": "Gemini 2.5 Flash",
                "toolCalls": ["query_topology", "query_cloudwatch_flow_logs"],
                "status": "success",
                "thoughtProcess": "Investigating the sentiment drop. Checking flow logs...",
                "inputTokenCount": 500,
                "outputTokenCount": 150,
                "costEstimate": "$0.002"
            }
        ]
    try:
        table = dynamodb.Table(TRACE_TABLE_NAME)
        # Using scan for MVP since we don't have a GSI on incidentId
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('incidentId').eq(incident_id)
        )
        items = response.get('Items', [])
        items.sort(key=lambda x: x.get('startedAt', ''))
        return items
    except Exception as e:
        logger.error(f"Failed to fetch traces: {e}")
        return []

@app.post("/api/traces")
async def create_trace(request: Request):
    try:
        data = await request.json()
        if 'runId' not in data:
            data['runId'] = f"run-{uuid.uuid4().hex[:8]}"
        if 'startedAt' not in data:
            data['startedAt'] = datetime.utcnow().isoformat() + "Z"
            
        table = dynamodb.Table(TRACE_TABLE_NAME)
        table.put_item(Item=data)
        return {"status": "success", "runId": data['runId']}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/agents/config")
async def get_agent_config():
    try:
        table = dynamodb.Table(POLICY_TABLE)
        response = table.get_item(Key={'policyId': 'AgentToolConfig'})
        
        default_config = {
            "logGroupName": "/aws/connect/default",
            "defaultTimeWindowMinutes": 60,
            "contactFlowLogsLocation": "s3://connect-contact-flow-logs/",
            "assumeRoleArn": ""
        }
        
        if 'Item' in response:
            stored_config = response['Item'].get('config', {})
            # Merge with defaults to ensure all fields are present
            return {**default_config, **stored_config, "iamExecutionRole": "arn:aws:iam::[account]:role/AgentRuntimeTaskRole"}
        else:
            return {**default_config, "iamExecutionRole": "arn:aws:iam::[account]:role/AgentRuntimeTaskRole"}
    except Exception as e:
        logger.error(f"Failed to fetch agent config: {e}")
        return {"error": str(e)}

@app.patch("/api/agents/config")
async def update_agent_config(payload: dict, mode: str = Query("demo")):
    if mode == "demo":
        return {"status": "success"}
    try:
        table = dynamodb.Table(POLICY_TABLE)
        table.put_item(Item={
            'policyId': 'AgentToolConfig',
            'enabled': True,
            'config': payload
        })
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to update agent config: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/topology")
async def get_topology(
    mode: str = Query("demo"),
    instanceId: Optional[str] = Query(None)
):
    # --- LIVE MODE: pull resources directly from Connect API ---
    if mode == "live" and instanceId:
        try:
            nodes = []
            edges = []

            # Fetch contact flows — use .get() for Name to guard against missing fields
            flows_resp = connect_client.list_contact_flows(InstanceId=instanceId, MaxResults=100)
            for i, flow in enumerate(flows_resp.get("ContactFlowSummaryList", [])):
                nodes.append({"id": flow.get("Id", f"flow-{i}"), "type": "default",
                               "data": {"label": f"Flow: {flow.get('Name', 'Unnamed Flow')}"},
                               "position": {"x": 50 + (i % 5) * 200, "y": 80}})

            # Fetch queues — use .get() for Name to guard against missing fields
            queues_resp = connect_client.list_queues(InstanceId=instanceId, QueueTypes=["STANDARD"], MaxResults=100)
            queue_summaries = queues_resp.get("QueueSummaryList", [])
            for i, q in enumerate(queue_summaries):
                nodes.append({"id": q.get("Id", f"queue-{i}"), "type": "default",
                               "data": {"label": f"Queue: {q.get('Name', 'Unnamed Queue')}"},
                               "position": {"x": 50 + (i % 5) * 200, "y": 280}})

            logger.info(f"Live topology: {len(nodes)} nodes fetched for instance {instanceId}")
            return {"nodes": nodes, "edges": edges, "source": "live"}
        except Exception as e:
            logger.warning(f"Live topology fetch failed, falling back to demo: {e}")
            # Fall through to demo mode below

    # --- DEMO MODE: DynamoDB scan (original behaviour) ---
    try:
        table = dynamodb.Table(TOPOLOGY_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        
        nodes = []
        edges = []
        
        for item in items:
            if item.get('edgeTypeTarget') == 'METADATA':
                col = len(nodes) % 5
                row = len(nodes) // 5
                nodes.append({
                    "id": item['nodeId'],
                    "type": "default",
                    "data": {"label": item.get('label', item['nodeId'])},
                    "position": {"x": 50 + col * 200, "y": 80 + row * 150}
                })
            else:
                edges.append({
                    "id": f"e-{item['nodeId']}-{item['edgeTypeTarget']}",
                    "source": item['nodeId'],
                    "target": item.get('targetNodeId', item['edgeTypeTarget']),
                    "animated": True
                })
        
        return {"nodes": nodes, "edges": edges, "source": "demo"}
    except Exception as e:
        logger.error(f"Failed to fetch topology: {e}")
        return {"nodes": [], "edges": [], "source": "error"}

@app.get("/api/approvals")
async def get_approvals(mode: str = Query("demo")):
    if mode == "demo":
        return [
            {
                "approvalId": "APP-DEMO-001",
                "incidentId": "INC-DEMO-002",
                "status": "PENDING",
                "createdAt": "2026-05-25T14:35:00Z",
                "actionType": "Update Lex Bot Alias",
                "resourceId": "SalesBot_V2"
            }
        ]
    try:
        table = dynamodb.Table(APPROVAL_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch approvals: {e}")
        return []

@app.post("/api/approvals/{approval_id}/action")
async def action_approval(approval_id: str, payload: dict, mode: str = Query("demo")):
    if mode == "demo":
        return {"status": "success", "approvalId": approval_id, "newStatus": payload.get("status", "REJECTED")}
    try:
        table = dynamodb.Table(APPROVAL_TABLE)
        status = payload.get("status", "REJECTED")
        justification = payload.get("justification", "")
        
        table.update_item(
            Key={'approvalId': approval_id},
            UpdateExpression="SET #s = :s, operatorJustification = :j",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': status, ':j': justification}
        )
        return {"status": "success", "approvalId": approval_id, "newStatus": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/journeys")
async def get_journeys(mode: str = Query("demo")):
    if mode == "demo":
        return [
            {"journeyId": "J-001", "name": "Main Sales Flow", "criticality": "High", "status": "Healthy"},
            {"journeyId": "J-002", "name": "Support Escalation", "criticality": "Medium", "status": "Degraded"}
        ]
    try:
        table = dynamodb.Table(JOURNEYS_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch journeys: {e}")
        return []

@app.get("/api/tools")
async def get_tools(mode: str = Query("demo")):
    if mode == "demo":
        return [
            {"toolId": "query_topology", "status": "Active", "description": "Fetches active connect resources"},
            {"toolId": "propose_remediation", "status": "Active", "description": "Generates approval ticket"}
        ]
    try:
        table = dynamodb.Table(TOOLS_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch tools: {e}")
        return []

@app.get("/api/policy")
async def get_policy(mode: str = Query("demo")):
    if mode == "demo":
        return [
            {"policyId": "POL-001", "name": "Require Human Approval for Remediations", "description": "Mandates that any state-changing remediation action must be explicitly approved by a human in the UI.", "enabled": True},
            {"policyId": "POL-002", "name": "Allow Connect Routing Profile Modification", "description": "Grants the agent permission to dynamically change routing profiles during a severe queue backup.", "enabled": False},
            {"policyId": "POL-003", "name": "Allow Connect Prompt Creation", "description": "Grants the agent permission to create temporary audio prompts for emergency IVR broadcasts.", "enabled": True}
        ]
    try:
        table = dynamodb.Table(POLICY_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        # Filter out AgentToolConfig which is internal
        return [item for item in items if item.get('policyId') != 'AgentToolConfig']
    except Exception as e:
        logger.error(f"Failed to fetch policy: {e}")
        return []

@app.patch("/api/policy")
async def update_policy(payload: list, mode: str = Query("demo")):
    if mode == "demo":
        return {"status": "success"}
    try:
        table = dynamodb.Table(POLICY_TABLE)
        with table.batch_writer() as batch:
            for policy in payload:
                batch.put_item(Item={
                    'policyId': policy['policyId'],
                    'name': policy.get('name'),
                    'description': policy.get('description'),
                    'enabled': policy.get('enabled', False)
                })
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to update policies: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/runbooks")
async def get_runbooks(mode: str = Query("demo")):
    if mode == "demo":
        return [
            {"key": "Runbook_Lex_Timeout.md", "size": 1024, "lastModified": "2026-05-25T10:00:00Z"}
        ]
    try:
        response = s3_client.list_objects_v2(Bucket=RUNBOOKS_BUCKET)
        items = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # For demo/MVP, fetch the content of the markdown file.
                # In prod, this should be a separate endpoint /api/runbooks/{id} to save bandwidth
                try:
                    obj_response = s3_client.get_object(Bucket=RUNBOOKS_BUCKET, Key=obj['Key'])
                    content = obj_response['Body'].read().decode('utf-8')
                except Exception as e:
                    content = f"Error loading content: {e}"

                items.append({
                    "id": obj['Key'],
                    "title": obj['Key'].split('/')[-1].replace('.md', '').replace('_', ' ').title(),
                    "category": obj['Key'].split('/')[0] if '/' in obj['Key'] else "General",
                    "status": "Active",
                    "lastUpdated": obj['LastModified'].isoformat() + "Z",
                    "content": content
                })
        return items
    except Exception as e:
        logger.error(f"Failed to fetch runbooks: {e}")
        return []

@app.get("/api/models/config")
async def get_model_config(mode: str = Query("demo")):
    if mode == "demo":
        return {"agentMode": "recommend_only", "primaryModel": "anthropic.claude-3-7-sonnet", "fallbackModel": "gemini-3.5-flash"}
    return _model_config

@app.patch("/api/models/config")
async def update_model_config(payload: ModelConfigPayload):
    _model_config.update(payload.model_dump(exclude_none=True))
    logger.info(f"Model config updated: {_model_config}")
    return {"status": "saved", "config": _model_config}

@app.get("/api/logs")
async def get_system_logs(mode: str = Query("demo")):
    if mode == "demo":
        return [
            { "time": "2026-05-25T14:32:01Z", "source": "EventBridge", "type": "Ingest", "details": "Received CW Metric Alarm", "status": "Success" },
            { "time": "2026-05-25T14:32:05Z", "source": "TopologyAgent", "type": "Query", "details": "Walk topology from ContactFlow_v4", "status": "Success" },
            { "time": "2026-05-25T14:32:45Z", "source": "PolicyEngine", "type": "Evaluate", "details": "Check rollback safety", "status": "Approved" }
        ]
    """
    Generate dynamic system logs based on traces and incident states.
    """
    logs = []
    try:
        table = dynamodb.Table(TRACE_TABLE_NAME)
        response = table.scan()
        for trace in response.get('Items', []):
            logs.append({
                "time": trace.get("startedAt", ""),
                "source": trace.get("agentName", "System"),
                "type": "Trace",
                "details": f"Ran tool {', '.join(trace.get('toolCalls', []))} for {trace.get('incidentId', '')}",
                "status": trace.get("status", "Success").capitalize()
            })
            
        incident_table = dynamodb.Table(INCIDENT_TABLE)
        inc_response = incident_table.scan()
        for inc in inc_response.get('Items', []):
            if inc.get("status") == "Investigating":
                logs.append({
                    "time": inc.get("updatedAt", datetime.utcnow().isoformat() + "Z"),
                    "source": "SupervisorAgent",
                    "type": "Investigation",
                    "details": f"Triggered full analysis for {inc.get('incidentId', '')}",
                    "status": "In Progress"
                })
                
        logs.sort(key=lambda x: x['time'], reverse=True)
    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        
    if not logs:
        # Fallback empty state
        return [{"time": datetime.utcnow().isoformat() + "Z", "source": "System", "type": "Info", "details": "No recent activity", "status": "Success"}]
    return logs

@app.get("/api/agents/status")
async def get_agents_status(mode: str = Query("demo")):
    """
    Returns the dynamic status of the Antigravity Agent Swarm.
    Checks if there are active investigations.
    """
    if mode == "demo":
        return {
          "supervisor": {
            "id": "supervisor", "name": "Connect Supervisor Agent", "status": "Investigating",
            "health": "100%", "model": _ACTIVE_MODEL_LABEL, "tasks": 12, "purpose": "Demo Mode Orchestration"
          },
          "specialists": [
            {
              "id": "flow", "name": "Flow Health Agent", "status": "Investigating",
              "health": "100%", "model": _ACTIVE_MODEL_LABEL, "tasks": 4, "purpose": "Demo Diagnostic"
            }
          ]
        }
    status_label = "Idle"
    try:
        table = dynamodb.Table(INCIDENT_TABLE)
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('Investigating')
        )
        if len(response.get('Items', [])) > 0:
            status_label = "Investigating"
    except Exception:
        pass

    return {
      "supervisor": {
        "id": "supervisor",
        "name": "Connect Supervisor Agent",
        "status": status_label,
        "health": "100%",
        "model": _ACTIVE_MODEL_LABEL,
        "tasks": 12,
        "purpose": "Owns the incident lifecycle, delegates tasks to specialists."
      },
      "specialists": [
        {
          "id": "flow",
          "name": "Flow Health Agent",
          "status": status_label if status_label == "Investigating" else "Idle",
          "health": "100%",
          "model": _ACTIVE_MODEL_LABEL,
          "tasks": 4,
          "purpose": "Diagnoses contact flow errors."
        },
        {
          "id": "queue",
          "name": "Queue & Routing Agent",
          "status": "Analyzing",
          "health": "98%",
          "model": _ACTIVE_MODEL_LABEL,
          "tasks": 1,
          "purpose": "Diagnoses queue wait time."
        }
      ]
    }

@app.get("/api/monitoring/metrics")
async def get_monitoring_metrics(
    mode: str = Query("demo"),
    instanceId: Optional[str] = Query(None)
):
    # --- LIVE MODE: fetch real-time metrics from Connect API ---
    if mode == "live" and instanceId:
        try:
            # Step 1: fetch STANDARD queue IDs — get_current_metric_data requires at least one
            queues_resp = connect_client.list_queues(InstanceId=instanceId, QueueTypes=["STANDARD"], MaxResults=100)
            queue_summaries = queues_resp.get("QueueSummaryList", [])
            queue_ids = [q["Id"] for q in queue_summaries if "Id" in q]

            if not queue_ids:
                logger.warning(f"No STANDARD queues found for instance {instanceId}, falling back to demo")
                raise ValueError("No queues found for this Connect instance")

            # Step 2: fetch real-time metrics scoped to those queues
            metric_resp = connect_client.get_current_metric_data(
                InstanceId=instanceId,
                Filters={"Queues": queue_ids, "Channels": ["VOICE"]},
                Groupings=["QUEUE"],
                CurrentMetrics=[
                    {"Name": "CONTACTS_IN_QUEUE", "Unit": "COUNT"},
                    {"Name": "AGENTS_ONLINE", "Unit": "COUNT"},
                    {"Name": "OLDEST_CONTACT_AGE", "Unit": "SECONDS"},
                ]
            )
            queue_data = metric_resp.get("MetricResults", [])
            # Build a name lookup so we can label queues by name in the response
            queue_name_map = {q["Id"]: q.get("Name", "Queue") for q in queue_summaries}
            total_contacts = sum(
                m.get("Value", 0)
                for r in queue_data for m in r.get("Collections", [])
                if m.get("Metric", {}).get("Name") == "CONTACTS_IN_QUEUE"
            )
            oldest_wait = max(
                (m.get("Value", 0)
                 for r in queue_data for m in r.get("Collections", [])
                 if m.get("Metric", {}).get("Name") == "OLDEST_CONTACT_AGE"),
                default=0
            )
            # Still pull incidents from DynamoDB for SEV counts
            inc_table = dynamodb.Table(INCIDENT_TABLE)
            inc_items = inc_table.scan(Limit=100).get("Items", [])
            open_sev1 = sum(1 for i in inc_items if i.get("status", "").lower() != "resolved" and i.get("severity", "").upper() == "SEV1")
            open_sev2 = sum(1 for i in inc_items if i.get("status", "").lower() != "resolved" and i.get("severity", "").upper() == "SEV2")

            # Build a live-sourced response matching the same schema as demo
            uptime = 99.99 - (0.05 * open_sev1) - (0.01 * open_sev2)
            queue_vols = [
                {
                    "name": queue_name_map.get(r.get("Dimensions", {}).get("Queue", {}).get("Id", ""), f"Queue {i+1}"),
                    "volume": int(next((m.get("Value", 0) for m in r.get("Collections", []) if m.get("Metric", {}).get("Name") == "CONTACTS_IN_QUEUE"), 0))
                }
                for i, r in enumerate(queue_data[:8])
            ]
            if not queue_vols:
                queue_vols = [{"name": "No queues", "volume": 0}]
            activity_feed = sorted(inc_items, key=lambda x: x.get("createdAt", ""), reverse=True)[:3]
            activity_feed = [{"id": i.get("incidentId", "?"), "severity": i.get("severity", "SEV4"), "title": i.get("title", ""), "createdAt": i.get("createdAt", "")} for i in activity_feed]
            return {
                "_source": "live",
                "sreOverview": {"status": "ACTIVE" if open_sev1 == 0 else "DEGRADED", "latency": "—", "throughput": f"{total_contacts} in queue"},
                "systemHealth": {"uptime": f"{uptime:.2f}%", "components": [
                    {"name": "OK", "value": float(f"{uptime:.2f}"), "color": "var(--status-ok)"},
                    {"name": "Warn", "value": float(f"{100.0 - uptime if open_sev2 > 0 else 0.01:.2f}"), "color": "var(--status-warn)"},
                    {"name": "Critical", "value": float(f"{open_sev1 * 2.5 if open_sev1 > 0 else 0.01:.2f}"), "color": "var(--status-critical)"}
                ]},
                "incidentsTimeSeries": [{"time": "live", "sev1": open_sev1, "sev2": open_sev2, "sev3": 0, "sev4": 0}],
                "queueVolumes": queue_vols,
                "queueHealthMetrics": [{"time": "now", "aht": 0, "wait": int(oldest_wait)}],
                "concurrentCalls": int(total_contacts),
                "abandonRate": "—",
                "lexBots": [],
                "activityFeed": activity_feed
            }
        except Exception as e:
            logger.warning(f"Live metrics fetch failed, falling back to demo: {e}")
            # Fall through to demo mode


    try:
        # 1. Fetch real-time values from DynamoDB
        incident_table = dynamodb.Table(INCIDENT_TABLE)
        incidents_response = incident_table.scan(Limit=100)
        inc_items = incidents_response.get('Items', [])
        
        approval_table = dynamodb.Table(APPROVAL_TABLE)
        approvals_response = approval_table.scan(Limit=50)
        app_items = approvals_response.get('Items', [])
        
        # 2. Count active incidents by severity
        # We classify open incidents as anything not having 'status' == 'Resolved'
        open_sev1 = 0
        open_sev2 = 0
        open_sev3 = 0
        open_sev4 = 0
        for item in inc_items:
            if item.get('status', '').lower() != 'resolved':
                sev = item.get('severity', '').upper()
                if sev == 'SEV1':
                    open_sev1 += 1
                elif sev == 'SEV2':
                    open_sev2 += 1
                elif sev == 'SEV3':
                    open_sev3 += 1
                elif sev == 'SEV4':
                    open_sev4 += 1

        # 3. Compile dynamic, micro-fluctuating SRE overview
        base_latency = 38.0 + random.uniform(-3.0, 5.0)
        if open_sev1 > 0:
            base_latency += 15.0 * open_sev1
        elif open_sev2 > 0:
            base_latency += 5.0 * open_sev2
            
        latency_str = f"{base_latency:.1f}ms"
        
        base_tps = 1.8 + random.uniform(-0.15, 0.15)
        if open_sev1 > 0:
            base_tps -= 0.3 * open_sev1
        tps_str = f"{base_tps:.2f}k TPS"
        
        # Overall Uptime
        uptime = 99.99
        if open_sev1 > 0:
            uptime -= 0.05 * open_sev1
        elif open_sev2 > 0:
            uptime -= 0.01 * open_sev2
        
        # Incident time-series
        time_series = [
            { "time": "00hrs", "sev1": 0, "sev2": 2, "sev3": 5, "sev4": 10 },
            { "time": "04hrs", "sev1": 1, "sev2": 3, "sev3": 8, "sev4": 12 },
            { "time": "08hrs", "sev1": 0, "sev2": 4, "sev3": 6, "sev4": 15 },
            { "time": "12hrs", "sev1": 2, "sev2": 5, "sev3": 9, "sev4": 14 },
            { "time": "16hrs", "sev1": 1, "sev2": 6, "sev3": 7, "sev4": 11 },
            { "time": "20hrs", "sev1": open_sev1, "sev2": open_sev2, "sev3": open_sev3, "sev4": open_sev4 }
        ]
        
        # Dynamic Queue volumes
        queue_vols = [
            { "name": "Sales", "volume": int(450 + random.randint(-30, 30)) },
            { "name": "Support", "volume": int(380 + random.randint(-25, 25)) },
            { "name": "Escalations", "volume": int(220 + random.randint(-15, 15) + (open_sev1 * 50)) },
            { "name": "Retention", "volume": int(310 + random.randint(-20, 20)) }
        ]
        
        # Concurrent calls
        concurrent = int(1120 + random.randint(-50, 50))
        wait_time = int(12 + random.randint(-3, 3) + (open_sev1 * 120) + (open_sev2 * 30))
        abandon_rate = f"{1.8 + random.uniform(-0.2, 0.2) + (open_sev1 * 8.5) + (open_sev2 * 2.1):.1f}%"
        
        # Lex Bot Health scores
        lex_bots = [
            { "name": "CustomerSupport_v2", "status": "Healthy" if open_sev1 == 0 else "Degraded", "score": int(98 - open_sev1 * 10), "color": "var(--status-ok)" if open_sev1 == 0 else "var(--status-warn)" },
            { "name": "BillingInquiry", "status": "Healthy", "score": int(96 + random.randint(-2, 2)), "color": "var(--status-ok)" },
            { "name": "Appointment", "status": "Healthy", "score": int(95 + random.randint(-3, 3)), "color": "var(--status-ok)" }
        ]
        
        # Activity feed items: compile real latest incidents
        activity_feed = []
        sorted_inc = sorted(inc_items, key=lambda x: x.get('createdAt', ''), reverse=True)
        for inc in sorted_inc[:3]:
            activity_feed.append({
                "id": inc.get("incidentId", "UNKNOWN"),
                "severity": inc.get("severity", "SEV3"),
                "title": inc.get("title", "Telemetry degradation"),
                "createdAt": inc.get("createdAt", "")
            })
            
        if not activity_feed:
            activity_feed.append({
                "id": "SYS-INIT",
                "severity": "SEV4",
                "title": "System degradation detected in EU-West-1 connection layer.",
                "createdAt": datetime.utcnow().isoformat() + "Z"
            })
            
        return {
            "sreOverview": {
                "status": "ACTIVE" if open_sev1 == 0 else "DEGRADED",
                "latency": latency_str,
                "throughput": tps_str
            },
            "systemHealth": {
                "uptime": f"{uptime:.2f}%",
                "components": [
                    { "name": "OK", "value": float(f"{uptime:.2f}"), "color": "var(--status-ok)" },
                    { "name": "Warn", "value": float(f"{100.0 - uptime if open_sev2 > 0 else 0.01:.2f}"), "color": "var(--status-warn)" },
                    { "name": "Critical", "value": float(f"{open_sev1 * 2.5 if open_sev1 > 0 else 0.01:.2f}"), "color": "var(--status-critical)" }
                ]
            },
            "incidentsTimeSeries": time_series,
            "queueVolumes": queue_vols,
            "queueHealthMetrics": [
                { "time": "00:00", "aht": 180, "wait": 12 },
                { "time": "12:00", "aht": 220, "wait": 45 },
                { "time": "15:00", "aht": 340, "wait": wait_time },
                { "time": "16:00", "aht": 250, "wait": max(5, wait_time // 2) },
                { "time": "20:00", "aht": 280, "wait": wait_time },
                { "time": "24:00", "aht": 200, "wait": max(5, wait_time // 4) }
            ],
            "concurrentCalls": concurrent,
            "abandonRate": abandon_rate,
            "lexBots": lex_bots,
            "activityFeed": activity_feed
        }
    except Exception as e:
        logger.error(f"Failed to compile SRE metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount React UI
UI_DIST_DIR = os.path.join(os.path.dirname(__file__), "ui", "dist")
if os.path.exists(UI_DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Serve index.html for any path not found (SPA routing fallback)
        return FileResponse(os.path.join(UI_DIST_DIR, "index.html"))
