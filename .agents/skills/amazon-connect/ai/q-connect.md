# Amazon Q Connect (formerly Wisdom)

## Overview

Amazon Q Connect is the LLM-enhanced agent assistance and knowledge management service for Amazon Connect. It provides real-time AI-powered recommendations to agents during customer interactions and serves as the management plane for AI agents, prompts, guardrails, and knowledge bases.

Previously known as **Amazon Connect Wisdom**, it was rebranded to Amazon Q Connect when generative AI capabilities were added.

**SDK**: `@aws-sdk/client-qconnect`

---

## Core Concepts

### Assistants

An assistant is the top-level resource that ties together knowledge bases, AI agents, prompts, and guardrails for a Connect instance.

```javascript
const { QConnectClient, CreateAssistantCommand } = require("@aws-sdk/client-qconnect");

const client = new QConnectClient({ region: "us-east-1" });

const assistant = await client.send(new CreateAssistantCommand({
  name: "MyAssistant",
  type: "AGENT",  // AGENT is the only supported type currently
  serverSideEncryptionConfiguration: {
    kmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/key-id"  // Optional
  },
  tags: {
    environment: "production"
  }
}));

// assistant.assistant.assistantId --> use this for all subsequent operations
```

Each Connect instance has one assistant. The assistant ID is required for most Q Connect API calls.

**Encryption:** Assistants support optional server-side encryption with a customer-managed KMS key. If not specified, AWS-managed encryption is used.

### Knowledge Bases

Knowledge bases store and index content that the AI uses to generate responses and recommendations.

#### Content Knowledge Base

Upload documents (PDF, HTML, Word, plain text) directly:

```javascript
const { CreateKnowledgeBaseCommand } = require("@aws-sdk/client-qconnect");

const kb = await client.send(new CreateKnowledgeBaseCommand({
  name: "ProductDocumentation",
  knowledgeBaseType: "CUSTOM",
  sourceConfiguration: {
    appIntegrations: {
      appIntegrationArn: "arn:aws:app-integrations:us-east-1:123456789012:application/app-id"
    }
  }
}));
```

**Supported content types:**
- **PDF** -- portable document format files
- **HTML** -- web pages and structured HTML content
- **Word** -- Microsoft Word documents (.docx)
- **Plain text** -- .txt files
- **CSV** -- for bulk import of quick responses

#### S3 Knowledge Base

Index content from an S3 bucket:

```javascript
const kb = await client.send(new CreateKnowledgeBaseCommand({
  name: "S3Documentation",
  knowledgeBaseType: "CUSTOM",
  sourceConfiguration: {
    appIntegrations: {
      appIntegrationArn: "arn:aws:app-integrations:...",
      objectFields: ["key", "content"]
    }
  }
}));
```

#### Web Crawler Knowledge Base

Crawl and index web pages:

```javascript
const kb = await client.send(new CreateKnowledgeBaseCommand({
  name: "WebDocs",
  knowledgeBaseType: "CUSTOM",
  sourceConfiguration: {
    managedSourceConfiguration: {
      webCrawlerConfiguration: {
        urlConfiguration: {
          seedUrlConfiguration: {
            seedUrls: [
              { url: "https://docs.example.com" }
            ]
          }
        },
        crawlerLimits: {
          rateLimit: 10  // Pages per second
        },
        scope: "HOST_ONLY"  // or "SUBDOMAINS"
      }
    }
  }
}));
```

**Crawler scope options:**
- **HOST_ONLY** -- crawl only the specified host
- **SUBDOMAINS** -- include subdomains of the specified host

#### Search Types

Knowledge bases support two search modes:

| Search Type | Description | Best For |
|---|---|---|
| **SEMANTIC** | Vector similarity search | Natural language queries, conversational questions |
| **HYBRID** | Combines semantic search with keyword matching | Queries containing specific terms, codes, product names |

Configure search type when associating a KB with an AI agent:

```javascript
{
  overrideKnowledgeBaseSearchType: "SEMANTIC"  // or "HYBRID"
}
```

### Content Management

Add, update, and manage individual content items within a knowledge base:

