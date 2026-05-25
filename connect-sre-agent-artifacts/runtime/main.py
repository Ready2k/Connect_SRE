import os
import logging
import random
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import boto3

from agent import get_supervisor_agent

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
    "primaryModel": "gemini-1.5-pro",
    "fallbackModel": "claude-3-sonnet",
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
async def get_incidents():
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
async def get_approvals():
    try:
        table = dynamodb.Table(APPROVAL_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch approvals: {e}")
        return []

@app.post("/api/approvals/{approval_id}/action")
async def action_approval(approval_id: str, payload: dict):
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
async def get_journeys():
    try:
        table = dynamodb.Table(JOURNEYS_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch journeys: {e}")
        return []

@app.get("/api/tools")
async def get_tools():
    try:
        table = dynamodb.Table(TOOLS_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch tools: {e}")
        return []

@app.get("/api/policy")
async def get_policy():
    try:
        table = dynamodb.Table(POLICY_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to fetch policy: {e}")
        return []

@app.get("/api/runbooks")
async def get_runbooks():
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
async def get_model_config():
    return _model_config

@app.patch("/api/models/config")
async def update_model_config(payload: ModelConfigPayload):
    _model_config.update(payload.model_dump(exclude_none=True))
    logger.info(f"Model config updated: {_model_config}")
    return {"status": "saved", "config": _model_config}

@app.get("/api/agents/status")
async def get_agents_status():
    """
    Returns the mocked status of the Antigravity Agent Swarm.
    In a fully stateful app, this would query an AgentRunTable DynamoDB table.
    """
    return {
      "supervisor": {
        "id": "supervisor",
        "name": "Connect Supervisor Agent",
        "status": "Orchestrating",
        "health": "100%",
        "model": "Gemini 2.5 Flash",
        "tasks": 12,
        "purpose": "Owns the incident lifecycle, delegates tasks to specialists."
      },
      "specialists": [
        {
          "id": "flow",
          "name": "Flow Health Agent",
          "status": "Idle",
          "health": "100%",
          "model": "Gemini 2.5 Flash",
          "tasks": 4,
          "purpose": "Diagnoses contact flow errors."
        },
        {
          "id": "queue",
          "name": "Queue & Routing Agent",
          "status": "Analyzing",
          "health": "98%",
          "model": "Gemini 2.5 Flash",
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
