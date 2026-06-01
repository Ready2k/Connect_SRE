# Amazon Connect App Integrations API Reference

The App Integrations API manages third-party application integrations, data integrations, and event integrations for Amazon Connect. These integrations power Q Connect knowledge bases, agent workspace apps, and real-time event processing. It includes **~23 actions** and approximately **20 data types**.

**SDK Package**: `@aws-sdk/client-appintegrations`

```typescript
import { AppIntegrationsClient } from '@aws-sdk/client-appintegrations';
const client = new AppIntegrationsClient({ region: 'us-east-1' });
```

## Use Cases

App Integrations serves three primary purposes:

1. **Agent workspace 3P apps** — embed third-party applications (Salesforce, Zendesk, etc.) in the Connect agent workspace
2. **Q Connect data sources** — connect external knowledge sources (ServiceNow, Salesforce Knowledge, SharePoint, etc.) to Q Connect knowledge bases
3. **Event-driven integrations** — stream Connect events to external systems via EventBridge partner event sources

## Actions by Category

### Applications

Applications represent third-party apps embedded in the Connect agent workspace.

- `CreateApplication` — register a 3P application
- `GetApplication` — get application details
- `UpdateApplication` — update application config
- `DeleteApplication` — delete application
- `ListApplications` — list all applications
- `ListApplicationAssociations` — list associations between apps and Connect resources

```typescript
import { CreateApplicationCommand } from '@aws-sdk/client-appintegrations';

const app = await client.send(new CreateApplicationCommand({
  Name: 'salesforce-crm',
  Namespace: 'salesforce',
  Description: 'Salesforce CRM integration for agent workspace',
  ApplicationSourceConfig: {
    ExternalUrlConfig: {
      AccessUrl: 'https://myorg.my.salesforce.com',
      ApprovedOrigins: ['https://myorg.my.salesforce.com'],
    },
  },
  Permissions: ['connect:StartChatContact', 'connect:DescribeContact'],
}));

console.log('Application ID:', app.Id);
console.log('Application ARN:', app.Arn);
```

```typescript
import { ListApplicationsCommand } from '@aws-sdk/client-appintegrations';

const apps = await client.send(new ListApplicationsCommand({
  MaxResults: 50,
}));

for (const app of apps.Applications ?? []) {
  console.log(`${app.Name} (${app.Id}) — ${app.Namespace}`);
}
```

### Data Integrations

Data integrations connect external data sources to Amazon Connect services (primarily Q Connect knowledge bases and Customer Profiles).

- `CreateDataIntegration` — create a data integration
- `GetDataIntegration` — get integration details
- `UpdateDataIntegration` — update integration config
- `DeleteDataIntegration` — delete integration
- `ListDataIntegrations` — list all data integrations
- `CreateDataIntegrationAssociation` — associate integration with a Connect resource
- `UpdateDataIntegrationAssociation` — update association
- `ListDataIntegrationAssociations` — list associations

```typescript
import { CreateDataIntegrationCommand } from '@aws-sdk/client-appintegrations';

// Create a data integration for ServiceNow knowledge articles
const dataIntegration = await client.send(new CreateDataIntegrationCommand({
  Name: 'servicenow-knowledge',
  Description: 'ServiceNow knowledge base articles',
  SourceURI: 'https://myinstance.service-now.com',
  KmsKey: 'arn:aws:kms:us-east-1:123456789012:key/xxx',
  ScheduleConfig: {
    FirstExecutionFrom: '2026-01-01T00:00:00Z',
    Object: 'kb_knowledge',
    ScheduleExpression: 'rate(1 hour)',
  },
  FileConfiguration: {
    Folders: ['/knowledge'],
    Filters: {
      'workflow_state': ['published'],
    },
  },
}));

console.log('Data Integration ARN:', dataIntegration.Arn);
```

```typescript
import { CreateDataIntegrationAssociationCommand } from '@aws-sdk/client-appintegrations';

// Associate data integration with Q Connect knowledge base
await client.send(new CreateDataIntegrationAssociationCommand({
  DataIntegrationIdentifier: dataIntegration.Id!,
  ClientAssociationMetadata: {
    'KnowledgeBaseArn': 'arn:aws:wisdom:us-east-1:123456789012:knowledge-base/kb-xxx',
  },
}));
```

### Event Integrations

Event integrations route Amazon Connect events to external systems via Amazon EventBridge.

- `CreateEventIntegration` — create an event integration
- `GetEventIntegration` — get integration details
- `UpdateEventIntegration` — update integration config
- `DeleteEventIntegration` — delete integration
- `ListEventIntegrations` — list all event integrations
- `ListEventIntegrationAssociations` — list associations

