# Amazon Connect SRE Agent

A domain-specific reliability and automation agent for Amazon Connect environments.

This platform operates a **Multi-Agent System** using the Google Antigravity SDK to automatically investigate, correlate, and remediate incidents across your Connect instance (Contact Flows, Modules, Queues, Lex Bots, and Lambda integrations).

## Documentation

* [Architecture Overview](docs/architecture.md) - Learn how EventBridge, the Control Plane, and the ADK Runtime interact.
* [Agents and Dynamic Personas](docs/agents.md) - Learn how the Supervisor dynamically spawns the 10 specialist personas to parallelize investigations.
* [Enterprise Ready Blueprint](ENTERPRISE_READY.md) - Guide for deploying this safely into a corporate Landing Zone.

## Directory Structure

* `/infra` - The AWS Control Plane. Contains the CloudFormation templates and the Python Lambdas for ingesting and normalizing Connect signals, mapping the topology, and executing safe remediations.
* `/runtime` - The ADK Agent Engine. A FastAPI application running on ECS Fargate that hosts the Google Antigravity Supervisor Agent and custom tools.
* `/ui` - The SRE Management Console. A React/Vite dashboard to view live topology, agent status, and approve pending remediations.
* `/docs` - System documentation.
