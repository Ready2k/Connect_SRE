# Historical Metrics

Amazon Connect provides 80+ historical metrics across 20+ categories. These metrics are computed from contact records, agent activity events, conversational analytics, flow/bot interactions, AI agent sessions, evaluation data, and case records.

---

## API: GetMetricDataV2

The primary API for querying historical metrics. Replaces the legacy `GetMetricData`.

```
POST /metrics/data
```

### Request Structure

```json
{
  "ResourceArn": "arn:aws:connect:region:account:instance/instance-id",
  "StartTime": "2026-05-01T00:00:00Z",
  "EndTime": "2026-05-02T00:00:00Z",
  "Interval": {
    "TimeZone": "UTC",
    "IntervalPeriod": "DAY"
  },
  "Filters": [
    {
      "FilterKey": "QUEUE",
      "FilterValues": ["queue-id"]
    },
    {
      "FilterKey": "CHANNEL",
      "FilterValues": ["VOICE"]
    }
  ],
  "Groupings": ["QUEUE", "CHANNEL"],
  "Metrics": [
    {
      "Name": "AVG_HANDLE_TIME"
    },
    {
      "Name": "ABANDONMENT_RATE"
    }
  ]
}
```

### Interval Periods

- `FIFTEEN_MINUTES` — 15-minute intervals.
- `THIRTY_MINUTES` — 30-minute intervals.
- `HOUR` — Hourly intervals.
- `DAY` — Daily intervals.
- `WEEK` — Weekly intervals.
- `TOTAL` — Entire time range as a single interval.

### Data Availability

- Data is available approximately **15 minutes** after a contact ends.
- Maximum query range: **35 days** per request.
- Data retained: up to **24 months**.

### Legacy API: GetMetricData

The older `GetMetricData` API is still supported but has fewer metrics and groupings. Key differences:

| Feature | GetMetricData (Legacy) | GetMetricDataV2 |
|---|---|---|
| Metric identifiers | Different names (e.g., `AFTER_CONTACT_WORK_TIME`) | Updated names (e.g., `SUM_AFTER_CONTACT_WORK_TIME`) |
| Groupings | Limited | Full set including CONTACT_FLOW, CASE_TEMPLATE |
| Filters | Basic | Extended with INITIATION_METHOD, DISCONNECT_REASON, metric-level filters |
| AI metrics | Not available | Full AI agent/session/prompt/tool metrics |

---

## Category 1: Abandonment and Queue Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Abandonment Rate | `ABANDONMENT_RATE` | PERCENT | Percentage of queued contacts abandoned before agent answer. Contacts queued for callback are excluded. Formula: (Contacts abandoned / Contacts queued) x 100. |
| Contacts Queued | `CONTACTS_QUEUED` | COUNT | Total contacts that entered a queue. |
| Contacts Abandoned | `CONTACTS_ABANDONED` | COUNT | Total contacts abandoned while in queue. |
| Max Queue Wait Time | `MAX_QUEUED_TIME` | SECONDS | Maximum time any contact waited in queue. |
| Average Queue Answer Time | `AVG_QUEUE_ANSWER_TIME` | SECONDS | Average time contacts waited in queue before being answered (service level). |
| Service Level | `SERVICE_LEVEL` | PERCENT | Percentage of contacts answered within X seconds (configurable threshold). |

---

## Category 2: Agent Activity Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Agent Answer Rate | `AGENT_ANSWER_RATE` | PERCENT | Percentage of contacts routed to agent that were answered. Formula: (Contacts accepted / Total routing attempts) x 100. Available since Dec 29, 2023. |
| Agent Non-Response | `AGENT_NON_RESPONSE` | COUNT | Contacts routed to agent but not answered, including customer abandons. Legacy: `CONTACTS_MISSED`. Available since Oct 1, 2023. |
| Agent Non-Response Without Customer Abandons | `AGENT_NON_RESPONSE_WITHOUT_CUSTOMER_ABANDONS` | COUNT | Voice contacts routed to agent but not answered, excluding customer abandons. Voice only. Available since Oct 1, 2023. |
| Agent Occupancy | `AGENT_OCCUPANCY` | PERCENT | Percentage of time agent was active on contacts vs. available. |
| Agent Non-Productive Time | `SUM_NON_PRODUCTIVE_TIME_AGENT` | SECONDS | Total time in custom (non-productive) statuses. Available since Dec 29, 2023. |
| Agent Idle Time | `SUM_IDLE_TIME_AGENT` | SECONDS | Time agent wasn't handling contacts after setting status to Available, plus time contacts were in Error state. Cannot be grouped/filtered by queue. Available since Dec 29, 2023. |
| Agent On Contact Time | `SUM_CONTACT_TIME_AGENT` | SECONDS | Total time agent spent on contacts including hold time and ACW. Does NOT include custom status or Offline time. Available since Oct 1, 2023. |

