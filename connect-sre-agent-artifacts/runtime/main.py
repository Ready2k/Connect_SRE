import os
import logging
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict
import boto3

from agent import get_supervisor_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Amazon Connect SRE Agent Runtime")

# DynamoDB Clients
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))
TOPOLOGY_TABLE = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
INCIDENT_TABLE = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")

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
async def get_topology():
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
        
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        logger.error(f"Failed to fetch topology: {e}")
        return {"nodes": [], "edges": []}

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
async def get_monitoring_metrics():
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
