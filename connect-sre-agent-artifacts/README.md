# Amazon Connect SRE Agent

A domain-specific reliability and automation agent for Amazon Connect environments.

This platform operates a **Multi-Agent System** that automatically investigates, correlates, and recommends remediations for incidents across your Connect instance (Contact Flows, Modules, Queues, Lex Bots, and Lambda integrations). It supports two inference provider paths — **Google ADK (Gemini)** and **AWS Strands (Bedrock)** — selected at container start time with no code changes required.

## Quick Start

```bash
# 1. Build the Docker image (run from connect-sre-agent-artifacts/)
docker build -t connect-sre-agent-runtime:latest -f runtime/Dockerfile .

# 2. Start — interactive prompt selects Gemini or Bedrock and model
./start.sh

# 3. Stop
./stop.sh
```

`start.sh` asks you to choose a provider:
- **Gemini** — prompts for a `GEMINI_API_KEY`, starts with `gemini-3.5-flash` by default
- **Bedrock** — uses the mounted `~/.aws` profile (`connect-sre-runtime`), lets you pick Claude Sonnet 4.6, Opus 4.7, or Haiku 4.5

The runtime is then available at `http://localhost:8000`.

## Documentation

* [Architecture Overview](docs/architecture.md) - Learn how EventBridge, the Control Plane, and the multi-agent runtime interact.
* [Agents and Dynamic Personas](docs/agents.md) - Learn how the Supervisor orchestrates the 10 specialist personas to parallelize investigations.
* [Enterprise Ready Blueprint](ENTERPRISE_READY.md) - Guide for deploying this safely into a corporate Landing Zone.

## Directory Structure

* `/infra` - The AWS Control Plane. Contains the CloudFormation templates and the Python Lambdas for ingesting and normalizing Connect signals, mapping the topology, and executing safe remediations.
* `/runtime` - The Agent Engine. A FastAPI application running on ECS Fargate that hosts the Supervisor Agent and custom tools, with provider-selectable inference (Google ADK or AWS Strands).
* `/ui` - The SRE Management Console. A React/Vite dashboard to view live topology, agent status, and approve pending remediations.
* `/docs` - System documentation.

## Demo vs Live Mode
The UI contains a toggle in the top right corner to switch between **Demo** and **Live** modes:
* **Live Mode**: The UI and FastAPI backend fetch real data from your DynamoDB tables and live AWS Connect resources.
* **Demo Mode**: The backend intercepts requests and serves robust mock data for Incidents, Traces, Agents, Approvals, and Logs, allowing for safe UI exploration and demonstrations without requiring a populated AWS environment.