```javascript
const { CreateContentCommand, UpdateContentCommand, DeleteContentCommand, SearchContentCommand } = require("@aws-sdk/client-qconnect");

// Start an upload (returns presigned URL)
const upload = await client.send(new StartContentUploadCommand({
  knowledgeBaseId: "kb-id",
  contentType: "application/pdf"
}));
// upload.uploadId --> use in CreateContentCommand
// upload.url --> presigned S3 URL to upload the file to

// Create content (after uploading file to presigned URL)
const content = await client.send(new CreateContentCommand({
  knowledgeBaseId: "kb-id",
  name: "Refund Policy",
  title: "Customer Refund Policy",
  uploadId: "upload-id",  // From StartContentUpload
  metadata: {
    department: "billing",
    category: "policies"
  },
  tags: {
    version: "2024-01"
  }
}));

// Update content
await client.send(new UpdateContentCommand({
  knowledgeBaseId: "kb-id",
  contentId: content.content.contentId,
  title: "Updated Refund Policy",
  uploadId: "new-upload-id"  // Optional: new file version
}));

// Delete content
await client.send(new DeleteContentCommand({
  knowledgeBaseId: "kb-id",
  contentId: "content-id"
}));

// Search content
const results = await client.send(new SearchContentCommand({
  knowledgeBaseId: "kb-id",
  searchExpression: {
    filters: [
      {
        field: "NAME",
        operator: "EQUALS",
        value: "Refund Policy"
      }
    ]
  }
}));
```

**Content lifecycle:**
1. Call `StartContentUpload` to get a presigned S3 URL and upload ID
2. Upload the file to the presigned URL
3. Call `CreateContent` with the upload ID to register and index the content
4. Content is automatically indexed and available for search/recommendations
5. Update content by uploading a new version and calling `UpdateContent`

### Message Templates

Templates for outbound customer communications across multiple channels:

```javascript
const { CreateMessageTemplateCommand } = require("@aws-sdk/client-qconnect");

const template = await client.send(new CreateMessageTemplateCommand({
  knowledgeBaseId: "kb-id",
  name: "OrderConfirmation",
  channelSubtype: "EMAIL",  // EMAIL, SMS, WHATSAPP, PUSH
  content: {
    email: {
      subject: "Order #{{orderNumber}} Confirmed",
      body: {
        html: {
          content: "<h1>Thank you for your order</h1><p>Order #{{orderNumber}} has been confirmed.</p>"
        },
        plainText: {
          content: "Thank you for your order. Order #{{orderNumber}} has been confirmed."
        }
      },
      headers: [
        { name: "X-Custom-Header", value: "value" }
      ]
    }
  },
  defaultAttributes: {
    customAttributes: {
      orderNumber: { values: [{ stringValue: "" }] }
    }
  }
}));
```

Supported channel subtypes:
- **EMAIL** -- full HTML/plain text with headers and attachments
- **SMS** -- plain text, character limit aware
- **WHATSAPP** -- supports WhatsApp message formatting
- **PUSH** -- mobile push notification format

### Quick Responses

Pre-written responses agents can insert into conversations with one click. Unlike Q Connect AI-generated recommendations, quick responses are static, human-authored text.

**Quick responses vs Q Connect AI recommendations:**

| Feature | Quick Responses | Q Connect Recommendations |
|---|---|---|
| Content source | Human-authored, static | AI-generated from knowledge base |
| Trigger | Agent searches/selects manually | Automatic based on conversation context |
| Personalization | Template variables only | Full contextual generation |
| Use case | Standard greetings, policies, FAQs | Dynamic, context-aware answers |
| Channel support | Chat-focused | All channels |

```javascript
const { CreateQuickResponseCommand } = require("@aws-sdk/client-qconnect");

const quickResponse = await client.send(new CreateQuickResponseCommand({
  knowledgeBaseId: "kb-id",
  name: "greeting_standard",
  shortcutKey: "hello",
  content: {
    quickResponseContent: {
      markdown: "Hello! Thank you for contacting us. How can I help you today?"
    }
  },
  contentType: "MARKDOWN",  // or "PLAIN_TEXT"
  channels: ["Chat"],
  language: "en-US",
  groupingConfiguration: {
    criteria: "CONTACT_LENS_CATEGORY",
    values: ["Billing"]
  }
}));
```

