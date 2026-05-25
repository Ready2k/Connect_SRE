# Connect SRE Agent Artifacts

Updated starter artifacts for a domain-specific Amazon Connect reliability agent.

Files:

- `SPEC.md`
- `BUILDER_PROMPT.md`
- `infra/cloudformation/connect-sre-agent-platform.yaml`
- Compatibility copy: `infra/cloudformation/sre-agent-platform.yaml`

The product is now positioned as a Connect-aware SRE agent for customer journeys, contact flows, modules, queues, routing profiles, agents, Lex bots, Lambda integrations, Contact Lens, Q in Connect, and AI agent integrations.

The generic AWS SRE layer is now just the substrate. About time the plumbing stopped pretending to be the product.

Updated to explicitly cover live topology graph traversal, deterministic incident digests for high-volume logs, and strict safe remediation schemas.

Further updated to cover DynamoDB traversal latency, partial topology refresh on CloudTrail mutations, async multi-agent orchestration, LLM/tool observability, and missing-log diagnostic handling.
