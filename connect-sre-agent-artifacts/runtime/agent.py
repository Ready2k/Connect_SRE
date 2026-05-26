import os
import asyncio
import functools
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "gemini").lower()
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")


def get_supervisor_agent(model_id: str = None, trace_fn=None):
    """Returns an async context manager that yields an agent with a .chat() method.

    Args:
        model_id: Optional model ID override. For Bedrock, replaces BEDROCK_MODEL_ID.
                  Allows runtime config changes to take effect without a restart.
        trace_fn: Optional callable(step: dict) for live trace streaming.
                  Supported on both Bedrock (specialist-level) and Gemini (tool-level).
    """
    if MODEL_PROVIDER == "bedrock":
        return _BedrockSupervisor(model_id=model_id, trace_fn=trace_fn)
    return _GeminiSupervisor(trace_fn=trace_fn)


# ---------------------------------------------------------------------------
# Shared utility
# ---------------------------------------------------------------------------

def _wrap_tool_with_trace(fn, trace_fn):
    """
    Return a wrapper that emits tool_call / tool_result trace steps around fn.

    functools.wraps copies __name__, __doc__, __annotations__, and sets
    __wrapped__, so ADK's inspect.signature() introspection sees the original
    parameter types and docstring unchanged.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # Build a compact arg summary for the headline
        all_args = list(args) + [f"{k}={v!r}" for k, v in kwargs.items()]
        arg_str = ", ".join(str(a)[:80] for a in all_args)
        trace_fn({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "tool_call",
            "agent": "ADK",
            "message": f"{fn.__name__}({arg_str[:140]})",
            "detail": f"Tool: {fn.__name__}\nArgs: {arg_str}",
        })
        result = fn(*args, **kwargs)
        # Build a short result summary
        try:
            parsed = json.loads(result) if isinstance(result, str) else result
            status = parsed.get("status", "")
            summary = f"{status} — {str(parsed)[:200]}" if status else str(parsed)[:200]
        except Exception:
            summary = str(result)[:200]
        trace_fn({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "tool_result",
            "agent": "ADK",
            "message": summary[:160],
            "detail": str(result)[:3000],
        })
        return result
    return wrapper


# ---------------------------------------------------------------------------
# Gemini (Google Antigravity ADK)
# ---------------------------------------------------------------------------

_GEMINI_TOOLS = None  # module-level cache so ADK import happens once


class _GeminiSupervisor:
    """
    Wraps google.antigravity.Agent as an async context manager.

    When trace_fn is provided, each SRE tool is wrapped so that every call
    emits tool_call / tool_result steps in real time.  functools.wraps
    preserves the original function signature so ADK introspection is unaffected.
    """

    def __init__(self, trace_fn=None):
        self._trace_fn = trace_fn
        self._agent = None
        self._handle = None   # whatever __aenter__ returns

    def _build_agent(self):
        from google.antigravity import Agent, LocalAgentConfig, types
        from prompts import SUPERVISOR_SYSTEM_INSTRUCTION
        from tools import (
            query_topology, calculate_blast_radius, query_recent_mutations,
            fetch_runbook, propose_remediation, query_connect_metrics,
            query_cloudwatch_flow_logs, recall_prior_incidents,
            record_investigation_memory,
        )

        tools = [
            query_topology, calculate_blast_radius, query_recent_mutations,
            fetch_runbook, propose_remediation, query_connect_metrics,
            query_cloudwatch_flow_logs, recall_prior_incidents,
            record_investigation_memory,
        ]

        if self._trace_fn:
            tools = [_wrap_tool_with_trace(t, self._trace_fn) for t in tools]

        capabilities = types.CapabilitiesConfig(enable_subagents=True)
        config = LocalAgentConfig(
            system_instructions=SUPERVISOR_SYSTEM_INSTRUCTION,
            capabilities=capabilities,
            tools=tools,
        )
        return Agent(config)

    async def __aenter__(self):
        self._agent = self._build_agent()
        # ADK Agent is an async context manager; __aenter__ may return self or a handle
        if hasattr(self._agent, '__aenter__'):
            self._handle = await self._agent.__aenter__()
        else:
            self._handle = self._agent
        logger.info("Gemini ADK supervisor ready (trace_fn=%s)", self._trace_fn is not None)
        return self

    async def __aexit__(self, *args):
        if self._agent and hasattr(self._agent, '__aexit__'):
            await self._agent.__aexit__(*args)

    async def chat(self, prompt: str):
        target = self._handle if self._handle is not None else self._agent
        return await target.chat(prompt)


# ---------------------------------------------------------------------------
# Bedrock (AWS Strands multi-agent)
# ---------------------------------------------------------------------------

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
