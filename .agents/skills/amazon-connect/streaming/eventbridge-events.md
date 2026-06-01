# EventBridge Events

Amazon Connect emits events to the **default EventBridge event bus** in your AWS account. These events enable event-driven architectures for contact center automation, monitoring, and integration with downstream services. Events are delivered on a best-effort basis and may arrive late or be duplicated.

As new features and event types are added, the data model is updated with new fields. All changes maintain backward compatibility. Build consumers to ignore unknown fields and handle new event types gracefully.

---

## Event Envelope

All Connect events follow this structure:

```json
{
  "version": "0",
  "id": "event-uuid",
  "detail-type": "Amazon Connect Contact Event",
  "source": "aws.connect",
  "account": "123456789012",
  "time": "2026-05-25T14:30:00Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:...",
    "contactArn",
    "instanceArn"
  ],
  "detail": { ... }
}
```

- **Source:** `aws.connect`
- **Detail-type:** `"Amazon Connect Contact Event"` for contact events (other detail-types for rules, evaluations, etc.)
- **Delivery:** Best effort -- events may be delayed or, in rare cases, duplicated
- **Ordering:** No ordering guarantee across events. Use timestamps for sequencing.
- **Region:** Events are emitted to the event bus in the same region as the Connect instance.

---

## Event Categories

There are **4 event categories**:

| Category | Detail-Type | Description |
|---|---|---|
| Contact events | `Amazon Connect Contact Event` | Contact lifecycle state changes (11 types). |
| Rule events | Contact Lens rule match | Contact Lens rule triggers. |
| Performance evaluation events | Evaluation event | Agent evaluation completions. |
| Screen recording events | Screen recording event | Screen recording state changes. |

---

## Contact Event Types (11 Types)

| Event Type | Description |
|---|---|
| `INITIATED` | Contact has been created (inbound call received, outbound call placed, chat started, task created, email received). |
| `CONNECTED_TO_SYSTEM` | Customer is connected to the IVR/flow system (media established). Generated for outbound calls, tasks, and chats. Includes all AnsweringMachineDetectionStatus codes. |
| `CONTACT_DATA_UPDATED` | Contact attributes, tags, routing criteria, scheduled timestamp, Contact Lens configuration, or segment attributes have been modified. |
| `QUEUED` | Contact has been placed in a queue. |
| `CONNECTED_TO_AGENT` | Contact has been routed to and accepted by an agent. |
| `DISCONNECTED` | One party has disconnected (call ended, chat closed, task disconnected). For outbound calls: dial attempt not successful, connected but not picked up, or SIT tone detected. |
| `PAUSED` | Active task contact has been paused. |
| `RESUMED` | Previously paused task contact has been resumed. |
| `COMPLETED` | Contact is fully completed (including ACW). For contacts with ACW, AfterContactWork timestamps and duration are populated. For contacts without ACW, COMPLETED is published immediately after DISCONNECT with the same data. |
| `AMD_DISABLED` | Answering machine detection has been disabled for this contact. |
| `WEBRTC_API` | Contact initiated via the WebRTC communication widget (in-app voice/video call). |

### Contact Event Lifecycle (Voice)

```
INITIATED -> CONNECTED_TO_SYSTEM -> QUEUED -> CONNECTED_TO_AGENT -> DISCONNECTED -> COMPLETED
```

Not all events occur for every contact. For example, a call answered by IVR and resolved without an agent will not have `QUEUED` or `CONNECTED_TO_AGENT`.

### COMPLETED Event Details

For contacts **with ACW**, the COMPLETED event populates:
- `AgentInfo.afterContactWorkStartTimestamp`
- `AgentInfo.afterContactWorkEndTimestamp`
- `AgentInfo.afterContactWorkDuration`

For contacts **without ACW** (no agent present, or agent did not enter ACW), COMPLETED is published immediately after DISCONNECT with the same data.

