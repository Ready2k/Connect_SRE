# Contact Records (CTRs)

Contact Trace Records (CTRs) are the foundational data model in Amazon Connect. Every contact generates one or more CTR segments that capture the complete lifecycle of the interaction. CTRs are delivered at least once and may be re-delivered when new information arrives (e.g., attribute updates). Use `LastUpdateTimestamp` to detect newer copies and `ContactId` for deduplication.

---

## CTR Data Model

### ContactTraceRecord Object

The top-level object for each contact segment.

| Field | Type | Description |
|---|---|---|
| `ContactId` | String (1-256) | Unique identifier for this contact. |
| `InitialContactId` | String (1-256) | The ContactId of the first contact in a chain (for transfers/callbacks). Same as ContactId if this is the original contact. |
| `PreviousContactId` | String (1-256) | The ContactId of the contact that preceded this one in a transfer chain. Null if this is the original contact. |
| `NextContactId` | String (1-256) | The ContactId of the next contact in the chain (if this contact was transferred). |
| `RelatedContactId` | String (1-256) | Links contacts that are related but not in a direct transfer chain. |
| `ContactAssociationId` | Integer | Common identifier across all contacts linked by RelatedContactId (used for email threads). |
| `Channel` | String | `VOICE`, `CHAT`, `TASK`, or `EMAIL`. |
| `InitiationMethod` | String | How the contact was initiated (see below). |
| `DisconnectReason` | String | Why the contact ended (see below). |
| `AnsweringMachineDetectionStatus` | String | AMD result for outbound campaign calls (see below). |
| `InitiationTimestamp` | ISO 8601 | When the contact was initiated. |
| `ConnectedToSystemTimestamp` | ISO 8601 | When the customer endpoint connected to Connect. For INBOUND, matches InitiationTimestamp. For OUTBOUND/CALLBACK/API, when the customer answers. |
| `ConnectedToAgentTimestamp` | ISO 8601 | When the contact was connected to an agent. Null if never connected. |
| `DisconnectTimestamp` | ISO 8601 | When the contact was disconnected. |
| `LastUpdateTimestamp` | ISO 8601 | Last update timestamp for the CTR. |
| `ScheduledTimestamp` | ISO 8601 | For tasks, the scheduled flow trigger time. |
| `LastPausedTimestamp` | ISO 8601 | When the contact was last paused. |
| `LastResumedTimestamp` | ISO 8601 | When the contact was last resumed. |
| `TransferCompletedTimestamp` | ISO 8601 | When a cold transfer was completed (agent disconnected before new agent joined). Not populated for warm transfers. |
| `TransferredToEndpoint` | Endpoint | The endpoint the contact was transferred to (if transferred out of Connect). |
| `AWSAccountId` | String | The AWS account that owns the contact. |
| `AWSContactTraceRecordFormatVersion` | String | The record format version. |
| `InstanceARN` | ARN | ARN of the Connect instance. |
| `Agent` | Agent | Agent info (if contact connected to an agent). |
| `Customer` | Customer | Customer info (capabilities). |
| `Queue` | QueueInfo | Queue info (if contact was queued). |
| `Recording` | RecordingInfo | First recording info. |
| `Recordings` | RecordingsInfo[] | All recordings (first recording appears in both Recording and Recordings). |
| `Attributes` | Map | Contact attributes (key-value pairs, 32 KB max total). |
| `SegmentAttributes` | Map | System-defined key-value pairs (channel subtype, direction, etc.). |
| `Tags` | Map | AWS-generated and user-defined tags for billing/tracking. |
| `ContactDetails` | Map | User-defined attributes for task contacts (key: 1-128, value: 0-1024). |
| `References` | Map | Links to related documents (URL, ATTACHMENT, NUMBER, STRING, DATE, EMAIL). |
| `MediaStreams` | MediaStream[] | Media streaming configuration. |
| `ContactLens` | ContactLens | Contact Lens configuration and analytics info. |
| `QualityMetrics` | QualityMetrics | Voice quality metrics (agent and customer audio quality). |
| `DisconnectDetails` | DisconnectDetails | Call disconnect troubleshooting info. |
| `CustomerVoiceActivity` | Object | Greeting timestamps for outbound AMD calls. |
| `CustomerId` | String | Customer identifier (from CRM via Lambda, or Voice ID SpeakerId). |
| `CustomerEndpoint` | Endpoint | Customer's phone number or email address. |
| `SystemEndpoint` | Endpoint | The phone number/email the customer dialed or that was used for outbound. |
| `AdditionalEmailRecipients` | String (1-256) | To and CC fields for email contacts. |
| `AgentConnectionAttempts` | Integer | Number of times Connect attempted to connect this contact with an agent. |
| `Campaign` | Campaign | Outbound campaign info. |
| `OutboundStrategy` | OutboundStrategy | Outbound campaign dialing configuration. |
| `VoiceIdResult` | VoiceIdResult | Voice ID authentication and fraud detection results (deprecated May 2026). |
| `WisdomInfo` | WisdomInfo | Connect AI agents (Amazon Q) session info. |
| `TotalPauseCount` | Integer | Total number of pauses. |
| `TotalPauseDurationInSeconds` | Integer | Total pause duration in seconds. |
| `GlobalResiliencyMetadata` | Object | Cross-region failover info (ActiveRegion, OriginRegion, TrafficDistributionGroupId). |

