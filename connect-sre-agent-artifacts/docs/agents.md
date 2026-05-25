# SRE Agent Personas & Dynamic Orchestration

The SRE platform uses the **Google Antigravity SDK** to run a powerful Multi-Agent System (MAS). Instead of hardcoding static workflows, we use a single overarching **Supervisor Agent** configured with dynamic sub-agents.

## How it Works (Dynamic Sub-Agents)
When an incident is received via FastAPI, the Supervisor is prompted with the error. Because `enable_subagents=True` is set in the `LocalAgentConfig`, the Supervisor uses its comprehensive System Instructions to autonomously spin up new "sub-agents". It gives these sub-agents specific personas, hands them the custom tools (e.g., `query_topology`), and asks them to investigate a narrow part of the problem.

This parallelizes the investigation and keeps the LLM's context window focused.

## The 10 Specialist Personas
The Supervisor is instructed to spin up the following personas when appropriate:

1. **FLOW (Flow Health Agent)**: Specialists in investigating Amazon Connect Contact Flows. Traverses flow dependencies.
2. **MODULE (Module Dependency Agent)**: Specialists in evaluating shared flow modules and mapping their parent dependencies.
3. **QUEUE (Queue and Routing Agent)**: Evaluates queue metrics, queue capacities, and Routing Profiles.
4. **LEXA (Lex Bot Agent)**: Checks Lex bot aliases, intents, and fallback routing in Connect.
5. **AIA (AI Assist Agent)**: Checks Amazon Q or Generative AI components inside Connect.
6. **CHANGE (Change Correlation Agent)**: Queries recent mutations to identify who or what broke the environment.
7. **IMPACT (Customer Impact Agent)**: Calculates how many calls or queues are affected by a node outage.
8. **RUNBOOK (Runbook Agent)**: Fetches and reads SOPs from the S3 runbook library.
9. **RISK (Risk and Policy Agent)**: Evaluates the safety of a proposed LLM action against policy.
10. **VERIFY (Verification Agent)**: Checks if an applied fix successfully cleared the alarm.
