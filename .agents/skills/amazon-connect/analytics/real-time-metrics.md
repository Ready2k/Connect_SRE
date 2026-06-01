# Real-Time Metrics

Real-time metrics in Amazon Connect provide a live view of contact center operations. They reflect the current state of agents, queues, and routing profiles and update continuously.

---

## API: GetCurrentMetricData

Returns current metric data for the specified filters (queues, channels, routing profiles).

```
POST /metrics/current/{InstanceId}
```

### Request Structure

```json
{
  "Filters": {
    "Queues": ["queue-id-1", "queue-id-2"],
    "Channels": ["VOICE", "CHAT"],
    "RoutingProfiles": ["rp-id-1"]
  },
  "Groupings": ["QUEUE", "CHANNEL"],
  "CurrentMetrics": [
    {
      "Name": "AGENTS_AVAILABLE",
      "Unit": "COUNT"
    }
  ],
  "MaxResults": 100,
  "NextToken": "..."
}
```

### Groupings

- `QUEUE` — Group results by queue.
- `CHANNEL` — Group results by channel (VOICE, CHAT, TASK, EMAIL).
- `ROUTING_PROFILE` — Group results by routing profile.
- `INSTANCE` — Aggregate across the instance.

### Throttling

- Default: **5 TPS** for `GetCurrentMetricData`.

---

## API: GetCurrentUserData

Returns real-time user data (agent-level detail) for the specified filters.

```
POST /metrics/userdata/{InstanceId}
```

Provides per-agent detail including current status, active contacts, routing profile, and hierarchy groups. Useful for building agent roster views.

---

## Agent Status Metrics

| Metric Name | API Identifier | Unit | Description |
|---|---|---|---|
| Available | `AGENTS_AVAILABLE` | COUNT | Agents who can take inbound contacts. Agent must manually set status to Available in CCP. An agent becomes unavailable when: status set to custom status, has at least one ongoing contact, or has contact in missed/error state. Different from Availability (slots) metric. |
| On Contact | `AGENTS_ON_CONTACT` | COUNT | Agents currently handling at least one contact. Contact states included: Connected, On Hold, In ACW, Paused, Outbound ring. Agent handling multiple concurrent contacts still counts as ONE. Legacy identifier: `AGENTS_ON_CALL` (still supported). |
| After Contact Work (ACW) | `AGENTS_AFTER_CONTACT_WORK` | COUNT | Counts **contacts** (not agents) in AfterContactWork state. Despite the API name suggesting agent count, this actually counts contacts in ACW state. |
| Non-Productive (NPT) | `AGENTS_NON_PRODUCTIVE` | COUNT | Agents with CCP status set to a custom status (any status other than Available or Offline). Agents CAN handle contacts while in NPT state (e.g., outbound call while on break). Agents can be counted as both "On contact" AND "NPT" simultaneously. No new inbound contacts are routed to NPT agents. |
| Error | `AGENTS_ERROR` | COUNT | Agents in Error state. Agents enter this state when they: miss a call, reject a chat/task, or experience a connection failure. |
| Online | `AGENTS_ONLINE` | COUNT | Agents who are not in Offline status. |
| Staffed | `AGENTS_STAFFED` | COUNT | Agents who are online or in ACW. |
| Agents Count | N/A (not available via API) | COUNT | Total agents logged into CCP. Agent is "online" when CCP status is Routable or a custom status. Available on Queue Performance Dashboard only. |

---

## Slot Metrics

| Metric Name | API Identifier | Unit | Description |
|---|---|---|---|
| Active Slots | `SLOTS_ACTIVE` | COUNT | Contact slots currently occupied across all agents. A slot is active when it contains a contact that is Connected, On Hold, In ACW, Paused, or in Outbound ring state. Use for monitoring concurrent contact handling capacity. |
| Available Slots (Availability) | `SLOTS_AVAILABLE` | COUNT | Contact slots available for routing new contacts. Based on agent routing profile configuration (e.g., 1 voice OR 3 chats). A slot is available when: agent is in Available status, slot is not handling a contact, agent's routing profile allows that channel, and agent is not at concurrent contact limit. Slot becomes unavailable when: contact is Connected/ACW/Ringing/Missed/Error/On Hold, agent is in custom status, or agent can't take contacts from that channel per routing profile. |

### Slot Example

Agent routing profile allows 1 voice contact OR 3 chat contacts. Agent currently handling 1 chat = 2 available slots remaining for chat.

---

## Queue Metrics

| Metric Name | API Identifier | Unit | Description |
|---|---|---|---|
| Contacts in Queue | `CONTACTS_IN_QUEUE` | COUNT | Number of contacts currently waiting in queue. |
| Oldest Contact in Queue | `OLDEST_CONTACT_AGE` | SECONDS | Wait time of the oldest contact currently in queue. |
| Contacts Scheduled | `CONTACTS_SCHEDULED` | COUNT | Number of contacts in queue that are scheduled callbacks. |

---

## Abandonment

| Metric Name | API Identifier | Unit | Description |
|---|---|---|---|
| Abandonment Rate | `ABANDONMENT_RATE` | PERCENT | Percentage of queued contacts that disconnected before being answered. Contacts queued for callback are excluded. Formula: `(Contacts abandoned / Contacts queued) * 100.0`. Available in both real-time and historical reports. |

---

## AI Agent Metrics

| Metric Name | API Identifier | Unit | Description |
|---|---|---|---|
| Active AI Agents | `ACTIVE_AI_AGENTS` | COUNT | Total number of unique AI Agents, identified by unique combination of Name and Version. |

---

## Agent Activity Indicator