---

## Category 3: Agent Connecting Time Metrics

All use the same base API identifier with different `INITIATION_METHOD` metric-level filters.

| Metric | API Name | Filter | Unit | Description |
|---|---|---|---|---|
| Agent Incoming Connecting Time | `SUM_CONNECTING_TIME_AGENT` | INITIATION_METHOD=INBOUND | SECONDS | Total ring time for inbound contacts. |
| Avg Incoming Connecting Time | `AVG_AGENT_CONNECTING_TIME` | INITIATION_METHOD=INBOUND | SECONDS | Average ring time for inbound contacts. |
| Agent Outbound Connecting Time | `SUM_CONNECTING_TIME_AGENT` | INITIATION_METHOD=OUTBOUND | SECONDS | Total connection time for outbound contacts. |
| Avg Outbound Connecting Time | `AVG_AGENT_CONNECTING_TIME` | INITIATION_METHOD=OUTBOUND | SECONDS | Average connection time for outbound contacts. |
| Agent Callback Connecting Time | `SUM_CONNECTING_TIME_AGENT` | INITIATION_METHOD=CALLBACK | SECONDS | Total connection time for callback contacts. |
| Avg Callback Connecting Time | `AVG_AGENT_CONNECTING_TIME` | INITIATION_METHOD=CALLBACK | SECONDS | Average connection time for callback contacts. |
| Agent API Connecting Time | `SUM_CONNECTING_TIME_AGENT` | INITIATION_METHOD=API | SECONDS | Total connection time for API-initiated contacts. |
| Avg API Connecting Time | `AVG_AGENT_CONNECTING_TIME` | INITIATION_METHOD=API | SECONDS | Average connection time for API-initiated contacts. |

All connecting time metrics available since Dec 29, 2023.

---

## Category 4: Agent Interaction Time Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Agent Interaction Time | `SUM_INTERACTION_TIME` | SECONDS | Total time agents spent interacting with customers. Excludes hold, ACW, and pause time. |
| Avg Agent Interaction Time | `AVG_INTERACTION_TIME` | SECONDS | Average interaction time per contact. Legacy: `INTERACTION_TIME`. |
| Agent Interaction and Hold Time | `SUM_INTERACTION_AND_HOLD_TIME` | SECONDS | Total time agent was connected including hold time. |
| Avg Interaction and Hold Time | `AVG_INTERACTION_AND_HOLD_TIME` | SECONDS | Average interaction + hold time. Legacy: `INTERACTION_AND_HOLD_TIME`. |

---

## Category 5: After Contact Work (ACW) Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| After Contact Work Time | `SUM_AFTER_CONTACT_WORK_TIME` | SECONDS | Total ACW time across all contacts. Legacy: `AFTER_CONTACT_WORK_TIME`. |
| Avg After Contact Work Time | `AVG_AFTER_CONTACT_WORK_TIME` | SECONDS | Average ACW time per contact. |

---

## Category 6: Hold Time Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Avg Customer Hold Time | `AVG_HOLD_TIME` | SECONDS | Average time customers spent on hold after agent connection. Includes transfer hold time. Does NOT apply to tasks (shows 0). |
| Avg Customer Hold Time All Contacts | `AVG_HOLD_TIME_ALL_CONTACTS` | SECONDS | Average hold time including contacts never put on hold (0 hold time contacts included in average). |
| Contacts Put on Hold | `CONTACTS_PUT_ON_HOLD` | COUNT | Number of contacts put on hold. |
| Avg Hold Count | `AVG_HOLDS` | COUNT | Average number of holds per contact. |

---

## Category 7: Contact Duration Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Avg Contact Duration | `AVG_CONTACT_DURATION` | SECONDS | Average time from initiation timestamp to disconnect timestamp. |
| Avg Active Time | `AVG_ACTIVE_TIME` | SECONDS | Average active handling time: interaction + hold + ACW. Includes time in custom status. |
| Avg Handle Time | `AVG_HANDLE_TIME` | SECONDS | Average handle time = agent interaction time + hold time + ACW time. |
| Avg Agent Pause Time | `AVG_AGENT_PAUSE_TIME` | SECONDS | Average time agent paused contact after connection. Applies only to tasks (0 for other channels). |

