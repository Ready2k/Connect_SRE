# Routing, Queues, and Contact Transfers

## Queue Types

Amazon Connect has two queue types:

### Standard Queues
Shared contact pools. Contacts enter a standard queue and any agent with that queue in their routing profile (and in Available status) can receive them.

- Used for: general inbound routing, department-level queues (Sales, Support, Billing)
- Multiple agents serve the same queue
- Priority and delay configured per routing profile
- Contacts wait in queue until an agent becomes available or a timeout fires

### Agent Queues
Auto-created for every agent. Each agent gets a dedicated queue named after their login. Contacts routed here go exclusively to that specific agent.

- Used for: callbacks to a specific agent, warm transfers, direct routing
- Cannot be deleted independently — lifecycle tied to the user
- Agent must be Available for contacts to deliver; otherwise contacts wait or timeout
- Not visible in the default queue list — accessed via `Transfer to Agent` or by referencing the agent queue ARN

### When to Use Each

| Scenario | Queue Type |
|---|---|
| General inbound support line | Standard |
| Route callback to the agent who handled original call | Agent |
| Department routing (Billing, Sales) | Standard |
| Supervisor wants to listen in on specific agent | Agent |
| Overflow routing across teams | Standard |

---

## Queue Configuration

### Creating a Queue

```
CreateQueue:
  Name: "Technical Support"
  Description: "Tier 1 technical support queue"
  HoursOfOperationId: "hours-id"        # Required — links operating hours
  MaxContacts: 100                       # Optional — cap on simultaneous contacts
  OutboundCallerConfig:
    OutboundCallerIdName: "Support"
    OutboundCallerIdNumberId: "number-id"
    OutboundFlowId: "whisper-flow-id"    # Optional — outbound whisper flow
```

### Key Properties

- **Hours of Operation**: Every queue must reference an HoO. Contacts arriving outside hours follow the `Check hours of operation` block logic in the flow.
- **Max Contacts**: Upper bound on contacts that can sit in this queue simultaneously. New contacts beyond this limit get a queue-full error in the flow. Default: no limit.
- **Outbound Caller ID**: Per-queue outbound number and display name. Agents making outbound calls from this queue show this caller ID.
- **Tags**: Key-value pairs for cost allocation and access control via tag-based policies.

---

## Routing Profiles

A routing profile defines which queues an agent serves and at what priority. Every agent has exactly one routing profile.

### Structure

```
CreateRoutingProfile:
  Name: "Tier 1 Support"
  Description: "Handles chat and voice for general support"
  DefaultOutboundQueueId: "queue-id"     # Required — used for outbound calls
  MediaConcurrencies:
    - Channel: VOICE
      Concurrency: 1                     # Always 1 for voice
    - Channel: CHAT
      Concurrency: 5                     # 1-10
    - Channel: TASK
      Concurrency: 10                    # 1-10
  QueueConfigs:
    - QueueReference:
        QueueId: "support-queue-id"
        Channel: VOICE
      Priority: 1                        # 1-99, lower = higher priority
      Delay: 0                           # Seconds before agent eligible
    - QueueReference:
        QueueId: "billing-queue-id"
        Channel: VOICE
      Priority: 2
      Delay: 30
```

### Channel Concurrency

| Channel | Min | Max | Notes |
|---|---|---|---|
| Voice | 1 | 1 | Always 1 — an agent handles one call at a time |
| Chat | 1 | 10 | Agent receives up to N concurrent chats |
| Task | 1 | 10 | Agent receives up to N concurrent tasks |

Cross-channel behavior: if an agent is on a voice call, they will not receive chats or tasks (voice blocks other channels). Chat and task can run concurrently with each other.

### Queue Priority and Delay

**Priority** (1-99): Lower number = higher priority. An agent eligible for multiple queues takes the contact from the highest-priority queue first.

**Delay** (seconds): The agent becomes eligible for this queue only after being Available for N seconds. Use delay to create overflow behavior.

#### Example: Overflow Routing

```
Routing Profile: "Sales + Overflow Support"
  Queue: Sales       → Priority: 1, Delay: 0
  Queue: Support     → Priority: 2, Delay: 60
```

Result: Agent immediately serves Sales contacts. After being Available for 60 seconds with no Sales contacts, they become eligible for Support contacts. If a Sales contact arrives while serving Support, the next available slot goes to Sales (higher priority).

#### Example: Equal Distribution

```
Routing Profile: "General Agent"
  Queue: Billing     → Priority: 1, Delay: 0
  Queue: Sales       → Priority: 1, Delay: 0
  Queue: Support     → Priority: 1, Delay: 0
```

Result: All queues have equal priority. The agent receives whichever contact has been waiting longest across all three queues (longest-idle routing within same priority).

---

## Quick Connects

Quick connects are preconfigured transfer destinations that appear in the agent's CCP transfer dialog.

### Four Types

| Type | Destination | Use Case |
|---|---|---|
| USER | Specific agent | Transfer to specialist or supervisor |
| QUEUE | Specific queue | Transfer to another department |
| EXTERNAL | External phone number | Transfer to external party |
| PHONE_NUMBER | Phone number | Transfer to a claimed Connect number |

