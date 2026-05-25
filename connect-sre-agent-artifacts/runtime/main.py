import os
import logging
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
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
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

# Mount React UI
UI_DIST_DIR = os.path.join(os.path.dirname(__file__), "ui", "dist")
if os.path.exists(UI_DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(UI_DIST_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Serve index.html for any path not found (SPA routing fallback)
        return FileResponse(os.path.join(UI_DIST_DIR, "index.html"))