```typescript
import { CreateEventIntegrationCommand } from '@aws-sdk/client-appintegrations';

const eventIntegration = await client.send(new CreateEventIntegrationCommand({
  Name: 'connect-contact-events',
  Description: 'Route Connect contact events to partner system',
  EventBridgeBus: 'default',
  EventFilter: {
    Source: 'aws.connect',
  },
  Tags: {
    Environment: 'production',
  },
}));

console.log('Event Integration ARN:', eventIntegration.EventIntegrationArn);
```

```typescript
import { ListEventIntegrationAssociationsCommand } from '@aws-sdk/client-appintegrations';

const associations = await client.send(new ListEventIntegrationAssociationsCommand({
  EventIntegrationName: 'connect-contact-events',
  MaxResults: 50,
}));

for (const assoc of associations.EventIntegrationAssociations ?? []) {
  console.log(`Association: ${assoc.EventIntegrationAssociationId}`);
  console.log(`  Resource: ${assoc.ClientId}`);
  console.log(`  Bus: ${assoc.EventBridgeRuleName}`);
}
```

## Key Data Types

### ApplicationSummary

```typescript
interface ApplicationSummary {
  Id: string;
  Arn: string;
  Name: string;
  Namespace?: string;
  CreatedTime: Date;
  LastModifiedTime: Date;
}
```

### DataIntegrationSummary

```typescript
interface DataIntegrationSummary {
  Arn: string;
  Name: string;
  SourceURI: string;
}
```

### DataIntegrationAssociationSummary

```typescript
interface DataIntegrationAssociationSummary {
  DataIntegrationAssociationArn: string;
  DataIntegrationArn: string;
  ClientId: string;
}
```

### EventIntegration

```typescript
interface EventIntegration {
  EventIntegrationArn: string;
  Name: string;
  Description?: string;
  EventFilter: EventFilter;
  EventBridgeBus: string;
  Tags?: Record<string, string>;
}
```

### EventFilter

```typescript
interface EventFilter {
  Source: string; // e.g., 'aws.connect'
}
```

### EventIntegrationAssociation

```typescript
interface EventIntegrationAssociation {
  EventIntegrationAssociationArn: string;
  EventIntegrationAssociationId: string;
  EventIntegrationName: string;
  ClientId: string;
  EventBridgeRuleName: string;
  ClientAssociationMetadata?: Record<string, string>;
}
```

### ScheduleConfiguration

```typescript
interface ScheduleConfiguration {
  FirstExecutionFrom: string; // ISO 8601
  Object: string; // source object type (e.g., 'kb_knowledge', 'Account')
  ScheduleExpression: string; // rate() or cron() expression
}
```

### ExternalUrlConfig

```typescript
interface ExternalUrlConfig {
  AccessUrl: string; // URL of the external application
  ApprovedOrigins?: string[]; // allowed CORS origins
}
```

### FileConfiguration

```typescript
interface FileConfiguration {
  Folders: string[]; // S3 prefixes or source paths
  Filters?: Record<string, string[]>; // field-level filters
}
```

## Integration Patterns

### Q Connect Knowledge Base Integration

```
External Source (ServiceNow/Salesforce/S3)
  → App Integrations (DataIntegration + Schedule)
  → AppFlow (data sync)
  → Q Connect Knowledge Base (indexing)
  → Agent Workspace (recommendations)
```

### Agent Workspace App Embedding

```
3P App (Salesforce/Zendesk/Custom)
  → App Integrations (Application + ExternalUrlConfig)
  → Connect Instance (IntegrationAssociation)
  → Agent Workspace (embedded iframe)
```

### Event-Driven Integration

```
Amazon Connect (contact/agent events)
  → EventBridge (event bus)
  → App Integrations (EventIntegration + filter)
  → External System (webhook/SaaS)
```

## IAM Permissions

Key IAM actions for App Integrations:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "app-integrations:CreateApplication",
        "app-integrations:GetApplication",
        "app-integrations:UpdateApplication",
        "app-integrations:DeleteApplication",
        "app-integrations:ListApplications",
        "app-integrations:CreateDataIntegration",
        "app-integrations:GetDataIntegration",
        "app-integrations:UpdateDataIntegration",
        "app-integrations:DeleteDataIntegration",
        "app-integrations:ListDataIntegrations",
        "app-integrations:CreateDataIntegrationAssociation",
        "app-integrations:ListDataIntegrationAssociations",
        "app-integrations:CreateEventIntegration",
        "app-integrations:GetEventIntegration",
        "app-integrations:UpdateEventIntegration",
        "app-integrations:DeleteEventIntegration",
        "app-integrations:ListEventIntegrations",
        "app-integrations:ListEventIntegrationAssociations"
      ],
      "Resource": "*"
    }
  ]
}
```