---

## Category 8: Contact Count Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Contacts Handled | `CONTACTS_HANDLED` | COUNT | Total contacts answered by an agent. |
| Contacts Handled Incoming | `CONTACTS_HANDLED_INCOMING` | COUNT | Inbound contacts handled. |
| Contacts Handled Outbound | `CONTACTS_HANDLED_OUTBOUND` | COUNT | Outbound contacts handled. |
| Callback Contacts Handled | `CALLBACK_CONTACTS_HANDLED` | COUNT | Callback contacts handled. |
| API Contacts | `CONTACTS_CREATED` (filter: INITIATION_METHOD=API) | COUNT | Contacts initiated via Connect API, including those not handled by agent. |
| API Contacts Handled | `CONTACTS_CREATED` (filter: INITIATION_METHOD=API) | COUNT | API-initiated contacts handled by agent. Legacy: `API_CONTACTS_HANDLED`. |
| Contacts Hold Disconnect | `CONTACTS_HOLD_DISCONNECT` | COUNT | Contacts disconnected while on hold. |

---

## Category 9: Transfer Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Contacts Transferred In | `CONTACTS_TRANSFERRED_IN` | COUNT | Contacts transferred into a queue from another queue or agent. |
| Contacts Transferred Out | `CONTACTS_TRANSFERRED_OUT` | COUNT | Contacts transferred out from a queue to another queue or agent. |
| Contacts Transferred In from Queue | `CONTACTS_TRANSFERRED_IN_FROM_QUEUE` | COUNT | Contacts transferred in from another queue. |
| Contacts Transferred Out from Queue | `CONTACTS_TRANSFERRED_OUT_FROM_QUEUE` | COUNT | Contacts transferred out to another queue. |
| Contacts Transferred In by Agent | `CONTACTS_TRANSFERRED_IN_BY_AGENT` | COUNT | Contacts transferred in by a specific agent. |
| Contacts Transferred Out by Agent | `CONTACTS_TRANSFERRED_OUT_BY_AGENT` | COUNT | Contacts transferred out by a specific agent. |

---

## Category 10: Conversational Analytics Metrics (Contact Lens)

These metrics require Contact Lens to be enabled.

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Agent Talk Time Percent | `PERCENT_TALK_TIME_AGENT` | PERCENT | Talk time by agent as percent of total conversation duration. Voice only. |
| Avg Agent Talk Time | `AVG_TALK_TIME_AGENT` | SECONDS | Average time spent talking by agent. |
| Customer Talk Time Percent | `PERCENT_TALK_TIME_CUSTOMER` | PERCENT | Talk time by customer as percent of total conversation duration. |
| Avg Customer Talk Time | `AVG_TALK_TIME_CUSTOMER` | SECONDS | Average time spent talking by customer. |
| Non-Talk Time Percent | `AVG_NON_TALK_TIME_PERCENT` | PERCENT | Percentage of conversation with silence. |
| Avg Agent Greeting Time | `AVG_GREETING_TIME_AGENT` | SECONDS | Average first response time of agents on chat. |
| Avg Agent Interruptions | `AVG_INTERRUPTIONS_AGENT` | COUNT | Average number of times agent interrupted the customer. |
| Avg Agent Interruption Time | `AVG_INTERRUPTION_TIME_AGENT` | SECONDS | Average total agent interruption time while talking. |
| Avg Conversation Duration | `AVG_CONVERSATION_DURATION` | SECONDS | Average duration of actual conversation (excludes hold, IVR). |
| Avg Customer Sentiment | `AVG_CUSTOMER_SENTIMENT` | SCORE | Average customer sentiment score (-5 to +5). |
| Avg Agent Sentiment | `AVG_AGENT_SENTIMENT` | SCORE | Average agent sentiment score (-5 to +5). |

---