---

## Sessions

A session represents a single customer interaction. Sessions track the conversation state and AI recommendations.

### Session Lifecycle

1. **Creation** -- session is created when a contact arrives (via flow or Lambda)
2. **Active** -- conversation in progress; transcript streams in, recommendations generated
3. **Recommendations** -- AI generates real-time suggestions based on conversation context
4. **Feedback** -- agent marks recommendations as helpful or not
5. **Closed** -- contact ends; session is finalized, feedback preserved for improvement

```javascript
const { CreateSessionCommand, SendMessageCommand, GetNextMessageCommand } = require("@aws-sdk/client-qconnect");

// Create a session (typically done via the contact flow)
const session = await client.send(new CreateSessionCommand({
  assistantId: "assistant-id",
  name: "session-name",
  description: "Voice contact session",
  tagFilter: {
    tagCondition: {
      key: "department",
      value: "support"
    }
  }
}));

// Send a message (for chat/messaging or programmatic interaction)
const sendResult = await client.send(new SendMessageCommand({
  assistantId: "assistant-id",
  sessionId: session.session.sessionId,
  message: {
    value: {
      text: {
        value: "I need to return my order"
      }
    }
  },
  type: "TEXT",
  conversationContext: {
    selfServiceConversationHistory: [
      {
        botMessage: "How can I help you?",
        inputTranscript: "I want to return something"
      }
    ]
  }
}));

// Get the AI-generated response
const nextMessage = await client.send(new GetNextMessageCommand({
  assistantId: "assistant-id",
  sessionId: session.session.sessionId,
  nextMessageToken: sendResult.nextMessageToken
}));
```

### Session Configuration Overrides

Sessions can be updated at runtime to override AI agent configuration:

```javascript
await client.send(new UpdateSessionCommand({
  assistantId: "assistant-id",
  sessionId: "session-id",
  aiAgentConfiguration: {
    [agentType]: {
      aiAgentId: "custom-agent-id"
    }
  }
}));
```

### Tag Filters

Sessions support tag filters to scope which knowledge base content is accessible:

- Filter by tags assigned to content items
- Useful for multi-tenant or department-specific deployments
- Applied at session creation time

---

## Real-Time Recommendations

### Automatic Recommendations

During a voice or chat conversation, Q Connect automatically:
1. Receives the conversation transcript from Contact Lens (voice) or chat stream
2. Detects customer intent from the conversation
3. Searches knowledge bases for relevant content
4. Generates AI-powered response suggestions
5. Displays recommendations in the agent workspace in real time

Recommendations update continuously as the conversation progresses.

### Manual Search (Agent-Initiated)

Agents can also manually search the knowledge base:
- Type a query in the Q Connect panel in the agent workspace
- Results include both exact matches and semantically similar content
- Powered by the **Manual Search** AI agent type

### Intent Detection

Q Connect automatically classifies customer intent from the conversation transcript:
- Uses the **Intent Labeling** AI prompt to categorize the customer's request
- Intent labels help retrieve more relevant knowledge base content
- Intents are available as session attributes for flow logic

### Response Generation

When generating responses, Q Connect:
1. Reformulates the customer's query for better KB retrieval (Query Reformulation prompt)
2. Retrieves relevant content from knowledge bases
3. Generates a contextual answer grounded in the retrieved content (Answer Generation prompt)
4. Applies guardrails to filter the response
5. Returns the recommendation to the agent

---

## Import Jobs

Bulk import content into a knowledge base from external sources:

```javascript
const { StartImportJobCommand, GetImportJobCommand } = require("@aws-sdk/client-qconnect");

const importJob = await client.send(new StartImportJobCommand({
  knowledgeBaseId: "kb-id",
  importJobType: "QUICK_RESPONSES",  // or "CONTENT"
  uploadId: "upload-id",
  externalSourceConfiguration: {
    source: "AMAZON_S3",
    configuration: {
      amazonS3: "s3://bucket/path/to/import-file.csv"
    }
  },
  metadata: {
    importedBy: "admin"
  }
}));

// Check import status
const status = await client.send(new GetImportJobCommand({
  knowledgeBaseId: "kb-id",
  importJobId: importJob.importJob.importJobId
}));
// status.importJob.status --> "START_IN_PROGRESS" | "COMPLETE" | "FAILED"
```

