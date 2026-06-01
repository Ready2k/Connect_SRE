# Amazon Connect Cases API Reference

The Cases API provides case management for Amazon Connect, enabling agents to track and manage customer issues. It includes **30+ actions** and approximately **80+ data types**.

**SDK Package**: `@aws-sdk/client-connectcases`

```typescript
import { ConnectCasesClient } from '@aws-sdk/client-connectcases';
const client = new ConnectCasesClient({ region: 'us-east-1' });
```

## Actions by Category

### Cases

Core case CRUD and search operations.

- `CreateCase` — create a new case
- `GetCase` — get case details by ID
- `UpdateCase` — update case fields
- `DeleteCase` — delete a case (soft delete)
- `SearchCases` — search cases with field-based filters
- `ListCasesForContact` — list cases linked to a contact
- `GetCaseAuditEvents` — get audit trail for a case
- `CreateRelatedItem` — add a related item (comment, contact) to a case
- `SearchRelatedItems` — search related items on a case
- `BatchGetCaseRule` — get multiple case rules by ID

```typescript
import { CreateCaseCommand, SearchCasesCommand } from '@aws-sdk/client-connectcases';

// Create a case
const newCase = await client.send(new CreateCaseCommand({
  domainId: 'domain-xxx',
  templateId: 'template-xxx',
  fields: [
    { id: 'title', value: { stringValue: 'Account access issue' } },
    { id: 'status', value: { stringValue: 'Open' } },
    { id: 'customer_id', value: { stringValue: 'CUST-12345' } },
  ],
  performedBy: {
    userArn: 'arn:aws:connect:us-east-1:123456789012:instance/xxx/agent/yyy',
  },
}));

console.log('Case ID:', newCase.caseId);
console.log('Case ARN:', newCase.caseArn);
```

```typescript
// Search cases
const results = await client.send(new SearchCasesCommand({
  domainId: 'domain-xxx',
  filter: {
    andAll: [
      { field: { id: 'status', value: { stringValue: 'Open' } }, equalTo: {} },
    ],
  },
  sorts: [{ fieldId: 'created_date', sortOrder: 'Desc' }],
  maxResults: 25,
  fields: [
    { id: 'title' },
    { id: 'status' },
    { id: 'created_date' },
  ],
}));

for (const c of results.cases ?? []) {
  console.log(`Case ${c.caseId}:`, c.fields);
}
```

### Domains

A domain is the top-level container for Cases resources (one per Connect instance).

- `CreateDomain` — create a Cases domain
- `GetDomain` — get domain details
- `UpdateDomain` — update domain configuration
- `DeleteDomain` — delete domain and all cases
- `ListDomains` — list all domains

```typescript
import { CreateDomainCommand } from '@aws-sdk/client-connectcases';

const domain = await client.send(new CreateDomainCommand({
  name: 'my-cases-domain',
}));

console.log('Domain ID:', domain.domainId);
```

### Fields & Field Options

Fields define the schema for cases. Field options define picklist values for single-select/multi-select fields.

- `CreateField` — create a custom field
- `UpdateField` — update field name/description
- `GetField` — get field details
- `ListFields` — list all fields in domain
- `BatchGetField` — get multiple fields by ID
- `CreateFieldOption` — create a picklist option
- `UpdateFieldOption` — update an option
- `BatchPutFieldOptions` — create/update multiple options
- `ListFieldOptions` — list options for a field

```typescript
import { CreateFieldCommand, BatchPutFieldOptionsCommand } from '@aws-sdk/client-connectcases';

// Create a single-select field
const field = await client.send(new CreateFieldCommand({
  domainId: 'domain-xxx',
  name: 'Priority',
  type: 'SingleSelect',
  description: 'Case priority level',
}));

// Add options to the field
await client.send(new BatchPutFieldOptionsCommand({
  domainId: 'domain-xxx',
  fieldId: field.fieldId!,
  options: [
    { name: 'Low', value: 'low', active: true },
    { name: 'Medium', value: 'medium', active: true },
    { name: 'High', value: 'high', active: true },
    { name: 'Critical', value: 'critical', active: true },
  ],
}));
```

### Layouts

Layouts define how case fields are arranged in the agent UI.

- `CreateLayout` — create a case layout
- `UpdateLayout` — update layout sections and fields
- `GetLayout` — get layout details
- `ListLayouts` — list all layouts
- `DeleteLayout` — delete a layout

```typescript
import { CreateLayoutCommand } from '@aws-sdk/client-connectcases';

await client.send(new CreateLayoutCommand({
  domainId: 'domain-xxx',
  name: 'Default Layout',
  content: {
    basic: {
      topPanel: {
        sections: [{
          fieldGroup: {
            fields: [
              { id: 'title' },
              { id: 'status' },
              { id: 'priority' },
            ],
          },
        }],
      },
      moreInfo: {
        sections: [{
          fieldGroup: {
            fields: [
              { id: 'customer_id' },
              { id: 'description' },
              { id: 'created_date' },
            ],
          },
        }],
      },
    },
  },
}));
```