## Category 11: Chat Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Avg Contact First Response Wait Time | `AVG_CONTACT_FIRST_RESPONSE_TIME_AGENT` | SECONDS | Average time from chat enqueue to first agent reply. CHAT only. |
| Avg Agent First Response Time | `AVG_FIRST_RESPONSE_TIME_AGENT` | SECONDS | Average time for agent to respond after obtaining chat contact. CHAT only. |
| Avg Agent Message Length | `AVG_MESSAGE_LENGTH_AGENT` | DOUBLE | Average length (characters) of messages sent by agents. CHAT only. |
| Avg Agent Messages | `AVG_MESSAGES_AGENT` | DOUBLE | Average number of messages sent by agent. CHAT only. |
| Avg Agent Response Time | `AVG_RESPONSE_TIME_AGENT` | SECONDS | Average agent response time in chat. Includes queue wait time. CHAT only. |
| Avg Customer Message Length | `AVG_MESSAGE_LENGTH_CUSTOMER` | DOUBLE | Average length (characters) of messages sent by customers. CHAT only. |
| Avg Customer Messages | `AVG_MESSAGES_CUSTOMER` | DOUBLE | Average number of messages sent by customer. CHAT only. |
| Avg Conversation Close Time | `AVG_CONVERSATION_CLOSE_TIME` | SECONDS | Average time from last customer message to disconnect. CHAT only. |
| Avg Bot Messages | `AVG_MESSAGES_BOT` | DOUBLE | Average number of messages sent by bots. CHAT only. |

---

## Category 12: Flow and Bot Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Avg Bot Conversation Time | `AVG_BOT_CONVERSATION_TIME` | SECONDS | Average duration of completed bot conversations. Can filter by `BOT_CONVERSATION_OUTCOME_TYPE`. Available since Dec 2, 2024. |
| Avg Bot Conversation Turns | `AVG_BOT_CONVERSATION_TURNS` | DOUBLE | Average number of turns in bot conversation (1 turn = request + response). Can filter by `BOT_CONVERSATION_OUTCOME_TYPE`. Available since Dec 2, 2024. |
| Avg Flow Time | `AVG_FLOW_TIME` | SECONDS | Average time contacts spent in contact flows (IVR). |
| Contacts Flow Out | `CONTACTS_FLOW_OUT` | COUNT | Contacts that exited a flow without being queued or handled. |

---

## Category 13: AI Agent Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Active AI Agents | `ACTIVE_AI_AGENTS` | COUNT | Total unique AI Agents by Name+Version combination. |
| AI Agent Invocations | `AI_AGENT_INVOCATIONS` | COUNT | Total count of AI Agent invocations across all agents per instance. |
| AI Agent Invocation Success | `AI_AGENT_INVOCATION_SUCCESS` | COUNT | Invocations that executed successfully without technical failures. |
| AI Agent Invocation Success Rate | `AI_AGENT_INVOCATION_SUCCESS_RATE` | PERCENT | Percentage of successful invocations. |
| AI Agent Response Helpful | `AI_AGENT_RESPONSE_HELPFUL` | COUNT | AI responses rated helpful (thumbs-up). Updates every 6 hours. |
| AI Agent Response Not Helpful | `AI_AGENT_RESPONSE_NOT_HELPFUL` | COUNT | AI responses rated not helpful (thumbs-down). Updates every 6 hours. |
| Avg AI Agent Conversation Turns | `AVG_AI_AGENT_CONVERSATION_TURNS` | DOUBLE | Average turns AI Agents took to reach an outcome. |

---

## Category 14: AI Session Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| AI Handoffs | `AI_HANDOFFS` | COUNT | Contacts handled by AI that escalated to human agents. |
| AI Handoff Rate | `AI_HANDOFF_RATE` | PERCENT | Percentage of AI contacts that escalated. Formula: (AI handoffs / AI involved contacts) x 100. |
| AI Involved Contacts | `AI_INVOLVED_CONTACTS` | COUNT | Contacts where AI Agents were involved (self-service or assisting human agents). |
| AI Response Completion Rate | `AI_RESPONSE_COMPLETION_RATE` | PERCENT | Percentage of AI sessions that successfully responded to customer requests. |
| Avg AI Conversation Turns | `AVG_AI_CONVERSATION_TURNS` | DOUBLE | Average conversation turns across all AI involved contacts. |
| Completeness Score | `COMPLETENESS_SCORE` | DOUBLE (0-1) | Proportion of sessions where AI fully addressed all parts of customer requests. Updates every 24 hours. |
| Faithfulness Score | `FAITHFULNESS_SCORE` | DOUBLE (0-1) | Proportion of sessions where AI responses remained faithful to conversational context. Updates every 24 hours. |
| Goal Success Rate | `GOAL_SUCCESS_RATE` | DOUBLE (0-1) | Proportion of sessions where AI successfully resolved customer issues. Updates every 24 hours. |
| Proactive Intents Detected | `PROACTIVE_INTENTS_DETECTED` | COUNT | Proactive intents (customer queries) detected during AI sessions. |
| Proactive Intents Engaged | `PROACTIVE_INTENTS_ENGAGED` | COUNT | Proactive intents clicked/engaged by human agents. |
| Proactive Intents Answered | `PROACTIVE_INTENTS_ANSWERED` | COUNT | Proactive intents successfully answered by AI. |
| Proactive Intent Engagement Rate | `PROACTIVE_INTENT_ENGAGEMENT_RATE` | PERCENT | Percentage of detected intents engaged by agents. |
| Proactive Intent Response Rate | `PROACTIVE_INTENT_RESPONSE_RATE` | PERCENT | Percentage of engaged intents answered by AI. |

