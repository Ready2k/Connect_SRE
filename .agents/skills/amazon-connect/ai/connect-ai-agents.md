# Amazon Connect AI Agents

## Overview

Amazon Connect AI is powered by Amazon Bedrock and provides GDPR/HIPAA-compliant generative AI capabilities across two primary modes:

- **Agentic self-service** -- autonomous AI agents that handle customer interactions end-to-end without human intervention
- **Agent-assist** -- real-time AI that supports human agents during live conversations

All AI features are managed through the Amazon Q Connect service APIs and configured via the Connect admin console or programmatically.

---

## Agentic Self-Service

### Orchestrator AI Agents

Agentic self-service uses an **orchestrator AI agent** that performs autonomous multi-step reasoning to resolve customer requests. The orchestrator:

- Breaks down complex customer intents into sub-tasks
- Decides which tools to invoke and in what order
- Maintains conversation context across multiple turns
- Handles disambiguation when customer intent is unclear
- Escalates to a human agent when it determines it cannot resolve the issue
- Retries failed tool calls with adjusted parameters
- Provides natural conversational responses while executing backend actions

### Orchestrator Behavior

The orchestrator follows a reasoning loop:

1. **Observe** -- receive the customer's message and conversation history
2. **Think** -- analyze intent, determine what information is needed, plan next steps
3. **Act** -- invoke a tool (MCP, Return to Control, or Constant) or generate a response
4. **Respond** -- provide a natural language response to the customer
5. **Repeat** -- continue the loop until the issue is resolved or escalation is needed

The orchestrator can chain multiple tool calls in a single turn (e.g., look up account, check order status, process return) without requiring the customer to repeat information.

### Architecture

```
Customer --> Connect Flow --> Conversational AI Bot (Lex) --> Orchestrator AI Agent
                                                                  |
                                                          +-------+-------+
                                                          |       |       |
                                                        Tools   KB    Guardrails
```

### MCP Tool Integration

The orchestrator agent invokes tools to perform actions. Four tool categories are supported:

#### 1. MCP Tools (Backend Actions)

MCP (Model Context Protocol) tools connect the AI agent to backend systems for real-time data retrieval and actions:

- Look up account information
- Check order status
- Process returns or cancellations
- Update customer records
- Query external APIs
- Execute business logic

MCP tools are defined with input/output schemas and the orchestrator decides when and how to invoke them based on conversation context.

**Tool definition includes:**
- **Name** -- unique identifier for the tool
- **Description** -- natural language description of what the tool does (used by the orchestrator to decide when to invoke)
- **Input schema** -- JSON schema defining required and optional parameters
- **Output schema** -- expected response format
- **Endpoint** -- the backend service URL or Lambda ARN

#### 2. Return to Control Tools

Return to Control tools hand execution back to the Connect flow for processing.

**Built-in Return to Control tools:**
- **Complete** -- signals the conversation is resolved; the flow can perform wrap-up actions
- **Escalate** -- signals the AI cannot handle the request; the flow routes to a human agent

**Custom Return to Control tools** allow structured data to be passed back to the flow with a defined JSON input schema:

```json
{
  "type": "object",
  "properties": {
    "customerIntent": {
      "type": "string",
      "description": "The detected customer intent"
    },
    "sentiment": {
      "type": "string",
      "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE", "FRUSTRATED"],
      "description": "Current customer sentiment"
    },
    "escalationSummary": {
      "type": "string",
      "description": "Brief summary of the conversation so far"
    },
    "escalationReason": {
      "type": "string",
      "description": "Why the AI is escalating to a human"
    }
  },
  "required": ["customerIntent", "sentiment", "escalationReason"]
}
```

**Handling Return to Control in flows:**

When a Return to Control tool fires, the flow receives control back. Use the **Check contact attributes** block to inspect the Lex session attribute `"Tool"`:

```
Check contact attributes
  Namespace: Lex
  Key: Tool
  Conditions:
    "Escalate" --> Route to queue
    "Complete" --> Disconnect
    "CustomTool" --> Custom handling branch
```

Custom tool output fields are available as additional Lex session attributes for downstream flow logic.

#### 3. Constant Tools

Constant tools return a static string value every time they are invoked. Useful for:

- Testing and development
- Providing fixed reference data (e.g., business hours, policy text)
- Mocking backend responses during flow development
- Injecting static context the orchestrator can reference

