# Amazon Connect SRE Agent - UI Specification

## 1. Overview
The SRE Dashboard is a specialized, real-time interface designed for monitoring Amazon Connect operational health, exploring topology, and managing safe remediations. The design emphasizes a modern, premium dark-mode aesthetic with glassmorphism elements, vibrant data visualizations, and clear, actionable insights.

## 2. Layout & Grid Structure
The dashboard uses a CSS Grid layout comprising three main sections:
- **Sidebar (Left)**: Primary navigation menu (Home, Incidents, Monitoring, Topology, Approvals, Config, Logs) and the active agent profile.
- **Header (Top)**: Application title ("AMAZON CONNECT | SRE DASHBOARD") and contextual agent information (Active Status, Region).
- **Main Dashboard Area**: A responsive grid containing specialized widgets.

## 3. Dashboard Widgets
1. **SRE Overview**: Displays high-level system status, current latency, and throughput (TPS).
2. **System Health**: A circular donut chart showing overall uptime percentage with color-coded health segments.
3. **Global Network Topology**: An interactive directed graph visualizing the connections between Regions, Connect instances, CCPs, Lex bots, and downstream endpoints. Includes connection latency and health status.
4. **Open Incidents by Severity**: A multi-line time-series chart plotting incident volume across severities (SEV1 to SEV4) over the last 24 hours.
5. **Queues (Volume)**: A vertical bar chart comparing call volume, wait times, and SLAs across different queue categories (Sales, Support, Escalations, Retention).
6. **Queue Health Metrics**: A detailed line chart showing Average Handle Time vs. Wait Time, supplemented by key metrics (Concurrent Calls, Abandon Rate).
7. **Lex Bot Health**: A list view of active Lex bots indicating their current health score, status (Healthy, Degraded), and visual health bars.
8. **Pending Remediation Approvals**: A data table listing actions requiring human approval before execution, displaying the Action, Trigger context, Requester, and explicit Approve/Reject buttons.
9. **Activity Feed**: A prominent alert banner/ticker at the bottom displaying the most recent system events or errors.

## 4. Design System & Aesthetics
- **Theme**: Premium Dark Mode.
- **Background**: Deep, rich dark blue/charcoal gradients (e.g., `#0A0F1C` to `#111827`).
- **Cards/Panels**: Glassmorphism effect. Semi-transparent backgrounds with backdrop blur (`backdrop-filter: blur(12px)`), subtle borders, and soft inner glows.
- **Typography**: Modern, geometric sans-serif fonts (e.g., *Inter*, *Outfit*, or *Roboto*).
- **Color Palette**:
  - **Healthy/OK**: Vibrant Emerald/Neon Green (`#10B981`, `#34D399`)
  - **Warning/Degraded**: Bright Amber/Orange (`#F59E0B`)
  - **Critical/Error**: Intense Crimson/Red (`#EF4444`)
  - **Data Visualizations**: Electric Blue (`#3B82F6`), Purple (`#8B5CF6`), Cyan (`#06B6D4`).
- **Micro-animations**: Smooth hover transitions on interactive elements (buttons, table rows), animated chart rendering, and subtle glowing effects on active nodes in the topology graph.

## 5. Technology Alignment
- **Framework**: React (via Vite) for component-driven architecture.
- **Styling**: Vanilla CSS utilizing CSS Variables, Flexbox, CSS Grid, and modern features like container queries.
- **Data Visualization**: Recharts or Chart.js for graphs; React Flow or similar for the interactive topology map.
