# Dashboards and Reports

Amazon Connect provides built-in dashboards, configurable reports, custom metric primitives, and granular access controls for operational visibility.

---

## Built-In Dashboards

Connect dashboards show real-time and historical metrics. Real-time dashboards refresh every 15 seconds (timeseries widgets every 15 minutes). Embedded agent workspace dashboards refresh every 2 minutes. Historical data is available up to 3 months in the past.

### Conversational Analytics Dashboard

Powered by Contact Lens. Displays:
- Sentiment trends over time
- Category distribution
- Theme detection results
- Talk time breakdowns (agent, customer, non-talk)
- Key highlights aggregation
- PII detection counts
- Interruption metrics

### Queue and Agent Performance Dashboard

Combined real-time and historical queue and agent metrics:
- Contacts in queue
- Service level trending
- Average speed of answer
- Abandonment rate
- Contacts handled vs. queued
- Per-agent occupancy, handle time trends, answer rate, ACW duration
- Contacts handled by channel
- Adherence (if scheduling is enabled)

### Agent Performance Evaluations Dashboard

Evaluation and quality management metrics:
- Evaluation scores by agent, queue, form
- Automated vs. manual evaluation counts
- Score distribution
- Coaching plan status

### AI Agent Performance Dashboard

Metrics for AI-powered autonomous agents:
- AI agent invocation counts and success rate
- Handoff rate to human agents
- Completeness and faithfulness scores
- Goal success rate
- Customer satisfaction correlation
- Response helpfulness ratings (thumbs up/down)
- Average conversation turns per invocation

### Flows and Conversational Bot Performance Dashboard

Flow and bot execution metrics:
- Flow outcomes
- Flow duration
- Bot conversation counts
- Bot intent detection and slot fill rates

### Outbound Campaigns Performance Dashboard

Outbound campaign metrics:
- Campaign event counts
- Connection rates
- Answering machine detection results

### Testing and Simulation Dashboard

Test case execution results:
- Pass/fail rates
- Test execution methods (manual, API, scheduled)
- Channel-specific test results

### Intraday Forecast Performance Dashboard

Forecasting accuracy metrics:
- Forecast vs. actual comparisons
- Intraday performance trending

### Agent Workspace Performance Dashboard

Embedded in the agent workspace. Refreshes every 2 minutes.

---

## Dashboard Customization

### Time Range and Benchmarking

All dashboards have required filters:
- **Time range**: Today (trailing window), Day, Week, Month, or Custom. Maximum 35 days in the last 3 months.
- **Week to date**: Current ongoing week from Sunday.
- **Month to date**: From the 1st of the month to current date.
- **Compare to**: Benchmark time range for comparison. Options include prior week same day/time, prior month same time range, or custom. Powers benchmarking across all widgets.

### Widget Configuration

- Resize and rearrange visuals within any dashboard.
- Edit individual widgets via **Actions > Edit**.
- Add or remove metrics columns.
- Configure filters per widget (queue, agent, channel, routing profile, hierarchy, Contact Lens categories, etc.).
- Each dashboard type has additional feature-specific filters (e.g., Contact category for conversational analytics).

### Custom Dashboards

- Save any customized dashboard with a new name via **Actions > Save** or **Save as**.
- Saved dashboards appear under **Saved dashboards** in the **Dashboards** tab.
- Integrate a published dashboard into the agent workspace.

---

## Real-Time Metrics Reports

Real-time metrics reports display the current state of the contact center.

### Predefined Reports

- **Queues** -- Real-time queue metrics (contacts in queue, agents available, oldest contact).
- **Agents** -- Agent status roster with activity indicators.
- **Routing profiles** -- Capacity metrics by routing profile.

### Customization

- Add or remove columns (metrics).
- Set column sort order.
- Configure refresh interval (default 15 seconds).
- Apply filters by queue, routing profile, agent hierarchy.
- Set thresholds for visual alerts (color coding when metrics exceed limits).

---

## Historical Metrics Reports

Historical reports query past data and can be scheduled.