#### 4. Built-in Tools

Built-in tools are provided by Amazon Connect and available without additional configuration:

- **Knowledge Base Search** -- queries associated knowledge bases for relevant content
- **Complete** -- ends the self-service interaction successfully
- **Escalate** -- transfers to a human agent

---

## Agent-Assist

Agent-assist provides real-time AI support to human agents during live conversations:

- **Generative responses** -- AI-generated suggested replies based on conversation context and knowledge base content
- **Document links** -- direct links to relevant knowledge base articles, SOPs, and documentation
- **Recommended actions** -- suggested next steps or actions the agent should take based on the current conversation state
- **Intent detection** -- real-time classification of customer intent displayed to the agent
- **Note taking** -- AI-generated structured notes from the conversation

Agent-assist surfaces in the agent workspace (CCP or custom agent desktop) as a panel that updates in real time as the conversation progresses.

### How Agent-Assist Works

1. Contact Lens streams the conversation transcript to Q Connect in real time
2. Q Connect analyzes the transcript and detects customer intent
3. Knowledge base content is retrieved based on the conversation context
4. AI generates response suggestions and surfaces relevant documents
5. Agent sees recommendations in the workspace panel
6. Agent can click to insert a suggestion, open a document, or ignore
7. Agent provides feedback (helpful/not helpful) to improve future recommendations

---

## AI Agent Types (10 Total)

Each AI agent type corresponds to a specific function. You can override the system default configuration for each type.

| # | Agent Type | API Type Value | Description |
|---|------------|----------------|-------------|
| 1 | **Orchestration** | `SELF_SERVICE` | Top-level orchestrator for agentic self-service; controls reasoning, planning, and tool selection |
| 2 | **Answer Recommendation** | `ANSWER_RECOMMENDATION` | Suggests answers to agents during live voice/chat conversations based on KB content |
| 3 | **Manual Search** | `MANUAL_SEARCH` | Powers agent-initiated knowledge base searches from the workspace panel |
| 4 | **Self Service** | `SELF_SERVICE` | Handles autonomous customer self-service interactions end-to-end |
| 5 | **Email Response** | `EMAIL_RESPONSE` | Generates complete email replies to customer inquiries |
| 6 | **Email Overview** | `EMAIL_OVERVIEW` | Summarizes email threads for agent context before responding |
| 7 | **Email Generative Answer** | `EMAIL_GENERATIVE_ANSWER` | Generates answer content for email responses from KB |
| 8 | **Note Taking** | `NOTE_TAKING` | Creates structured notes from voice/chat conversations |
| 9 | **Agent Assistance** | `AGENT_ASSISTANCE` | Provides real-time suggestions during agent conversations |
| 10 | **Case Summarization** | `CASE_SUMMARIZATION` | Summarizes multi-interaction customer cases across contacts |

### Overriding System Defaults

Each agent type has a system-managed default configuration. You can create custom overrides:

```javascript
const { QConnectClient, CreateAIAgentCommand } = require("@aws-sdk/client-qconnect");

const client = new QConnectClient({ region: "us-east-1" });

await client.send(new CreateAIAgentCommand({
  assistantId: "assistant-id",
  name: "CustomOrchestrator",
  type: "SELF_SERVICE",
  configuration: {
    selfServiceAIAgentConfiguration: {
      selfServiceAIGuardrailId: "guardrail-id",
      selfServicePreProcessingConfiguration: {
        aiPromptId: "custom-preprocess-prompt-id"
      },
      selfServiceAnswerGenerationConfiguration: {
        aiPromptId: "custom-answer-prompt-id"
      }
    }
  }
}));
```

### Versioning

AI agents support versioning:

- Each update creates a new version
- Previous versions can be referenced and restored
- Flows can pin to a specific version or use `LATEST`
- Enables safe rollback if a prompt change degrades quality

```javascript
// Create a version snapshot
await client.send(new CreateAIAgentVersionCommand({
  assistantId: "assistant-id",
  aiAgentId: "agent-id"
}));

// List all versions
const versions = await client.send(new ListAIAgentVersionsCommand({
  assistantId: "assistant-id",
  aiAgentId: "agent-id"
}));
```

---

## AI Prompt Customization

### Prompt Types (12 Total)

Amazon Connect supports customizing 12 distinct AI prompt types:

| # | Prompt Type | Purpose |
|---|-------------|---------|
| 1 | **Orchestration** | Controls how the orchestrator AI agent reasons, plans, and selects tools |
| 2 | **Answer generation** | Generates responses to customer questions from knowledge base content |
| 3 | **Intent labeling** | Classifies customer intent from conversation transcript |
| 4 | **Query reformulation** | Rewrites customer queries for better knowledge base retrieval |
| 5 | **Self-service pre-processing** | Prepares and validates input before self-service answer generation |
| 6 | **Self-service answer generation** | Generates answers in the self-service (no human agent) context |
| 7 | **Email response** | Generates full email replies to customer emails |
| 8 | **Email overview** | Produces a summary overview of an email thread |
| 9 | **Email generative answer** | Generates answer content for email responses from KB |
| 10 | **Email query reformulation** | Rewrites email queries for better KB search |
| 11 | **Note taking** | Generates structured notes from conversation content |
| 12 | **Case summarization** | Produces summaries of customer cases across interactions |

### YAML Template Format

Prompts are defined as YAML templates:

```yaml
prompt:
  system: |
    You are a helpful customer service assistant for {{$.Custom.companyName}}.
    Always respond in {{$.locale}}.
    
    Use the following knowledge to answer questions:
    {{$.contentExcerpt}}
    
    Conversation so far:
    {{$.transcript}}
```

### Message Format

Two formats are supported:

- **MESSAGES** -- structured multi-turn conversation format (system/user/assistant messages). Preferred for most use cases.
- **TEXT_COMPLETIONS** -- single text block format. Use for simpler prompts or legacy compatibility.

### Template Variables

| Variable | Description |
|----------|-------------|
| `$.transcript` | Full conversation transcript up to current point |
| `$.contentExcerpt` | Retrieved knowledge base content relevant to the query |
| `$.locale` | Customer's detected or configured locale (e.g., `en-US`) |
| `$.query` | The current customer query or utterance |
| `$.Custom.<name>` | Custom variables passed from the Connect flow (e.g., `$.Custom.accountType`, `$.Custom.companyName`) |

### Prompt Caching

Prompt caching is **enabled by default**. The system caches compiled prompt templates to reduce latency on subsequent invocations. Cache invalidation occurs automatically when prompts are updated.

### Prompt Engineering Best Practices

- Be specific about the desired output format (e.g., "respond in 2-3 sentences")
- Include example interactions in the system prompt for few-shot learning
- Use the `$.Custom.*` variables to inject context-specific instructions
- Test prompts with diverse conversation scenarios before deploying
- Use the MESSAGES format for multi-turn conversations
- Keep orchestration prompts focused on tool selection logic, not response generation
- For detailed prompt engineering guidance, see [prompt-engineering.md](../prompt-engineering.md) if available

---

## AI Guardrails

Guardrails enforce safety and compliance boundaries on AI-generated content. A maximum of **3 custom guardrails** can be configured per instance.

### Content Filters

Six categories with configurable strength levels (NONE, LOW, MEDIUM, HIGH):

| Category | What It Filters |
|----------|----------------|
| **Hate** | Discriminatory or prejudiced content based on identity |
| **Insults** | Demeaning, belittling, or offensive language |
| **Sexual** | Sexually explicit or suggestive content |
| **Violence** | Graphic violence, threats, or harm |
| **Misconduct** | Illegal activities, self-harm, or dangerous instructions |
| **Prompt Attack** | Jailbreak attempts, prompt injection, role-play exploitation |

Each filter can be configured independently for **input** (customer messages) and **output** (AI responses).

### Denied Topics

- Define up to **30 denied topics** per guardrail
- Each topic includes a name, description, and sample phrases
- The AI will refuse to engage with denied topics and provide a configured fallback response
- Example topics: "competitor comparisons", "investment advice", "medical diagnosis"

### Contextual Grounding (Hallucination Detection)

Detects when AI responses are not grounded in the provided knowledge base content:

- Compares generated text against source documents
- Configurable grounding threshold (0.0 to 1.0)
- Responses below the threshold are blocked or flagged
- Reduces fabricated information in customer-facing responses

### Word Filters

- Block specific words or phrases from appearing in AI output
- Supports exact match and pattern matching
- Useful for blocking profanity, competitor names, or internal terminology

### Sensitive Information (PII)