---

## Category 15: AI Prompt Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| AI Prompt Invocations | `AI_PROMPT_INVOCATIONS` | COUNT | Total AI prompt invocations. |
| AI Prompt Invocation Success | `AI_PROMPT_INVOCATION_SUCCESS` | COUNT | Successful AI prompt invocations. |
| AI Prompt Invocation Success Rate | `AI_PROMPT_INVOCATION_SUCCESS_RATE` | PERCENT | Percentage of successful prompt invocations. |
| Avg AI Prompt Invocation Latency | `AVG_AI_PROMPT_INVOCATION_LATENCY` | MILLISECONDS | Average latency of AI prompt responses. |

---

## Category 16: AI Tool Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| AI Tool Invocations | `AI_TOOL_INVOCATIONS` | COUNT | Total AI tool invocations. |
| AI Tool Invocation Success | `AI_TOOL_INVOCATION_SUCCESS` | COUNT | Successful AI tool invocations. |
| AI Tool Invocation Success Rate | `AI_TOOL_INVOCATION_SUCCESS_RATE` | PERCENT | Percentage of successful tool invocations. |
| AI Tool Parameter Accuracy | `AI_TOOL_PARAMETER_ACCURACY` | DOUBLE (0-1) | Rate of invocations where AI provided correct parameters. Updates every 24 hours. |
| AI Tool Selection Accuracy | `AI_TOOL_SELECTION_ACCURACY` | DOUBLE (0-1) | Rate of correct tool selections by AI. Updates every 24 hours. |
| AI Tool Use Accuracy | `AI_TOOL_UTILIZATION_ACCURACY` | DOUBLE (0-1) | Overall rate of correct tool use (selection + parameters). Updates every 24 hours. |
| Avg AI Tool Invocation Latency | `AVG_AI_TOOL_INVOCATION_LATENCY` | MILLISECONDS | Average latency of AI tool invocations. |

---

## Category 17: AI Knowledge Base Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Knowledge Content References | `KNOWLEDGE_CONTENT_REFERENCES` | COUNT | Count of knowledge content articles referenced by AI Agents. |

---

## Category 18: Case Metrics

Metrics from Amazon Connect Cases.

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Avg Case Resolution Time | `AVG_CASE_RESOLUTION_TIME` | SECONDS | Average time from case creation to resolution. |
| Avg Contacts Per Case | `AVG_CASE_RELATED_CONTACTS` | COUNT | Average number of contacts associated with each case. |
| Cases Created | `CASES_CREATED` | COUNT | Number of cases created in the period. |
| Cases Resolved | `CASES_RESOLVED` | COUNT | Number of cases resolved in the period. |

---

## Category 19: Evaluation Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Automatic Fails Percent | `AUTOMATIC_FAILS_PERCENT` | PERCENT | Percentage of evaluations where the agent automatically failed due to a critical section. Excludes calibration evaluations. Automatic fail cascades up (question -> section -> form). Requires at least one filter: queues, routing profiles, agents, or hierarchy groups. Available since Jan 10, 2025. |
| Average Evaluation Score | `AVG_EVALUATION_SCORE` | PERCENT | Average evaluation score across all completed evaluations. |

---

## Category 20: Schedule Adherence Metrics

| Metric | API Name | Unit | Description |
|---|---|---|---|
| Adherence | `AGENT_SCHEDULE_ADHERENCE` | PERCENT | Percentage of time agent correctly follows their schedule. When schedule changes, adherence is re-calculated up to 30 days in the past. Available in regions with Forecasting, Capacity Planning, and Scheduling. |
| Adherent Time | `AGENT_ADHERENT_TIME` | SECONDS | Total time agent adhered to their schedule. |

---

## Groupings

Historical metrics can be grouped by:

