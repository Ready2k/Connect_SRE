# Admin Workspace

## Overview

The Amazon Connect admin workspace is the web-based console for supervisors and administrators. It provides real-time visibility into contact center operations, configuration management, and administrative tools. The admin workspace is separate from the agent workspace (CCP/agent desktop) and is accessed via the Amazon Connect console URL.

---

## Theme Customization

Customize the visual appearance of the admin workspace to match organizational branding.

### What Can Be Customized

- **Logo**: Upload a custom logo displayed in the header
- **Colors**: Primary, secondary, and accent colors for the workspace UI
- **Fonts**: Custom font families for headings and body text
- **Favicon**: Custom browser tab icon

### API

Use `UpdateWorkspaceTheme` to apply theme changes programmatically:

```javascript
const { ConnectClient } = require("@aws-sdk/client-connect");

// Theme customization is configured through the Connect console
// under Application settings > Workspace themes
//
// Key properties:
// - HeaderBackground: Primary header color
// - LogoUrl: URL to hosted logo image (HTTPS, PNG/SVG recommended)
// - PrimaryColor: Accent color for buttons and interactive elements
// - FontFamily: Font stack for the workspace
```

### Scope

Theme customization applies to the entire admin console for that instance. All administrators and supervisors see the same theme. Per-user theming is not supported.

---

## Home Dashboard

When administrators log in, they land on the home dashboard — a configurable summary of contact center health.

### Default Widgets

The home dashboard includes:

- **Queue performance**: Current contacts in queue, longest wait time, service level
- **Agent status summary**: Available, on call, after-contact work, offline counts
- **Contact volume**: Inbound/outbound contact counts for today
- **Service level**: Percentage of contacts answered within SLA threshold

### Customization

- **Add/remove widgets**: Select which metric cards and charts appear
- **Rearrange layout**: Drag widgets to preferred positions
- **Set time range**: Configure the default time window (today, last 24 hours, etc.)
- **Auto-refresh interval**: Widgets refresh automatically (typically every 15 seconds for real-time data)

### Role-Based Dashboards

Different admin roles can see different dashboard configurations:

- **Supervisors**: Focus on their assigned queues and agents
- **Workforce managers**: Emphasis on adherence, forecast accuracy, agent schedules
- **Quality analysts**: Evaluation scores, Contact Lens insights, trending topics
- **System administrators**: System health, API errors, capacity metrics

Dashboard visibility is controlled through security profiles in Amazon Connect. Each security profile determines which metrics and widgets are accessible.

---

## Notifications

The admin workspace includes an in-app notification system in the workspace header.

### Notification Types

| Type | Description | Example |
|------|-------------|---------|
| System alerts | Instance-level events | "Telephony provider experiencing degraded performance" |
| SLA breaches | Service level drops below threshold | "Sales queue SLA dropped below 80% (currently 62%)" |
| Queue threshold alerts | Queue metrics exceed configured limits | "Support queue has 25 contacts waiting (threshold: 15)" |
| Agent alerts | Agent state anomalies | "3 agents in ACW for more than 10 minutes" |
| Evaluation notifications | Quality evaluation events | "New evaluation submitted for review" |

### Configuring Notification Rules

Notification rules are configured through Amazon Connect Rules:

1. Navigate to **Analytics and optimization > Rules**
2. Create a new rule with the desired trigger condition
3. Set the action to **Generate notification**
4. Specify the notification message and target security profiles

```
Rule example:
  Trigger: Queue metric "Contacts in queue" > 20 for queue "Main Support"
  Action: Send notification "Support queue exceeds 20 contacts — consider adding agents"
  Target: Supervisor security profile
```

### Notification URLs

Notifications can include URLs for quick navigation. When an SLA breach notification appears, clicking it can navigate the admin directly to the relevant queue's real-time metrics page.

### Notification Persistence

- Notifications appear in the bell icon in the workspace header
- Unread notifications show a badge count
- Notifications persist until dismissed or until they expire (configurable)
- Historical notifications are available in the notifications panel

---

## Data Tables in Admin Workspace

Administrators can create and manage data tables directly from the admin console. Data tables store structured data that flows can reference at runtime.

### Managing Data Tables

From the admin workspace:

1. Navigate to **Contact flows > Data tables**
2. **Create table**: Define table name, primary key, sort key (optional), and additional columns
3. **View/edit rows**: Browse table contents, add rows, edit values, delete rows
4. **Manage schema**: Add or remove columns (non-key columns only)
5. **Import data**: Bulk upload rows from CSV

### Use Cases

- **Business hours**: Store hours by location, check in flows to route accordingly
- **Routing rules**: Map customer segments to queues without modifying flows
- **Feature flags**: Enable/disable flow features without redeploying
- **Prompt text**: Store dynamic prompt messages that non-technical staff can update

### Integration with Flows

Data tables are accessed in flows via the "Invoke data table" block. For detailed flow integration patterns, see [`flows/data-tables.md`](../data/data-tables.md).

### Access Control

Data table management is controlled by security profile permissions:

- **View data tables**: Read-only access to table schemas and data
- **Edit data tables**: Add/edit/delete rows
- **Manage data tables**: Create/delete tables, modify schema

Restrict edit access to authorized administrators to prevent accidental changes that affect live flows.

---

## Security Profiles for Admin Access

Admin workspace access is governed by security profiles. Key permissions for administrators:

| Permission | Grants |
|------------|--------|
| Access metrics | View real-time and historical metrics |
| Manager monitor | Listen to live calls, barge in |
| Contact search | Search and review past contacts |
| Rules | Create and manage automation rules |
| Users and permissions | Manage agent accounts and security profiles |
| Contact flows | Create and edit contact flows |
| Data tables | Create and manage data tables |

Assign the minimum permissions required for each admin role. Avoid granting full admin access broadly — use role-specific security profiles.
