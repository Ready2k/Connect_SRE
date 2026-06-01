# Prompt Engineering for Amazon Connect AI Agents

## Overview

Prompt engineering is the practice of designing effective system prompts and instructions for AI agents in Amazon Connect. Well-crafted prompts directly impact response quality, latency, customer satisfaction, and containment rate. This guide covers principles, patterns, anti-patterns, and operational monitoring for AI agent prompts.

---

## Prompt Design Principles

### Be Specific

Tell the AI agent exactly what it should and should not do. Avoid ambiguity.

**Weak**: "Help customers with their issues."
**Strong**: "You are a billing support agent. Help customers check their balance, make payments, and dispute charges. Do not handle technical support requests — transfer those to the Technical queue."

### Provide Context

Give the agent the context it needs to do its job. Include the company's domain, the types of customers it serves, and the tools it has access to.

```
You assist customers of an online retail store. Customers may ask about order status,
returns, and shipping. You have access to the OrderLookup and ReturnStatus tools.
```

### Set Boundaries

Define what the agent must never do. Boundaries prevent hallucination and scope creep.

```
- Never promise refunds without verifying eligibility through the RefundEligibility tool.
- Never share internal policy documents with customers.
- Do not discuss competitor products.
- Do not ask customers for credit card numbers, SSNs, or full account numbers.
```

### Define Output Format

Specify how the agent should respond — tone, length, structure.

```
Respond in 1-3 sentences. Use a professional but friendly tone. If the customer's
request requires human assistance, say: "Let me connect you with a specialist who
can help with that."
```

---

## System Prompt Structure

A well-structured system prompt has four sections:

### 1. Role Definition

```
You are a customer service agent for a telecommunications company. You handle
billing inquiries, plan changes, and general account questions via phone.
```

### 2. Task Description

```
Your job is to:
1. Greet the customer and identify their need.
2. Use available tools to look up account information.
3. Resolve the issue or escalate to a human agent if needed.
4. Confirm resolution with the customer before ending the interaction.
```

### 3. Constraints

```
Rules:
- Never ask for or repeat sensitive information (SSN, credit card numbers).
- If the customer asks about service outages, use the OutageStatus tool.
- If you cannot resolve the issue in 3 attempts, transfer to the Escalation queue.
- Do not make up information. If unsure, say "Let me check on that for you."
- Keep responses under 50 words when speaking via voice channel.
```

### 4. Examples

```
Example — Good:
Customer: "What's my current balance?"
Agent: [Uses AccountLookup tool] "Your current balance is $47.50, due on March 15th.
Would you like to make a payment now?"

Example — Bad:
Customer: "What's my current balance?"
Agent: "Your balance should be around $50 based on your plan." (No tool used, guessed)
```

---

## Best Practices

### Keep Prompts Concise

Shorter prompts produce faster responses. Every additional token in the system prompt adds latency. Aim for 200-500 words. If the prompt exceeds 800 words, audit it for redundancy.

### Use Explicit Instructions

Replace vague directives with concrete rules:

| Vague | Explicit |
|-------|----------|
| "Be helpful" | "Answer the customer's question using available tools. If no tool applies, transfer to a human agent." |
| "Be careful with sensitive data" | "Do not ask for credit card numbers. If the customer provides one, say: 'For security, please do not share card numbers here.'" |
| "Handle escalations appropriately" | "Transfer to the Escalation queue if: the customer asks for a supervisor, expresses extreme dissatisfaction, or the issue cannot be resolved after 2 tool calls." |

### Define Escalation Criteria

Always include explicit escalation rules. Without them, AI agents either escalate too aggressively (low containment) or not enough (poor CX).

```
Transfer to a human agent when:
- The customer explicitly requests a human.
- The issue involves a billing dispute over $100.
- The customer has repeated the same question 3 times.
- A tool call returns an error and retry also fails.
- The interaction has exceeded 5 minutes without resolution.
```

### Test with Edge Cases

Before deploying, test prompts against these scenarios:

- **Angry customer**: Profanity, threats, demands for supervisor
- **Multiple intents**: "I want to check my balance AND change my plan"
- **Silence**: Customer stops responding mid-conversation
- **Out of scope**: "What's the weather like today?"
- **PII volunteered**: Customer reads out a credit card number unprompted
- **Language switching**: Customer switches between languages mid-call

---

## Anti-Patterns

### Overly Long System Prompts

Prompts exceeding 1000+ words slow response time and dilute important instructions. The model may ignore rules buried deep in a long prompt. Split complex logic into tools/knowledge bases instead.

### Vague Instructions

"Be helpful and professional" gives the model no actionable guidance. Every instruction should be testable — you should be able to look at a response and determine whether the instruction was followed.

### No Escalation Path

Without escalation rules, the AI agent will attempt to handle every scenario, including ones it cannot resolve. This leads to loops and frustrated customers.

### Not Handling PII