### Predefined Reports

- **Contact metrics** -- Contacts handled, abandoned, hold time, handle time, etc.
- **Agent metrics** -- Agent activity, occupancy, answer rate, NPT.
- **Queue metrics** -- Service level, wait time, abandonment.

### Scheduling

- Schedule reports to run at specific intervals (daily, weekly, monthly).
- Output to S3 in CSV format.
- Reports include the configured time range, groupings, and filters.
- Scheduled reports are not supported when tag-based access control is enabled.

---

## Login/Logout Reports

Track agent login and logout events:
- Login timestamp
- Logout timestamp
- Duration of session
- Agent hierarchy group at time of login

Data sourced from agent event stream. Available in historical reports with agent grouping.

---

## Save, Share, and Publish Reports

### Save

- Save a report configuration with a unique name for future use.
- Saved to your user profile; appears under **Saved dashboards** / **Saved reports**.
- Personal saved reports count towards the per-instance service quota.
- Establish a naming convention (e.g., team name as suffix) so published reports are traceable to owners.
- Delete saved reports via the report list if you have **Saved reports - Delete** permission.

### Share

- Share a saved report by choosing **Actions > Share report** then **Copy link address**.
- Anyone with the link AND the appropriate security profile permissions can access the report.
- You do not need to publish the report to share a link with specific people.
- Requires **Saved reports - Publish** permission.

### Publish

- Toggle **Publish report** to **On** in the **Share report** dialog.
- The report appears in the **Saved reports** list for everyone with appropriate permissions.
- Unpublish by toggling **Off**; the report is removed from everyone's list.
- Only users with **Create** and/or **Edit** permissions on saved reports can modify a published report.

### Make Read-Only

- Toggle **Read-only** to **On** in the **Share report** dialog.
- When read-only, no user (including the report owner) can save changes to report settings (Interval & Time range, Groupings, Filters, Metrics).
- Users can still adjust the report view temporarily but cannot save; the **Save** button is disabled.
- Users can use **Save as** to create their own copy.
- Non-owners cannot toggle the Read-only setting.

### Manage Saved Reports (Admin)

- Requires **Saved reports (admin)** permission.
- View and delete ALL saved reports in the instance, including reports not created by you or not currently published.
- Navigate to **Analytics and Optimization > Dashboards and reports > All reports**.
- Filter by report name, report type, published status, and user.
- Select and **Remove** reports in bulk.

---

## Custom Metric Primitives

Metric primitives are building blocks for creating custom metrics. They use metric-level filters and can be combined with arithmetic operations. Primitives are organized into 4 categories:

### Category 1: Contact Primitives

Metrics computed from completed contact records:

