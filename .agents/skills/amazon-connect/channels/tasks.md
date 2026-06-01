# Tasks Channel

Amazon Connect Tasks let you create, prioritize, assign, and track work items alongside voice, chat, and email contacts. Tasks route through the same queues and routing profiles, giving agents a unified workspace for all work.

Currently approved for GDPR, SOC, PCI, HITRUST, ISO, and HIPAA compliance.

## Overview

Tasks represent units of work that need to be completed -- follow-ups, case reviews, data entry, callbacks, or any action that does not require a real-time conversation. They appear in the agent's CCP alongside other contacts.

**Key properties:**
- Tasks are contacts -- they have a ContactId, appear in contact records, and generate CTR data
- Routed via the same routing profiles and queues as voice/chat/email
- Priority and routing logic apply identically
- Agents accept, work on, and complete tasks through the CCP
- Everything applicable to a voice or chat contact is also applicable to a task contact

---

## Creating Tasks

### Manual Creation (Agent CCP)

Agents create tasks directly from the Contact Control Panel.

- Click "Create task" in the CCP
- If task templates are published, agent must select a template first
- Fill in task name, description, and any template-defined fields
- Assign to a queue (or self-assign if template and permissions allow)
- Set priority if allowed
- Optionally link to a previous contact (e.g., "follow up on call #ABC")
- Optionally schedule the task for a future date and time

**Tracking who created a task:**
- Agents who create tasks through CCP automatically have their agent resource ARN added to the contact record as a segment attribute called `CreatedByUser`
- This attribute is not accessible via the admin console -- use the `DescribeContact` API
- The `CreatedByUser` attribute is also available on the Create task flow block

### Automatic Creation via Contact Flows

Contact flows can create tasks as part of their logic using the **Create task** block.

- Populate task fields from contact attributes, Lambda results, or static values
- Trigger tasks based on flow conditions (e.g., create a follow-up task when a call ends with an unresolved issue)
- Chain multiple task creations in a single flow
- **Link to contact** option: automatically link the task to the current contact
- Set **Contact Expiry** on the block to control task duration

**Important:** The Default customer queue flow does not support tasks out-of-the-box. It contains a Loop prompts block, which does not support tasks. Create a new flow that checks the channel and routes tasks to the desired queue, or update the Loop prompts block so the Error branch does not terminate.

### Automatic Creation via Rules

Connect Rules can automatically generate tasks based on events.

- Contact Lens detects a specific phrase or sentiment and triggers a task
- A contact sits in queue beyond a threshold and a supervisor task is created
- An agent evaluation score drops below a threshold and a coaching task is generated
- Rules are configured in the Connect console under "Rules"

**Third-party integration rules:**
- Salesforce: automatically create tasks when a new case is created (via Amazon AppFlow integration)
- Zendesk: automatically create tasks when a ticket is created or status changes (via Amazon EventBridge integration)
- Rule conditions: specify the event source, the instance of the external application, and the conditions that must be met
- Rule actions: specify the task to generate, including name, description, and reference links visible to the agent

### Programmatic Creation via APIs

Create tasks from external systems -- CRM, ticketing, scheduling, or custom applications.

```javascript
import { ConnectClient, StartTaskContactCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

const response = await client.send(new StartTaskContactCommand({
  InstanceId: instanceId,
  ContactFlowId: contactFlowId,
  Name: "Follow up on billing dispute",
  Description: "Customer reported incorrect charge of $49.99 on invoice #12345. Verify and process refund if valid.",
  // Optional: link to a previous contact
  PreviousContactId: previousContactId,
  // Optional: reference to a related contact
  RelatedContactId: relatedContactId,
  // Task attributes
  Attributes: {
    customerId: "C-12345",
    issueType: "billing_dispute",
    amount: "49.99",
    urgency: "high",
  },
  // Optional: schedule for later
  ScheduledTime: new Date("2026-05-26T09:00:00Z"),
  // Optional: use a task template
  TaskTemplateId: taskTemplateId,
  // Optional: references (links, attachments)
  References: {
    "InvoiceLink": {
      Type: "URL",
      Value: "https://billing.example.com/invoices/12345",
    },
  },
  // Optional: quick connect for routing
  QuickConnectId: quickConnectId,
}));

// response.ContactId -- the task's contact ID
```

**Self-assignment via API:**
- Set `assignmentType` to `SELF` on the `StartTaskContact` API
- Must specify a valid `CreatedByUser` and `TaskTemplateID`
- Agent also needs the security profile permission "Contact Control Panel - Allow self assigning of contacts"