### API Operations

```
CreateQuickConnect:
  Name: "Billing Department"
  QuickConnectConfig:
    QuickConnectType: QUEUE
    QueueConfig:
      QueueId: "billing-queue-id"
      ContactFlowId: "transfer-flow-id"   # Flow that runs on transfer

# For external transfers:
CreateQuickConnect:
  Name: "External Vendor"
  QuickConnectConfig:
    QuickConnectType: PHONE_NUMBER
    PhoneConfig:
      PhoneNumber: "+15551234567"

# Associate quick connects with a queue (makes them visible to agents serving that queue):
AssociateQueueQuickConnects:
  QueueId: "support-queue-id"
  QuickConnectIds: ["qc-id-1", "qc-id-2"]
```

Quick connects must be associated with the queue the agent is currently serving — otherwise they do not appear in the agent's transfer list.

---

## Contact Transfers

### Warm Transfer (Consult)
1. Agent places current contact on hold
2. Agent connects to the transfer destination (another agent, queue, or external number)
3. Agent consults with the destination
4. Agent completes transfer (contact moves to destination) or conferences all parties

The original contact hears hold music during consultation. The `Transfer to Phone Number` flow block controls what happens during and after the transfer.

### Cold / Blind Transfer
Agent transfers the contact immediately without consulting the destination first. The contact goes directly to the destination queue or agent.

- Faster but the destination has no context
- In the flow, use `Transfer to Queue` block for queue transfers

### Queue Transfer
Contact moves from one queue to another. Commonly used in flows:

```
Flow block: "Transfer to Queue"
  QueueId: "escalation-queue-id"
  # Contact enters the new queue and waits for an available agent
```

The contact's queue metrics (time in queue) reset when transferred to a new queue. The contact flow associated with the destination queue runs.

### Transfer Flows
A `Transfer to Agent` or `Transfer to Queue` flow type runs when a transfer occurs. Use these to:
- Play a whisper to the receiving agent ("Incoming transfer from Sales")
- Set contact attributes before the destination agent answers
- Route based on transfer metadata

---

## Hours of Operation

Hours of operation (HoO) define when a queue is "open." Used in contact flows via the `Check hours of operation` block.

### Creating Hours of Operation

```
CreateHoursOfOperation:
  Name: "Business Hours - Eastern"
  TimeZone: "America/New_York"        # IANA timezone
  Config:
    - Day: MONDAY
      StartTime: { Hours: 8, Minutes: 0 }
      EndTime: { Hours: 17, Minutes: 0 }
    - Day: TUESDAY
      StartTime: { Hours: 8, Minutes: 0 }
      EndTime: { Hours: 17, Minutes: 0 }
    # ... repeat for each day
    - Day: SATURDAY
      StartTime: { Hours: 10, Minutes: 0 }
      EndTime: { Hours: 14, Minutes: 0 }
    # Omit SUNDAY → closed
```

### Key Behaviors

- **Timezone**: Each HoO has its own timezone. DST transitions are handled automatically based on the IANA timezone.
- **Time Slices**: Each day can have multiple time slices (e.g., 8-12 and 13-17 for a lunch break closure).
- **Omitted Days**: Days not listed are treated as closed.
- **24/7 Operation**: Set every day to `00:00 - 00:00` (midnight to midnight) — but note this still respects overrides.

### Holiday and Special Event Overrides

Overrides temporarily replace the normal schedule for specific dates.

```
CreateHoursOfOperationOverride:
  HoursOfOperationId: "hoo-id"
  Name: "New Year's Day"
  Description: "Closed for holiday"
  EffectiveFrom: "2026-01-01"
  EffectiveTill: "2026-01-01"
  Config:
    - Day: WEDNESDAY
      StartTime: { Hours: 0, Minutes: 0 }
      EndTime: { Hours: 0, Minutes: 0 }   # 0-0 = closed

# Partial day override (open 10-2 only):
CreateHoursOfOperationOverride:
  HoursOfOperationId: "hoo-id"
  Name: "Holiday Eve - Reduced Hours"
  EffectiveFrom: "2026-12-24"
  EffectiveTill: "2026-12-24"
  Config:
    - Day: WEDNESDAY
      StartTime: { Hours: 10, Minutes: 0 }
      EndTime: { Hours: 14, Minutes: 0 }
```

### Related APIs

| Operation | Purpose |
|---|---|
| `CreateHoursOfOperation` | Create new HoO |
| `UpdateHoursOfOperation` | Modify time slices or timezone |
| `CreateHoursOfOperationOverride` | Add a holiday/override |
| `UpdateHoursOfOperationOverride` | Modify an existing override |
| `DeleteHoursOfOperationOverride` | Remove an override |
| `ListHoursOfOperationOverrides` | List all overrides for an HoO |

### Flow Integration

In a contact flow, the `Check hours of operation` block evaluates the current time against the HoO linked to the specified queue. It branches to `In hours` or `Out of hours`, where you typically play a closed message and disconnect, or offer a callback/voicemail.

```
Check Hours of Operation
  → In Hours: route to queue
  → Out of Hours: play "We are currently closed" → Disconnect
  → Error: play fallback message → Disconnect
```
