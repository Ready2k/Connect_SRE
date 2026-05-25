import os
import asyncio
import logging

logger = logging.getLogger(__name__)

MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "gemini").lower()
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")


def get_supervisor_agent(model_id: str = None, trace_fn=None):
    """Returns an async context manager that yields an agent with a .chat() method.

    Args:
        model_id: Optional model ID override. For Bedrock, replaces BEDROCK_MODEL_ID.
                  Allows runtime config changes to take effect without a restart.
        trace_fn: Optional callable(step: dict) for live trace streaming (Bedrock only).
    """
    if MODEL_PROVIDER == "bedrock":
        return _BedrockSupervisor(model_id=model_id, trace_fn=trace_fn)
    return _get_gemini_agent()


# --- Gemini (Google Antigravity ADK) ---

def _get_gemini_agent():
    from google.antigravity import Agent, LocalAgentConfig, types
    from prompts import SUPERVISOR_SYSTEM_INSTRUCTION
    from tools import (
        query_topology, calculate_blast_radius, query_recent_mutations,
        fetch_runbook, propose_remediation, query_connect_metrics,
        query_cloudwatch_flow_logs,
    )

    capabilities = types.CapabilitiesConfig(enable_subagents=True)
    config = LocalAgentConfig(
        system_instructions=SUPERVISOR_SYSTEM_INSTRUCTION,
        capabilities=capabilities,
        tools=[
            query_topology, calculate_blast_radius, query_recent_mutations,
            fetch_runbook, propose_remediation, query_connect_metrics,
            query_cloudwatch_flow_logs,
        ],
    )
    return Agent(config)


# --- Bedrock (AWS Strands multi-agent) ---

class _BedrockResponse:
    def __init__(self, text: str):
        self._text = text

    async def text(self) -> str:
        return self._text


class _BedrockSupervisor:
    """
    Wraps the Strands multi-agent supervisor as an async context manager,
    matching the google.antigravity.Agent interface used by main.py.

    On __aenter__ it builds the full supervisor + 10 specialist agents via
    agents_bedrock.build_strands_supervisor(). Strands is synchronous, so
    chat() dispatches to a thread-pool executor to avoid blocking the event loop.
    """

    def __init__(self, model_id: str = None, trace_fn=None):
        self._model_id = model_id or BEDROCK_MODEL_ID
        self._trace_fn = trace_fn

    async def __aenter__(self):
        from strands.models.bedrock import BedrockModel
        from agents_bedrock import build_strands_supervisor

        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))
        model = BedrockModel(model_id=self._model_id, region_name=region)
        self._agent = build_strands_supervisor(model, trace_fn=self._trace_fn)
        logger.info("Bedrock multi-agent supervisor ready: %s in %s", self._model_id, region)
        return self

    async def __aexit__(self, *args):
        pass

    async def chat(self, prompt: str) -> _BedrockResponse:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._agent, prompt)
        return _BedrockResponse(str(result))
