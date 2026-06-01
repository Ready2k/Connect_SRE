# Amazon Connect — Instance Management

## Instance Lifecycle

### Creation
- **Console**: Connect console → "Get started" or "Add an instance" → 5-step wizard
- **CLI/API**: `CreateInstance` — programmatic creation
- **CloudFormation**: `AWS::Connect::Instance` resource
- **Alias**: Appears in URL `https://{alias}.my.connect.aws/` — **cannot be changed after creation**
- **Permissions**: Requires `AmazonConnect_FullAccess` policy or equivalent custom IAM permissions
- **Regional**: Instances are region-specific; you can have multiple instances per region
- **Next Generation**: Enabled by default on new instances — all-inclusive AI pricing model; can be disabled after creation to pay separately for channels and optimization features
- **Restriction**: Amazon Connect is not available to customers in India using AWS India Private Limited

### Deletion
- `DeleteInstance` — **permanent**, removes all configuration and associated resources
- No built-in undo — all data (users, flows, queues, etc.) is permanently removed
- S3 data (recordings, transcripts) stored in your buckets is **not** deleted

### Default Limit
- **2 instances per AWS account** (adjustable via Service Quotas)

## Identity Management

Choose one at instance creation — **cannot be changed after creation**:

| Option | Description | User Management |
|---|---|---|
| **Store users in Connect** | Connect-managed user directory | Users created/managed within Connect; cannot share with other apps |
| **Link to existing directory** | AWS Directory Service integration | Users managed in directory; each directory links to one Connect instance at a time |
| **SAML 2.0** | Federate with external IdP | Users managed through IdP; access URL uses custom alias |

### Access URL
- Format: `https://{alias}.my.connect.aws/`
- For Connect-managed or SAML: you choose the alias (must be globally unique across all instances in all regions)
- For Directory: directory name becomes the alias
- **Cannot be changed** after instance creation

### Administrator Setup
- Optional during creation — can skip and add later
- Created user gets the **Admin** security profile
- For SAML: admin name maps to IdP user
- For Directory: admin must be existing directory user

## Instance Attributes

Enable/disable features per instance via `UpdateInstanceAttribute`:

| Attribute | Description |
|---|---|
| `INBOUND_CALLS` | Allow inbound calls to contact center |
| `OUTBOUND_CALLS` | Allow outbound calling from contact center |
| `CONTACT_LENS` | Conversational analytics (real-time and post-call) |
| `AUTO_RESOLVE_BEST_VOICES` | Use best available Amazon Polly neural TTS voice |
| `CONTACTFLOW_LOGS` | Flow event logging to CloudWatch Logs |
| `EARLY_MEDIA` | Agents hear pre-connection audio (busy signals, errors) on outbound calls |
| `MULTI_PARTY_CONFERENCE` | Up to 6 participants on voice calls + supervisor barge-in |
| `HIGH_VOLUME_OUTBOUND` | Outbound campaigns support |
| `ENHANCED_CONTACT_MONITORING` | Enhanced multi-party monitoring and barge capability |
| `MULTI_PARTY_CHAT` | Up to 6 participants on chats + chat barge-in |

### Notes on Attributes
- **Early media**: Enabled by default for instances created after April 17, 2020; older instances must enable manually
- **Multi-party voice**: Requires CCPv2; enables barge capabilities
- **Multi-party chat**: If chat barge was enabled before Dec 2024, toggle off then on to enable multi-party chats
- **Contact Lens**: Configured separately under Analytics tools in console
- **Flow logs**: Sends flow execution events to CloudWatch; enable under Flows settings

## Storage Configuration

Configure via `AssociateInstanceStorageConfig`. Default S3 buckets are created automatically during instance setup.

### S3 Storage (with optional KMS encryption)

| Storage Type | Purpose | Notes |
|---|---|---|
| **Call recordings** | Voice conversation recordings | Enables call recording at instance level; still requires flow-level "Set recording behavior" block |
| **Chat transcripts** | Chat conversation transcripts | All chat transcripts stored automatically once bucket exists |
| **Screen recordings** | Agent screen recordings | Not enabled by default; requires agent app install + flow block |
| **Exported reports** | Scheduled/exported reports | |
| **Contact Lens output** | Analyzed conversation output | Voice uses recording KMS key; chat uses chat recording key |
| **Contact evaluations** | Performance evaluation data | Enables evaluations at instance level |
| **Email messages** | Email channel storage | Enables email channel at instance level |
| **Attachments** | File sharing for agents/customers | Requires CORS policy on attachments bucket for email to work |

**Important**: Amazon Connect does **not** support S3 Object Lock in compliance mode (WORM).

### Kinesis Streaming

