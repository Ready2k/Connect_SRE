# Agent Event Streams

Agent event streams provide near-real-time agent activity data via Amazon Kinesis Data Streams. They enable external systems to track agent state, routing configuration changes, and contact lifecycle without polling the Connect API.

---

## Enabling Agent Event Streams

1. Navigate to the Connect console > **Data streaming**.
2. Under **Agent events**, enable streaming.
3. Select an existing Kinesis Data Stream.
4. Agent events are published as JSON records to the configured stream.

---

## Event Types

There are **4 event types**:

| EventType | Trigger | Frequency |
|---|---|---|
| `LOGIN` | Agent logs in to the CCP | Once per session |
| `LOGOUT` | Agent logs out of the CCP | Once per session |
| `STATE_CHANGE` | Agent status, conversation state, or configuration changes | Per change |
| `HEART_BEAT` | Periodic pulse for connected agents | Every **120 seconds** |

### STATE_CHANGE Subtypes

`STATE_CHANGE` fires for several categories of change:

- **Status change** -- Agent moves between Available, Offline, or custom statuses (e.g., Break, Lunch)
- **Conversation state change** -- Contact transitions through states (INCOMING, CONNECTED, ENDED, etc.)
- **Configuration change** -- Any of these are modified:
  - Routing profile assignment
  - Queue membership (queues in routing profile)
  - Auto-accept call setting
  - SIP address
  - Agent hierarchy group assignment
  - Language preference setting in the CCP

### HEART_BEAT Behavior

- Emitted every **120 seconds** if no other events are published during that interval
- Continues for **1 hour after logout** -- this lets consumers detect stale sessions
- Contains the same `CurrentAgentSnapshot` as the most recent `STATE_CHANGE`
- Useful as a liveness signal for dashboards and monitoring systems

---

## Data Model

### Top-Level AgentEvent

```json
{
  "AgentARN": "arn:aws:connect:us-east-1:123456789012:instance/i-id/agent/a-id",
  "AWSAccountId": "123456789012",
  "EventId": "unique-event-uuid",
  "EventTimestamp": "2026-05-25T14:30:00.000Z",
  "EventType": "STATE_CHANGE",
  "InstanceARN": "arn:aws:connect:us-east-1:123456789012:instance/i-id",
  "CurrentAgentSnapshot": { ... },
  "PreviousAgentSnapshot": { ... },
  "Version": "2019-05-25"
}
```

| Field | Type | Description |
|---|---|---|
| `AgentARN` | ARN | ARN of the agent account |
| `AWSAccountId` | String | 12-digit AWS account ID |
| `EventId` | String (UUID) | Unique identifier for this event |
| `EventTimestamp` | ISO 8601 | When the event occurred |
| `EventType` | String | `LOGIN`, `LOGOUT`, `STATE_CHANGE`, or `HEART_BEAT` |
| `InstanceARN` | ARN | ARN of the Connect instance |
| `CurrentAgentSnapshot` | AgentSnapshot | Agent state after the event |
| `PreviousAgentSnapshot` | AgentSnapshot | Agent state before the event (null for LOGIN) |
| `Version` | String | Schema version in date format (e.g., `2019-05-25`) |

### AgentSnapshot

Both `CurrentAgentSnapshot` and `PreviousAgentSnapshot` share this structure:

```json
{
  "AgentStatus": {
    "ARN": "arn:aws:connect:.../agent-status/status-id",
    "Name": "Available",
    "StartTimestamp": "2026-05-25T14:28:00.000Z",
    "Type": "ROUTABLE"
  },
  "NextAgentStatus": {
    "ARN": "arn:aws:connect:.../agent-status/status-id",
    "Name": "Break",
    "EnqueuedTimestamp": "2026-05-25T14:29:55.000Z"
  },
  "Configuration": {
    "FirstName": "Jane",
    "LastName": "Smith",
    "Username": "jsmith",
    "RoutingProfile": { ... },
    "AgentHierarchyGroups": { ... },
    "Proficiencies": [ ... ]
  },
  "Contacts": [ ... ]
}
```

### AgentStatus

| Field | Type | Description |
|---|---|---|
| `ARN` | ARN | ARN of the agent status (not the agent). |
| `Name` | String | Display name the agent manually set in the CCP (e.g., "Available", "Break", "Offline"). A value of `Error` indicates an internal Connect error. |
| `StartTimestamp` | ISO 8601 | When the agent entered this status. |
| `Type` | Enum | `ROUTABLE` (available for contacts), `CUSTOM` (user-defined like Break, Lunch -- inbound contacts not routed but outbound calls allowed), or `OFFLINE`. |

