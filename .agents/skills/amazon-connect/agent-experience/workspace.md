# Agent Workspace Architecture

The Amazon Connect agent workspace is the unified, browser-based application where agents handle customer contacts across all channels. It consolidates eight integrated components into a single pane of glass.

**URLs:**

- Agent workspace: `https://{instance}.my.connect.aws/agent-app-v2/`
- CCP (standalone): `https://{instance}.my.connect.aws/ccp-v2/`

---

## 1. Contact Control Panel (CCP)

The CCP is the core telephony and contact-handling widget embedded in the workspace. It handles:

- **Voice calls** -- accept, reject, hold, resume, transfer, conference, disconnect.
- **Chats** -- accept, send messages, transfer, end conversation. Supports concurrent multi-chat.
- **Emails** -- accept, reply, forward, compose drafts with rich text editor. Full threading support.
- **Tasks** -- accept, create, pause, resume, transfer, complete. Tasks can be assigned via flows, APIs, or other agents.

The CCP surfaces agent status controls, the number pad (DTMF), quick connects for transfers, and device settings (softphone vs. desk phone).

When embedded in the workspace, the CCP appears as a narrow panel on the left side. It can also run standalone at the `/ccp-v2/` URL for minimal deployments or third-party CRM integrations.

---

## 2. Third-Party Applications (Apps Launcher)

Third-party applications are external web applications loaded inside the workspace via HTTPS iframes. They appear as tabs in the workspace and can be launched from the Apps launcher button in the right corner of the workspace.

- Built with any frontend framework (React, Angular, Vue, plain HTML/JS).
- Communicate with the workspace via the `@amazon-connect/sdk` packages.
- Receive contact events, agent state changes, and theme updates from the workspace.
- Can be configured to auto-launch on specific contact events (e.g., incoming call, ACW).
- Support screen pop functionality via the no-code UI builder -- third-party apps can be embedded in step-by-step guide views.
- MCP server integrations are also supported as an integration type.

### Registration

Applications are registered in the Amazon Connect console under **Integrations**:

1. Navigate to **Integrations** in the Connect console.
2. Choose **Add integration**.
3. Configure the following:

**Basic Information:**

| Field | Description |
|---|---|
| **Display name** | Friendly name shown on security profiles and agent tabs. Editable after creation. |
| **Description** | Optional internal description, not displayed to agents. |
| **Integration type** | Standard web application, service, or MCP server. |
| **Integration identifier** | Unique name for the integration. If one app per access URL, use the URL origin. Immutable after creation. |
| **Initialization timeout** | Max time (ms) to establish connection with workspace. |

**Application Details:**

| Field | Description |
|---|---|
| **Contact Scope** | Whether the app refreshes per contact or per browser session. |
| **Initialization timeout** | Max time (ms) for connection startup. |

**Access:**

| Field | Description |
|---|---|
| **Access URL** | HTTPS URL where the application is hosted. Must be iframeable (Content-Security-Policy frame-ancestors must allow the Connect domain). |
| **Approved origins** | Additional allowlisted URLs beyond the access URL. |

**Iframe Requirements:**
- The app's Content-Security-Policy `frame-ancestors` directive must be set to `https://{your-instance}.my.connect.aws`.
- If the directive is `same-origin` or `deny`, the URL cannot be iframed.
- Use the app developer recommendations to ensure apps can only be embedded in the Connect workspace.

### Events and Requests Permissions

Third-party applications can subscribe to workspace events and make requests. Permissions are assigned during integration registration and control what data the app can access (contact events, agent state, theme updates, etc.).

### SSO Federation

Third-party applications support SSO federation setup for seamless authentication between the workspace and the embedded app.