| Stream Type | Destination | Purpose |
|---|---|---|
| **Contact records (CTR)** | Kinesis Data Stream or Kinesis Firehose | Real-time contact record export |
| **Agent events** | Kinesis Data Stream | Agent state change events |

Enable under Data streaming settings. Not enabled by default.

### CloudWatch

- **Flow logs**: Flow execution events sent to CloudWatch Logs
- Enable under Flows settings or via `UpdateInstanceAttribute` with `CONTACTFLOW_LOGS`

### Live Media Streaming
- Not enabled by default
- Streams customer audio in real-time via Kinesis Video Streams

### Customer Profiles
- Domain created by default during instance setup
- Stores profiles combining contact history with customer information (account number, address, etc.)
- Encrypted with KMS (can configure customer-managed key after setup)

## Instance Settings Update

Update via console navigation or API:

| Setting Category | Console Path | Key Options |
|---|---|---|
| **Telephony** | Telephony | Inbound/outbound calls, early media, multi-party, campaigns |
| **Data storage** | Data storage | S3 buckets + KMS keys for each storage type |
| **Data streaming** | Data streaming | Kinesis streams for CTR and agent events |
| **Analytics tools** | Analytics tools | Contact Lens enable/disable |
| **Flows** | Flows | Signing keys, Lex bots, Lambda functions, flow logs, Polly voices |

## Service Quotas

**All quotas are adjustable unless noted otherwise.** Request increases via Service Quotas console.

### Core Instance Quotas

| Resource | Default | Adjustable | Level |
|---|---|---|---|
| Amazon Connect instances per account | 2 | Yes | Account |
| Concurrent active calls per instance | 10 | Yes | Resource |
| Concurrent active chats per instance | 500 | Yes | Resource |
| Concurrent active emails per instance | 1,000 | Yes | Resource |
| Concurrent active tasks per instance | 2,500 | Yes | Resource |
| Phone numbers per instance | 5 | Yes | Resource |
| Flows per instance | 100 | Yes | Resource |
| Modules per instance | 200 | Yes | Resource |
| Queues per instance | 100 | Yes | Resource |
| Queues per routing profile | 50 | Yes | Resource |
| Max contacts in agent queue per instance | 10 | Yes | Resource |
| Routing profiles per instance | 500 | Yes | Resource |
| Users per instance | 500 | Yes | Resource |
| Security profiles per instance | 100 | Yes | Resource |
| Quick connects per instance | 100 | Yes | Resource |
| Prompts per instance | 500 | Yes | Resource |
| Hours of operation per instance | 100 | Yes | Resource |
| Overrides per hours of operation | 50 | **No** | N/A |
| Inherit recurring overrides per HoO | 3 | **No** | N/A |
| Agent status per instance | 50 | **No** | N/A |
| Reports per instance | 2,000 | Yes | Resource |
| Scheduled reports per instance | 100 | Yes | Resource |
| User hierarchy groups per instance | 500 | Yes | Resource |
| AWS Lambda functions per instance | 50 | Yes | Resource |
| Amazon Lex bots per instance | 70 | **No** | Resource |
| Amazon Lex V2 bot aliases per instance | 100 | Yes | Resource |
| Predefined attributes per instance | 150 | Yes | Resource |
| Proficiencies per agent | 10 | Yes | Resource |
| Custom metrics per instance | 1,000 | **No** | Resource |
| Task templates per instance | 50 | **No** | N/A |
| Task template customized fields | 50 | **No** | N/A |
| Data tables per instance | 100 | Yes | Resource |
| Attributes per data table | 100 | **No** | N/A |
| Primary attributes per data table | 5 | **No** | N/A |
| Values per data table | 1,000 | Yes | Resource |
| Email addresses per instance | 100 (up to 500) | Yes | Resource |
| Email domains per instance | 1 Connect + 100 custom | **No** | Resource |
| Max future task schedule | 6 days | **No** | N/A |
| Max task reschedules | 20 | **No** | N/A |

### Contact Lens Quotas

| Resource | Default | Adjustable |
|---|---|---|
| Concurrent real-time calls with analytics | 300 | Yes |
| Concurrent post-call analytics jobs | 200 | Yes |
| Concurrent chat analytics jobs | 200 | Yes |
| Concurrent automated interaction analytics | 20 | Yes |
| Concurrent post-contact agent summary jobs | 10 | Yes |
| Concurrent post-contact auto interaction summary | 2 | Yes |
| Concurrent after-call agent summary jobs | 2 | Yes |

### Outbound Campaigns Quotas

| Resource | Default | Adjustable |
|---|---|---|
| Campaigns per account | 25 | Yes |
| Concurrent campaign active calls per instance | 0 (must request) | Yes |

### Cases Quotas