**Import job types:**
- **QUICK_RESPONSES** -- bulk import quick responses from CSV
- **CONTENT** -- bulk import knowledge base articles

**Import status values:**
- `START_IN_PROGRESS` -- import has started
- `COMPLETE` -- all items imported successfully
- `FAILED` -- import encountered errors (check error details)

---

## AI Agents, Prompts, and Guardrails

Q Connect is the management API for all AI configuration in Amazon Connect. See [connect-ai-agents.md](./connect-ai-agents.md) for detailed coverage of:

- AI agent types and configuration
- AI prompt customization (12 prompt types)
- AI guardrails (content filters, denied topics, PII handling)

Key management operations:

```javascript
// AI Agents
CreateAIAgent, UpdateAIAgent, DeleteAIAgent, GetAIAgent, ListAIAgents
CreateAIAgentVersion, ListAIAgentVersions

// AI Prompts
CreateAIPrompt, UpdateAIPrompt, DeleteAIPrompt, GetAIPrompt, ListAIPrompts
CreateAIPromptVersion, ListAIPromptVersions

// AI Guardrails
CreateAIGuardrail, UpdateAIGuardrail, DeleteAIGuardrail, GetAIGuardrail, ListAIGuardrails
CreateAIGuardrailVersion, ListAIGuardrailVersions
```

### Guardrails Overview

Guardrails enforce safety and compliance boundaries on AI-generated content (max 3 custom guardrails per instance):

- **Content filters** -- 6 categories (Hate, Insults, Sexual, Violence, Misconduct, Prompt Attack) with configurable strength (NONE/LOW/MEDIUM/HIGH)
- **Denied topics** -- up to 30 per guardrail; AI refuses to engage and provides fallback response
- **Contextual grounding** -- detects hallucination by comparing responses against source documents (configurable threshold 0.0-1.0)
- **Word filters** -- block specific words/phrases from AI output (exact match and pattern matching)
- **PII handling** -- Block (prevent PII in responses) or Mask (replace with placeholders like `[SSN]`, `[EMAIL]`)

---

## Key API Operations Reference

### Assistant Management
| Operation | Description |
|-----------|-------------|
| `CreateAssistant` | Create a new assistant for a Connect instance |
| `GetAssistant` | Retrieve assistant details |
| `ListAssistants` | List all assistants in the account |
| `DeleteAssistant` | Delete an assistant |

### Knowledge Base Management
| Operation | Description |
|-----------|-------------|
| `CreateKnowledgeBase` | Create a new knowledge base |
| `GetKnowledgeBase` | Retrieve knowledge base details |
| `ListKnowledgeBases` | List all knowledge bases for an assistant |
| `DeleteKnowledgeBase` | Delete a knowledge base |
| `UpdateKnowledgeBaseTemplateUri` | Update the template URI |

### Content Operations
| Operation | Description |
|-----------|-------------|
| `CreateContent` | Add content to a knowledge base |
| `UpdateContent` | Update existing content |
| `DeleteContent` | Remove content |
| `GetContent` | Retrieve content by ID |
| `SearchContent` | Search content by filters |
| `StartContentUpload` | Initiate a content upload (returns presigned URL) |
| `CreateContentAssociation` | Link content to a guide flow or other resource |
| `DeleteContentAssociation` | Remove a content association |

### Session Operations
| Operation | Description |
|-----------|-------------|
| `CreateSession` | Create a new session for a contact |
| `GetSession` | Retrieve session details |
| `UpdateSession` | Update session configuration (e.g., AI agent overrides) |
| `SendMessage` | Send a message to the AI in a session |
| `GetNextMessage` | Retrieve the AI's response message |

