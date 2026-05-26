"""
Strands multi-agent supervisor for the Bedrock provider path.

Architecture mirrors the Google ADK path (supervisor + 10 specialist agents)
but uses AWS Strands' explicit tool-delegation pattern rather than the ADK's
dynamic subagent spawning.  Each specialist is a full Strands Agent instance
wrapped as a @tool so the supervisor can call it by name.

The supervisor calls specialists via tool calls; specialists call the
underlying Connect/DynamoDB tools directly.  Only the supervisor may call
`propose_remediation` — specialists are read-only by design.
"""

import logging
import os
from datetime import datetime, timezone

from prompts import (
    SUPERVISOR_STRANDS_INSTRUCTION,
    FLOW_HEALTH_PROMPT,
    MODULE_DEPENDENCY_PROMPT,
    QUEUE_ROUTING_PROMPT,
    LEX_BOT_PROMPT,
    AI_ASSIST_PROMPT,
    CHANGE_CORRELATION_PROMPT,
    CUSTOMER_IMPACT_PROMPT,
    RUNBOOK_PROMPT,
    RISK_POLICY_PROMPT,
    VERIFICATION_PROMPT,
)
from strands import tool as _strands_tool
from tools import (
    calculate_blast_radius as _calculate_blast_radius,
    fetch_runbook as _fetch_runbook,
    propose_remediation as _propose_remediation,
    query_cloudwatch_flow_logs as _query_cloudwatch_flow_logs,
    query_connect_metrics as _query_connect_metrics,
    query_recent_mutations as _query_recent_mutations,
    query_topology as _query_topology,
    query_connect_ctrs as _query_connect_ctrs,
    recall_prior_incidents as _recall_prior_incidents,
    record_investigation_memory as _record_investigation_memory,
)

# Wrap with @tool so Strands can build JSON schemas for each function.
# tools.py stays provider-agnostic; the decorator is applied here at the
# Strands boundary only.
query_topology = _strands_tool(_query_topology)
calculate_blast_radius = _strands_tool(_calculate_blast_radius)
query_recent_mutations = _strands_tool(_query_recent_mutations)
fetch_runbook = _strands_tool(_fetch_runbook)
propose_remediation = _strands_tool(_propose_remediation)
query_connect_metrics = _strands_tool(_query_connect_metrics)
query_connect_ctrs = _strands_tool(_query_connect_ctrs)
query_cloudwatch_flow_logs = _strands_tool(_query_cloudwatch_flow_logs)
recall_prior_incidents = _strands_tool(_recall_prior_incidents)
record_investigation_memory = _strands_tool(_record_investigation_memory)

logger = logging.getLogger(__name__)


def _summarize(text: str, length: int = 160) -> str:
    """Return a short plain-text headline from potentially markdown-heavy output."""
    for line in text.split('\n'):
        clean = line.strip().lstrip('#*->-| ')
        if clean:
            return clean[:length] + ('…' if len(clean) > length else '')
    return text[:length]