| Resource | Default | Adjustable |
|---|---|---|
| Cases domains per account | 5 | Yes |
| Fields per domain | 500 | Yes |
| Field options per single-select field | 500 | Yes |
| Layouts per domain | 100 | Yes |
| Templates per domain | 100 | Yes |
| Related items per case | 200 | Yes |
| Files per case | 50 | Yes |
| Case fields per layout | 100 | **No** |
| SLAs per case | 10 | Yes |

### Customer Profiles Quotas

| Resource | Default | Adjustable |
|---|---|---|
| Domains per region | 100 | Yes |
| Keys per object type | 10 | Yes |
| Max expiration (days) | 1,098 | Yes |
| Calculated attributes per domain | 50 | **No** |
| Event streams per domain | 1 | **No** |
| Event triggers per domain | 20 | Yes |
| Integrations per domain | 50 | Yes |
| Segment snapshots per day | 200 | Yes |
| Max total profile size | 51,200 KB | Yes |
| Max single object/profile size | 250 KB | **No** |
| Object types per domain | 100 | Yes |
| Objects per profile | 1,000 | Yes |
| Concurrent bulk export jobs | 20 | **No** |

### AI Agents (Q Connect) Quotas

| Resource | Default | Adjustable |
|---|---|---|
| Assistants | 5 | **No** |
| Knowledge bases | 10 | Yes |
| Assistant associations | 20 | **No** |
| Quick responses per KB | 1,000 | Yes |
| Content per KB | 5,000 | Yes |
| Max document size | 5 MB | Yes |
| Message templates per KB | 200 | Yes |

### Quota Adjustability Notes
- **Account level**: Adjustment applies to all instances in the account/region (e.g., API TPS)
- **Resource level**: Adjustment applies to a specific instance only
- Smaller increases can be approved in hours; larger ones take up to 3 weeks; extra-large worldwide increases can take months
- Must create instance before requesting increases
- Quotas are per-region; can raise quotas for all instances in a region
- Requires AWS CLI 2.13.20+ for resource-level quota management

### API Throttling (Default)
- Most Connect APIs: **2 TPS** rate limit, **5 TPS** burst limit
- Notable exceptions:

| API | Rate | Burst |
|---|---|---|
| `GetMetricDataV2` | 10 | 10 |
| `GetMetricData` | 5 | 8 |
| `GetCurrentMetricData` | 5 | 8 |
| `GetContactAttributes` | 10 | 15 |
| `UpdateContactAttributes` | 10 | 15 |
| `DescribeContact` | 10 | 15 |
| `StopContact` | 10 | 15 |
| `TagContact` / `UntagContact` | 20 | 25 |
| `SearchContacts` | 0.5 | 1 |
| `StartChatContact` | 5 | 8 |
| `SendChatIntegrationEvent` | 17 | 26 |

Throttling is per-account per-region (shared across all users and instances).

## Multi-Instance Management

- Multiple instances allowed per account (default 2, adjustable)
- Each instance is independent: own users, flows, queues, phone numbers
- Instances can be in different regions
- `ListInstances` — enumerate all instances in the account
- `ReplicateInstance` — replicate instance for Global Resiliency (cross-region failover)

## How Concurrent Contacts Are Counted

**Counted** toward concurrent active calls:
- Contacts handled by a flow
- Contacts waiting in queue
- Contacts handled by an agent
- Outbound calls

**Not counted**:
- Callbacks waiting in a callback queue (counted only when offered to agent)
- External transfers

If quota exceeded: contacts receive a reorder/fast-busy tone.

Monitor via CloudWatch metrics: `ConcurrentCalls`, `ConcurrentCallsPercentage`.

## Getting Started

1. Create instance in console (choose identity management — cannot change later)
2. Configure telephony options (inbound, outbound, early media, multi-party)
3. Configure data storage (S3 buckets, encryption keys)
4. Claim phone number (DID or toll-free)
5. Create queues and routing profiles
6. Create users and assign routing profiles
7. Create flows (or use defaults)
8. Associate phone number with flow
9. Test by calling the number

## Key APIs

| API | Purpose |
|---|---|
| `CreateInstance` | Create a new Connect instance |
| `DescribeInstance` | Get instance details |
| `ListInstances` | List all instances in the account |
| `DeleteInstance` | Permanently delete instance and all config |
| `UpdateInstanceAttribute` | Toggle instance features on/off |
| `DescribeInstanceAttribute` | Get current value of an instance attribute |
| `AssociateInstanceStorageConfig` | Configure S3/Kinesis storage for an instance |
| `UpdateInstanceStorageConfig` | Update existing storage configuration |
| `ListInstanceStorageConfigs` | List storage configs for an instance |
| `DisassociateInstanceStorageConfig` | Remove a storage configuration |
| `ReplicateInstance` | Replicate instance for Global Resiliency |
