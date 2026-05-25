import os
import logging
from tools import query_topology, query_recent_mutations, fetch_runbook, propose_remediation, calculate_blast_radius
from prompts import SUPERVISOR_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

from google.antigravity import Agent, LocalAgentConfig, types

def get_supervisor_agent() -> Agent:
    """
    Instantiates and returns the Google Antigravity Supervisor Agent with all required capabilities,
    tools, and system instructions.
    """
    
    # Enable dynamic subagents so the Supervisor can autonomously spawn specialist personas
    capabilities = types.CapabilitiesConfig(
        enable_subagents=True
    )
    
    # Configure the tools available to the Supervisor and its subagents
    tools_config = types.ToolsConfig(
        enabled_tools=[
            query_topology,
            calculate_blast_radius,
            query_recent_mutations,
            fetch_runbook,
            propose_remediation
        ]
    )
    
    config = LocalAgentConfig(
        system_instruction=SUPERVISOR_SYSTEM_INSTRUCTION,
        capabilities=capabilities,
        tools=tools_config
    )
    
    return Agent(config)