| Primitive | Supported Statistics | Description |
|---|---|---|
| `After contact work time` | SUM, AVG, MIN, MAX | Time agent spent in ACW for a contact. |
| `Agent active time` | SUM, AVG, MIN, MAX | Agent interaction time + hold time + ACW, including custom status time. |
| `Agent interaction time` | SUM, AVG, MIN, MAX | Time agent spent interacting with customer (excludes ACW, hold, pause). |
| `Contact hold time` | SUM, AVG, MIN, MAX | Total time customer was on hold after connecting to agent. |
| `Agent pause time` | SUM, AVG, MIN, MAX | Time agent kept a task paused (TASK channel only). |
| `Contact duration` | SUM, AVG, MIN, MAX | Time from initiation to disconnect. |
| `Contact queue time` | SUM, AVG, MIN, MAX | Time contact waited in queue before agent answered. |
| `Contacts abandoned` | SUM | Contacts disconnected by customer while in queue. |
| `Contacts created` | SUM | All contacts created (inbound + outbound). |
| `Contacts handled` | SUM | Contacts connected to an agent. |
| `Contacts hold disconnect` | SUM | Contacts disconnected while customer was on hold. |
| `Contacts put on hold` | SUM | Contacts put on hold at least once. |
| `Contacts queued` | SUM | Contacts added to a queue. |
| `Contacts transferred out` | SUM | Contacts transferred out (queue-to-queue or agent CCP). |
| `Contact handle time` | SUM | Total time from connect to finish (talk + hold + ACW + pause). |
| `Contact holds` | SUM, AVG, MIN, MAX | Number of times voice contacts were put on hold. |
| `Contact resolution time` | SUM, AVG, MIN, MAX | Total time from initiation to resolution (ACW end or disconnect). |
| `Contact flow duration` | SUM, AVG, MIN, MAX | IVR time from start until queued/transferred/disconnected. |
| `Agent greeting time` | SUM, AVG, MIN, MAX | First response time on chat (Contact Lens required). |
| `Agent interruption time` | SUM, AVG, MIN, MAX | Total agent interruption time (Contact Lens required). |
| `Agent interruptions` | SUM, AVG, MIN, MAX | Count of agent interruptions (Contact Lens required). |
| `Agent talk time` | SUM, AVG, MIN, MAX | Time agent spent talking (Contact Lens required). |
| `Customer talk time` | SUM, AVG, MIN, MAX | Time customer spent talking (Contact Lens required). |
| `Non-talk time` | SUM, AVG, MIN, MAX | Hold time + silence >3s (Contact Lens required). |
| `Talk time` | SUM, AVG, MIN, MAX | Total talk time, agent + customer (Contact Lens required). |
| `Conversation duration` | SUM, AVG, MIN, MAX | Time from conversation start to last word spoken (Contact Lens required). |
| `Contacts routed` | SUM | Number of contacts routed to an agent. |

### Category 2: Agent Primitives

Metrics computed from agent activity:

| Primitive | Supported Statistics | Description |
|---|---|---|
| `Contacts routed` | SUM | Contacts routed to an agent. |
| `Agent contacts missed` | SUM | Contacts routed to agent but not answered. |
| `Agent idle time` | SUM | Time agent was Available but not handling contacts. Cannot group/filter by queue, phone, channel. |
| `Agent on contact time` | SUM | Total time on contacts including hold + ACW (excludes custom/offline status). Cannot group/filter by queue, phone, channel. |
| `Agent online time` | SUM | Total time agent CCP was not Offline. Cannot group/filter by queue, phone, channel. |
| `Agent error status time` | SUM | Total time contacts were in error status. Cannot group/filter by queue, phone, channel. |
| `Agent online time - non-productive` | SUM | Time in custom status (not Available or Offline). Cannot group/filter by queue, phone, channel. |
| `Agent connecting time` | SUM | Time from reservation to agent connection. |

### Category 3: Current Contact Primitives

Metrics computed from contacts currently in progress:

| Primitive | Supported Statistics | Description |
|---|---|---|
| `Contacts in queue` | SUM | Contacts currently in queue. |
| `Contact queue time` | MAX | Longest time current contact has been in queue. |
| `Contacts Scheduled` | SUM | Scheduled callbacks entering queue in the future. |

**Limitation**: Current Contact category supports at most 1 component per custom metric.

### Category 4: Current Agent Primitives

Metrics computed from current agent state:

| Primitive | Supported Statistics | Description |
|---|---|---|
| `Contact availability` | SUM | How many more contacts agents can handle (slots available). |
| `Contacts active` | SUM | Total contacts currently being handled by agents. |
| `Agents online` | SUM | Agents with CCP status other than Offline. |

---

## Metric-Level Filters

Each metric primitive category supports specific metric-level filters:

### Contact Category Filters

