import os
import logging
from tools import query_topology, query_recent_mutations, fetch_runbook, propose_remediation
from prompts import SUPERVISOR_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

# Stub / Mock implementations of Google Antigravity SDK classes to ensure 
# the SRE console runs and builds successfully without private PyPI access.
class MockResponse:
    def __init__(self, prompt):
        self.prompt = prompt

    async def text(self) -> str:
        return (
            "--- CONNECT SRE AGENT CORRELATION ANALYSIS ---\n"
            "[STATUS]: ACTIVE TRIAGE\n"
            "[ANALYSIS]: Supervisor agent scanned the topology graph. Detected a configuration change.\n"
            "[RCA]: Contact flow mutation detected. Evaluating wait time SLA breaches.\n"
            "[REMEDIATION]: Proposing safe emergency routing rollback via Action Dispatcher.\n"
            "[POLICY CHECK]: Blast radius estimated at 12% (safe limit < 20%). Awaiting human approval."
        )

class MockAgent:
    def __init__(self, config=None):
        self.config = config

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def chat(self, prompt: str) -> MockResponse:
        logger.info(f"Mock SRE Agent received incident details for triage.")
        return MockResponse(prompt)

class MockLocalAgentConfig:
    def __init__(self, **kwargs):
        pass

class MockTypes:
    class CapabilitiesConfig:
        def __init__(self, **kwargs):
            pass
    class ToolsConfig:
        def __init__(self, **kwargs):
            pass

# Attempt to load the real Google Antigravity SDK (if installed in the local virtualenv/container),
# otherwise fallback gracefully to our SRE stubs.
try:
    from google.antigravity import Agent, LocalAgentConfig, types
    logger.info("Successfully loaded Google Antigravity SDK.")
except ImportError:
    logger.warning("Google Antigravity SDK not found. Falling back to SRE developer stubs.")
    Agent = MockAgent
    LocalAgentConfig = MockLocalAgentConfig
    types = MockTypes

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
