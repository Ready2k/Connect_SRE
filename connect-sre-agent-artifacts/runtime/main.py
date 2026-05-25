import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from agent import get_supervisor_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Amazon Connect SRE Agent Runtime")

class IncidentPayload(BaseModel):
    incidentId: str
    source: str
    severity: str
    description: str
    metadata: Dict[str, Any]

async def investigate_incident_background(payload: IncidentPayload):
    """
    Background task that spins up the Antigravity Agent to investigate the incident.
    """
    logger.info(f"Starting investigation for incident {payload.incidentId}")
    
    try:
        # We use an async context manager for the Antigravity Agent
        async with get_supervisor_agent() as supervisor:
            prompt = (
                f"A new critical incident has been detected in Amazon Connect.\n"
                f"Incident ID: {payload.incidentId}\n"
                f"Source: {payload.source}\n"
                f"Severity: {payload.severity}\n"
                f"Description: {payload.description}\n"
                f"Metadata: {payload.metadata}\n\n"
                f"Please begin your investigation immediately by spawning the appropriate subagents."
            )
            
            logger.info("Sending prompt to Supervisor Agent...")
            response = await supervisor.chat(prompt)
            
            # The agent may take several minutes to run subagents and tools. 
            # When it finishes, we log the final root cause analysis.
            final_report = await response.text()
            logger.info(f"Investigation Complete for {payload.incidentId}. Final Report:\n{final_report}")
            
    except Exception as e:
        logger.error(f"Agent execution failed for incident {payload.incidentId}: {str(e)}")

@app.get("/health")
async def health_check():
    """
    ALB Health check endpoint.
    """
    return {"status": "healthy"}

@app.post("/api/incidents")
async def receive_incident(payload: IncidentPayload, background_tasks: BackgroundTasks):
    """
    Receives normalized incidents from EventBridge/Lambda and triggers the SRE Agent.
    Returns a 202 Accepted immediately so the Lambda doesn't timeout while the agent investigates.
    """
    logger.info(f"Received new incident webhook: {payload.incidentId}")
    
    # Fire off the long-running LLM investigation into the background
    background_tasks.add_task(investigate_incident_background, payload)
    
    return {
        "status": "accepted",
        "message": f"Incident {payload.incidentId} queued for investigation.",
        "supervisor_started": True
    }
