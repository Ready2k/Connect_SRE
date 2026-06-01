# Amazon Connect Q Connect (Wisdom) API Reference

Q Connect provides AI-powered agent assistance — knowledge bases, AI agents, guardrails, message templates, quick responses, and real-time recommendations. It includes **70+ actions** and approximately **200+ data types**.

**SDK Package**: `@aws-sdk/client-qconnect`

```typescript
import { QConnectClient } from '@aws-sdk/client-qconnect';
const client = new QConnectClient({ region: 'us-east-1' });
```

## Actions by Category

### AI Agents

AI agents are the configurable AI personalities that power Q Connect.

- `CreateAIAgent` — create an AI agent configuration
- `GetAIAgent` — get AI agent details
- `UpdateAIAgent` — update AI agent settings
- `DeleteAIAgent` — delete an AI agent
- `ListAIAgents` — list all AI agents
- `CreateAIAgentVersion` — create a versioned snapshot
- `ListAIAgentVersions` — list all versions
- `DeleteAIAgentVersion` — delete a version

```typescript
import { CreateAIAgentCommand } from '@aws-sdk/client-qconnect';

await client.send(new CreateAIAgentCommand({
  assistantId: 'assistant-xxx',
  name: 'customer-support-agent',
  type: 'ANSWER_RECOMMENDATION',
  description: 'AI agent for customer support recommendations',
  configuration: {
    answerRecommendationAIAgentConfiguration: {
      locale: 'en_US',
      intentLabelingGenerationAIPromptId: 'prompt-xxx',
      queryReformulationAIPromptId: 'prompt-yyy',
      answerGenerationAIPromptId: 'prompt-zzz',
    },
  },
}));
```

### AI Prompts

Custom prompts that control AI agent behavior.

- `CreateAIPrompt` — create a custom prompt template
- `GetAIPrompt` — get prompt details
- `UpdateAIPrompt` — update prompt content
- `DeleteAIPrompt` — delete a prompt
- `ListAIPrompts` — list all prompts
- `CreateAIPromptVersion` — create a versioned snapshot
- `ListAIPromptVersions` — list all versions
- `DeleteAIPromptVersion` — delete a version

### AI Guardrails

Safety guardrails for AI agent responses.

- `CreateAIGuardrail` — create a guardrail
- `GetAIGuardrail` — get guardrail details
- `UpdateAIGuardrail` — update guardrail policies
- `DeleteAIGuardrail` — delete a guardrail
- `ListAIGuardrails` — list all guardrails
- `CreateAIGuardrailVersion` — create a versioned snapshot
- `ListAIGuardrailVersions` — list versions
- `DeleteAIGuardrailVersion` — delete a version

```typescript
import { CreateAIGuardrailCommand } from '@aws-sdk/client-qconnect';

await client.send(new CreateAIGuardrailCommand({
  assistantId: 'assistant-xxx',
  name: 'pii-guardrail',
  description: 'Block PII in AI responses',
  blockedInputMessaging: 'Input contains restricted content.',
  blockedOutputsMessaging: 'Response contains restricted content.',
  sensitiveInformationPolicyConfig: {
    piiEntitiesConfig: [
      { type: 'EMAIL', action: 'ANONYMIZE' },
      { type: 'PHONE', action: 'ANONYMIZE' },
      { type: 'SSN', action: 'BLOCK' },
      { type: 'CREDIT_DEBIT_CARD_NUMBER', action: 'BLOCK' },
    ],
  },
  contentPolicyConfig: {
    filtersConfig: [
      { type: 'HATE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
      { type: 'VIOLENCE', inputStrength: 'HIGH', outputStrength: 'HIGH' },
    ],
  },
}));
```

### Assistants

Assistants are the top-level container for Q Connect resources.

- `CreateAssistant` — create a Q Connect assistant
- `GetAssistant` — get assistant details
- `DeleteAssistant` — delete an assistant
- `ListAssistants` — list all assistants
- `CreateAssistantAssociation` — associate a knowledge base with assistant
- `GetAssistantAssociation` — get association details
- `DeleteAssistantAssociation` — remove association
- `ListAssistantAssociations` — list associations

```typescript
import { CreateAssistantCommand } from '@aws-sdk/client-qconnect';

const assistant = await client.send(new CreateAssistantCommand({
  name: 'support-assistant',
  type: 'AGENT',
  description: 'Q Connect assistant for support agents',
}));
```

### Knowledge Bases

Knowledge bases store content that AI agents reference for recommendations.

- `CreateKnowledgeBase` — create a knowledge base
- `GetKnowledgeBase` — get knowledge base details
- `UpdateKnowledgeBase` — update settings
- `DeleteKnowledgeBase` — delete knowledge base
- `ListKnowledgeBases` — list all knowledge bases
- `GetKnowledgeBaseTemplateUri` — get template URI for object mappings

```typescript
import { CreateKnowledgeBaseCommand } from '@aws-sdk/client-qconnect';

await client.send(new CreateKnowledgeBaseCommand({
  name: 'support-kb',
  knowledgeBaseType: 'CUSTOM',
  description: 'Support articles and FAQs',
  sourceConfiguration: {
    appIntegrations: {
      appIntegrationArn: 'arn:aws:app-integrations:us-east-1:123:data-integration/xxx',
      objectFields: ['Id', 'Body', 'Title'],
    },
  },
}));
```

### Content

Content items are individual articles/documents in a knowledge base.

- `CreateContent` — add content to a knowledge base
- `GetContent` — get content details
- `UpdateContent` — update content metadata or body
- `DeleteContent` — delete content
- `SearchContent` — search content by keyword/filter
- `ListContents` — list all content in a knowledge base
- `CreateContentAssociation` — associate content with other resources
- `GetContentAssociation` — get association details
- `DeleteContentAssociation` — remove association
- `ListContentAssociations` — list content associations