| Grouping | Description |
|---|---|
| `QUEUE` | Results per queue. |
| `CHANNEL` | Results per channel (VOICE, CHAT, TASK, EMAIL). |
| `AGENT` | Results per individual agent. |
| `ROUTING_PROFILE` | Results per routing profile. |
| `AGENT_HIERARCHY_LEVEL_ONE` through `LEVEL_FIVE` | Results per agent hierarchy group at each level. |
| `FEATURE` | Results per feature (e.g., Contact Lens). |
| `CONTACT_FLOW` | Results per contact flow. |
| `CASE_TEMPLATE` | Results per case template. |

---

## Filters

| Filter Key | Values |
|---|---|
| `QUEUE` | Queue IDs |
| `CHANNEL` | VOICE, CHAT, TASK, EMAIL |
| `ROUTING_PROFILE` | Routing profile IDs |
| `AGENT` | Agent IDs |
| `AGENT_HIERARCHY_LEVEL_ONE` through `FIVE` | Hierarchy group IDs |
| `FEATURE` | VOICE_ANALYTICS (Contact Lens) |
| `INITIATION_METHOD` | INBOUND, OUTBOUND, TRANSFER, CALLBACK, API, QUEUE_TRANSFER, EXTERNAL_OUTBOUND |
| `DISCONNECT_REASON` | CUSTOMER_DISCONNECT, AGENT_DISCONNECT, THIRD_PARTY_DISCONNECT, TELECOM_PROBLEM, CONTACT_FLOW_DISCONNECT, OTHER, EXPIRED |
| `CONTACT_FLOW_TYPE` | Various flow types |

### Metric-Level Filters

Some metrics support additional metric-level filters:

| Filter | Used With | Values |
|---|---|---|
| `INITIATION_METHOD` | Connecting time metrics | API, CALLBACK, INBOUND, OUTBOUND |
| `BOT_CONVERSATION_OUTCOME_TYPE` | Bot metrics | Various bot conversation outcomes |

---

## Statistic Types

Each metric can be requested with different statistics:

| Statistic | Description |
|---|---|
| `SUM` | Total across all contacts in the period. Used for time accumulation metrics. |
| `AVG` | Average across all contacts in the period. Used for percentage and average metrics. |
| `MIN` | Minimum value in the period. |
| `MAX` | Maximum value in the period. |

Not all statistics apply to all metrics. COUNT metrics typically use SUM. Duration metrics support all four.

---

## Scheduled Reports

Historical metrics can be configured as scheduled reports:
- Reports can be generated on a recurring schedule (daily, weekly).
- Output delivered to S3 or available in the Connect console.
- CSV exports use display names (e.g., "Contact missed" instead of `AGENT_NON_RESPONSE`).

---

## Data Availability Timeline

| Date | Metrics Added |
|---|---|
| Oct 1, 2023 | Agent on contact time, Agent non-response, Agent non-response without customer abandons |
| Dec 29, 2023 | Agent connecting times, Agent answer rate, Agent idle time, Agent non-productive time |
| Dec 2, 2024 | Bot conversation time, Bot conversation turns |
| Jan 10, 2025 | Automatic fails percent |

---

## Related Metric Documentation

The following additional metric categories are documented separately:
- Custom metric primitives
- Connect Cases metrics
- Connect bot metrics and analytics
- Conversational analytics metrics (Contact Lens)
- Evaluation metrics
- Outbound campaign metrics
- Schedule Adherence metrics

---

## Common Patterns

### Daily Queue Performance Report

Query `CONTACTS_HANDLED`, `CONTACTS_ABANDONED`, `AVG_QUEUE_ANSWER_TIME`, `SERVICE_LEVEL`, `AVG_HANDLE_TIME` grouped by `QUEUE` with `DAY` interval.

### Agent Scorecard

Query `AGENT_ANSWER_RATE`, `AVG_HANDLE_TIME`, `AVG_AFTER_CONTACT_WORK_TIME`, `AGENT_OCCUPANCY`, `CONTACTS_HANDLED` grouped by `AGENT` with `DAY` interval.

### Trend Analysis

Query key metrics with `FIFTEEN_MINUTES` or `HOUR` interval over multiple days to identify peak hours and staffing gaps.

### AI Agent Performance Dashboard

Query `AI_AGENT_INVOCATIONS`, `AI_AGENT_INVOCATION_SUCCESS_RATE`, `AI_HANDOFF_RATE`, `GOAL_SUCCESS_RATE`, `COMPLETENESS_SCORE`, `FAITHFULNESS_SCORE` to assess AI agent effectiveness.