**Chat caveat:** If an agent switches status to offline without clearing the contact in CCP, the COMPLETED event might not be delivered and `AfterContactWorkEndTimestamp` may show discrepancies.

---

## Contact Event Object

The `detail` object in a contact event contains:

| Field | Type | Description |
|---|---|---|
| `contactId` | String (1-256) | Contact identifier. |
| `initialContactId` | String (1-256) | First contact in the chain. |
| `previousContactId` | String (1-256) | Preceding contact in transfer chain. |
| `relatedContactId` | String (1-256) | Related contact (not direct transfer chain). |
| `channel` | String | `VOICE`, `CHAT`, `TASK`, or `EMAIL`. |
| `instanceArn` | ARN | Connect instance ARN. |
| `initiationMethod` | String | How the contact was initiated (see below). |
| `eventType` | String | Event type (see above). |
| `disconnectReason` | String | Why the contact ended (see below). |
| `answeringMachineDetectionStatus` | String | AMD result for outbound calls (see below). |
| `updatedProperties` | String[] | Properties updated (for CONTACT_DATA_UPDATED). Values: `ScheduledTimestamp`, `UserDefinedAttributes`, `ContactLens.ConversationalAnalytics.Configuration`, `Segment Attributes`, `Tags`, `GlobalResiliencyMetadata`, `RoutingCriteria.Step.Status`. |
| `agentInfo` | AgentInfo | Agent information (see below). |
| `queueInfo` | QueueInfo | Queue information. Not included for OUTBOUND contacts. |
| `routingCriteria` | RoutingCriteria[] | Routing criteria with steps. |
| `customerVoiceActivity` | CustomerVoiceActivity | Greeting timestamps for outbound AMD calls. |
| `recordings` | RecordingsInfo[] | Recording/transcript information. |
| `contactLens` | ContactLens | Contact Lens configuration if enabled. |
| `segmentAttributes` | Map | System-defined key-value pairs (channel subtype, etc.). |
| `tags` | Map | AWS-generated and user-defined tags. |
| `customerId` | String | Customer identifier (from CRM or Voice ID). |
| `chatMetrics` | ChatMetrics | Chat-specific metrics (see below). |
| `globalResiliencyMetadata` | GlobalResiliencyMetadata | Cross-region failover info. |
| `campaign` | Campaign | Outbound campaign info. |
| `outboundStrategy` | OutboundStrategy | Outbound campaign dialing configuration. |
| `systemEndpoint` | Endpoint | System phone number/email (not populated for CALLBACK, MONITOR, QUEUE_TRANSFER). |
| `customerEndpoint` | Endpoint | Customer phone number/email. |
| `contactDetails` | Map | User-defined attributes for task contacts. |
| `contactEvaluations` | Map | Performance evaluations keyed by FormId. |
| `stateTransitions` | StateTransition[] | Supervisor state transitions (SILENT_MONITOR, BARGE). |

---

## Data Model Objects

### AgentInfo

Present in events where an agent is involved (`CONNECTED_TO_AGENT`, `DISCONNECTED`, `COMPLETED`):