---

## Task Templates

Templates define the structure and fields for a task, ensuring consistency and completeness. When the first template is published, agents are required to select a template when creating tasks.

### Template Fields

Available field types:
- **Text** -- free-form text input
- **Number** -- numeric input
- **Date/Time** -- date and time picker
- **Single-select** -- dropdown with predefined options
- **Email** -- email address field
- **URL** -- URL field
- **Phone** -- phone number field
- **Boolean** -- true/false toggle

Each field supports:
- **Required** -- agent must populate the field to create the task
- **Optional** -- agent can skip the field
- **Default value** -- pre-populate the field when the agent opens the template
- **Ordering** -- use up/down arrows to change field display order

**Important:** It is not possible to use contact attributes in the task templates page to populate field values.

### Template Configuration Sections

**Task assignment:**
- **Assign to** -- allow agents to view and edit task assignment, or set a default contact flow that runs when the task is created
- Only published flows appear in the default value dropdown
- Agents do not see the name of the flow on the CCP

**Self-assign:**
- Enable/disable agents assigning tasks to themselves
- Set default state (checkbox pre-selected or not on the CCP)
- Requires "Allow self assigning of contacts" security profile permission

**Task schedule:**
- Enable/disable agents scheduling a future start date and time for tasks

**Expiry:**
- Default: 7 days
- Configurable up to 90 days (129,600 minutes)

### Template API

```javascript
import { ConnectClient, CreateTaskTemplateCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

const response = await client.send(new CreateTaskTemplateCommand({
  InstanceId: instanceId,
  Name: "Billing Dispute Follow-Up",
  Description: "Template for billing dispute resolution tasks",
  Status: "ACTIVE",
  Fields: [
    {
      Id: { Name: "customerName" },
      Type: "TEXT",
      Description: "Customer's full name",
    },
    {
      Id: { Name: "disputeAmount" },
      Type: "NUMBER",
      Description: "Disputed amount in dollars",
    },
    {
      Id: { Name: "invoiceNumber" },
      Type: "TEXT",
      Description: "Related invoice number",
    },
    {
      Id: { Name: "resolution" },
      Type: "SINGLE_SELECT",
      Description: "Resolution action",
      SingleSelectOptions: ["Refund", "Credit", "No Action", "Escalate"],
    },
    {
      Id: { Name: "dueDate" },
      Type: "DATE_TIME",
      Description: "Resolution deadline",
    },
  ],
  Defaults: {
    DefaultFieldValues: [
      {
        Id: { Name: "resolution" },
        DefaultValue: "No Action",
      },
    ],
  },
}));

// response.Id -- the template ID
```

**Template lifecycle:**
- Templates can be set to `ACTIVE` or `INACTIVE` status
- Inactive templates cannot be used to create new tasks but existing tasks are unaffected
- To return to the standard task experience (no template selection required), disable all published templates
- Templates are versioned -- updates create a new version; active tasks retain their original field structure

---

## Linked and Related Contacts

Tasks can be linked to other contacts for context chains.

### PreviousContactId vs RelatedContactId

| Property | `PreviousContactId` | `RelatedContactId` |
|----------|--------------------|--------------------|
| Attribute propagation | Updates percolate through the **entire chain** | Updates percolate only to the referenced contactId |
| Use case | Sequential follow-up chain | Loosely related contact reference |

**Rules:**
- You can specify only one -- `PreviousContactId` OR `RelatedContactId` -- not both
- Specifying both returns `InvalidRequestException` (400)
- The new task receives a copy of the contact attributes from the linked contact

### Agent-Initiated Linking

While agents are **actively working on a task**, the Number pad appears on the CCP. If they make an outbound call using the Number pad, the call is automatically linked to the task via the `relatedContactID` parameter.

---

## Task References

Tasks support references that appear as links or metadata in the agent's CCP.

**Reference types at creation time:**
- `URL` -- clickable link
- `NUMBER` -- numeric reference
- `STRING` -- text reference
- `DATE` -- date reference
- `EMAIL` -- email address reference

**Note:** `ATTACHMENT` is not a supported reference type during task creation.

**Supported attachment file types (added post-creation):**
.csv, .doc, .docx, .heic, .jfif, .jpeg, .jpg, .mov, .mp4, .pdf, .png, .ppt, .pptx, .rtf, .txt, .wav, .xls, .xlsx (administrators can configure custom extensions)

**Maximum attachment size:** 20 MB (configurable up to 100 MB)

---

## Priority and Routing