The agent activity indicator reflects the agent's current state with a priority-based logic. When an agent has multiple concurrent activities, the highest-priority state is displayed.

### Priority Order (Highest to Lowest)

| Priority | State | Description |
|---|---|---|
| 1 | **Error** | Agent encountered a system error or failed to accept a contact. |
| 2 | **Missed** | Agent was offered a contact but did not answer within the timeout. |
| 3 | **Rejected** | Agent explicitly rejected an offered contact. |
| 4 | **On Contact** | Agent is actively connected (Connected, On Hold, Paused, or Outbound ring). |
| 5 | **After Contact Work** | Agent is in ACW for a recently completed contact. |
| 6 | **Incoming** | Agent has a contact being offered/ringing (Incoming or Inbound Callback) but has not yet accepted. |
| 7 | **Custom Status** | Agent is in a custom agent status (break, lunch, training, etc.). |
| 8 | **Available** | Agent is available for new contacts. |
| 9 | **Offline** | Agent is logged in but set to Offline status. Agent disappears from real-time metrics page 5-10 minutes after going offline. |

### Multi-Channel Behavior

An agent handling concurrent contacts (e.g., 2 chats + 1 task) shows the highest-priority state across all channels. If one chat is ringing (Incoming) while the agent is connected on another chat (On Contact), the indicator shows **On Contact** because priority 4 > priority 6.

### Manager Monitor

When a manager uses the Manager Monitor feature, the manager's Agent Activity shows **Monitoring**. The monitored agent still shows **On Contact**.

---

## Refresh Behavior

- Real-time metrics in the console refresh approximately every **15 seconds**.
- API calls to `GetCurrentMetricData` return point-in-time snapshots.
- There is no push/streaming mechanism for real-time metrics; **polling is required**.
- API throttling: default **5 TPS** for `GetCurrentMetricData`.

---

## Filters

Real-time metrics support filtering by:

| Filter | Description |
|---|---|
| **Queues** | One or more queue IDs. |
| **Channels** | VOICE, CHAT, TASK, EMAIL. |
| **Routing Profiles** | One or more routing profile IDs. |
| **Agent Hierarchy Groups** | Filter by agent hierarchy group. |

---

## Console Views

### Queue Dashboard

Shows per-queue real-time metrics including contacts in queue, agents available, agents on contact, oldest contact age, and service level. Supports drill-down into individual queues for detailed agent-level data.

### Agent Activity

Shows each agent's current status, duration in status, active contacts, and the agent activity indicator with the priority logic described above. Agents in Offline status disappear from this view after 5-10 minutes.

### Routing Profile

Aggregates real-time metrics by routing profile to show capacity utilization across routing profiles.

### Queue Performance Dashboard

Includes an Agent Status Drill-Down showing Agents Count (total logged-in agents). This metric is only available in the dashboard, not via API.

---

## Agent Event Stream

For event-driven real-time agent state tracking (rather than polling), use the Amazon Connect Agent Event Stream. This publishes agent state changes to a Kinesis stream in near real-time.

Events include:
- Agent login/logout
- Status changes (Available, Offline, custom statuses)
- Contact state transitions (connecting, connected, ACW, ended)

This is the recommended approach for building custom real-time dashboards that need sub-second latency.

---

## Complete Real-Time Metrics Reference

| Metric Name | API Identifier | Unit | Category |
|---|---|---|---|
| Available | `AGENTS_AVAILABLE` | COUNT | Agent |
| On Contact | `AGENTS_ON_CONTACT` | COUNT | Agent |
| After Contact Work | `AGENTS_AFTER_CONTACT_WORK` | COUNT | Agent |
| Non-Productive | `AGENTS_NON_PRODUCTIVE` | COUNT | Agent |
| Error | `AGENTS_ERROR` | COUNT | Agent |
| Online | `AGENTS_ONLINE` | COUNT | Agent |
| Staffed | `AGENTS_STAFFED` | COUNT | Agent |
| Active Slots | `SLOTS_ACTIVE` | COUNT | Slot |
| Available Slots | `SLOTS_AVAILABLE` | COUNT | Slot |
| Contacts in Queue | `CONTACTS_IN_QUEUE` | COUNT | Queue |
| Oldest Contact Age | `OLDEST_CONTACT_AGE` | SECONDS | Queue |
| Contacts Scheduled | `CONTACTS_SCHEDULED` | COUNT | Queue |
| Abandonment Rate | `ABANDONMENT_RATE` | PERCENT | Contact |
| Active AI Agents | `ACTIVE_AI_AGENTS` | COUNT | AI Agent |

---

## Common Patterns

### Real-Time Wallboard

Poll `GetCurrentMetricData` every 15-30 seconds with grouping by QUEUE and CHANNEL. Display:
- Contacts in queue per queue
- Agents available vs. agents on contact
- Oldest contact age (highlight if > SLA threshold)
- Service level

### Agent Roster

Use the Agent Event Stream for live agent status, or poll `GetCurrentMetricData` with `AGENTS_AVAILABLE`, `AGENTS_ON_CONTACT`, `AGENTS_NON_PRODUCTIVE`, `AGENTS_AFTER_CONTACT_WORK`, `AGENTS_ERROR` grouped by ROUTING_PROFILE.

### Capacity Planning Alert

Monitor `SLOTS_AVAILABLE`. When available slots approach zero for a queue/channel combination, trigger an alert via CloudWatch or EventBridge.

### Real-Time Abandonment Tracking

For real-time abandonment tracking, use the combination of Contacts in Queue changes and the agent event stream, or reference the historical metric `ABANDONMENT_RATE` in `GetMetricDataV2` with a short time window.