### IAM Permissions for Registration

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "app-integrations:CreateApplication",
        "app-integrations:GetApplication",
        "app-integrations:CreateApplicationAssociation",
        "app-integrations:DeleteApplicationAssociation",
        "iam:GetRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy"
      ],
      "Resource": "arn:aws:app-integrations:{region}:{account}:application/*",
      "Effect": "Allow"
    }
  ]
}
```

### Instance Association

- Applications must be associated with one or more Connect instances to be usable.
- For MCP servers, only the instance configured with the selected Gateway's Discovery URL can be selected.

### Deleting Integrations

- The integration must be disassociated from all instances before deletion.
- Disassociating temporarily removes access without full deletion.

---

## 3. Connect AI Agents (Real-Time Recommendations)

Amazon Connect AI agents (formerly Amazon Q in Connect / Wisdom) provide real-time recommendations to agents during live contacts:

- Automatically detects customer intent from the conversation transcript.
- Surfaces relevant knowledge articles, recommended responses, and next-best actions.
- Recommendations update in real time as the conversation progresses.
- Agents can search the knowledge base manually if automatic detection does not surface the right content.
- Supports custom AI guardrails and self-service configurations.

The AI agents panel appears as a tab in the workspace alongside the contact details.

---

## 4. Tasks

Tasks are a contact channel for tracking follow-up work, assignments, and non-real-time activities:

- **Create tasks** -- agents create tasks manually from the workspace, or tasks are generated automatically via contact flows, rules, or API calls.
- **Assign tasks** -- route to specific agents, queues, or quick connects.
- **Task templates** -- define structured fields (required/optional) for consistent task creation.
- **Task scheduling** -- schedule tasks for future dates and times.
- **Linked tasks** -- associate tasks with the originating contact for context.
- **Pause and resume** -- agents can pause a task (with a reason) and resume later. Paused tasks do not count against concurrency.

Tasks appear in the CCP contact list alongside calls, chats, and emails.

---

## 5. Cases Tab

Amazon Connect Cases provides case management directly in the workspace:

- Agents view, create, and update cases linked to customer profiles.
- Each case has fields (status, priority, summary, custom fields), a timeline of events, and linked contacts.
- Cases can be created automatically via contact flows or rules.
- Case templates define the required and optional fields for case creation.
- Cases persist across contacts -- an agent can reference a case from a previous interaction.

The Cases tab appears in the workspace when Cases is enabled for the instance.

---

## 6. Step-by-Step Guides

Guides are no-code, flow-designed UI workflows that surface inside the agent workspace. They walk agents through structured processes (identity verification, troubleshooting scripts, disposition capture).

- Created in the contact flow designer using the "Show view" block.
- Can be invoked at the start of a contact, during handling, or during After Contact Work (ACW).
- Support form inputs, dropdowns, radio buttons, and conditional branching.
- Can read and write contact attributes for dynamic content.
- Support PII redaction for sensitive fields via Contact Lens integration.
- Default ACW guides auto-launch when the agent enters ACW state.
- When a guide runs, a separate background chat contact is created (agents are not aware of this).

See `step-by-step-guides.md` for full details.

---

## 7. Customer Profile Tab

The Customer Profile tab displays a unified customer view assembled from multiple data sources:

- Shows customer identity (name, phone, email, account number) resolved via Customer Profiles domain.
- Displays contact history, case history, and product/asset information.
- Data ingested from S3, Salesforce, ServiceNow, Zendesk, Segment, Shopify, and custom integrations.
- Identity resolution uses ML to merge duplicate profiles across sources.
- Agents can edit profile fields directly from the workspace.
- Contact flows can auto-populate the profile tab based on caller ID or IVR-collected data.

---

## 8. Voice ID (Excluded -- End of Life)

Amazon Connect Voice ID reached end of life and is excluded from new implementations. Previously provided real-time caller authentication via voiceprint and fraud detection.

---

## Theme Customization

Administrators customize the workspace appearance by creating a workspace, customizing its theme, and assigning it to agents.

### Theme Components

A theme consists of four elements:

| Component | Description |
|---|---|
| **Logo** | Replaces the Connect branding at top-left. Upload PNG or SVG. |
| **Favicon** | Replaces the browser tab icon. Upload in specified dimensions. |
| **Font family** | Select from available font families via dropdown. |
| **Color palette** | Set of colors applied throughout the workspace. |

### Light and Dark Mode

Agents can toggle between light and dark modes from user settings at the top right of the workspace. Administrators should test theme changes in both modes. Different logos, favicons, and color sets can be specified for light vs. dark mode.

### Color Palette Categories

Colors are organized into four categories, each with customizable tokens:

**Canvas Colors:**
- Apply to background elements of the workspace.

**Primary Action Colors:**
- Apply to buttons, links, and key interactive elements.

**Header Colors:**
- Apply to elements of the header bar and settings menu at the top.

**Navigation Colors:**
- Apply to the navigation bar on the left side.

Colors can be specified via hex code, RGB values, HSL values, or named colors.

### Accessibility

Default colors provide sufficient contrast for accessibility compliance. If colors are changed, they must be tested for accessibility (sufficient contrast for readability by individuals with visual impairments).

### Theme Import/Export

| Action | Description |
|---|---|
| **Export** | Outputs theme configurations as JSON for uploading to another workspace. |
| **Import** | Import configurations from other workspaces or upload a JSON file. |
| **Reset** | Reverts to last saved state. |
| **Reset to default** | Returns to the standard Connect theme. |

### Style Precedence

Component-level styling (set in views) takes precedence over workspace-level styling. View styling is only used when workspace and component styling are absent.

### Third-Party App Theme Integration

Third-party applications receive theme changes via the SDK theme integration and can adapt their UI to match the workspace theme automatically.

---

## Persona-Based Workspace Pages

Persona-based workspaces allow administrators to create custom workspace layouts tailored to specific user roles. Each workspace page defines which components are visible and their arrangement.

### Creating Workspace Pages

1. Create a workspace in the Connect console.
2. Select the workspace purpose:
   - **Guide Views** -- for contact-specific workflows (agents, customers, managers).
   - **Workspace Views** -- for general interface pages (home pages) independent of contact handling.
3. Use the UI builder to design the page layout.

### Available Components

Workspace views support components including:
- **Alert** -- notification banners.
- **Carousel** -- rotating content displays.
- **Containers** -- layout grouping.
- **Data Table** -- real-time data management (call routing adjustments, emergency protocols).
- **Connect Application** -- embed first-party Connect apps (Guides, Cases, Profiles, etc.).

### Dynamic Input Data

When creating workspace pages, input data can be passed at runtime through the page configuration wizard:

- Create reusable views that adapt to different contexts without separate implementations.
- Dynamic header components display personalized greetings or context-specific content.
- A single view can be reused across multiple workspaces with different customized content.

### Role-Based Assignment

- Assign workspace pages to users via security profiles or routing profiles.
- Examples:
  - **Sales agent page** -- CCP + Customer Profile + CRM app + Cases.
  - **Support agent page** -- CCP + AI Agents + Knowledge Base app + Step-by-Step Guides.
  - **Supervisor page** -- Real-time metrics + Agent monitoring + Quality Management.
- Workspace pages are evaluated at login time based on the user's profile assignment.

### Manager Workspace Pages

Managers can use workspace pages with embedded guides for:
- **Coaching forms** -- structured evaluation forms during agent monitoring.
- **Escalation workflows** -- step-by-step processes for supervisor assistance requests.
- **Quality review checklists** -- standardized evaluation criteria.
- **Data tables** -- real-time contact center operations management.

Manager guides use the **Connect Application** component with the Guide application namespace and a specified ContactFlowId. Users start the guide with a "Begin" button and can restart with a "Restart" button.

---

## Disposition Codes

Disposition codes let agents categorize the outcome of a contact:

- Configured via step-by-step guides using a Show view block with a Form view and a Set contact attributes block.
- Agents select a disposition during or after the contact (typically during ACW).
- Disposition values are stored as contact attributes and appear in contact records.
- Can be made required (agent cannot clear the contact without selecting a disposition).
- Dispositions can trigger downstream rules (e.g., auto-create a follow-up task, update a case).

### Implementation Pattern

1. Create a flow with one **Show view** block (Form view for disposition input) and one **Set contact attributes** block (to save the response).
2. Optionally add a **Lambda function** block to send data to an external system.
3. Set the `DisconnectFlowForAgentUI` custom attribute in contact flows to dynamically determine which disposition form surfaces at contact end.
4. As long as this attribute is set before a contact ends, the agent UI surfaces the form automatically after disconnect.

### Making Disposition Required

- Do not include a "Skip" or "Close" action on the disposition view.
- The agent must complete the guide to clear the contact.
- Alternatively, use a rule that flags contacts missing a disposition attribute.

---

## Workspace Notifications

The workspace surfaces notifications to agents for:

- Incoming contact alerts (voice ringtone, chat/email/task notifications).
- Schedule reminders ("Break in 15 minutes") from WFM integration.
- AI agent recommendations that update in real time.
- View integration refresh prompts when polled data changes.
- Error state notifications requiring agent acknowledgment.

---

## Admin Workspace Setup

To configure the agent workspace:

1. **Enable the workspace** -- In the Amazon Connect console, navigate to "Agent application" under "Application integration."
2. **Register third-party apps** -- Add each app under "Integrations" with its access URL, allowed origins, contact scope, and permissions.
3. **Create workspaces** -- Define persona-based layouts via the console or API.
4. **Apply themes** -- Customize logo, favicon, fonts, and color palette. Export/import for consistency across workspaces.
5. **Configure guides** -- Build step-by-step guides in the flow designer and assign them to contact flows.
6. **Enable AI agents** -- Set up knowledge bases and enable Amazon Q in Connect.
7. **Set security profiles** -- Control which components each agent role can access:
   - **Agent Applications - Custom views - All** -- enables agents to see step-by-step guides.
   - **Channels and flows - Views** -- enables managers to create guides.
   - Third-party app access is gated by security profile assignments.
8. **Distribute the URL** -- Agents access the workspace at `https://{instance}.my.connect.aws/agent-app-v2/`.
