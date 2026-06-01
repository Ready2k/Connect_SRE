# Amazon Connect Cases

Amazon Connect Cases enables tracking of customer issues across multiple interactions. Cases provide a structured way to document, escalate, and resolve customer problems that span multiple contacts, agents, and channels.

## Core Concepts

### Domains

A Cases **domain** is the top-level container. Each Connect instance is associated with one Cases domain.

```javascript
import { ConnectCasesClient, CreateDomainCommand } from "@aws-sdk/client-connectcases";

const client = new ConnectCasesClient({ region: "us-east-1" });

const { domainId, domainArn, domainStatus } = await client.send(new CreateDomainCommand({
  Name: "support-cases",
}));
```

### Templates

Templates define the **structure** of a case -- which fields are included, required, and their default values. Different templates serve different case types (billing inquiry, technical support, complaint).

```javascript
import { CreateTemplateCommand } from "@aws-sdk/client-connectcases";

await client.send(new CreateTemplateCommand({
  DomainId: domainId,
  Name: "Technical Support",
  Description: "Template for technical support cases",
  RequiredFields: [
    { FieldId: "title" },
    { FieldId: "status" },
    { FieldId: "priority" },
  ],
  LayoutConfiguration: {
    DefaultLayout: layoutId,
  },
}));
```

### Layouts

Layouts control the **UI arrangement** of fields in the agent workspace. They define which fields appear, their order, and grouping into sections.

```javascript
import { CreateLayoutCommand } from "@aws-sdk/client-connectcases";

await client.send(new CreateLayoutCommand({
  DomainId: domainId,
  Name: "Standard Support Layout",
  Content: {
    TopPanel: {
      Sections: [
        {
          FieldGroup: {
            Fields: [
              { Id: "title" },
              { Id: "status" },
              { Id: "priority" },
            ],
          },
        },
      ],
    },
    MoreInfo: {
      Sections: [
        {
          FieldGroup: {
            Fields: [
              { Id: "customer_name" },
              { Id: "account_number" },
            ],
          },
        },
      ],
    },
  },
}));
```

## Fields

Fields are the individual data elements within a case. Connect Cases supports several field types:

| Field Type | Description | Notes |
|---|---|---|
| Single-line text | Short text input | Standard text field |
| Multi-line text | Long text input | Up to **4,100 characters** |
| Number | Numeric value | Integer or decimal |
| Boolean | True/false | Toggle field |
| Date-time | Timestamp | ISO 8601 format |
| URL | Web address | Rendered as clickable link |
| Single select | Dropdown with one selection | Define options |
| User | Connect user reference | Agent lookup |

### Dependent Dropdowns

Dependent dropdowns allow cascading selections where the options in one field depend on the value selected in another. Configuration is done via **CSV upload**:

```csv
ParentValue,ChildValue
Billing,Overcharge
Billing,Refund Request
Billing,Payment Failed
Technical,Login Issue
Technical,Performance
Technical,Feature Request
```

Upload the CSV when creating or updating field options to establish the parent-child dependency.

### System Fields

Cases includes several built-in system fields that cannot be deleted:

| System Field | Description |
|---|---|
| `title` | Case title (required) |
| `status` | Case status (Open, In Progress, Pending, Closed) |
| `case_id` | Auto-generated unique identifier |
| `created_date` | When the case was created |
| `last_updated_date` | When the case was last modified |
| `reference_number` | Human-readable reference number |
| `assignee` | User or queue assigned to the case |

## Case Rules

Case rules enforce business logic on case fields:

| Rule Type | Description |
|---|---|
| `HiddenCaseRule` | Hides a field based on conditions (e.g., hide "Resolution Notes" when status is "Open") |
| `RequiredCaseRule` | Makes a field required based on conditions (e.g., require "Resolution Notes" when closing a case) |
| `FieldOptionsCaseRule` | Filters dropdown options based on other field values (drives dependent dropdowns) |

Rules are applied at the template level and evaluated in real-time as agents interact with cases.

## Related Items

Cases can have several types of related items attached:

### Contacts

Link contacts (calls, chats, tasks) to a case. When an agent handles a contact and opens a case, the contact is automatically associated.

```javascript
import { CreateRelatedItemCommand } from "@aws-sdk/client-connectcases";

await client.send(new CreateRelatedItemCommand({
  DomainId: domainId,
  CaseId: caseId,
  Type: "Contact",
  Content: {
    Contact: {
      ContactArn: "arn:aws:connect:us-east-1:123456789012:instance/i-id/contact/c-id",
    },
  },
}));
```