| Filter Key | Description |
|---|---|
| **Initiation method** | INBOUND, OUTBOUND, TRANSFER, QUEUE_TRANSFER, CALLBACK, API, etc. |
| **Disconnect reason** | AGENT_DISCONNECT, CUSTOMER_DISCONNECT, TRANSFER, THIRD_PARTY_DISCONNECT, BARGED, CONTACT_FLOW_DISCONNECT, etc. |
| **Channel** | VOICE, CHAT, TASK, EMAIL. |
| **Contact source** (ValidationTestType) | Filter simulated vs. real contacts. |
| **Subtype** | Channel subtype (connect:SMS, connect:WebRTC, etc.). |
| **User defined attribute keys** | Any predefined attribute enabled for analytics. |
| **Feature** | Whether Contact Lens conversational analytics is enabled. |
| **Is abandoned** | true/false. |
| **Is resulted in callback** | true/false. |
| **Is handled** | true/false. |
| **Is put on hold** | true/false. |
| **Is queued** | true/false. |
| **Is transferred out** | true/false. |
| Duration filters (ms) | After contact work time, Agent active time, Agent interaction time, Agent pause time, Contact duration, Contact flow duration, Contact handle time, Contact hold time, Queue time, Contact resolution time, Agent greeting time, Agent interruption time, Talk time (customer/agent/total), Non-talk time, Conversation duration. |
| Count filters | Agent interruptions, Contact holds. |

### Agent Category Filters

| Filter Key | Description |
|---|---|
| **Channel** | VOICE, CHAT, TASK, EMAIL. |
| **Initiation Method** | Only supported for Agent Connecting Time. |

### Current Contact Category Filters

| Filter Key | Description |
|---|---|
| **Channel** | VOICE, CHAT, TASK, EMAIL. |
| **Initiation Method** | INBOUND, OUTBOUND, TRANSFER, etc. |
| **Contact source** (ValidationTestType) | Simulated vs. real contacts. |
| **Subtype** | Channel subtype. |
| **User defined attribute keys** | Predefined attributes enabled for analytics. |

### Current Agent Category Filters

| Filter Key | Description |
|---|---|
| **Channel** | VOICE, CHAT, TASK, EMAIL. |
| **Initiation Method** | Only supported for Contacts active. |
| **Agent Contact State** (contactStatus) | INCOMING, PENDING, CONNECTED, etc. Only supported for Agents online. |

---

## Groupings

Reports and custom metrics can be grouped by dimensions, depending on the primitive category:

### Contact Category Groupings

Agent, Agent hierarchy levels 1-5, Channel, Queue, Amazon Q, Routing profile, Subtype, Contact source.

### Agent Category Groupings

Agent, Agent hierarchy levels 1-5, Channel, Queue, Routing profile.

### Current Contact Category Groupings

Channel, Queue, Routing profile, Subtype, ValidationTestType.

### Current Agent Category Groupings

Channel, Queue, Routing profile.

---

## Arithmetic Rules for Custom Metrics

### Rule 1: Same Category

All primitives in a custom metric must come from the same category. You cannot mix Contact primitives with Agent primitives. Disabled primitives in the dropdown are from a different category.

### Rule 2: Each Primitive Uses a Filter Only Once

Each metric primitive can only use a specific filter attribute once. Applying the same filter attribute again overwrites the previous condition.

### Rule 3: Consistent Filters Within a Statistic

When performing arithmetic operations (+, -, *, /) on multiple primitives within a single statistic (e.g., `SUM(Metric-1 + Metric-2)`), all primitives must use the same filter attribute. The filter values can differ; only the attribute must match.

### Rule 4: Different Filters Across Statistics

When performing arithmetic operations on multiple statistics operations (e.g., `SUM(Metric-1) + SUM(Metric-2)`), you can combine primitive groups with different filters.

### Rule 5: Maximum 5 Components

A custom metric can contain a maximum of **5 arithmetic components** (primitives). Current Contact category supports at most 1 component.

### Rule 6: Maximum 10 Elements Per Statistic

Each statistic can reference a maximum of **10 elements** (primitives, constants, operators).

### Rule 7: Supported Operators

- Addition (+)
- Subtraction (-)
- Multiplication (*)
- Division (/)

Division by zero returns null (no error).

### Rule 8: Statistics Must Match Primitives

Not every primitive supports all statistics. Count-based metrics (e.g., Contacts Created) support SUM only. Duration metrics support SUM, AVG, MIN, MAX.

### Rule 9: Widget Compatibility

A custom metric can only be added to a dashboard widget if its underlying primitives support ALL filters and groupings applied to that widget.