def build_strands_supervisor(model, trace_fn=None):
    """
    Instantiate all 10 specialist Strands agents, wrap each as a @tool, and
    return a configured supervisor Agent that delegates to them.

    Args:
        model: A fully configured Strands model instance (e.g. BedrockModel).
        trace_fn: Optional callable(step: dict) invoked at each specialist
                  dispatch and result for live trace streaming.
                  On the Gemini path, tool-level wrapping is done in agent.py.
    Returns:
        A Strands Agent acting as the multi-agent supervisor.
    """
    from strands import Agent, tool

    def _emit(event_type: str, agent: str, message: str, detail: str = ""):
        if trace_fn:
            trace_fn({
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "agent": agent,
                "message": message,
                "detail": detail,
            })

    # ------------------------------------------------------------------
    # 1. Specialist agent instances
    # ------------------------------------------------------------------

    flow_agent = Agent(
        model=model,
        system_prompt=FLOW_HEALTH_PROMPT,
        tools=[query_topology, query_connect_metrics, query_cloudwatch_flow_logs],
    )

    module_agent = Agent(
        model=model,
        system_prompt=MODULE_DEPENDENCY_PROMPT,
        tools=[query_topology, calculate_blast_radius],
    )

    queue_agent = Agent(
        model=model,
        system_prompt=QUEUE_ROUTING_PROMPT,
        tools=[query_topology, query_connect_metrics, query_connect_ctrs],
    )

    lex_agent = Agent(
        model=model,
        system_prompt=LEX_BOT_PROMPT,
        tools=[query_topology, query_connect_metrics],
    )

    ai_assist_agent = Agent(
        model=model,
        system_prompt=AI_ASSIST_PROMPT,
        tools=[query_topology],
    )

    change_agent = Agent(
        model=model,
        system_prompt=CHANGE_CORRELATION_PROMPT,
        tools=[query_recent_mutations],
    )

    impact_agent = Agent(
        model=model,
        system_prompt=CUSTOMER_IMPACT_PROMPT,
        tools=[calculate_blast_radius, query_topology],
    )

    runbook_agent = Agent(
        model=model,
        system_prompt=RUNBOOK_PROMPT,
        tools=[fetch_runbook],
    )

    risk_agent = Agent(
        model=model,
        system_prompt=RISK_POLICY_PROMPT,
        tools=[calculate_blast_radius, query_topology],
    )

    verify_agent = Agent(
        model=model,
        system_prompt=VERIFICATION_PROMPT,
        tools=[query_connect_metrics, query_cloudwatch_flow_logs],
    )

    # ------------------------------------------------------------------
    # 2. Specialist tools — each wraps its agent as a callable tool.
    #    The @tool decorator reads the function's type hints and docstring
    #    to auto-generate the JSON schema the model sees.
    #    Closures capture the agent instances created above.
    # ------------------------------------------------------------------

    @tool
    def flow_health_specialist(query: str) -> str:
        """Delegate to the Flow Health Specialist (FLOW).
        Use when investigating errors inside a specific Amazon Connect contact flow,
        including broken blocks, Lambda invocation failures, or fatal flow errors.

        Args:
            query: The investigation question or task for the specialist.
        """
        logger.info("[FLOW] delegating: %.120s", query)
        _emit("specialist_call", "FLOW", query[:160], query)
        result = str(flow_agent(query))
        _emit("specialist_result", "FLOW", _summarize(result), result[:3000])
        return result

    @tool
    def module_dependency_specialist(query: str) -> str:
        """Delegate to the Module Dependency Specialist (MODULE).
        Use when a shared contact flow module may be broken and you need to find all
        parent flows affected by that module.

        Args:
            query: The investigation question or task for the specialist.
        """
        logger.info("[MODULE] delegating: %.120s", query)
        _emit("specialist_call", "MODULE", query[:160], query)
        result = str(module_agent(query))
        _emit("specialist_result", "MODULE", _summarize(result), result[:3000])
        return result

    @tool
    def queue_routing_specialist(query: str) -> str:
        """Delegate to the Queue and Routing Specialist (QUEUE).
        Use when diagnosing queue overflow, abnormal wait times, or routing profile
        misconfigurations in Amazon Connect.

        Args:
            query: The investigation question or task for the specialist.
        """
        logger.info("[QUEUE] delegating: %.120s", query)
        _emit("specialist_call", "QUEUE", query[:160], query)
        result = str(queue_agent(query))
        _emit("specialist_result", "QUEUE", _summarize(result), result[:3000])
        return result

    @tool
    def lex_bot_specialist(query: str) -> str:
        """Delegate to the Lex Bot Specialist (LEXA).
        Use when diagnosing Amazon Lex integration failures, intent recognition errors,
        or broken Lex bot alias references in Connect flows.

        Args:
            query: The investigation question or task for the specialist.
        """
        logger.info("[LEXA] delegating: %.120s", query)
        _emit("specialist_call", "LEXA", query[:160], query)
        result = str(lex_agent(query))
        _emit("specialist_result", "LEXA", _summarize(result), result[:3000])
        return result

    @tool
    def ai_assist_specialist(query: str) -> str:
        """Delegate to the AI Assist Specialist (AIA).
        Use when investigating Amazon Q in Connect or other generative AI components
        embedded in contact flows.

        Args:
            query: The investigation question or task for the specialist.
        """
        logger.info("[AIA] delegating: %.120s", query)
        _emit("specialist_call", "AIA", query[:160], query)
        result = str(ai_assist_agent(query))
        _emit("specialist_result", "AIA", _summarize(result), result[:3000])
        return result

    @tool
    def change_correlation_specialist(query: str) -> str:
        """Delegate to the Change Correlation Specialist (CHANGE).
        Use to identify recent configuration mutations on a specific Connect resource
        that may have triggered the current incident.

        Args:
            query: The investigation question or task for the specialist, including
                   the resource ID to investigate.
        """
        logger.info("[CHANGE] delegating: %.120s", query)
        _emit("specialist_call", "CHANGE", query[:160], query)
        result = str(change_agent(query))
        _emit("specialist_result", "CHANGE", _summarize(result), result[:3000])
        return result

    @tool
    def customer_impact_specialist(query: str) -> str:
        """Delegate to the Customer Impact Specialist (IMPACT).
        Use to calculate the blast radius of a failure: how many callers, queues,
        flows, and entry-point phone numbers are currently affected.

        Args:
            query: The investigation question or task for the specialist, including
                   the node ID that has failed.
        """
        logger.info("[IMPACT] delegating: %.120s", query)
        _emit("specialist_call", "IMPACT", query[:160], query)
        result = str(impact_agent(query))
        _emit("specialist_result", "IMPACT", _summarize(result), result[:3000])
        return result

    @tool
    def runbook_specialist(query: str) -> str:
        """Delegate to the Runbook Specialist (RUNBOOK).
        Use to retrieve the approved Standard Operating Procedure for a given outage type
        from the S3 runbook library.

        Args:
            query: The outage type or runbook topic to look up
                   (e.g. 'lex_bot_failure', 'flow_fatal_error', 'queue_overflow').
        """
        logger.info("[RUNBOOK] delegating: %.120s", query)
        _emit("specialist_call", "RUNBOOK", query[:160], query)
        result = str(runbook_agent(query))
        _emit("specialist_result", "RUNBOOK", _summarize(result), result[:3000])
        return result

    @tool
    def risk_policy_specialist(query: str) -> str:
        """Delegate to the Risk and Policy Specialist (RISK).
        Use before calling propose_remediation to validate that the planned action is
        within blast-radius limits and does not violate any active policies.

        Args:
            query: Description of the proposed remediation action, including the target
                   node ID and action type.
        """
        logger.info("[RISK] delegating: %.120s", query)
        _emit("specialist_call", "RISK", query[:160], query)
        result = str(risk_agent(query))
        _emit("specialist_result", "RISK", _summarize(result), result[:3000])
        return result

    @tool
    def verification_specialist(query: str) -> str:
        """Delegate to the Verification Specialist (VERIFY).
        Use after a remediation has been applied to confirm that the triggering alarm
        has cleared and error rates have returned to normal.

        Args:
            query: The verification request, including the instance ID, resource ID,
                   and the metric or log group to check.
        """
        logger.info("[VERIFY] delegating: %.120s", query)
        _emit("specialist_call", "VERIFY", query[:160], query)
        result = str(verify_agent(query))
        _emit("specialist_result", "VERIFY", _summarize(result), result[:3000])
        return result

    # ------------------------------------------------------------------
    # 3. Supervisor — sees all 10 specialist tools plus propose_remediation.
    #    Does NOT get raw DynamoDB/CloudWatch tools directly; it delegates.
    # ------------------------------------------------------------------

    supervisor = Agent(
        model=model,
        system_prompt=SUPERVISOR_STRANDS_INSTRUCTION,
        tools=[
            flow_health_specialist,
            module_dependency_specialist,
            queue_routing_specialist,
            lex_bot_specialist,
            ai_assist_specialist,
            change_correlation_specialist,
            customer_impact_specialist,
            runbook_specialist,
            risk_policy_specialist,
            verification_specialist,
            query_recent_mutations,
            query_topology,
            query_connect_ctrs,
            propose_remediation,
            recall_prior_incidents,
            record_investigation_memory,
        ],
    )

    logger.info("Strands multi-agent supervisor built with 10 specialist agents")
    return supervisor