### Comments

Free-text comments added by agents or system processes:

```javascript
await client.send(new CreateRelatedItemCommand({
  DomainId: domainId,
  CaseId: caseId,
  Type: "Comment",
  Content: {
    Comment: {
      Body: "Customer confirmed the issue is resolved after applying the fix.",
      ContentType: "Text/Plain",
    },
  },
}));
```

### Files

Attach files (screenshots, logs, documents) to cases as evidence or supporting documentation.

### SLAs

Service Level Agreements track response and resolution time commitments. SLA timers start when a case is created and can pause/resume based on case status changes.

## Audit Events

Track all changes made to a case for compliance and accountability:

```javascript
import { GetCaseAuditEventsCommand } from "@aws-sdk/client-connectcases";

const { auditEvents } = await client.send(new GetCaseAuditEventsCommand({
  DomainId: domainId,
  CaseId: caseId,
  MaxResults: 50,
}));

// auditEvents contains: field changes, status transitions, assignments, comments added, related items linked
```

Each audit event includes:
- Who made the change (user ARN or system)
- What changed (field name, old value, new value)
- When it changed (timestamp)
- Event type (Created, Updated, RelatedItemAdded)

## Identity Resolution Integration

When Customer Profiles identity resolution merges two profiles, cases associated with the merged profiles are automatically **reassociated** to the surviving profile. This ensures case history follows the customer even after deduplication.

## SLA Configuration

Configure SLAs to track case handling performance:

- **Response SLA** -- time from case creation to first agent response
- **Resolution SLA** -- time from case creation to case closure
- **Pause conditions** -- SLA timers pause when case status is "Pending Customer" or other configured statuses
- **Breach notifications** -- trigger alerts or rules when SLA targets are approaching or breached

## Cases in Data Lake

Export case data to your data lake for analytics:

- Cases data can be included in Connect's data lake export
- Exported as structured records to S3
- Queryable via Athena, Redshift Spectrum, or other analytics tools
- Includes case fields, related items, status history, and audit events

## Service Quotas

| Resource | Default Limit |
|---|---|
| Cases per domain | No hard limit (throttled by API rate) |
| Fields per domain | 200 |
| Templates per domain | 25 |
| Layouts per domain | 25 |
| Related items per case | 1,000 |
| Field options per field | 200 |

Quotas can be increased via AWS Service Quotas.

## Key APIs

| API | Purpose |
|---|---|
| `CreateDomain` | Create a Cases domain |
| `CreateTemplate` | Create a case template |
| `CreateLayout` | Create a field layout |
| `CreateField` | Create a custom field |
| `CreateCase` | Create a new case |
| `UpdateCase` | Update case fields |
| `GetCase` | Retrieve a case by ID |
| `SearchCases` | Search cases by field values |
| `CreateRelatedItem` | Add a contact, comment, file, or SLA to a case |
| `SearchRelatedItems` | List related items for a case |
| `GetCaseAuditEvents` | Retrieve change history |
| `BatchGetField` | Get multiple field definitions |
| `BatchPutFieldOptions` | Set field dropdown options |
| `ListTemplates` | List all templates |
| `UpdateTemplate` | Modify a template |
| `DeleteDomain` | Delete a Cases domain and all its data |

All APIs are available via `@aws-sdk/client-connectcases`.

## Case Assignment

Cases can be assigned to agents automatically or manually.

### Auto-Assignment

Configure assignment rules to route cases automatically based on queue membership, agent skills, or round-robin distribution:

- **Queue-based** -- assign cases to agents in a specific queue
- **Skill-based** -- match case attributes (e.g., language, product line) to agent skills
- **Round-robin** -- distribute cases evenly across available agents

### Manual Assignment

Agents or supervisors can assign cases manually through the agent workspace or via the API:

```javascript
await client.send(new UpdateCaseCommand({
  DomainId: domainId,
  CaseId: caseId,
  Fields: [
    {
      Id: "assignee",
      Value: { UserArn: "arn:aws:connect:us-east-1:123456789012:instance/i-id/agent/a-id" },
    },
  ],
}));
```

### Re-Assignment

To reassign a case, update the `assignee` field with a new user ARN. The previous assignee is recorded in the audit trail. Re-assignment can also be triggered by case rules or contact flow logic.

## Cases Metrics

Track case handling performance through available metrics:

| Metric | Description |
|---|---|
| Cases created | Total cases created in a time period |
| Cases resolved | Total cases moved to a closed/resolved status |
| Cases reopened | Cases that were closed and then reopened |
| Average resolution time | Mean time from case creation to closure |
| SLA breach rate | Percentage of cases that exceeded SLA targets |
| Cases by status | Breakdown of cases across Open, In Progress, Pending, Closed |
| Cases by template | Distribution of cases across different templates |

Cases data exported to the data lake (S3) can be queried via Athena or Redshift Spectrum for custom analytics and dashboarding beyond the built-in metrics.

## Case Event Streams

Cases publishes lifecycle events to Amazon EventBridge for real-time integration with external systems.

### Event Types

| Event Type | Trigger |
|---|---|
| `CaseCreated` | A new case is created |
| `CaseUpdated` | One or more case fields are modified |
| `CaseStatusChanged` | The status field transitions to a new value |
| `CaseClosed` | A case is moved to a closed status |

### Event Payload Structure

```json
{
  "version": "0",
  "source": "aws.cases",
  "detail-type": "Amazon Connect Cases Event",
  "detail": {
    "eventType": "CaseStatusChanged",
    "domainId": "domain-uuid",
    "caseId": "case-uuid",
    "fields": {
      "status": { "oldValue": "Open", "newValue": "Closed" }
    },
    "performedBy": {
      "userArn": "arn:aws:connect:us-east-1:123456789012:instance/i-id/agent/a-id"
    },
    "eventTimestamp": "2025-01-15T10:30:00Z"
  }
}
```

### Use Cases

- **External system sync** -- push case updates to a CRM or ticketing system
- **SLA monitoring** -- trigger alerts when cases approach SLA breach thresholds
- **Notifications** -- send email or SMS notifications on case status changes
- **Audit logging** -- stream all case events to a centralized log for compliance

## Tag-Based Access Controls on Cases

Use tags to restrict case visibility and actions by team, department, or priority.

### Tagging Cases

Apply tags when creating or updating cases to classify them by organizational attributes:

- `team:billing` -- cases owned by the billing team
- `department:engineering` -- cases escalated to engineering
- `priority:critical` -- high-priority cases requiring immediate attention

### IAM and Security Profile Conditions

Restrict agent access to cases based on tags using IAM policy conditions or Connect security profiles:

- Agents only see cases tagged with their team
- Supervisors can view cases across multiple teams
- Sensitive cases (e.g., `priority:critical`) can be restricted to senior agents

### Example Use Case

A contact center with separate billing and technical support teams can tag cases accordingly. Billing agents only see cases tagged `team:billing`, while technical agents only see `team:technical`. Supervisors see all cases regardless of tag.

## IAM Permissions for Cases

When building custom IAM policies for Cases access, use the following actions:

| Action | Description |
|---|---|
| `cases:CreateCase` | Create a new case |
| `cases:GetCase` | Retrieve a case by ID |
| `cases:UpdateCase` | Update case fields |
| `cases:SearchCases` | Search cases by field values |
| `cases:CreateTemplate` | Create a case template |
| `cases:CreateLayout` | Create a field layout |
| `cases:CreateField` | Create a custom field |
| `cases:CreateRelatedItem` | Add contacts, comments, or files to a case |
| `cases:GetCaseAuditEvents` | Retrieve case change history |
| `cases:CreateDomain` | Create a Cases domain |
| `cases:DeleteDomain` | Delete a Cases domain |
| `cases:BatchGetField` | Retrieve multiple field definitions |
| `cases:BatchPutFieldOptions` | Set field dropdown options |
| `cases:ListTemplates` | List all templates in a domain |
| `cases:UpdateTemplate` | Modify an existing template |

Resource ARN format: `arn:aws:cases:<region>:<account-id>:domain/<domain-id>`

## Key Considerations

- **One domain per instance** -- a Connect instance can only have one Cases domain
- **Soft delete** -- closing a case does not delete it; cases persist until domain deletion
- **Multi-line text limit** -- 4,100 characters maximum for multi-line text fields
- **Agent workspace** -- cases are surfaced automatically in the agent workspace when Customer Profiles matches the contact to a profile with open cases
- **Automation** -- use Contact Lens rules or EventBridge events to auto-create, update, or close cases based on contact outcomes
- **Access control** -- case visibility is controlled by Connect security profiles; agents only see cases for contacts they handle unless granted broader access