### NextAgentStatus

Present when an agent has queued a status change (e.g., selected "Break" while still on a call). The agent will transition to this status after their current contact ends.

| Field | Type | Description |
|---|---|---|
| `ARN` | ARN | ARN of the next agent status. |
| `Name` | String | Display name of the upcoming status. |
| `EnqueuedTimestamp` | ISO 8601 | When the agent selected the next status and paused routing of incoming contacts. |

### Configuration

| Field | Type | Description |
|---|---|---|
| `FirstName` | String (1-100) | Agent's first name. |
| `LastName` | String (1-100) | Agent's last name. |
| `Username` | String (1-100) | Agent's Connect user name. |
| `RoutingProfile` | RoutingProfile | Current routing profile (see below). |
| `AgentHierarchyGroups` | AgentHierarchyGroups | Agent's position in the hierarchy (see below). |
| `Proficiencies` | Proficiency[] | Language and skill proficiencies (see below). |

### RoutingProfile

```json
{
  "ARN": "arn:aws:connect:.../routing-profile/rp-id",
  "Name": "Basic Routing Profile",
  "InboundQueues": [
    {
      "ARN": "arn:aws:connect:.../queue/q-id",
      "Name": "BasicQueue",
      "Channels": ["VOICE", "CHAT"]
    }
  ],
  "DefaultOutboundQueue": {
    "ARN": "arn:aws:connect:.../queue/q-id",
    "Name": "OutboundQueue"
  },
  "Concurrency": [
    {
      "AvailableSlots": 1,
      "Channel": "VOICE",
      "MaximumSlots": 1
    },
    {
      "AvailableSlots": 3,
      "Channel": "CHAT",
      "MaximumSlots": 5
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `ARN` | ARN | Routing profile ARN. |
| `Name` | String | Routing profile name. |
| `InboundQueues` | Queue[] | Queues the agent receives contacts from. Each queue has ARN, Name, and Channels. |
| `DefaultOutboundQueue` | Queue | Queue used for outbound contacts (ARN, Name). |
| `Concurrency` | Concurrency[] | Per-channel slot configuration. |

**Concurrency fields:**

| Field | Type | Description |
|---|---|---|
| `AvailableSlots` | Integer | Remaining capacity for this channel. |
| `Channel` | String | `VOICE`, `CHAT`, or `TASK`. |
| `MaximumSlots` | Integer | Maximum concurrent contacts for this channel. |

### AgentHierarchyGroups

Up to 5 levels of grouping. Each level is a HierarchyGroup object.

| Field | Type | Description |
|---|---|---|
| `Level1` | HierarchyGroup | First level of hierarchy. |
| `Level2` | HierarchyGroup | Second level of hierarchy. |
| `Level3` | HierarchyGroup | Third level of hierarchy. |
| `Level4` | HierarchyGroup | Fourth level of hierarchy. |
| `Level5` | HierarchyGroup | Fifth level of hierarchy. |

**HierarchyGroup:**

| Field | Type | Description |
|---|---|---|
| `ARN` | ARN | ARN of the hierarchy group. |
| `Name` | String | Name of the hierarchy group. |

### Proficiency

| Field | Type | Description |
|---|---|---|
| `Name` | String (1-64) | Predefined attribute name (e.g., "Language", "Technology"). |
| `Value` | String | Attribute value (e.g., "English", "AWS Kinesis"). |
| `ProficiencyLevel` | Float | Proficiency level: `1.0`, `2.0`, `3.0`, `4.0`, or `5.0`. |

### Contacts Array

Each element in the `Contacts` array represents an active or recently ended contact:

```json
{
  "ContactId": "contact-uuid",
  "InitialContactId": "initial-contact-uuid",
  "Channel": "VOICE",
  "InitiationMethod": "INBOUND",
  "State": "CONNECTED",
  "StateStartTimestamp": "2026-05-25T14:29:00.000Z",
  "ConnectedToAgentTimestamp": "2026-05-25T14:29:05.000Z",
  "QueueTimestamp": "2026-05-25T14:28:30.000Z",
  "Queue": {
    "ARN": "arn:aws:connect:.../queue/q-id",
    "Name": "Support",
    "Channels": ["VOICE"]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `ContactId` | String (1-256) | Contact identifier. |
| `InitialContactId` | String (1-256) | Original contact identifier (for transfers). |
| `Channel` | String | `VOICE`, `CHAT`, or `TASKS`. |
| `InitiationMethod` | String | How the contact was initiated (see values below). |
| `State` | String | Current contact state (see values below). |
| `StateStartTimestamp` | ISO 8601 | When the contact entered the current state. |
| `ConnectedToAgentTimestamp` | ISO 8601 | When the contact was connected to the agent. |
| `QueueTimestamp` | ISO 8601 | When the contact was placed in queue. |
| `Queue` | Queue | Queue the contact was placed in (ARN, Name, Channels). |

**Contact State values (10 states):**

| State | Description |
|---|---|
| `INCOMING` | Contact is ringing on the agent's CCP. |
| `PENDING` | Contact is pending acceptance (chat/task). |
| `CONNECTING` | Outbound call is connecting. |
| `CONNECTED` | Agent and customer are actively connected. |
| `CONNECTED_ONHOLD` | Customer is on hold. |
| `MISSED` | Agent did not accept the contact in time. |
| `PAUSED` | Contact is paused (tasks only). |
| `REJECTED` | Agent rejected the contact. |
| `ERROR` | An error occurred during contact handling. |
| `ENDED` | Contact has ended, agent is in ACW. |

**InitiationMethod values (14 methods):**

| Method | Description |
|---|---|
| `INBOUND` | Customer-initiated voice (phone) contact. |
| `OUTBOUND` | Agent-initiated outbound call via CCP. |
| `TRANSFER` | Transferred by an agent via quick connects. |
| `CALLBACK` | Queued callback. |
| `API` | Initiated via API (StartOutboundVoiceContact, StartChatContact, etc.). |
| `WEBRTC_API` | In-app voice/video call via communication widget. |
| `QUEUE_TRANSFER` | Transferred between queues using a flow block. |
| `MONITOR` | Supervisor monitoring (silent monitor or barge). |
| `DISCONNECT` | Post-disconnect flow contact. |
| `EXTERNAL_OUTBOUND` | Agent-initiated outbound to external party. |
| `AGENT_REPLY` | Agent reply to inbound email. |
| `FLOW` | Email initiated by flow block. |
| `CAMPAIGN_PREVIEW` | Outbound campaign preview dialing mode. |

---

## Calculating ACW Duration

After-call work (ACW) time can be derived from agent event streams by measuring the time between the contact entering `ENDED` state and the next `STATE_CHANGE` event:

```javascript
// ACW = time from contact ENDED to the next state change (agent becomes Available, etc.)
const acwStart = contact.StateStartTimestamp; // when State became ENDED
const acwEnd = nextStateChangeEvent.EventTimestamp; // when agent changed status

const acwDurationMs = new Date(acwEnd) - new Date(acwStart);
```

The `ENDED` state represents the ACW period -- the agent is completing post-contact work. When the agent sets themselves back to an available status (or another status), the ACW period ends.

---

## Consumer Patterns

**Real-time agent dashboard:**
```javascript
import { KinesisClient, GetRecordsCommand, GetShardIteratorCommand } from "@aws-sdk/client-kinesis";

// Process agent events from Kinesis
// Filter by EventType to track specific agent activities
// Use CurrentAgentSnapshot.AgentStatus.Type === "ROUTABLE" to count available agents
// Use Contacts[].State === "CONNECTED" to count active contacts
```

**Detecting stale sessions:**
- If a `HEART_BEAT` is not received for an agent within 300 seconds (2.5x the 120s interval), consider the session potentially stale
- `HEART_BEAT` events continue for 1 hour after `LOGOUT`, so a missing heartbeat before logout is more concerning

**Workforce management (WFM) integration:**
- Track agent login/logout events for attendance and schedule adherence
- Monitor `STATE_CHANGE` events to calculate time spent in each agent status (Available, Break, Training, etc.)
- Use `Contacts[].State` transitions to compute handle time, hold time, and ACW

---

## Key Considerations

- **Delivery:** Near-real-time, not exactly real-time. Expect sub-second to a few seconds of latency.
- **Ordering:** Events for a single agent are ordered within a shard. Use `AgentARN` as the partition key for per-agent ordering.
- **Duplicates:** At-least-once delivery. Consumer logic should be idempotent.
- **Volume:** One event per state change per agent, plus a heartbeat every 120s per active agent. Plan shard capacity accordingly.
- **Retention:** Configure Kinesis stream retention based on your recovery needs (default 24 hours, configurable up to 365 days).
- **Backward compatibility:** New fields may be added to the data model. Build consumers to ignore unknown fields gracefully.