### Example

```
Custom Metric: "Transfer Rate"
= SUM(Contacts Transferred Out) / SUM(Contacts Handled) * 100
Category: Contact primitives
Filters: Channel = VOICE
```

---

## Access Control

### Hierarchy-Based Access Control

Agent hierarchies control who can view specific agents and their metrics in dashboards and reports.

**Configuration options**:
- **Enforce based on user's hierarchy**: User can only manage agents in their hierarchy group or child groups.
- **Enforce based on specific/custom hierarchy**: User can only manage agents in the hierarchy defined in the security profile.

**Limitations**:
- Only the agent resource supports hierarchy-based access control.
- Access to view Agent Queues is disabled.
- When combined with tag-based access control, both are enforced independently -- users must meet both requirements.
- If two security profiles have unique configurations for both tag-based and hierarchy-based controls, hierarchy-based control may not be enforced effectively.
- Agent performance summary widget shows metrics only for the accessible hierarchy.

### Tag-Based Access Control

Resource tags restrict access to users, queues, routing profiles, flows, flow modules, evaluation forms, and test cases on analytics pages.

**Setup**:
1. Apply tags to resources (users, queues, routing profiles, flows, etc.).
2. Assign a security profile with tag-based conditions via **Show advanced** options.
3. Grant one of the dashboard/report access permissions in the same security profile.
4. Grant resource-level **View** permissions (Routing profiles, Queues, Users, Flows, etc.).

**Behavior**:
- Dashboards and reports automatically filter to show only data for resources matching the user's tag-based access.
- When filtering by resources you do not have access to, an access restriction error is displayed.
- Use **All accessible tags** filter value when sharing reports across users with different security profiles.
- Changes to resource tags are eventually consistent.
- Scheduled reports are not supported with tag-based access control.

**Scope by report type**:
- Dashboards: users, queues, routing profiles, flows, flow modules, evaluation forms, test cases.
- Real-time/Historical metrics: users, queues, routing profiles.
- Agent Activity Audit: users only.
- Login/Logout report: users and routing profiles.

---

## Change Agent Status from Dashboard

Supervisors can change an agent's status directly from the real-time metrics dashboard:

- Click on an agent in the agent roster.
- Select a new status from the dropdown (Available, Offline, any custom status).
- The agent's CCP updates immediately to reflect the new status.

This requires the `Agent status - change` permission in the supervisor's security profile.

---

## Permissions

### Dashboard and Report Permissions

| Permission | Grants |
|---|---|
| **Access metrics - Access** | Automatically assigns Real-time metrics, Historical metrics, Agent activity audit Access. Grants access to all tabs on Dashboards and reports page. |
| **Dashboards - Access** | Access only the Dashboards tab. Requires Real-time metrics Access for real-time data on dashboards. |
| **Real-time metrics - Access** | Access only real-time metrics reports. |
| **Historical metrics - Access** | Access only historical metrics reports. |
| **Agent Activity Audit - Access** | Access agent activity audit. |
| **Login/Logout report - View** | View login/logout reports. |
| **Saved reports - View** | View saved/published reports. |
| **Saved reports - Create** | Create and save new reports. |
| **Saved reports - Edit** | Edit and save changes to reports. |
| **Saved reports - Delete** | Delete saved reports. |
| **Saved reports - Publish** | Share and publish reports. |
| **Saved reports (admin) - All** | View and delete all saved reports in the instance. |
| **Custom metrics** | View, create, and manage custom metrics with custom filters and functions. |

---

## Report Data Export

| Method | Format | Description |
|---|---|---|
| **Download CSV** | CSV | Download entire dashboard data set or individual widget data. |
| **Download PDF** | PDF | Download entire dashboard as PDF. |
| **Scheduled export** | CSV | Scheduled reports exported to S3. |
| **API** | JSON | `GetMetricDataV2` returns JSON results for programmatic consumption. |
| **Data lake** | Parquet | Contact records and analytics available via Athena in the analytics data lake. |
