import os
import asyncio
import logging

logger = logging.getLogger(__name__)

MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "gemini").lower()
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")


def get_supervisor_agent():
    """Returns an async context manager that yields an agent with a .chat() method."""
    if MODEL_PROVIDER == "bedrock":
        return _BedrockSupervisor()
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
    tools_config = types.ToolsConfig(enabled_tools=[
        query_topology, calculate_blast_radius, query_recent_mutations,
        fetch_runbook, propose_remediation, query_connect_metrics,
        query_cloudwatch_flow_logs,
    ])
    config = LocalAgentConfig(
        system_instruction=SUPERVISOR_SYSTEM_INSTRUCTION,
        capabilities=capabilities,
        tools=tools_config,
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

    async def __aenter__(self):
        from strands.models.bedrock import BedrockModel
        from agents_bedrock import build_strands_supervisor

        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))
        model = BedrockModel(model_id=BEDROCK_MODEL_ID, region_name=region)
        self._agent = build_strands_supervisor(model)
        logger.info("Bedrock multi-agent supervisor ready: %s in %s", BEDROCK_MODEL_ID, region)
        return self

    async def __aexit__(self, *args):
        pass

    async def chat(self, prompt: str) -> _BedrockResponse:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._agent, prompt)
        return _BedrockResponse(str(result))
