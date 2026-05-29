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
    if MODEL_PROVIDER == "demo":
        return _DemoSupervisor(trace_fn=trace_fn)
    if MODEL_PROVIDER == "bedrock":
        return _BedrockSupervisor(model_id=model_id, trace_fn=trace_fn)
    return _GeminiSupervisor(trace_fn=trace_fn)


# ---------------------------------------------------------------------------
# Demo supervisor — fully mocked, no external calls
# ---------------------------------------------------------------------------

class _DemoResponse:
    approx_input_tokens = 50
    approx_output_tokens = 220

    def __init__(self, text: str):
        self._text = text

    async def text(self) -> str:
        return self._text


class _DemoSupervisor:
    def __init__(self, trace_fn=None):
        self._trace_fn = trace_fn

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def chat(self, prompt: str) -> _DemoResponse:
        trace = self._trace_fn or (lambda _: None)

        def _now():
            return datetime.now(timezone.utc).isoformat()

        steps = [
            {"ts": _now(), "type": "specialist_call", "agent": "SUPERVISOR",
             "message": "→ FLOW agent: analysing contact flow health",
             "detail": "Checking error rates on primary IVR flow"},
            {"ts": _now(), "type": "tool_call", "agent": "FLOW",
             "message": "get_flow_health(contactFlowId='default-ivr')",
             "detail": "Querying flow error rate over the last 30 minutes"},
            {"ts": _now(), "type": "tool_result", "agent": "FLOW",
             "message": "Flow DEGRADED — 14.2% error rate (threshold 5%)",
             "detail": "contactFlowId=default-ivr status=DEGRADED errorRate=14.2 window=30m"},
            {"ts": _now(), "type": "specialist_call", "agent": "SUPERVISOR",
             "message": "→ IMPACT agent: calculating blast radius",
             "detail": "Traversing topology graph from default-ivr"},
            {"ts": _now(), "type": "tool_call", "agent": "IMPACT",
             "message": "calculate_blast_radius(nodeId='default-ivr', depth=3)",
             "detail": "BFS traversal of DEPENDS_ON edges"},
            {"ts": _now(), "type": "tool_result", "agent": "IMPACT",
             "message": "Blast radius: 3 queues, 2 routing profiles (~840 contacts/hr)",
             "detail": "queues=[Sales, Support, Billing] routingProfiles=[Standard, Priority]"},
            {"ts": _now(), "type": "specialist_call", "agent": "SUPERVISOR",
             "message": "→ RUNBOOK agent: searching remediation procedures",
             "detail": "Query: contact flow error rate degraded Lex"},
            {"ts": _now(), "type": "tool_call", "agent": "RUNBOOK",
             "message": "search_runbooks(query='contact flow error rate degraded')",
             "detail": "Vector search across runbook library"},
            {"ts": _now(), "type": "tool_result", "agent": "RUNBOOK",
             "message": "Runbook found: RB-CF-RECOVERY-001 (score 0.94)",
             "detail": "RB-CF-RECOVERY-001 — Contact Flow Recovery: bypass failing module, reroute to queue"},
        ]

        for step in steps:
            await asyncio.sleep(0.35)
            trace(step)

        report = (
            "## Investigation Summary\n\n"
            "**Root Cause:** Contact flow `default-ivr` is returning errors at 14.2% — nearly 3× "
            "the alerting threshold of 5%. A Lex V2 bot invoked by the routing module returned "
            "HTTP 503 responses starting at 14:22 UTC, causing the flow to fall to its error branch.\n\n"
            "**Blast Radius:**\n"
            "- 3 queues affected: Sales, Support, Billing\n"
            "- 2 routing profiles impacted: Standard, Priority\n"
            "- Estimated ~840 contacts/hr at risk of incorrect routing\n\n"
            "**Recommended Remediation:** Invoke runbook RB-CF-RECOVERY-001.\n"
            "1. Temporarily bypass the failing Lex module and route contacts directly to the agent queue.\n"
            "2. Investigate Lex bot service health in us-west-2.\n"
            "3. Redeploy or roll back the bot alias once service is confirmed healthy.\n\n"
            "*This is a demo investigation — no real AWS resources were queried.*"
        )
        return _DemoResponse(report)


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
            query_connect_ctrs, query_cloudwatch_flow_logs,
            recall_prior_incidents, record_investigation_memory,
        )

        tools = [
            query_topology, calculate_blast_radius, query_recent_mutations,
            fetch_runbook, propose_remediation, query_connect_metrics,
            query_connect_ctrs, query_cloudwatch_flow_logs,
            recall_prior_incidents, record_investigation_memory,
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
        result = await target.chat(prompt)
        # Attach approximate token counts so main.py can log them uniformly
        if not hasattr(result, 'approx_input_tokens'):
            result.approx_input_tokens = max(1, len(prompt) // 4)
            result.approx_output_tokens = 0
        return result


# ---------------------------------------------------------------------------
# Bedrock (AWS Strands multi-agent)
# ---------------------------------------------------------------------------

class _BedrockResponse:
    def __init__(self, text: str, approx_input_tokens: int = 0, approx_output_tokens: int = 0):
        self._text = text
        self.approx_input_tokens = approx_input_tokens
        self.approx_output_tokens = approx_output_tokens

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
        self._agent, self._accumulator = build_strands_supervisor(model, trace_fn=self._trace_fn)
        logger.info("Bedrock multi-agent supervisor ready: %s in %s", self._model_id, region)
        return self

    async def __aexit__(self, *args):
        pass

    async def chat(self, prompt: str) -> _BedrockResponse:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._agent, prompt)
        approx_output_tokens = getattr(self._accumulator, 'approx_output_tokens', 0)
        approx_input_tokens = max(1, len(prompt) // 4)
        return _BedrockResponse(str(result), approx_input_tokens, approx_output_tokens)
