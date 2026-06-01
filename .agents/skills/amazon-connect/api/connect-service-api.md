# Amazon Connect Service API Reference

The core Amazon Connect Service API provides **200+ actions** organized across **33 resource types** and approximately **530 data types**.

**SDK Package**: `@aws-sdk/client-connect`

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';
const client = new ConnectClient({ region: 'us-east-1' });
```

## Actions by Resource Type

### Analytics Data Lake

- `CreateAnalyticsDataAssociation` — associate data lake with Connect instance
- `DeleteAnalyticsDataAssociation` — remove data lake association
- `ListAnalyticsDataAssociations` — list all data lake associations
- `BatchGetFlowAssociation` — get flow associations in batch

### Agent Status

- `CreateAgentStatus` — create a custom agent status
- `UpdateAgentStatus` — update agent status name/description/order
- `DescribeAgentStatus` — get agent status details
- `ListAgentStatuses` — list all agent statuses for instance
- `SearchAgentStatuses` — search agent statuses with filters

### Chat

- `StartChatContact` — initiate a chat contact
- `CreatePersistentContactAssociation` — link persistent chat to contact
- `SendChatIntegrationEvent` — send external chat events (SNS, custom)

### Contacts

- `DescribeContact` — get contact details (duration, attributes, agent, queue)
- `UpdateContact` — update contact attributes/description
- `UpdateContactAttributes` — update key-value attributes on active contact
- `ListContactReferences` — list references attached to contact
- `SearchContacts` — search contacts by time range, channels, attributes (10 TPS)
- `GetContactAttributes` — get all attributes on a contact
- `StartContactRecording` — start recording an active voice contact
- `StopContactRecording` — stop recording
- `SuspendContactRecording` — pause recording
- `ResumeContactRecording` — resume paused recording
- `MonitorContact` — start silent monitoring or barge-in
- `PauseContact` — pause an active contact (hold)
- `ResumeContact` — resume a paused contact
- `StopContact` — disconnect a contact
- `TransferContact` — transfer to queue or agent
- `CreateContact` — create an outbound or task contact programmatically
- `BatchPutContact` — create multiple contacts in batch
- `StartContactStreaming` — start real-time contact streaming to Kinesis

### Data Tables

- `CreateDataTable` — create a custom data table
- `UpdateDataTable` — update schema or description
- `DeleteDataTable` — delete a data table
- `GetDataTable` — get data table metadata
- `ListDataTables` — list all data tables
- `GetDataTableRow` — get a single row by key
- `CreateDataTableRow` — insert a row
- `UpdateDataTableRow` — update a row
- `DeleteDataTableRow` — delete a row
- `ListDataTableRows` — list/search rows with filters

### Email

- `StartEmailContact` — initiate an inbound email contact
- `SendOutboundEmail` — send an outbound email from a Connect instance
- `CreateEmailAddress` — create a managed email address
- `UpdateEmailAddressMetadata` — update display name/description
- `DeleteEmailAddress` — delete a managed email address
- `DescribeEmailAddress` — get email address details
- `ListEmailAddresses` — list email addresses by instance
- `SearchEmailAddresses` — search with filters

### Evaluations

- `CreateEvaluationForm` — create evaluation form template
- `UpdateEvaluationForm` — update form questions/scoring
- `DeleteEvaluationForm` — delete a form
- `DescribeEvaluationForm` — get form details
- `ListEvaluationForms` — list all forms
- `ListEvaluationFormVersions` — list versions of a form
- `ActivateEvaluationForm` — activate a form version
- `DeactivateEvaluationForm` — deactivate a form
- `StartContactEvaluation` — start evaluating a contact
- `UpdateContactEvaluation` — update evaluation answers
- `SubmitContactEvaluation` — submit completed evaluation
- `DeleteContactEvaluation` — delete a draft evaluation
- `DescribeContactEvaluation` — get evaluation details
- `ListContactEvaluations` — list evaluations for a contact

### Files (Attached Files)

- `StartAttachedFileUpload` — get presigned upload URL
- `CompleteAttachedFileUpload` — confirm upload completion
- `DeleteAttachedFile` — delete an attached file
- `GetAttachedFile` — get file metadata and download URL
- `BatchGetAttachedFileMetadata` — get metadata for multiple files
- `ListAttachedFiles` — list files for a resource

### Flows & Flow Modules

- `CreateContactFlow` — create a contact flow (JSON definition)
- `UpdateContactFlowContent` — update flow definition
- `UpdateContactFlowMetadata` — update flow name/description/status
- `DeleteContactFlow` — delete a flow
- `DescribeContactFlow` — get flow details including content
- `ListContactFlows` — list all flows by type
- `SearchContactFlows` — search flows with filters
- `CreateContactFlowVersion` — publish a flow version
- `ListContactFlowVersions` — list versions
- `CreateContactFlowModule` — create a reusable flow module
- `UpdateContactFlowModuleContent` — update module definition
- `UpdateContactFlowModuleMetadata` — update module metadata
- `DeleteContactFlowModule` — delete a module
- `DescribeContactFlowModule` — get module details
- `ListContactFlowModules` — list all modules
- `SearchContactFlowModules` — search modules with filters

### Hierarchy Groups

- `CreateUserHierarchyGroup` — create hierarchy group
- `UpdateUserHierarchyGroupName` — rename group
- `DeleteUserHierarchyGroup` — delete group
- `DescribeUserHierarchyGroup` — get group details
- `ListUserHierarchyGroups` — list groups
- `SearchUserHierarchyGroups` — search groups
- `UpdateUserHierarchyStructure` — update hierarchy levels (up to 5)
- `DescribeUserHierarchyStructure` — get hierarchy structure

### Hours of Operation

- `CreateHoursOfOperation` — create business hours schedule
- `UpdateHoursOfOperation` — update schedule
- `DeleteHoursOfOperation` — delete schedule
- `DescribeHoursOfOperation` — get schedule details
- `ListHoursOfOperation` — list all schedules
- `SearchHoursOfOperation` — search schedules
- `CreateHoursOfOperationOverride` — create holiday/exception override
- `UpdateHoursOfOperationOverride` — update override
- `DeleteHoursOfOperationOverride` — delete override
- `GetHoursOfOperationOverride` — get override details
- `ListHoursOfOperationOverrides` — list overrides

### Instances

- `CreateInstance` — create a Connect instance
- `UpdateInstanceAttribute` — update instance settings
- `DeleteInstance` — delete an instance
- `DescribeInstance` — get instance details
- `DescribeInstanceAttribute` — get specific attribute
- `ListInstances` — list all instances in account
- `ListInstanceAttributes` — list all instance attributes
- `UpdateInstanceStorageConfig` — configure storage (S3, Kinesis, etc.)
- `DescribeInstanceStorageConfig` — get storage config
- `ListInstanceStorageConfigs` — list storage configs
- `AssociateInstanceStorageConfig` — associate storage config
- `DisassociateInstanceStorageConfig` — remove storage config

### Integration Associations

- `CreateIntegrationAssociation` — associate external integration
- `DeleteIntegrationAssociation` — remove integration
- `ListIntegrationAssociations` — list integrations

### Metrics

- `GetMetricDataV2` — get historical metrics with advanced filters (10 TPS)
- `GetCurrentMetricData` — get real-time queue/agent metrics (5 TPS)
- `GetCurrentUserData` — get real-time agent data
- `ListMetricDataCollections` — list metric collections
- `SearchContactFlowExecutions` — search flow execution metrics
- `ListFlowAssociations` — list flow associations

### Notifications

- `CreatePushNotificationRegistration` — register for push notifications
- `DeletePushNotificationRegistration` — unregister
- `PutPushNotificationRegistrations` — batch register
- `ListPushNotificationRegistrations` — list registrations

### Phone Numbers

- `ClaimPhoneNumber` — claim a phone number
- `ReleasePhoneNumber` — release a phone number
- `UpdatePhoneNumber` — update phone number target (flow/queue)
- `UpdatePhoneNumberMetadata` — update description
- `DescribePhoneNumber` — get phone number details
- `ListPhoneNumbers` — list phone numbers (legacy)
- `ListPhoneNumbersV2` — list phone numbers with enhanced filters
- `SearchAvailablePhoneNumbers` — search claimable numbers by country/type
- `ImportPhoneNumber` — import external phone number
- `SendOutboundEmail` — send email via phone number

### Predefined Attributes

- `CreatePredefinedAttribute` — create a predefined attribute
- `UpdatePredefinedAttribute` — update values
- `DeletePredefinedAttribute` — delete attribute
- `DescribePredefinedAttribute` — get attribute details
- `ListPredefinedAttributes` — list all predefined attributes
- `SearchPredefinedAttributes` — search with filters

### Prompts

- `CreatePrompt` — create audio prompt (upload to S3)
- `UpdatePrompt` — update prompt audio/metadata
- `DeletePrompt` — delete a prompt
- `DescribePrompt` — get prompt details
- `ListPrompts` — list all prompts
- `SearchPrompts` — search prompts

### Queues

- `CreateQueue` — create a queue
- `UpdateQueueName` — rename queue
- `UpdateQueueHoursOfOperation` — change queue hours
- `UpdateQueueMaxContacts` — set max contacts in queue
- `UpdateQueueOutboundCallerConfig` — set outbound caller ID
- `UpdateQueueOutboundEmailConfig` — set outbound email config
- `UpdateQueueStatus` — enable/disable queue
- `DeleteQueue` — delete a queue
- `DescribeQueue` — get queue details
- `ListQueues` — list all queues
- `SearchQueues` — search queues with filters

### Quick Connects

- `CreateQuickConnect` — create quick connect (agent/queue/phone)
- `UpdateQuickConnectConfig` — update quick connect target
- `UpdateQuickConnectName` — rename
- `DeleteQuickConnect` — delete
- `DescribeQuickConnect` — get details
- `ListQuickConnects` — list all
- `SearchQuickConnects` — search with filters

### Routing Profiles

- `CreateRoutingProfile` — create routing profile
- `UpdateRoutingProfileName` — rename
- `UpdateRoutingProfileDefaultOutboundQueue` — change default queue
- `UpdateRoutingProfileConcurrency` — update channel concurrency
- `UpdateRoutingProfileQueues` — update queue associations
- `UpdateRoutingProfileAgentAvailabilityTimer` — set availability timer
- `DeleteRoutingProfile` — delete
- `DescribeRoutingProfile` — get details
- `ListRoutingProfiles` — list all
- `ListRoutingProfileQueues` — list queues in profile
- `SearchRoutingProfiles` — search with filters
- `AssociateRoutingProfileQueues` — add queues to profile
- `DisassociateRoutingProfileQueues` — remove queues

### Rules

- `CreateRule` — create automation rule
- `UpdateRule` — update rule conditions/actions
- `DeleteRule` — delete a rule
- `DescribeRule` — get rule details
- `ListRules` — list rules by event source

### Security Profiles

- `CreateSecurityProfile` — create security profile
- `UpdateSecurityProfile` — update permissions
- `DeleteSecurityProfile` — delete
- `DescribeSecurityProfile` — get details
- `ListSecurityProfiles` — list all
- `SearchSecurityProfiles` — search with filters
- `ListSecurityProfileApplications` — list app access
- `ListSecurityProfilePermissions` — list permissions
- `GetSecurityProfileAttachment` — download attachment

### Tags

- `TagResource` — add tags to any Connect resource
- `UntagResource` — remove tags
- `ListTagsForResource` — list tags on a resource
- `TagContact` — add tags to a contact
- `UntagContact` — remove tags from contact
- `ListContactTags` — list tags on a contact

### Tasks

- `StartTaskContact` — create a task contact
- `UpdateTaskTemplate` — update task template
- `CreateTaskTemplate` — create task template
- `DeleteTaskTemplate` — delete task template
- `GetTaskTemplate` — get task template details
- `ListTaskTemplates` — list all task templates

### Traffic Distribution Groups

- `CreateTrafficDistributionGroup` — create TDG for multi-region
- `UpdateTrafficDistribution` — update traffic percentages
- `DeleteTrafficDistributionGroup` — delete TDG
- `DescribeTrafficDistributionGroup` — get details
- `GetTrafficDistribution` — get current distribution
- `ListTrafficDistributionGroups` — list TDGs
- `ListTrafficDistributionGroupUsers` — list users in TDG
- `ReplicateInstance` — replicate instance to another region

### Use Cases

- `CreateUseCase` — create use case for integration
- `DeleteUseCase` — delete use case
- `ListUseCases` — list use cases

### User Management

- `CreateUser` — create an agent/user
- `UpdateUserIdentityInfo` — update name/email
- `UpdateUserPhoneConfig` — update phone settings (soft/desk phone)
- `UpdateUserRoutingProfile` — change routing profile
- `UpdateUserSecurityProfiles` — change security profiles
- `UpdateUserHierarchy` — change hierarchy group assignment
- `UpdateUserProficiencies` — update skill proficiencies
- `DeleteUser` — delete a user
- `DescribeUser` — get user details
- `ListUsers` — list all users
- `SearchUsers` — search users with filters (recommended over List)
- `ListUserProficiencies` — list user skill proficiencies

### Views

- `CreateView` — create an agent workspace view
- `UpdateViewContent` — update view definition
- `UpdateViewMetadata` — update view name/description
- `DeleteView` — delete a view
- `DescribeView` — get view details
- `ListViews` — list all views
- `CreateViewVersion` — publish a view version
- `ListViewVersions` — list view versions
- `SearchViews` — search views

### Vocabulary

- `CreateVocabulary` — create custom vocabulary for transcription
- `UpdateVocabulary` — update vocabulary
- `DeleteVocabulary` — delete vocabulary
- `DescribeVocabulary` — get vocabulary details
- `ListDefaultVocabularies` — list default vocabularies
- `AssociateDefaultVocabulary` — set default vocabulary for language
- `DisassociateDefaultVocabulary` — remove default

### Voice

- `StartOutboundVoiceContact` — initiate outbound voice call
- `StartOutboundChatContact` — initiate outbound chat
- `StartWebRTCContact` — initiate WebRTC video contact

### Workspaces

- `CreateWorkspace` — create agent workspace
- `UpdateWorkspace` — update workspace config
- `DeleteWorkspace` — delete workspace
- `DescribeWorkspace` — get workspace details
- `ListWorkspaces` — list workspaces

## Key Data Types

These are the most important data types returned by the Connect Service API:

### Contact

```typescript
interface Contact {
  Arn: string;
  Id: string;
  InitialContactId?: string;
  PreviousContactId?: string;
  InitiationMethod: 'INBOUND' | 'OUTBOUND' | 'TRANSFER' | 'QUEUE_TRANSFER' | 'CALLBACK' | 'API' | 'DISCONNECT' | 'MONITOR' | 'EXTERNAL_OUTBOUND';
  Channel: 'VOICE' | 'CHAT' | 'TASK' | 'EMAIL';
  Name?: string;
  Description?: string;
  QueueInfo?: { Id: string; EnqueueTimestamp: Date };
  AgentInfo?: { Id: string; ConnectedToAgentTimestamp: Date };
  InitiationTimestamp: Date;
  DisconnectTimestamp?: Date;
  LastUpdateTimestamp?: Date;
  ScheduledTimestamp?: Date;
  Tags?: Record<string, string>;
}
```

### Queue

```typescript
interface Queue {
  Name: string;
  QueueArn: string;
  QueueId: string;
  Description?: string;
  OutboundCallerConfig?: OutboundCallerConfig;
  HoursOfOperationId: string;
  MaxContacts?: number;
  Status: 'ENABLED' | 'DISABLED';
  Tags?: Record<string, string>;
}
```

### RoutingProfile

```typescript
interface RoutingProfile {
  InstanceId: string;
  Name: string;
  RoutingProfileArn: string;
  RoutingProfileId: string;
  Description?: string;
  MediaConcurrencies: MediaConcurrency[];
  DefaultOutboundQueueId: string;
  Tags?: Record<string, string>;
}
```

### User

```typescript
interface User {
  Id: string;
  Arn: string;
  Username: string;
  IdentityInfo?: { FirstName: string; LastName: string; Email: string };
  PhoneConfig: { PhoneType: 'SOFT_PHONE' | 'DESK_PHONE'; AutoAccept?: boolean; AfterContactWorkTimeLimit?: number };
  DirectoryUserId?: string;
  SecurityProfileIds: string[];
  RoutingProfileId: string;
  HierarchyGroupId?: string;
  Tags?: Record<string, string>;
}
```

### ContactFlow

```typescript
interface ContactFlow {
  Arn: string;
  Id: string;
  Name: string;
  Type: 'CONTACT_FLOW' | 'CUSTOMER_QUEUE' | 'CUSTOMER_HOLD' | 'CUSTOMER_WHISPER' | 'AGENT_HOLD' | 'AGENT_WHISPER' | 'OUTBOUND_WHISPER' | 'AGENT_TRANSFER' | 'QUEUE_TRANSFER';
  State: 'ACTIVE' | 'ARCHIVED';
  Status?: 'PUBLISHED' | 'SAVED';
  Description?: string;
  Content: string; // JSON string of flow definition
  Tags?: Record<string, string>;
}
```

### EvaluationForm

```typescript
interface EvaluationForm {
  EvaluationFormId: string;
  EvaluationFormVersion: number;
  EvaluationFormArn: string;
  Title: string;
  Description?: string;
  Status: 'DRAFT' | 'ACTIVE';
  Items: EvaluationFormItem[];
  ScoringStrategy?: { Mode: 'QUESTION_ONLY' | 'SECTION_ONLY'; Status: 'ENABLED' | 'DISABLED' };
}
```

### Rule

```typescript
interface Rule {
  Name: string;
  RuleId: string;
  RuleArn: string;
  TriggerEventSource: { EventSourceName: string; IntegrationAssociationId?: string };
  Function: string; // JSON Rules Function Language expression
  Actions: RuleAction[];
  PublishStatus: 'DRAFT' | 'PUBLISHED';
}
```

### DataTable

```typescript
interface DataTable {
  DataTableArn: string;
  DataTableId: string;
  DisplayName: string;
  Description?: string;
  Fields: DataTableField[];
  Status: 'ACTIVE' | 'CREATING' | 'DELETING';
}
```

### View

```typescript
interface View {
  Id: string;
  Arn: string;
  Name: string;
  Status: 'PUBLISHED' | 'SAVED';
  Type: 'CUSTOMER_MANAGED' | 'AWS_MANAGED';
  Description?: string;
  Version?: number;
  Content?: ViewContent;
  Tags?: Record<string, string>;
}
```

### Workspace

```typescript
interface Workspace {
  WorkspaceId: string;
  WorkspaceArn: string;
  Alias: string;
  Description?: string;
  Status: 'ACTIVE' | 'CREATING' | 'DELETING';
}
```

## Approximate Data Type Count

The Connect Service API defines approximately **530 data types** including request/response structures, enums, and nested types. The types listed above are the most commonly used resource types.