### Templates

Templates define the default fields, layout, and required fields for case creation.

- `CreateTemplate` — create a case template
- `UpdateTemplate` — update template configuration
- `GetTemplate` — get template details
- `ListTemplates` — list all templates
- `DeleteTemplate` — delete a template

```typescript
import { CreateTemplateCommand } from '@aws-sdk/client-connectcases';

await client.send(new CreateTemplateCommand({
  domainId: 'domain-xxx',
  name: 'General Inquiry',
  description: 'Template for general customer inquiries',
  layoutConfiguration: { defaultLayout: 'layout-xxx' },
  requiredFields: [
    { fieldId: 'title' },
    { fieldId: 'status' },
  ],
  status: 'Active',
}));
```

### Case Rules

Automation rules triggered by case events.

- `CreateCaseRule` — create a case automation rule
- `UpdateCaseRule` — update rule conditions/actions
- `DeleteCaseRule` — delete a rule
- `BatchGetCaseRule` — get multiple rules by ID
- `ListCaseRules` — list all rules

### Related Items

Related items link contacts, comments, and files to cases.

- `CreateRelatedItem` — add a comment, contact reference, or file to a case
- `SearchRelatedItems` — search related items on a case

```typescript
import { CreateRelatedItemCommand } from '@aws-sdk/client-connectcases';

// Add a comment to a case
await client.send(new CreateRelatedItemCommand({
  domainId: 'domain-xxx',
  caseId: 'case-xxx',
  type: 'Comment',
  content: {
    comment: {
      body: 'Customer confirmed the issue is resolved.',
      contentType: 'Text/Plain',
    },
  },
  performedBy: {
    userArn: 'arn:aws:connect:us-east-1:123456789012:instance/xxx/agent/yyy',
  },
}));

// Link a contact to a case
await client.send(new CreateRelatedItemCommand({
  domainId: 'domain-xxx',
  caseId: 'case-xxx',
  type: 'Contact',
  content: {
    contact: {
      contactArn: 'arn:aws:connect:us-east-1:123456789012:instance/xxx/contact/zzz',
    },
  },
}));
```

### Audit Events

- `GetCaseAuditEvents` — get the change history for a case

```typescript
import { GetCaseAuditEventsCommand } from '@aws-sdk/client-connectcases';

const audit = await client.send(new GetCaseAuditEventsCommand({
  domainId: 'domain-xxx',
  caseId: 'case-xxx',
  maxResults: 50,
}));

for (const event of audit.auditEvents ?? []) {
  console.log(`${event.performedTime}: ${event.type} by ${event.performedBy?.userArn}`);
}
```

## Key Data Types

### CaseSummary

```typescript
interface CaseSummary {
  caseId: string;
  templateId: string;
  fields: FieldValue[];
  tags?: Record<string, string>;
}
```

### FieldValue

```typescript
interface FieldValue {
  id: string;
  value: {
    stringValue?: string;
    doubleValue?: number;
    booleanValue?: boolean;
    emptyValue?: {};
  };
}
```

### LayoutContent

```typescript
interface LayoutContent {
  basic?: {
    topPanel?: { sections: Section[] };
    moreInfo?: { sections: Section[] };
  };
}

interface Section {
  fieldGroup?: {
    name?: string;
    fields: { id: string }[];
  };
}
```

### TemplateSummary

```typescript
interface TemplateSummary {
  templateId: string;
  templateArn: string;
  name: string;
  status: 'Active' | 'Inactive';
}
```

### CaseRuleDetails

```typescript
interface CaseRuleDetails {
  caseRuleId: string;
  caseRuleArn: string;
  name: string;
  description?: string;
  rule: {
    required?: {
      conditions: CaseRuleCondition[];
      actions: CaseRuleAction[];
    };
  };
  status: 'Active' | 'Inactive';
  createdTime: Date;
  lastModifiedTime: Date;
}
```

## System Fields

Every Cases domain includes these built-in system fields (cannot be deleted):

| Field ID | Type | Description |
|---|---|---|
| `title` | Text | Case title |
| `status` | SingleSelect | Case status (Open, In Progress, Closed, etc.) |
| `created_date` | DateTime | When the case was created |
| `last_updated_date` | DateTime | When the case was last modified |
| `reference_number` | Text | Auto-generated unique reference number |
| `customer_id` | Text | Linked customer profile ID |
| `assigned_user` | Text | Agent user ARN assigned to the case |