If the prompt does not address PII, the AI agent may ask for credit card numbers, repeat SSNs back to the customer, or log sensitive data in conversation history. Always include explicit PII handling rules.

### Contradictory Instructions

Avoid instructions that conflict. For example: "Always resolve the issue on first contact" combined with "Transfer to a human if the customer seems frustrated" creates ambiguity. Prioritize rules explicitly.

---

## Testing and Iteration

### A/B Test Prompts

Deploy two prompt variants to different queues or percentage splits. Compare metrics:

- **Containment rate**: % of contacts resolved without human transfer
- **Average handle time**: Total interaction duration
- **Customer satisfaction**: Post-contact survey scores
- **Escalation rate**: % transferred to human agents

### Review Contact Lens Transcripts

Use Contact Lens to review AI agent conversations. Look for:

- Responses that missed the customer's intent
- Unnecessary escalations
- Cases where the agent looped or repeated itself
- PII handling violations

### Iterate Weekly

Prompts are not set-and-forget. Review performance metrics and transcript samples weekly. Common iteration patterns:

1. Add a rule when a new edge case appears
2. Remove redundant instructions that the model already follows
3. Strengthen rules that the model occasionally violates
4. Update tool descriptions when tool behavior changes

---

## Troubleshooting AI Agent Issues

### Agent Loops (Repeating Same Question)

**Symptom**: AI agent asks the same question repeatedly or cycles between the same responses.

**Fixes**:
- Simplify the prompt — overly complex logic causes confusion
- Add explicit stop conditions: "If the customer has answered this question, do not ask again"
- Check if a tool is returning empty/error results, causing the agent to retry
- Add a max-turns limit: "After 3 exchanges without resolution, transfer to human"

### Tool Call Failures

**Symptom**: Agent says "I'm unable to look that up" or takes the error branch.

**Fixes**:
- Verify the Lambda function or MCP tool has correct IAM permissions
- Check the Lambda timeout (must complete within the configured timeout)
- Validate the tool input schema matches what the agent sends
- Review CloudWatch logs for the tool's Lambda function

### Slow Responses

**Symptom**: Long pauses before the AI agent speaks or responds.

**Fixes**:
- Reduce system prompt length — every token adds latency
- Check model selection — smaller models respond faster
- Review tool call latency — a slow Lambda adds to total response time
- Check knowledge base size and indexing status

### Hallucination

**Symptom**: Agent states information that is not grounded in tools or knowledge bases.

**Fixes**:
- Add grounding instructions: "Only state facts retrieved from tools. Do not guess."
- Attach a knowledge base for domain-specific information
- Add guardrails to block responses that contain unverified claims
- Use more specific prompts that constrain the response space

### Guardrail Blocks

**Symptom**: Responses are blocked or replaced with a default message.

**Fixes**:
- Review the guardrail configuration for overly aggressive filters
- Check for false positives — legitimate responses being blocked
- Add the blocked topic/phrase to the guardrail's allow list if appropriate
- Test the guardrail independently with sample inputs

---

## CloudWatch Monitoring for AI Agents

### Log Group

AI agent invocations are logged to:

```
/aws/connect/ai-agents/{instance-id}
```

Enable logging in the Amazon Connect console under the AI agent configuration.

### Key Metrics

| Metric | Description |
|--------|-------------|
| `InvocationCount` | Number of AI agent invocations |
| `Latency` | Time from invocation to response (ms) |
| `ErrorRate` | Percentage of invocations that failed |
| `TokenUsage` | Input + output tokens consumed per invocation |
| `EscalationRate` | Percentage of contacts transferred to human |

### Setting Up Alarms

Create CloudWatch alarms for operational awareness:

```javascript
const { CloudWatchClient, PutMetricAlarmCommand } = require("@aws-sdk/client-cloudwatch");

const client = new CloudWatchClient({ region: "us-east-1" });

await client.send(new PutMetricAlarmCommand({
  AlarmName: "AIAgentHighErrorRate",
  Namespace: "AWS/Connect",
  MetricName: "AIAgentErrors",
  Statistic: "Sum",
  Period: 300,
  EvaluationPeriods: 2,
  Threshold: 10,
  ComparisonOperator: "GreaterThanThreshold",
  AlarmActions: ["arn:aws:sns:us-east-1:123456789012:ops-alerts"]
}));
```

### Querying Logs for Debugging

Use CloudWatch Logs Insights to debug specific contacts:

```
fields @timestamp, @message
| filter contactId = "abc12345-def6-7890-abcd-ef1234567890"
| sort @timestamp asc
| limit 100
```

To find high-latency invocations:

```
fields @timestamp, contactId, latency
| filter latency > 3000
| sort latency desc
| limit 20
```

To find error patterns:

```
fields @timestamp, errorType, errorMessage
| filter @message like /ERROR/
| stats count(*) by errorType
| sort count desc
```