### Recommendation Operations
| Operation | Description |
|-----------|-------------|
| `QueryAssistant` | Query the assistant for recommendations (agent-initiated search) |
| `GetRecommendations` | Get real-time AI recommendations for a session |
| `PutFeedback` | Submit agent feedback on a recommendation (helpful/not helpful) |
| `NotifyRecommendationsReceived` | Acknowledge that recommendations were displayed |

### Message Template Operations
| Operation | Description |
|-----------|-------------|
| `CreateMessageTemplate` | Create a message template |
| `UpdateMessageTemplate` | Update a message template |
| `DeleteMessageTemplate` | Delete a message template |
| `GetMessageTemplate` | Retrieve a message template |
| `SearchMessageTemplates` | Search message templates |
| `RenderMessageTemplate` | Render a template with variable substitution |
| `CreateMessageTemplateVersion` | Create a versioned snapshot |
| `CreateMessageTemplateAttachment` | Add an attachment to a template |
| `DeleteMessageTemplateAttachment` | Remove an attachment |

### Quick Response Operations
| Operation | Description |
|-----------|-------------|
| `CreateQuickResponse` | Create a quick response |
| `UpdateQuickResponse` | Update a quick response |
| `DeleteQuickResponse` | Delete a quick response |
| `GetQuickResponse` | Retrieve a quick response |
| `SearchQuickResponses` | Search quick responses |

### Import Operations
| Operation | Description |
|-----------|-------------|
| `StartImportJob` | Begin bulk content import |
| `GetImportJob` | Check import job status |

### AI Agent Management
| Operation | Description |
|-----------|-------------|
| `CreateAIAgent` | Create a custom AI agent |
| `UpdateAIAgent` | Update AI agent configuration |
| `DeleteAIAgent` | Delete an AI agent |
| `GetAIAgent` | Retrieve AI agent details |
| `ListAIAgents` | List all AI agents |
| `CreateAIAgentVersion` | Create a versioned snapshot |
| `ListAIAgentVersions` | List versions of an AI agent |

### AI Prompt Management
| Operation | Description |
|-----------|-------------|
| `CreateAIPrompt` | Create a custom AI prompt |
| `UpdateAIPrompt` | Update an AI prompt |
| `DeleteAIPrompt` | Delete an AI prompt |
| `GetAIPrompt` | Retrieve AI prompt details |
| `ListAIPrompts` | List all AI prompts |
| `CreateAIPromptVersion` | Create a versioned snapshot |
| `ListAIPromptVersions` | List versions of an AI prompt |

### AI Guardrail Management
| Operation | Description |
|-----------|-------------|
| `CreateAIGuardrail` | Create a custom guardrail |
| `UpdateAIGuardrail` | Update a guardrail |
| `DeleteAIGuardrail` | Delete a guardrail |
| `GetAIGuardrail` | Retrieve guardrail details |
| `ListAIGuardrails` | List all guardrails |
| `CreateAIGuardrailVersion` | Create a versioned snapshot |
| `ListAIGuardrailVersions` | List versions of a guardrail |

---

## Integration Pattern

Typical integration flow in a Connect contact flow:

1. **Contact arrives** --> flow creates a Q Connect session via Lambda
2. **Conversation starts** --> Contact Lens streams transcript to Q Connect
3. **Intent detected** --> Q Connect classifies customer intent from transcript
4. **AI generates recommendations** --> displayed in agent workspace in real time
5. **Agent uses recommendations** --> clicks to insert, searches manually, or ignores
6. **Agent provides feedback** --> PutFeedback marks recommendations as helpful or not
7. **Contact ends** --> session is closed, feedback is used to improve future recommendations

### Integration with Step-by-Step Guides

AI-generated recommendations can include "Launch Guide" actions that open relevant step-by-step guides in the agent workspace:

```javascript
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

### Integration with AI Agents (Knowledge Layer)

Q Connect knowledge bases serve as the knowledge layer for AI agents:

- Self-service AI agents query KBs to answer customer questions autonomously
- Agent-assist AI agents use KBs to generate real-time suggestions
- Multiple KBs can be associated with a single AI agent
- Content tag filters scope which KB content is accessible per session
- KB search type (SEMANTIC or HYBRID) is configurable per agent association