Two modes for handling personally identifiable information:

- **Block** -- prevents the AI from including PII in responses entirely
- **Mask** -- replaces PII with placeholder tokens (e.g., `[SSN]`, `[EMAIL]`)

Supported PII types include: SSN, credit card numbers, email addresses, phone numbers, physical addresses, dates of birth, account numbers, and more.

### Streaming Latency Tradeoff

Guardrails introduce a latency tradeoff when streaming is enabled:

- **With guardrails on streaming**: responses are buffered and checked before each chunk is sent, adding 200-500ms per chunk
- **Without guardrails on streaming**: responses stream immediately with lower latency
- For non-streaming responses, guardrails add a single check at the end with minimal impact

Evaluate whether the safety benefit justifies the latency cost for your use case.

---

## Setup Sequence

### Self-Service Setup

1. **Create orchestrator agent** -- define the agent with its base configuration, select model, attach guardrail
2. **Create custom prompts (optional)** -- customize orchestration, pre-processing, and answer generation prompts
3. **Create guardrail (optional)** -- configure content filters, denied topics, PII handling
4. **Add tools** -- attach MCP tools, Return to Control tools, and/or Constant tools with input/output schemas
5. **Associate knowledge bases** -- link one or more KBs with content tag filters and search type configuration
6. **Configure orchestration prompt** -- customize the system prompt that guides agent reasoning and tool selection behavior
7. **Set as default** -- designate the orchestrator as the default for the instance (or override per-session via Lambda)
8. **Create conversational AI bot (Lex)** -- create a Lex V2 bot that serves as the conversational front-end
9. **Build contact flow** -- wire the Lex bot into a Connect contact flow with appropriate Return to Control handling
10. **Test end-to-end** -- verify tool invocations, escalation paths, and guardrail enforcement

### Agent-Assist Setup

1. **Create/configure AI agent** -- customize the Answer Recommendation or Agent Assistance agent type
2. **Associate knowledge bases** -- link KBs containing support documentation
3. **Enable Contact Lens** -- required for real-time transcript streaming to Q Connect
4. **Configure the contact flow** -- add the "Create Q Connect Session" block or use a Lambda to create sessions
5. **Enable in agent workspace** -- ensure the Q Connect panel is visible in the agent workspace configuration
6. **Test with live contacts** -- verify recommendations appear and are relevant

### Security Profiles for AI Agents

AI agent administration requires security profile permissions:

| Permission | Allows |
|---|---|
| **AI Agents - View** | View AI agent configurations |
| **AI Agents - Edit** | Create and modify AI agents |
| **AI Prompts - View** | View prompt configurations |
| **AI Prompts - Edit** | Create and modify prompts |
| **AI Guardrails - View** | View guardrail configurations |
| **AI Guardrails - Edit** | Create and modify guardrails |

---

## Knowledge Base Configuration

When configuring an AI agent with a knowledge base, the following parameters are available:

```javascript
{
  associationId: "kb-association-id",       // Links the KB to the agent
  contentTagFilter: {                        // Filter KB content by tags
    tagCondition: {
      key: "department",
      value: "billing"
    }
  },
  maxResults: 5,                             // Max documents to retrieve (1-100)
  overrideKnowledgeBaseSearchType: "SEMANTIC" // "SEMANTIC" or "HYBRID"
}
```

- **SEMANTIC** -- vector similarity search; best for natural language queries
- **HYBRID** -- combines semantic search with keyword matching; better for queries containing specific terms, codes, or product names

### Multiple Knowledge Base Setup

- Create separate KBs for different topics (billing, technical support, policies)
- Tag KBs with metadata for content segmentation
- AI agent queries relevant KB based on contact context and intent
- Best practice: segment by department or product line, not by document type
- Use `CreateContentAssociation` to link specific content items to step-by-step guides

---

## Supported Models by Region

Model availability varies by AWS region:

| Model | Best For | Availability |
|-------|---------|-------------|
| Claude Sonnet 4.5 | Complex reasoning, nuanced responses | Select regions (us-east-1, us-west-2, eu-west-2, ap-southeast-2) |
| Amazon Nova Pro | General-purpose, balanced performance/cost | All Connect regions |
| Claude Haiku | Fast responses, simple queries, lowest cost | Select regions |