### Sessions

Sessions represent a Q Connect interaction for a specific contact.

- `CreateSession` — create a session for a contact
- `GetSession` — get session details (recommendations, transcript)
- `UpdateSession` — update session data
- `SearchSessions` — search sessions
- `PutSessionData` — add data to a session
- `UpdateSessionData` — update session data
- `ListSessionDataItems` — list data items in a session

```typescript
import { CreateSessionCommand } from '@aws-sdk/client-qconnect';

const session = await client.send(new CreateSessionCommand({
  assistantId: 'assistant-xxx',
  name: `session-${contactId}`,
  description: 'Real-time agent assist session',
  tagFilter: {
    tagCondition: { key: 'department', value: 'support' },
  },
}));
```

### Messages

Conversational messaging with AI agents.

- `SendMessage` — send a message to an AI agent
- `GetNextMessage` — get the next AI response
- `ListMessages` — list messages in a session

```typescript
import { SendMessageCommand, GetNextMessageCommand } from '@aws-sdk/client-qconnect';

// Send a message
const sendRes = await client.send(new SendMessageCommand({
  assistantId: 'assistant-xxx',
  sessionId: 'session-xxx',
  message: {
    value: {
      text: { value: 'How do I reset my password?' },
    },
  },
  type: 'TEXT',
  conversationContext: {
    selfServiceConversationHistory: [],
  },
}));

// Get AI response
const getRes = await client.send(new GetNextMessageCommand({
  assistantId: 'assistant-xxx',
  sessionId: 'session-xxx',
  nextMessageToken: sendRes.nextMessageToken!,
}));

console.log('AI Response:', getRes.response?.value?.text?.value);
```

### Message Templates

Reusable message templates for agent responses.

- `CreateMessageTemplate` — create a template
- `GetMessageTemplate` — get template details
- `UpdateMessageTemplate` — update template content
- `DeleteMessageTemplate` — delete a template
- `SearchMessageTemplates` — search templates
- `ListMessageTemplates` — list all templates
- `ActivateMessageTemplate` — activate a template version
- `DeactivateMessageTemplate` — deactivate a template
- `RenderMessageTemplate` — render template with variable substitution
- `CreateMessageTemplateVersion` — create a version
- `ListMessageTemplateVersions` — list versions
- `CreateMessageTemplateAttachment` — add file attachment
- `DeleteMessageTemplateAttachment` — remove attachment

```typescript
import { CreateMessageTemplateCommand, RenderMessageTemplateCommand } from '@aws-sdk/client-qconnect';

await client.send(new CreateMessageTemplateCommand({
  knowledgeBaseId: 'kb-xxx',
  name: 'password-reset-instructions',
  channelSubtype: 'CHAT',
  content: {
    body: {
      plainText: {
        content: 'Hi {{customer_name}}, to reset your password: 1) Go to Settings 2) Click "Reset Password" 3) Follow the email link. Let me know if you need help!',
      },
    },
    subject: 'Password Reset Instructions',
  },
}));

// Render with variables
const rendered = await client.send(new RenderMessageTemplateCommand({
  knowledgeBaseId: 'kb-xxx',
  messageTemplateId: 'template-xxx',
  attributes: {
    customerProfileAttributes: {
      'customer_name': 'Jane Smith',
    },
  },
}));
```

### Quick Responses

Pre-written responses agents can use during chats.

- `CreateQuickResponse` — create a quick response
- `GetQuickResponse` — get details
- `UpdateQuickResponse` — update content
- `DeleteQuickResponse` — delete
- `SearchQuickResponses` — search by keyword
- `ListQuickResponses` — list all quick responses

### Import Jobs

Bulk import content or quick responses.

- `CreateImportJob` — start a bulk import from S3
- `GetImportJob` — get import job status
- `ListImportJobs` — list import jobs
- `StartImportJob` — start processing an import

### Recommendations

Real-time AI recommendations during contacts.

- `GetRecommendations` — get AI recommendations for a session (legacy)
- `NotifyRecommendationsReceived` — acknowledge receipt of recommendations
- `QueryAssistant` — query the assistant for answers (legacy)
- `RetrieveContent` — retrieve relevant content from knowledge bases
- `PutFeedback` — submit agent feedback on a recommendation (helpful/not helpful)

```typescript
import { PutFeedbackCommand } from '@aws-sdk/client-qconnect';

await client.send(new PutFeedbackCommand({
  assistantId: 'assistant-xxx',
  targetId: 'recommendation-xxx',
  targetType: 'RECOMMENDATION',
  contentFeedback: {
    generativeContentFeedbackData: {
      relevance: 'HELPFUL', // or 'NOT_HELPFUL'
    },
  },
}));
```

## Key Data Types

The Q Connect API defines approximately **200+ data types**. Key types include:

- **AIAgentSummary** — name, type, status, ARN, version info
- **AIPromptSummary** — name, type, model ID, API format
- **AIGuardrailSummary** — name, status, version
- **AssistantData** — assistant name, type, status, integration config
- **KnowledgeBaseData** — name, type, status, source config, rendering config
- **ContentData** — title, content type, status, metadata, URL
- **SessionData** — name, session ID, description, integration config
- **MessageOutput** — message ID, participant, timestamp, value (text/spans)
- **MessageTemplateData** — name, channel subtype, content (body/subject), attributes
- **QuickResponseData** — name, content, channels, grouping labels
- **RecommendationData** — recommendation ID, relevance score, content/document
- **ImportJobData** — status, URL, metadata, failed records
