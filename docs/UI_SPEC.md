# Amazon Connect SRE Agent — UI Specification

## Overview

The SRE Console is a single-page React 19 application (React Router 7, Vite) served directly from the FastAPI container at `:8000`. It provides real-time incident monitoring, topology exploration, Connect AI Agent management, and supervised remediation for Amazon Connect environments.

---

## Layout

Three fixed regions via CSS Grid:

- **Sidebar (left, 240px)** — navigation + user identity footer
- **Header (top)** — instance/mode selector, active model banner, demo/live toggle
- **Main area** — page content, scrollable

---

## Navigation (Sidebar)

| Icon | Label | Route | Notes |
|---|---|---|---|
| `Server` | Instances | `/instances` | Live mode only — instance picker |
| `Home` | Home | `/` | Dashboard with widgets |
| `AlertTriangle` | Incidents | `/incidents` | Incident list + traces |
| `Bot` | Agents | `/agents` | SRE agent swarm (supervisor + 10 specialists) |
| `BrainCircuit` | AI Agents | `/ai-agents` | Connect Q Connect AI Agents management |
| `CheckCircle` | Approvals | `/approvals` | Pending + history |
| `Activity` | Monitoring | `/monitoring` | Queue metrics, Recharts panels |
| `Network` | Topology | `/topology` | ReactFlow dependency graph |
| `Route` | Journeys | `/journeys` | Customer journey CRUD |
| `Wrench` | Tool Registry | `/tools` | Enabled/disabled tool management |
| `ShieldAlert` | Policy | `/policy` | Active policy rules |
| `BookOpen` | Runbooks | `/runbooks` | S3 SOP browser |
| `Settings` | Config | `/config` | Model config + active provider banner |
| `FileText` | Logs | `/logs` | Container log tail |

All icons are from `lucide-react`. Routes are defined in `ui/src/App.jsx`.

---

## Pages

### `/` — Home
Dashboard view. Widgets: SRE Overview (uptime, concurrent calls, abandon rate), System Health donut, IncidentsChart (Recharts time-series by severity), QueuesChart (bar chart by queue), QueueMetrics (AHT vs wait time line chart), LexBotHealth list, PendingApprovals summary, ActivityFeed ticker.

### `/instances` (Live mode only)
Auto-discovers Connect instances via `GET /api/connect/instances`. Selecting an instance sets `activeInstance` in `AppContext` and redirects to `/`.

### `/incidents`
Filterable incident list. Click → detail panel with traces, step-by-step agent reasoning, linked incidents, and manual trigger button. Sourced from `GET /api/incidents` + `GET /api/incidents/{id}/traces` + `GET /api/incidents/{id}/steps`.

### `/agents`
ReactFlow graph showing the Supervisor node connected to 10 specialist nodes. Node borders animate (amber) when a specialist is active during an investigation. Status sourced from `GET /api/agents/status`.

### `/ai-agents`
Connect AI Agent management. Sourced from `GET /api/connect/ai-agents` and `GET /api/connect/ai-agents/health`.

- Summary KPIs: total agents, active count, published count, Bedrock error %
- Expandable cards per agent: name, type, status badge, visibility badge, locale, model ID
- Expanded detail: tool list, Bedrock 60-min metrics (invocations, error rate, latency), Lex runtime metrics (request count, user errors), config metadata (agent ID, prompt status, last modified)
- Both demo and live mode supported

### `/approvals`
Tabbed pending / history view. Pending: approve/reject buttons per record with justification text. Sourced from `GET /api/approvals` and `GET /api/approvals/history`.

### `/monitoring`
Recharts panels: queue volumes bar chart, AHT/wait time line chart, concurrent calls, abandon rate, Lex bot health list, activity feed. Supports `?mode=live&instanceId=` for real Connect `GetCurrentMetricData` data.

### `/topology`
ReactFlow interactive directed graph of the Connect instance topology (phone numbers → flows → modules → queues → Lex bots → AI agents). Supports live mode with real-time topology from DynamoDB. Trigger topology scan via button → `POST /api/topology/scan`.

### `/journeys`
CRUD for customer journey definitions stored in `dev-connect-sre-journey-map`. Sourced from `GET/POST/PATCH/DELETE /api/journeys`.

### `/tools`
Tool registry table. Toggle enabled/disabled per tool. Sourced from `GET /api/tools` + `PATCH /api/tools/{id}`.

### `/policy`
Active policy rule list. Edit rules inline. Sourced from `GET /api/policy` + `PATCH /api/policy`.

### `/runbooks`
Browse and read markdown runbooks from S3. Sourced from `GET /api/runbooks`.

### `/config`
Active model configuration. Shows provider banner (Bedrock model ID or Gemini model name). Edit model settings. Sourced from `GET/PATCH /api/models/config`.

### `/logs`
Tail of container stdout/stderr. Sourced from `GET /api/logs`.

---

## Demo vs Live mode

The header toggle writes `mode` to `AppContext`. All pages append `?mode=demo|live` (and `?instanceId=` in live mode) to their API calls. No component contains hardcoded mock data — all mocking lives in the FastAPI backend, making the UI code mode-agnostic.

In live mode with no `activeInstance` selected, the app redirects to `/instances` automatically.

---

## Design system

**Theme:** Premium dark mode.

**CSS variables (defined in `ui/src/index.css`):**

| Variable | Usage |
|---|---|
| `--bg-primary` | Page background |
| `--bg-secondary` | Card / panel backgrounds |
| `--bg-glass` | Glassmorphism chip backgrounds |
| `--border-glass` | Card borders |
| `--accent-cyan` | Active states, highlights, topology edges |
| `--text-primary` | Primary text |
| `--text-muted` | Labels, metadata |
| `--status-ok` | Healthy (green) |
| `--status-warn` | Degraded (amber) |
| `--status-error` | Critical (red) |

**No CSS framework.** All layout is vanilla CSS with CSS Grid and Flexbox. No Tailwind, no MUI, no Bootstrap.

**Key libraries:**

| Library | Use |
|---|---|
| `reactflow` | Topology graph, Agents swarm graph |
| `recharts` | All metric charts |
| `lucide-react` | All icons |
| `react-router-dom` v7 | Client-side routing |

---

## API dependency map

| Page | Primary endpoints |
|---|---|
| Home | `/api/incidents`, `/api/monitoring/metrics`, `/api/approvals`, `/api/agents/status` |
| Incidents | `/api/incidents`, `/api/incidents/{id}/traces`, `/api/incidents/{id}/steps`, `/api/incidents/{id}/linked` |
| Agents | `/api/agents/status`, `/api/agents/config`, `/api/agents/tasks` |
| AI Agents | `/api/connect/ai-agents`, `/api/connect/ai-agents/health` |
| Approvals | `/api/approvals`, `/api/approvals/history`, `/api/approvals/{id}/action` |
| Monitoring | `/api/monitoring/metrics` |
| Topology | `/api/topology`, `/api/topology/scan`, `/api/connect/instances` |
| Journeys | `/api/journeys` |
| Tool Registry | `/api/tools` |
| Policy | `/api/policy` |
| Runbooks | `/api/runbooks` |
| Config | `/api/models/config` |
| Logs | `/api/logs` |
| Instances | `/api/connect/instances`, `/api/instances/overview` |