```json
{
  "agentInfo": {
    "agentArn": "arn:aws:connect:.../agent/agent-id",
    "connectedToAgentTimestamp": "2026-05-25T14:29:09.000Z",
    "agentInitiatedHoldDuration": 15,
    "afterContactWorkStartTimestamp": "2026-05-25T14:35:00.000Z",
    "afterContactWorkEndTimestamp": "2026-05-25T14:37:30.000Z",
    "afterContactWorkDuration": 150,
    "acceptedByAgentTimestamp": "2026-05-25T14:28:00.000Z",
    "previewEndTimestamp": "2026-05-25T14:28:30.000Z",
    "hierarchyGroups": {
      "level1": { "arn": "arn:aws:connect:.../agent-group/group-id" },
      "level2": { "arn": "arn:aws:connect:.../agent-group/group-id" },
      "level3": { "arn": "arn:aws:connect:.../agent-group/group-id" },
      "level4": { "arn": "arn:aws:connect:.../agent-group/group-id" },
      "level5": { "arn": "arn:aws:connect:.../agent-group/group-id" }
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `agentArn` | ARN | ARN of the assigned agent. |
| `connectedToAgentTimestamp` | ISO 8601 | When agent accepted the contact. |
| `agentInitiatedHoldDuration` | Integer | Total hold duration in seconds initiated by the agent. |
| `afterContactWorkStartTimestamp` | ISO 8601 | When ACW began. |
| `afterContactWorkEndTimestamp` | ISO 8601 | When ACW ended. |
| `afterContactWorkDuration` | Integer | ACW duration in seconds. |
| `acceptedByAgentTimestamp` | ISO 8601 | When outbound campaign preview mode contact was accepted. |
| `previewEndTimestamp` | ISO 8601 | When agent finished previewing outbound campaign contact. |
| `hierarchyGroups` | Object | Agent's hierarchy (up to 5 levels, each with ARN). |

### QueueInfo

```json
{
  "queueInfo": {
    "queueArn": "arn:aws:connect:.../queue/queue-id",
    "queueType": "STANDARD",
    "enqueueTimestamp": "2026-05-25T14:28:30.000Z",
    "dequeueTimestamp": "2026-05-25T14:29:05.000Z"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `queueArn` | ARN | ARN of the queue. |
| `queueType` | String | `STANDARD` or `AGENT` (direct-to-agent queue). |
| `enqueueTimestamp` | ISO 8601 | When contact entered the queue. |
| `dequeueTimestamp` | ISO 8601 | When contact left the queue. |

### RoutingCriteria

Describes how the contact was routed, including step-based routing:

```json
{
  "routingCriteria": [{
    "activationTimestamp": "2026-05-25T14:29:04.000Z",
    "index": 0,
    "steps": [{
      "status": "JOINED",
      "expiry": {
        "durationInSeconds": 60,
        "expiryTimestamp": "2026-05-25T14:30:04.000Z"
      },
      "expression": {
        "orExpression": [{
          "attributeCondition": {
            "name": "Technology",
            "value": "AWS Kinesis",
            "comparisonOperator": "NumberGreaterOrEqualTo",
            "proficiencyLevel": 2.0
          }
        }],
        "andExpression": [{
          "attributeCondition": {
            "name": "Language",
            "value": "Spanish",
            "comparisonOperator": "NumberGreaterOrEqualTo",
            "proficiencyLevel": 2.0
          }
        }]
      }
    }]
  }]
}
```

| Field | Type | Description |
|---|---|---|
| `activationTimestamp` | ISO 8601 | When routing criteria was activated (contact transferred to queue). |
| `index` | Integer (min 0) | Update index for this routing criteria. |
| `steps` | Step[] (1-5) | Ordered routing steps with criteria. |

**Step fields:**

| Field | Type | Description |
|---|---|---|
| `status` | String | `ACTIVE`, `EXPIRED`, `JOINED`, `INACTIVE`, `DEACTIVATED`, or `INTERRUPTED`. |
| `expression` | Expression | Matching conditions (And/Or/AttributeCondition/NotAttributeCondition). |
| `expiry` | Expiry | `durationInSeconds` (min 1) and `expiryTimestamp`. |

When all steps are exhausted, the contact is offered to any agent in the queue.

**AttributeCondition fields:**

| Field | Type | Description |
|---|---|---|
| `name` | String (1-64) | Predefined attribute name. |
| `value` | String (1-64) | Attribute value. |
| `comparisonOperator` | String | `NumberGreaterOrEqualTo`, `Match`, or `Range`. |
| `proficiencyLevel` | Float | `1.0`, `2.0`, `3.0`, `4.0`, or `5.0`. |
| `matchCriteria.agentsCriteria.agentIds` | String[] | Specific agent IDs to match (for `Match` operator). |

### CustomerVoiceActivity

Tracks when the customer speaks during outbound AMD calls:

```json
{
  "customerVoiceActivity": {
    "greetingStartTimestamp": "2026-05-25T14:28:02.000Z",
    "greetingEndTimestamp": "2026-05-25T14:28:05.000Z"
  }
}
```

### Endpoint

```json
{
  "address": "+11234567890",
  "type": "TELEPHONE_NUMBER",
  "displayName": "Main Line"
}
```

| Field | Type | Description |
|---|---|---|
| `address` | String (1-256) | Phone number in E.164 format, or email address. |
| `type` | String | `TELEPHONE_NUMBER`, `VOIP`, `CONTACT_FLOW`, `CONNECT_PHONENUMBER_ARN`, or `EMAIL_ADDRESS`. |
| `displayName` | String (0-256) | Display name of the endpoint. |

### RecordingsInfo

```json
{
  "recordings": [{
    "storageType": "S3",
    "location": "s3://connect-recordings-bucket/recordings/2026/05/25/contact-id.wav",
    "mediaStreamType": "AUDIO",
    "participantType": "CUSTOMER",
    "fragmentStartNumber": "...",
    "fragmentStopNumber": "...",
    "startTimestamp": "2026-05-25T14:29:00.000Z",
    "stopTimestamp": "2026-05-25T14:35:00.000Z",
    "status": "AVAILABLE",
    "deletionReason": null
  }]
}
```

| Field | Type | Description |
|---|---|---|
| `storageType` | String | `Amazon S3` or `KINESIS_VIDEO_STREAM`. |
| `location` | String (0-256) | S3 URI or KVS location. |
| `mediaStreamType` | String | `AUDIO`, `VIDEO`, or `CHAT`. |
| `participantType` | String | `All`, `Manager`, `Agent`, `Customer`, `Thirdparty`, or `Supervisor`. |
| `startTimestamp` | ISO 8601 | Recording start time. |
| `stopTimestamp` | ISO 8601 | Recording stop time. |
| `status` | String | `AVAILABLE`, `DELETED`, or `NULL`. |
| `deletionReason` | String | Reason if deleted. |
| `fragmentStartNumber` | String | KVS fragment start. |
| `fragmentStopNumber` | String | KVS fragment stop. |

### ContactEvaluations

```json
{
  "contactEvaluations": {
    "form-id-1": {
      "evaluationArn": "arn:aws:connect:.../evaluation/eval-id",
      "status": "COMPLETE",
      "startTimestamp": "2026-05-25T14:40:00.000Z",
      "endTimestamp": "2026-05-25T14:42:00.000Z",
      "deleteTimestamp": null,
      "exportLocation": "s3://..."
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `evaluationArn` | ARN | ARN of the evaluation. |
| `status` | String | `COMPLETE`, `IN_PROGRESS`, or `DELETED`. |
| `startTimestamp` | ISO 8601 | When evaluation started. |
| `endTimestamp` | ISO 8601 | When evaluation was submitted. |
| `deleteTimestamp` | ISO 8601 | When evaluation was deleted. |
| `exportLocation` | String (0-256) | S3 export path. |

### StateTransitions (Supervisor)

```json
{
  "stateTransitions": [
    {
      "stateStartTimestamp": "2026-05-25T14:30:00.000Z",
      "stateEndTimestamp": "2026-05-25T14:32:00.000Z",
      "state": "SILENT_MONITOR"
    },
    {
      "stateStartTimestamp": "2026-05-25T14:32:00.000Z",
      "stateEndTimestamp": "2026-05-25T14:35:00.000Z",
      "state": "BARGE"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `stateStartTimestamp` | ISO 8601 | When the state started. |
| `stateEndTimestamp` | ISO 8601 | When the state ended. |
| `state` | String | `SILENT_MONITOR` or `BARGE`. |

### ChatMetrics

**ChatContactMetrics:**

| Field | Type | Description |
|---|---|---|
| `multiParty` | Boolean | Whether multiparty chat or supervisor barge were enabled. |
| `totalMessages` | Integer | Total chat messages on the contact. |
| `totalBotMessages` | Integer | Total bot and automated messages. |
| `totalBotMessageLengthInChars` | Integer | Total characters from bot messages. |
| `conversationCloseTimeInMillis` | Long | Time to end after last customer message. |
| `conversationTurnCount` | Integer | Number of back-and-forth exchanges. |
| `agentFirstResponseTimestamp` | ISO 8601 | When agent first responded. |
| `agentFirstResponseTimeInMillis` | Long | Time for agent to respond after obtaining contact. |

**ParticipantMetrics (Agent and Customer):**

| Field | Type | Description |
|---|---|---|
| `participantId` | String (1-256) | Participant identifier. |
| `participantType` | String | `Agent`, `Customer`, or `Supervisor`. |
| `conversationAbandon` | Boolean | Whether participant abandoned the conversation. |
| `messagesSent` | Integer | Messages sent. |
| `numResponses` | Integer | Responses sent. |
| `messageLengthInChars` | Integer | Total characters sent. |
| `totalResponseTimeInMillis` | Long | Total response time. |
| `maxResponseTimeInMillis` | Long | Maximum response time. |
| `lastMessageTimestamp` | ISO 8601 | Timestamp of last message. |

### GlobalResiliencyMetadata

| Field | Type | Description |
|---|---|---|
| `activeRegion` | String (0-1024) | Current AWS region where contact is being processed. |
| `originRegion` | String (0-1024) | AWS region where contact was originally created. |
| `trafficDistributionGroupId` | String (UUID) | Traffic distribution group identifier. |

### OutboundStrategy

Information about the outbound campaign dialing configuration (dialing mode, retry settings). See the Connect API reference for the full OutboundStrategy object.

---

## Timestamps

Events include multiple timestamps to track the full contact lifecycle:

| Timestamp | Description |
|---|---|
| `initiationTimestamp` | When the contact was created. For outbound campaigns, updated to when the call starts after the INITIATED event. |
| `connectedToSystemTimestamp` | When the customer endpoint connected to Connect. For INBOUND, matches initiationTimestamp. For OUTBOUND/CALLBACK/API, when the customer answers. |
| `enqueueTimestamp` | When the contact entered a queue. |
| `connectedToAgentTimestamp` | When the agent accepted the contact. |
| `disconnectTimestamp` | When disconnection occurred. In transfer scenarios, indicates when the previous contact ended. |
| `scheduledTimestamp` | For tasks only: the scheduled trigger time. |
| `greetingStartTimestamp` | For outbound AMD: beginning of customer greeting. |
| `greetingEndTimestamp` | For outbound AMD: end of customer greeting. |

All timestamps are ISO 8601 format in UTC.

---

## DisconnectReason

The `disconnectReason` field explains why a contact ended. Codes vary by channel.

### Voice Disconnect Reasons

| Code | Description |
|---|---|
| `CUSTOMER_DISCONNECT` | Customer hung up. |
| `AGENT_DISCONNECT` | Agent ended the contact. |
| `THIRD_PARTY_DISCONNECT` | Third party on a conference call disconnected. |
| `TELECOM_PROBLEM` | Telephony network issue. |
| `TELECOM_BUSY` | Network busy signal. |
| `TELECOM_NUMBER_INVALID` | Invalid or non-existent number. |
| `TELECOM_POTENTIAL_BLOCKING` | Number faces network-level blocking. |
| `TELECOM_UNANSWERED` | Call cannot be delivered via multiple routes. |
| `TELECOM_TIMEOUT` | 60 seconds of ringing with no answer. |
| `TELECOM_ORIGINATOR_CANCEL` | Originating party cancelled before connection. |
| `CUSTOMER_NEVER_ARRIVED` | Web calling contact auto-terminated (customer did not connect). |
| `CONTACT_FLOW_DISCONNECT` | Flow terminated the contact. |
| `BARGED` | Supervisor barged and ended the contact. |
| `OTHER` | Other/unknown reason. |

### Outbound Campaign Disconnect Reasons

| Code | Description |
|---|---|
| `OUTBOUND_DESTINATION_ENDPOINT_ERROR` | Destination cannot be dialed. |
| `OUTBOUND_RESOURCE_ERROR` | Insufficient permissions or resources. |
| `OUTBOUND_ATTEMPT_FAILED` | Unknown error or invalid parameter. |
| `OUTBUND_PREVIEW_DISCARDED` | Recipient removed from list. |
| `EXPIRED` | Not enough agents or telecom capacity. |
| `DISCARDED` | Agent discarded an email contact. |

### Chat Disconnect Reasons

| Code | Description |
|---|---|
| `AGENT_DISCONNECT` | Agent disconnected or rejected chat. |
| `CUSTOMER_DISCONNECT` | Customer disconnected. |
| `AGENT_NETWORK_DISCONNECT` | Agent network issue. |
| `CUSTOMER_CONNECTION_NOT_ESTABLISHED` | Customer never established WebSocket. |
| `EXPIRED` | Chat duration expired. |
| `CONTACT_FLOW_DISCONNECT` | Flow disconnected chat. |
| `API` | StopContact API called. |
| `BARGED` | Manager disconnected agent from barged chat. |
| `IDLE_DISCONNECT` | Idle participant timeout. |
| `THIRD_PARTY_DISCONNECT` | Multi-participant: one agent disconnected another. |
| `SYSTEM_ERROR` | System error ended session. |

### Task Disconnect Reasons

| Code | Description |
|---|---|
| `AGENT_COMPLETED` | Agent completed task before expiry. |
| `AGENT_DISCONNECT` | Agent marked task complete. |
| `EXPIRED` | Task expired (7-day default). |
| `CONTACT_FLOW_DISCONNECT` | Flow disconnected task. |
| `API` | StopContact API called. |
| `OTHER` | Other reasons. |

### Email Disconnect Reasons

| Code | Description |
|---|---|
| `TRANSFERRED` | Email transferred. |
| `AGENT_DISCONNECT` | Agent closed without responding. |
| `EXPIRED` | Email expired. |
| `DISCARDED` | Outbound email discarded in draft. |
| `CONTACT_FLOW_DISCONNECT` | Flow disconnected email. |
| `API` | StopContact API called. |
| `OTHER` | Other reasons. |

---

## AnsweringMachineDetectionStatus (12 Values)

For outbound calls with answering machine detection (AMD) enabled:

| Status | Description |
|---|---|
| `HUMAN_ANSWERED` | A human answered the call. |
| `VOICEMAIL_BEEP` | Voicemail detected (with beep). |
| `VOICEMAIL_NO_BEEP` | Voicemail detected (no beep). |
| `AMD_UNANSWERED` | No answer detected (kept ringing). |
| `AMD_UNRESOLVED` | Detection could not determine human or voicemail. |
| `AMD_UNRESOLVED_SILENCE` | Connected but detection observed silence. |
| `AMD_NOT_APPLICABLE` | Call disconnected before ringing; no media to detect. |
| `SIT_TONE_BUSY` | Busy SIT tone. |
| `SIT_TONE_INVALID_NUMBER` | Invalid number SIT tone. |
| `SIT_TONE_DETECTED` | Special information tone detected. |
| `FAX_MACHINE_DETECTED` | Fax machine detected. |
| `AMD_ERROR` | Error during detection. |

---

## InitiationMethod (13 Values)

| Method | Description |
|---|---|
| `INBOUND` | Customer-initiated inbound contact (voice, email). |
| `OUTBOUND` | Agent-initiated outbound call or email via CCP. |
| `TRANSFER` | Transferred from another agent or queue via quick connects. |
| `CALLBACK` | Queued callback. |
| `API` | API-initiated contact (StartOutboundVoiceContact, StartChatContact, StartTaskContact, StartEmailContact). |
| `QUEUE_TRANSFER` | Transferred between queues using a flow block. |
| `EXTERNAL_OUTBOUND` | Agent-initiated outbound to external party. |
| `MONITOR` | Supervisor monitoring (silent monitor or barge). |
| `DISCONNECT` | Post-disconnect flow execution. |
| `AGENT_REPLY` | Agent reply to inbound email. |
| `FLOW` | Email initiated by flow block. |
| `CAMPAIGN_PREVIEW` | Outbound campaign preview dialing mode. |

---

## Subscribing to Events

Create an EventBridge rule in the AWS console or via infrastructure as code:

### Match All Connect Contact Events

```json
{
  "source": ["aws.connect"],
  "detail-type": ["Amazon Connect Contact Event"]
}
```

### Match Specific Event Types

```json
{
  "source": ["aws.connect"],
  "detail-type": ["Amazon Connect Contact Event"],
  "detail": {
    "eventType": ["DISCONNECTED", "COMPLETED"]
  }
}
```

### Exclude Specific Event Types

```json
{
  "source": ["aws.connect"],
  "detail-type": ["Amazon Connect Contact Event"],
  "detail": {
    "eventType": [{
      "anything-but": ["CONTACT_DATA_UPDATED"]
    }]
  }
}
```

### Filter by Channel and Instance

```json
{
  "source": ["aws.connect"],
  "detail-type": ["Amazon Connect Contact Event"],
  "detail": {
    "eventType": ["DISCONNECTED"],
    "channel": ["VOICE"],
    "instanceArn": ["arn:aws:connect:us-east-1:123456789012:instance/abc"]
  }
}
```

### Setup Steps

1. In the Amazon EventBridge console, choose **Create rule**.
2. Assign a name, choose **Rule with an event pattern**, then **Next**.
3. Under Event source, verify **AWS events or EventBridge partner events** is selected.
4. For Sample event type, choose **AWS events** > **Amazon Connect Contact Event**.
5. For Creation method, choose **Use pattern form** > **AWS services** > **Amazon Connect** > **Amazon Connect Contact Event**.
6. Select a target (Lambda, SQS, SNS, Step Functions, CloudWatch Logs, etc.).
7. Optionally configure tags, then **Create rule**.

### Common Targets

| Target | Use Case |
|---|---|
| **Lambda** | Custom business logic on contact events. |
| **SQS** | Buffer events for async/batch processing. |
| **SNS** | Fan-out notifications to multiple subscribers. |
| **Step Functions** | Orchestrate multi-step workflows triggered by events. |
| **CloudWatch Logs** | Audit trail and analysis. |
| **Kinesis Data Streams** | Stream events for real-time analytics. |

---

## Key Considerations

- **Delivery guarantee:** Best effort. Events may arrive late or be duplicated. Design consumers to be idempotent.
- **Latency:** Events are typically delivered within seconds but can be delayed under high load.
- **Event size:** Large contacts with many state transitions can produce sizable event payloads. Monitor Lambda payload limits (6 MB synchronous, 256 KB asynchronous).
- **Filtering:** Use EventBridge content-based filtering to route only relevant events to each target, reducing Lambda invocations and cost.
- **Cross-account:** EventBridge supports cross-account event delivery if your processing infrastructure is in a different account.
- **Ordering:** No ordering guarantee across events. Use timestamps for sequencing.
- **Region:** Events are emitted to the event bus in the same region as the Connect instance.
- **Backward compatibility:** New fields and event types may be added. Build consumers to ignore unknown fields and handle new event types gracefully.