Tasks are routed through the same system as all other contact types.

**Priority:**
- Tasks can have a priority value (lower number = higher priority)
- Priority determines order in queue -- higher-priority tasks are offered to agents first
- Priority can be set at creation time or modified in the contact flow via the "Change routing priority/age" block

**Routing:**
- Tasks are assigned to queues and routed via routing profiles
- An agent's routing profile determines which queues they receive tasks from
- Task concurrency is configured separately from voice/chat concurrency in the routing profile
- Example: an agent might handle 1 voice call + 3 chats + 2 tasks simultaneously

**Queue behavior:**
- Tasks wait in queue like any other contact
- Queue metrics (oldest contact, contacts in queue) include tasks
- Supervisors can see task queue depth in real-time metrics
- Quick connects are used to enable agent-to-agent task assignment in the CCP dropdown

**How to send tasks to a queue (recommended pattern):**
1. Add a Loop block with desired iteration count (e.g., 10 for 10-minute wait)
2. On the Looping branch, use a Check staffing block to check agent availability
3. If agents are available, transfer to the queue via Transfer to queue block
4. Set the Complete branch to route to Disconnect/hang up (triggered if no agents available during the loop)

---

## Task Expiry and Duration

Tasks have a configurable expiration window.

| Setting | Value |
|---------|-------|
| Default expiry | 7 days |
| Maximum expiry (via template) | 90 days (129,600 minutes) |
| Maximum duration (hard limit) | 30 days |

**When a task ends:**
1. An agent completes the task
2. A flow runs a Disconnect/hang up block
3. The task reaches the default 7-day limit
4. The task reaches its configured `Expiry Duration In Minutes` (from the template)
5. The `StopContact` API is called
6. The Contact Expiry setting on the Create task block is reached

- Expired tasks are automatically closed
- Expired/completed tasks still appear in contact records and historical metrics

---

## Pausing and Resuming Tasks

Agents can pause a task and return to it later.

**How it works:**
- Agent accepts a task and begins working
- Agent pauses the task (e.g., waiting for information from another team)
- Task returns to a paused state -- the agent's slot is freed for other work
- Agent (or another agent) resumes the task later
- Full context is preserved across pause/resume cycles

**Use cases:**
- Waiting for customer callback
- Pending approval from a manager
- Blocked on information from an external system
- Multi-day tasks that require incremental progress

**Behavioral details:**
- Paused tasks do not count against the agent's concurrency limit
- Paused tasks can be reassigned to a different agent or queue
- The pause timestamp and resume timestamp are recorded in the contact record

**APIs:**
- `PauseContact` -- pause an active task
- `ResumeContact` -- resume a paused task

---

## Task Transfer

Tasks can be transferred between agents or queues.

- Use `TransferContact` API to transfer a task programmatically
- Agents can transfer tasks from the CCP to another queue or agent
- Maximum number of transfers for a single task: **11 transfers**
- Transferred tasks retain their attributes and context

---

## Follow-Up Automation

Tasks enable structured follow-up workflows.

**Patterns:**
- A voice call ends and a flow automatically creates a follow-up task linked to that contact
- A task is completed and a rule creates a subsequent task (task chaining)
- A scheduled task fires at a specific date/time for proactive outreach
- An SLA breach triggers an escalation task to a supervisor queue

**Scheduled tasks:**
- Set the `ScheduledTime` parameter when creating a task via API
- The task will not be routed to an agent until the scheduled time
- Scheduled tasks display the scheduled time in the Contact Summary on contact records
- Useful for callbacks, reminders, and time-sensitive follow-ups

```javascript
await client.send(new StartTaskContactCommand({
  InstanceId: instanceId,
  ContactFlowId: contactFlowId,
  Name: "Scheduled callback - Jane Doe",
  ScheduledTime: new Date("2026-05-26T14:00:00Z"), // Route at 2 PM UTC
  Attributes: {
    callbackNumber: "+14155551234",
    reason: "Follow up on claim #789",
  },
}));
```

---

## Third-Party Integrations

### Salesforce

- Uses Amazon AppFlow for integration
- Automatically create tasks based on Salesforce case events
- No custom development required -- configure via the Connect admin console

### Zendesk

- Uses Amazon EventBridge for integration
- Automatically create tasks based on Zendesk ticket creation or status changes
- Configure rules with event source, conditions, and task actions

**Event integration resource limit:** 10 per instance (used for task triggers)

---

## Supported Flow Types