### Agent Object

| Field | Type | Description |
|---|---|---|
| `ARN` | ARN | Agent ARN. |
| `Username` | String (1-100) | Agent username. |
| `RoutingProfile` | RoutingProfile | Agent's routing profile (ARN and Name). |
| `HierarchyGroups` | AgentHierarchyGroups | Agent's hierarchy group at each level (Level1 through Level5). Each level has ARN and GroupName. |
| `AgentInteractionDuration` | Integer | Seconds agent was interacting with the contact (excludes hold and pause). |
| `AgentPauseDuration` | Integer | Seconds a task was paused while assigned to the agent. |
| `CustomerHoldDuration` | Integer | Seconds the customer was on hold (from customer's perspective). |
| `AgentInitiatedHoldDuration` | Integer | Seconds the agent initiated hold. In multi-party calls, hold time is attributed to the specific agent who initiated it. |
| `AfterContactWorkDuration` | Integer | Seconds the agent spent in ACW. |
| `AfterContactWorkStartTimestamp` | ISO 8601 | When ACW started. |
| `AfterContactWorkEndTimestamp` | ISO 8601 | When ACW ended. |
| `ConnectedToAgentTimestamp` | ISO 8601 | When agent connected to the contact. |
| `AcceptedByAgentTimestamp` | ISO 8601 | When the agent accepted a preview dialing mode outbound campaign contact. |
| `PreviewEndTimestamp` | ISO 8601 | When the agent finished previewing an outbound campaign contact. |
| `NumberOfHolds` | Integer | Number of times the agent put the customer on hold. |
| `LongestHoldDuration` | Integer | Duration of the longest hold in seconds. |
| `StateTransitions` | StateTransitions[] | Supervisor state transitions (SILENT_MONITOR, BARGE) with start/end timestamps. |
| `Capabilities` | Capabilities | Agent's video/screenshare capabilities. |
| `DeviceInfo` | DeviceInfo | Agent's device info (PlatformName, PlatformVersion, OperatingSystem). |

### Customer Object

| Field | Type | Description |
|---|---|---|
| `Capabilities` | Capabilities | Customer's video/screenshare capabilities. Valid values: SEND. |

### Queue Object

| Field | Type | Description |
|---|---|---|
| `ARN` | ARN | Queue ARN. |
| `Name` | String (1-256) | Queue name. |
| `EnqueueTimestamp` | ISO 8601 | When the contact was placed in queue. |
| `DequeueTimestamp` | ISO 8601 | When the contact was removed from queue (answered or abandoned). |
| `Duration` | Integer | Time in queue in seconds. |

### RecordingInfo Object (Single Recording)

| Field | Type | Description |
|---|---|---|
| `Type` | String | `AUDIO`. |
| `Status` | String | `AVAILABLE`, `DELETED`, or `NULL`. |
| `Location` | String (0-256) | S3 URI of the recording file. |
| `DeletionReason` | String | Reason if recording was deleted. |

### RecordingsInfo Object (Multiple Recordings)

| Field | Type | Description |
|---|---|---|
| `Status` | String | `AVAILABLE`, `DELETED`, or `NULL`. |
| `Location` | String (0-256) | S3 URI of the recording/transcript. |
| `DeletionReason` | String | Reason if recording was deleted. |
| `StorageType` | String | `Amazon S3` or `KINESIS_VIDEO_STREAM`. |
| `MediaStreamType` | String | `AUDIO`, `VIDEO`, or `CHAT`. |
| `ParticipantType` | String | `All`, `Manager`, `Agent`, `Customer`, `Thirdparty`, `Supervisor`, or `IVR`. |
| `StartTimestamp` | ISO 8601 | When the last leg of recording started. |
| `StopTimestamp` | ISO 8601 | When the last leg of recording stopped. |
| `FragmentStartNumber` | String | Kinesis Video Streams fragment start number. |
| `FragmentStopNumber` | String | Kinesis Video Streams fragment stop number. |

### Attributes Object

A map of key-value pairs representing contact attributes set during the contact flow or by the agent.

```json
{
  "Attributes": {
    "CustomerType": "Premium",
    "AccountNumber": "12345",
    "Language": "en-US"
  }
}
```

Maximum 32 KB total size for all attributes combined.

### SegmentAttributes Object

System-defined key-value pairs on individual contact segments:

| Field | Description |
|---|---|
| `connect:Subtype` | Channel subtype (e.g., `connect:SMS`, `connect:WebRTC`, `connect:Telephony`, `connect:Guide`). |
| `connect:Direction` | INBOUND or OUTBOUND. |
| `connect:CreatedByUser` | ARN of the user who created the contact (for agent-initiated). |
| `connect:MediaStreams` | Media streaming configuration. |

Email-specific segment attributes store email subject and SES flags.

### QualityMetrics Object

Voice call quality metrics measuring the media connection while participants are talking.

```json
{
  "QualityMetrics": {
    "Agent": {
      "Audio": {
        "QualityScore": 4.35,
        "PotentialQualityIssues": []
      }
    },
    "Customer": {
      "Audio": {
        "QualityScore": 3.10,
        "PotentialQualityIssues": ["HighPacketLoss", "HighRoundTripTime"]
      }
    }
  }
}
```

**AudioQualityMetricsInfo:**

| Field | Type | Description |
|---|---|---|
| `QualityScore` | Number (1.00-5.00) | Estimated quality score of the media connection (MOS-like). |
| `PotentialQualityIssues` | String[] | Empty array if no issues. Values: `HighPacketLoss`, `HighRoundTripTime`, `HighJitterBuffer`. |

- **Agent quality metrics**: Available for all voice calls. Measures how the agent sounded to the customer.
- **Customer quality metrics**: Available for in-app and web voice calls only. Measures how the customer sounded to the agent.

### DisconnectDetails Object

| Field | Type | Description |
|---|---|---|
| `PotentialDisconnectIssue` | String (0-128) | `AGENT_CONNECTIVITY_ISSUE`, `AGENT_DEVICE_ISSUE`, `CUSTOMER_CONNECTIVITY_ISSUE`, or `CUSTOMER_DEVICE_ISSUE`. Null if no issue detected. |

### ContactLens Object

| Field | Type | Description |
|---|---|---|
| `ConversationalAnalytics.Configuration.Enabled` | Boolean | Whether Contact Lens is enabled. |
| `ConversationalAnalytics.Configuration.ChannelConfiguration.AnalyticsModes` | String[] | Voice: `PostContact`, `RealTime`. Chat: `ContactLens`. |
| `ConversationalAnalytics.Configuration.LanguageLocale` | String | Language locale (e.g., `en-US`). |
| `ConversationalAnalytics.Configuration.RedactionConfiguration.Behavior` | String | `Enable` or `Disable`. |
| `ConversationalAnalytics.Configuration.RedactionConfiguration.Policy` | String | `None`, `RedactedOnly`, or `RedactedAndOriginal`. |
| `ConversationalAnalytics.Configuration.RedactionConfiguration.Entities` | String[] | Entity types to redact (e.g., `EMAIL`, `CREDIT_DEBIT_NUMBER`, `NAME`). |
| `ConversationalAnalytics.Configuration.RedactionConfiguration.MaskMode` | String | `PII` (replaces with `[PII]`) or `EntityType` (replaces with `[EMAIL]`, etc.). |
| `ConversationalAnalytics.Configuration.SentimentConfiguration.Behavior` | String | `Enable` or `Disable`. |

### MediaStream Object

| Field | Type | Description |
|---|---|---|
| `Type` | String | `AUDIO`, `CHAT`, or `AUTOMATED_INTERACTION`. |

### ExternalThirdParty Object

| Field | Type | Description |
|---|---|---|
| `ExternalThirdPartyInteractionDuration` | Integer | Seconds the external participant interacted with the customer. |

### Endpoint Object

| Field | Type | Description |
|---|---|---|
| `Address` | String (1-256) | Phone number in E.164 format, or email address. |
| `Type` | String | `TELEPHONE_NUMBER`, `VOIP`, `CONTACT_FLOW`, `CONNECT_PHONENUMBER_ARN`, or `EMAIL_ADDRESS`. |

### VoiceIdResult Object (Deprecated May 2026)

| Field | Type | Description |
|---|---|---|
| `GeneratedSpeakerId` | String (25) | Voice ID-generated speaker identifier. |
| `SpeakerEnrolled` | Boolean | Whether the customer was enrolled during this contact. |
| `SpeakerOptedOut` | Boolean | Whether the customer opted out during this contact. |
| `Authentication.Score` | Integer (0-100) | Voice authentication score. |
| `Authentication.ScoreThreshold` | Integer (0-100) | Minimum authentication threshold. |
| `Authentication.MinimumSpeechInSeconds` | Integer (5-10) | Seconds of speech used to authenticate. |
| `Authentication.Result` | String | `Authenticated`, `Not Authenticated`, `Not Enrolled`, `Opted Out`, `Inconclusive`, `Error`. |
| `FraudDetection.Result` | String | `High Risk`, `Low Risk`, `Inconclusive`, `Error`. |
| `FraudDetection.ScoreThreshold` | Integer (0-100) | Fraud detection threshold. |
| `FraudDetection.RiskScoreKnownFraudster` | Integer (0-100) | Known fraudster risk score. |
| `FraudDetection.RiskScoreVoiceSpoofing` | Integer | Voice spoofing risk score. |
| `FraudDetection.GeneratedFraudsterID` | String (25) | Fraudster ID if fraud type is Known Fraudster. |
| `FraudDetection.WatchlistID` | String (22) | Watchlist used for fraud detection. |

### WisdomInfo Object

| Field | Type | Description |
|---|---|---|
| `SessionArn` | ARN | ARN of the Connect AI agents session. |

### References Object

| Field | Type | Description |
|---|---|---|
| `Name` | String | Reference name. |
| `Type` | String | `URL`, `ATTACHMENT`, `NUMBER`, `STRING`, `DATE`, or `EMAIL`. |
| `Value` | String | Reference value. |
| `Status` | String | For ATTACHMENT type only: `APPROVED` or `REJECTED`. |

### ContactEvaluations Object

| Field | Type | Description |
|---|---|---|
| `FormId` | String | Unique identifier for the evaluation form. |
| `EvaluationArn` | String | ARN of the evaluation. |
| `Status` | String | `COMPLETE`, `IN_PROGRESS`, or `DELETED`. |
| `StartTimestamp` | ISO 8601 | When the evaluation was started. |
| `EndTimestamp` | ISO 8601 | When the evaluation was submitted. |
| `DeleteTimestamp` | ISO 8601 | When the evaluation was deleted. |
| `ExportLocation` | String (0-256) | S3 path where evaluation was exported. |

### ChatMetrics Object

Chat-specific metrics including contact-level and per-participant metrics.

**ContactMetrics:**

| Field | Type | Description |
|---|---|---|
| `MultiParty` | Boolean | Whether multiparty chat or supervisor barge were enabled. |
| `TotalMessages` | Integer | Total chat messages. |
| `TotalBotMessages` | Integer | Total bot and automated messages. |
| `TotalBotMessageLengthInChars` | Integer | Total characters from bot messages. |
| `ConversationCloseTimeInMillis` | Long | Time to end after last customer message. |
| `ConversationTurnCount` | Integer | Number of back-and-forth exchanges. |
| `AgentFirstResponseTimestamp` | ISO 8601 | When agent first responded. |
| `AgentFirstResponseTimeInMillis` | Long | Time for agent to respond after obtaining contact. |

**ParticipantMetrics (Agent and Customer):**

| Field | Type | Description |
|---|---|---|
| `ParticipantId` | String (1-256) | Participant identifier. |
| `ParticipantType` | String | `Agent`, `Customer`, or `Supervisor`. |
| `ConversationAbandon` | Boolean | Whether participant abandoned the conversation. |
| `MessagesSent` | Integer | Messages sent by participant. |
| `NumResponses` | Integer | Responses sent by participant. |
| `MessageLengthInChars` | Integer | Total characters sent by participant. |
| `TotalResponseTimeInMillis` | Long | Total response time. |
| `MaxResponseTimeInMillis` | Long | Maximum response time. |
| `LastMessageTimestamp` | ISO 8601 | Timestamp of last message. |

### RoutingCriteria Object

| Field | Type | Description |
|---|---|---|
| `ActivationTimestamp` | ISO 8601 | When routing criteria was activated. |
| `Index` | Integer | Routing criteria update index (only last 3 stored). |
| `Steps` | Step[] (1-5) | Ordered routing steps with criteria. |

**Step:**

| Field | Type | Description |
|---|---|---|
| `Status` | String | `EXPIRED`, `ACTIVE`, `JOINED`, `INACTIVE`, `DEACTIVATED`, or `INTERRUPTED`. |
| `Expression` | Expression | Attribute-based matching (And/Or/AttributeCondition/NotAttributeCondition). |
| `Expiry` | Expiry | `DurationInSeconds` (min 1) and `ExpiryTimestamp`. |

**AttributeCondition:**

| Field | Type | Description |
|---|---|---|
| `Name` | String (1-64) | Predefined attribute name. |
| `Value` | String (1-64) | Predefined attribute value. |
| `ComparisonOperator` | String | `NumberGreaterOrEqualTo`, `Match`, or `Range`. |
| `ProficiencyLevel` | Float | `1.0`, `2.0`, `3.0`, `4.0`, or `5.0`. |
| `MatchCriteria.AgentsCriteria.AgentIds` | String[] | Specific agent IDs to match. |

---

## Initiation Methods (13 Values)

| Value | Description |
|---|---|
| `INBOUND` | Customer-initiated contact (incoming call, chat, email). |
| `OUTBOUND` | Agent-initiated outbound contact via CCP. |
| `TRANSFER` | Contact transferred from another agent or queue via quick connects. |
| `CALLBACK` | Queued callback initiated by the system. |
| `API` | Contact initiated via StartChatContact, StartOutboundVoiceContact, StartTaskContact, or StartEmailContact API. |
| `QUEUE_TRANSFER` | Contact transferred between queues using a flow block (not agent-to-agent). |
| `EXTERNAL_OUTBOUND` | Agent-initiated outbound to an external participant via quick connect or flow block. |
| `MONITOR` | Supervisor monitoring session (silent monitor or barge). |
| `DISCONNECT` | Post-disconnect flow execution. New contact created during a disconnect flow. |
| `WEBRTC_API` | Contact initiated via the WebRTC communication widget (in-app voice/video). |
| `AGENT_REPLY` | Agent reply to an inbound email contact. |
| `FLOW` | Email initiated by the Send Message flow block. |
| `CAMPAIGN_PREVIEW` | Outbound campaign using preview dialing mode. |

---

## Disconnect Reasons

### Voice Disconnect Reasons

| Value | Description |
|---|---|
| `CUSTOMER_DISCONNECT` | Customer hung up. Cannot distinguish between poor reception and deliberate disconnect. |
| `AGENT_DISCONNECT` | Agent ended the contact. |
| `THIRD_PARTY_DISCONNECT` | Remote side of the call initiated disconnect. |
| `TELECOM_PROBLEM` | Multiple network responses indicate a problem with the destination network. |
| `TELECOM_BUSY` | Network busy signal; endpoint is currently engaged. |
| `TELECOM_NUMBER_INVALID` | Number lacks proper E.164 formatting, does not exist, or is no longer in use. |
| `TELECOM_POTENTIAL_BLOCKING` | Multiple network responses suggest the number faces blocking. |
| `TELECOM_UNANSWERED` | Multiple routes confirm the call cannot be delivered at this time. |
| `TELECOM_TIMEOUT` | Call reached 60 seconds of ringing on multiple networks without answer. |
| `TELECOM_ORIGINATOR_CANCEL` | Originating party cancelled before connection. Inbound: customer cancelled. Outbound: agent/API cancelled or unanswered after 60s. |
| `CUSTOMER_NEVER_ARRIVED` | Inbound web calling contact auto-terminated because customer did not connect. |
| `CONTACT_FLOW_DISCONNECT` | Flow terminated the contact via a disconnect/hang-up block. |
| `BARGED` | Supervisor barged and disconnected the agent from the call. |
| `OTHER` | Other/unknown reason, including API-initiated disconnects. |

### Outbound Campaign Voice Disconnect Reasons

| Value | Description |
|---|---|
| `OUTBOUND_DESTINATION_ENDPOINT_ERROR` | Destination cannot be dialed (e.g., ineligible instance). |
| `OUTBOUND_RESOURCE_ERROR` | Insufficient permissions or missing resources for outbound calls. |
| `OUTBOUND_ATTEMPT_FAILED` | Unknown error, invalid parameter, or insufficient permissions. |
| `OUTBUND_PREVIEW_DISCARDED` | Recipient removed from list; no further attempts. |
| `EXPIRED` | Not enough agents available or insufficient telecom capacity. |

### Chat Disconnect Reasons

| Value | Description |
|---|---|
| `AGENT_DISCONNECT` | Agent explicitly disconnected or rejected chat. |
| `CUSTOMER_DISCONNECT` | Customer explicitly disconnected. |
| `AGENT_NETWORK_DISCONNECT` | Agent disconnected due to network issue. |
| `CUSTOMER_CONNECTION_NOT_ESTABLISHED` | Customer started chat but never established WebSocket/streaming connection. |
| `EXPIRED` | Chat expired due to configured chat duration limit. |
| `CONTACT_FLOW_DISCONNECT` | Chat disconnected or completed by a flow. |
| `API` | StopContact API was called. |
| `BARGED` | Manager disconnected the agent from a barged-in chat. |
| `IDLE_DISCONNECT` | Disconnect due to idle participant. |
| `THIRD_PARTY_DISCONNECT` | In multi-participant chat, Agent 1 disconnected Agent 2 while contact was active. |
| `SYSTEM_ERROR` | System error caused chat session to end abnormally. |

### Task Disconnect Reasons

| Value | Description |
|---|---|
| `AGENT_COMPLETED` | Agent completed the task and disconnected before allotted time expired. |
| `AGENT_DISCONNECT` | Agent marked the task as complete. |
| `EXPIRED` | Task expired (not assigned or completed within 7 days). |
| `CONTACT_FLOW_DISCONNECT` | Task disconnected or completed by a flow. |
| `API` | StopContact API was called. |
| `OTHER` | Other reasons. |

### Email Disconnect Reasons

| Value | Description |
|---|---|
| `TRANSFERRED` | Email transferred to another queue or agent. |
| `AGENT_DISCONNECT` | Agent closed the email without responding. |
| `EXPIRED` | Email expired before being handled. |
| `DISCARDED` | Outbound email contact was discarded in draft state. |
| `CONTACT_FLOW_DISCONNECT` | Email disconnected in a flow. |
| `API` | StopContact API was called. |
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

## Contact States (10 States)

Contacts transition through the following states during their lifecycle:

| State | Description |
|---|---|
| `INCOMING` | Contact has arrived and is in the contact flow (IVR). |
| `PENDING` | Contact is waiting to be routed (in queue). |
| `CONNECTING` | Contact is being offered to an agent (ringing). |
| `CONNECTED` | Contact is connected to an agent (active conversation). |
| `CONNECTED_ONHOLD` | Contact is connected but customer is on hold. |
| `PAUSED` | Contact is paused (task channel only). |
| `MISSED` | Agent did not answer within the timeout. Contact will be re-queued. |
| `ERROR` | An error occurred during the contact. |
| `ENDED` | The contact interaction has ended but ACW may still be in progress. |
| `REJECTED` | Agent explicitly rejected the contact. |

### State Transition Flow

```
INCOMING -> PENDING -> CONNECTING -> CONNECTED -> ENDED
                                  -> CONNECTED_ONHOLD -> CONNECTED -> ENDED
                                  -> MISSED -> PENDING (re-queued)
                                  -> REJECTED -> PENDING (re-queued)
                                  -> ERROR
```

---

## Contact Chains

Contacts are linked through transfer and callback chains using three ID fields:

### Original Contact

```
ContactId: A
InitialContactId: A
PreviousContactId: null
NextContactId: B (if transferred)
```

### Transferred Contact

```
ContactId: B
InitialContactId: A (points to the original)
PreviousContactId: A (points to the contact that transferred)
NextContactId: C (if transferred again)
```

### Second Transfer

```
ContactId: C
InitialContactId: A (always points to the very first contact)
PreviousContactId: B (points to the immediate predecessor)
NextContactId: null (end of chain)
```

### Chain Rules

- `InitialContactId` always points to the **first contact** in the entire chain.
- `PreviousContactId` points to the **immediately preceding** contact.
- `NextContactId` points to the **immediately following** contact.
- All contacts in a chain share the same `InitialContactId`.
- To reconstruct a full chain, start from any contact, follow `InitialContactId` to the root, then traverse `NextContactId` forward.

---

## Conferences and Transfers Identification

### Identifying Transfers

A contact was transferred if:
- `NextContactId` is not null (this contact was the source of a transfer).
- `InitiationMethod` is `TRANSFER` or `QUEUE_TRANSFER` (this contact is the result of a transfer).
- `TransferCompletedTimestamp` is populated (cold transfer only).

### Identifying Conferences

A conference (multi-party call) is identified when:
- Multiple agent segments exist for the same `ContactId`.
- The `DisconnectReason` of the original agent segment shows `THIRD_PARTY_DISCONNECT` if they left the conference.
- Conference participants appear as additional agent records in the CTR.

### Warm vs. Cold Transfer

- **Warm (consultative) transfer** -- The original agent stays on the line while the new agent joins. Both agents appear in the CTR for a period. The original agent then disconnects. `TransferCompletedTimestamp` is NOT populated on the initial agent's contact.
- **Cold (blind) transfer** -- The original agent disconnects immediately after initiating the transfer. `TransferCompletedTimestamp` is populated when the initiating agent disconnects before the new agent joins.

---

## Queued Callbacks

Callback contacts have specific CTR behavior:

| Behavior | Description |
|---|---|
| **InitiationMethod** | Set to `CALLBACK`. |
| **ScheduledTimestamp** | The time the callback was scheduled for. |
| **InitialContactId** | Points to the original inbound contact that requested the callback. |
| **Contact flow** | The callback-specific contact flow is invoked when the callback is initiated. |
| **Retry behavior** | If the customer doesn't answer, the callback may retry based on the queue's callback configuration. Each retry creates a new CTR segment. |

---

## Identifying Abandoned Contacts

A contact is abandoned when the customer disconnected while in queue (never connected to an agent). The CTR will have:
- A `Queue` object with `EnqueueTimestamp` populated.
- No `ConnectedToAgentTimestamp` (null).
- No agent-related fields populated.

---

## Data Retention

- CTRs are retained for **24 months** in Amazon Connect from the time the contact was initiated.
- After 24 months, CTRs are no longer available via the Connect console or APIs.
- For longer retention, stream CTRs to an external store.

### Kinesis Streaming for Longer Retention

Configure a Kinesis Data Stream or Kinesis Data Firehose in the instance settings:

1. Navigate to **Data storage** in the Connect console.
2. Under **Contact trace records**, enable Kinesis streaming.
3. Select an existing Kinesis Data Stream or Firehose delivery stream.
4. CTRs are published to Kinesis in near real-time as JSON.

The Kinesis consumer (e.g., Firehose to S3, Lambda processing) stores the CTRs for your desired retention period.

---

## CTR Size and Limits

| Limit | Value |
|---|---|
| Contact attributes total size | 32 KB |
| CTR availability after contact ends | ~15 minutes |
| Maximum retention in Connect | 24 months |
| Kinesis record size | Up to 1 MB per CTR record |

---

## Accessing CTRs

| Method | Description |
|---|---|
| **Console** | Contact search page -- search and view individual CTRs. |
| **API** | `DescribeContact`, `SearchContacts`, `GetContactAttributes`. |
| **Kinesis** | Real-time streaming of CTRs as JSON records. |
| **Data lake** | Query CTRs via Athena in the analytics data lake. |
| **S3 export** | Scheduled historical reports export CTR data to S3 in CSV format. |