Check the [Amazon Connect documentation](https://docs.aws.amazon.com/connect/latest/adminguide/) for current region-model availability matrices.

### Model Upgrade Guide

- Upgrade via `UpdateAIAgent` API -- change the model reference in the agent config
- Test in non-production first -- different models may interpret prompts differently
- No downtime during model switch -- takes effect on next contact
- Rollback: revert to previous model version via `UpdateAIAgent`
- Version your agents before switching models for safe rollback

---

## Associating AI Agents with Flows

Use a Lambda function to associate a specific AI agent version with a contact flow at runtime:

```javascript
// In your Lambda function invoked from the contact flow
exports.handler = async (event) => {
  const { QConnectClient, UpdateSessionCommand } = require("@aws-sdk/client-qconnect");
  const client = new QConnectClient({ region: "us-east-1" });

  await client.send(new UpdateSessionCommand({
    assistantId: "assistant-id",
    sessionId: event.Details.ContactData.Attributes.qconnectSessionId,
    aiAgentConfiguration: {
      [agentType]: {
        aiAgentId: "custom-agent-id"
      }
    }
  }));

  return { success: true };
};
```

---

## Integration with Step-by-Step Guides

AI agents can be integrated with step-by-step guides (agent workspace views) using the `CreateContentAssociation` API:

```javascript
const { QConnectClient, CreateContentAssociationCommand } = require("@aws-sdk/client-qconnect");

const client = new QConnectClient({ region: "us-east-1" });

await client.send(new CreateContentAssociationCommand({
  knowledgeBaseId: "kb-id",
  contentId: "content-id",
  associationType: "AMAZON_CONNECT_GUIDE",
  association: {
    amazonConnectGuideAssociation: {
      flowId: "flow-arn"  // ARN of the guide flow
    }
  }
}));
```

This allows AI-generated recommendations to include "Launch Guide" actions that open the relevant step-by-step guide in the agent workspace.

---

## CloudWatch Monitoring

Monitor AI agent performance with CloudWatch metrics:

| Metric | Description |
|---|---|
| `SessionCount` | Number of Q Connect sessions created |
| `RecommendationCount` | Number of recommendations generated |
| `RecommendationAcceptedCount` | Number of recommendations accepted by agents |
| `QueryLatency` | Time to retrieve knowledge base results |
| `ResponseGenerationLatency` | Time to generate AI responses |
| `ToolInvocationCount` | Number of tool invocations by the orchestrator |
| `ToolInvocationErrorCount` | Number of failed tool invocations |
| `EscalationCount` | Number of self-service escalations to human agents |
| `GuardrailBlockedCount` | Number of responses blocked by guardrails |

Set up CloudWatch alarms for:
- High escalation rates (may indicate prompt or tool issues)
- High tool error rates (may indicate backend service issues)
- Elevated response latency (may indicate model or KB issues)
- Low recommendation acceptance rates (may indicate relevance issues)

---

## Troubleshooting

### AI Agent Not Responding

- Verify the assistant ID is correct and the agent is associated with the session
- Check that the Lex bot is properly configured and the flow invokes it
- Verify the AI agent type is set as default or overridden in the session
- Check CloudWatch logs for errors in the Q Connect service

### Recommendations Not Appearing

- Verify Contact Lens is enabled and streaming transcripts
- Check that knowledge bases have indexed content
- Verify the Q Connect session was created for the contact
- Ensure the agent workspace has the Q Connect panel enabled

### Tool Invocation Failures

- Check MCP tool endpoint availability and authentication
- Verify input schema matches what the orchestrator is sending
- Review CloudWatch logs for tool invocation errors
- Test the tool endpoint independently

### Poor Response Quality

- Review and customize prompts for your use case
- Ensure knowledge base content is relevant and up-to-date
- Check guardrail settings -- overly restrictive filters may block good responses
- Try switching search type between SEMANTIC and HYBRID
- Increase `maxResults` for knowledge base retrieval

---

## Legacy Self-Service

The legacy self-service approach used Amazon Lex bots with static intents and slot-filling logic. This approach:

- Is **not receiving new features**
- Requires manual intent/slot definition for every conversation path
- Does not support multi-step reasoning or tool invocation
- Cannot dynamically adapt to novel customer requests

**Recommendation**: Use the agentic self-service approach for all new implementations. Migrate existing legacy bots when feasible. The agentic approach provides better customer experience, lower maintenance burden, and access to all new AI features.