Tasks can be used in the following flow types:
- Inbound flow
- Customer queue flow
- Agent whisper flow
- Transfer to queue flow
- Transfer to agent flow

## Supported Contact Blocks

| Block | Purpose |
|-------|---------|
| Create task | Generate a new task from within a flow |
| Check contact attributes | Branch logic based on task attributes |
| Check hours of operation | Route tasks based on business hours |
| Check queue status | Check queue depth before routing |
| Check staffing | Verify agent availability |
| Set contact attributes | Add/modify task metadata |
| Invoke Lambda | Enrich task data from external systems |
| Transfer to queue | Route task to a specific queue |
| Transfer to flow | Transfer to another flow |
| Set working queue | Change the task's target queue |
| Set customer queue flow | Set the queue flow for the task |
| Set disconnect flow | Set the disconnect flow |
| Change routing priority/age | Modify priority or age in queue |
| Distribute by percentage | A/B routing for tasks |
| Loop | Iterate with wait conditions |
| Wait | Wait block for timing |
| Get queue metrics | Query queue state |
| End flow / resume | End or resume the flow |
| Disconnect / hang up | Close/complete the task |

---

## Task APIs Summary

| API | Purpose |
|-----|---------|
| `StartTaskContact` | Create a new task contact |
| `CreateTaskTemplate` | Define a new task template with custom fields |
| `UpdateTaskTemplate` | Modify an existing task template |
| `GetTaskTemplate` | Retrieve a task template definition |
| `ListTaskTemplates` | List all task templates in an instance |
| `DeleteTaskTemplate` | Remove a task template |
| `TransferContact` | Transfer a task to another queue or agent |
| `StopContact` | Complete/close a task |
| `UpdateContact` | Update task name, description, or references |
| `UpdateContactAttributes` | Update task contact attributes |
| `PauseContact` | Pause an active task |
| `ResumeContact` | Resume a paused task |
| `DescribeContact` | Retrieve task details including `CreatedByUser` |

---

## Limits and Quotas

| Item | Specification |
|------|---------------|
| Task templates per instance | 50 |
| Task template customized fields per instance | 50 |
| Maximum duration of a task | Default 7 days, extensible up to 30 days |
| Maximum expiry via template | 90 days (129,600 minutes) |
| Maximum transfers per task | 11 |
| Maximum linked tasks on an existing contact | 11 |
| Contact record retention | 24 months from contact initiation |
| Attributes per contact | Up to 32,768 UTF-8 bytes across all key-value pairs |
| Attribute key length | 1-32,767 characters (alphanumeric, `-`, `_` only) |
| Attribute value length | 0-32,767 characters |

---

## Metrics and Reporting

Tasks appear in both real-time and historical metrics.

**Real-time metrics:**
- Tasks in queue
- Agents handling tasks
- Oldest task in queue
- Task acceptance rate

**Historical metrics:**
- Tasks created, completed, expired, transferred
- Average handle time for tasks
- Task-specific agent performance
- Filter by queue, agent, routing profile, or time range
- Average active time
- Average agent pause time

**Metrics that show 0 for tasks (not applicable):**
- Average agent interaction time
- Average customer hold time
- Agent interaction and hold time
- Agent interaction time

**Custom service levels:**
- Tasks may have SLAs measured in hours or days (unlike voice/chat measured in seconds/minutes)
- Create custom service level durations appropriate to each channel

**Contact records:**
- Every task generates a Contact Trace Record (CTR)
- CTR includes: creation time, assignment time, completion time, agent, queue, attributes, linked contacts
- CTRs available via Kinesis Data Stream or S3 export
- Contact record data includes ContactDetails (Name, Description), References (links/URLs), and Flow ID
- Scheduled tasks also display the scheduled time in Contact Summary
- Use Contact search page to search for and review completed tasks

---

## Key Considerations

- **Not real-time:** Tasks are asynchronous work items, not live conversations
- **Linking:** Tasks can be linked to previous contacts via `PreviousContactId` for full context chains
- **No customer participant:** Tasks do not have a customer-facing component -- the agent works on them independently
- **Concurrency:** Task slots are separate from voice/chat slots in routing profile configuration
- **Automation:** Combine tasks with Rules, Contact Lens, and Lambda for powerful workflow automation
- **SLA tracking:** Use scheduled tasks and expiry to enforce business SLAs programmatically
- **IAM permissions:** Ensure users have task-related permissions in custom IAM policies
- **Default queue flow:** Does not support tasks -- create a dedicated task queue flow
- **Template-first:** Once the first template is published, agents must always select a template to create tasks
