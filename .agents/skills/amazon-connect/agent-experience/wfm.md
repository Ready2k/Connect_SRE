# Workforce Management (WFM)

Amazon Connect Workforce Management provides ML-powered forecasting, capacity planning, scheduling, and adherence monitoring. It is a native capability within Amazon Connect -- no third-party WFM software required.

---

## Forecasting

Forecasting predicts future contact volume and average handle time using historical data from the Connect instance.

### How It Works

1. **Data ingestion** -- WFM reads historical contact records (volume, handle time, abandonment) from the Connect instance. Minimum 8 weeks of data recommended; more data improves accuracy.
2. **ML model training** -- Amazon Connect trains ML models on the historical data, automatically detecting patterns: day-of-week, time-of-day, seasonality, holidays, and trends.
3. **Forecast generation** -- the system generates forecasts for configurable periods (daily, weekly, up to 18 months out).
4. **Auto-update** -- forecasts are automatically refreshed daily as new data arrives.

### Short-Term vs. Long-Term Forecasting

| Type | Horizon | Granularity | Use Case |
|---|---|---|---|
| **Short-term** | Days to weeks | 15-min, 30-min, or hourly intervals | Daily scheduling, intraday staffing adjustments |
| **Long-term** | Weeks to 18 months | Daily, weekly, or monthly | Capacity planning, hiring decisions, budget |

### ML Model Details

- Models automatically detect and account for:
  - Day-of-week patterns (e.g., Monday peaks).
  - Time-of-day patterns (e.g., lunch-hour dips).
  - Seasonal trends (e.g., holiday surges).
  - Growth/decline trends.
  - Holiday effects.
- No manual model tuning required -- Connect handles model selection and training.
- Forecast accuracy improves with more historical data.

### Data Requirements

- **Minimum:** 8 weeks of historical contact data.
- **Recommended:** 12+ months for accurate seasonal patterns.
- Data sources: inbound contact volume, handle time, abandonment rates.
- Data is read directly from the Connect instance -- no manual export needed.

### Forecast Outputs

| Output | Description |
|---|---|
| **Contact volume** | Predicted number of inbound contacts per interval (15-min, 30-min, or hourly). |
| **Average handle time (AHT)** | Predicted average handle time per interval. |
| **Confidence intervals** | Upper and lower bounds showing forecast uncertainty. |

### Accuracy Tracking

- Forecasts are compared against actuals after the period passes.
- Overlay charts show predicted vs. actual volume for past periods.
- Accuracy metrics help calibrate manual overrides and validate model performance.

### Visualization

Forecasts are displayed as graphs in the WFM console:

- Line charts showing predicted volume over time.
- Overlays of actual vs. predicted for past periods.
- Adjustable date range and granularity.

### Manual Overrides

Forecasters can manually adjust forecasts for known events:

- Marketing campaigns expected to spike volume.
- Planned outages or service disruptions.
- Holidays or special events not captured in historical data.
- Product launches or promotional periods.

Overrides are applied as percentage adjustments or absolute volume changes to specific date ranges.

### Forecast Import

- Import external forecast data to supplement or replace ML-generated forecasts.
- Useful when migrating from another WFM system or incorporating external demand signals.

### Forecast Groups

Organize queues into forecast groups for aggregate forecasting:

- Group queues that share similar traffic patterns or are staffed by the same agent pool.
- Forecasts are generated per forecast group.
- Each queue can belong to only one forecast group.
- Forecast groups align with staffing groups for scheduling.

---

## Capacity Planning

Capacity planning estimates long-term staffing requirements based on forecasts and service level goals.

### Planning Horizon

- Plan up to **18 months** into the future.
- Granularity: weekly or monthly.

### Inputs

| Input | Description |
|---|---|
| **Forecast** | Contact volume and AHT predictions from the forecasting module. |
| **Service level goal** | Target percentage of contacts answered within a threshold (e.g., 80% in 30 seconds). |
| **Shrinkage** | Percentage of scheduled time agents are unavailable (breaks, training, meetings, absenteeism). Typically 25-35%. |
| **Occupancy target** | Maximum agent utilization to prevent burnout (e.g., 85%). |
| **Agent cost rates** | Hourly cost per agent for budget calculations. |

### Scenario-Based Optimization (What-If Analysis)

Create multiple capacity plans with different assumptions:

- **Base scenario** -- standard forecast, current service level goals.
- **Growth scenario** -- forecast adjusted +20% for business growth.
- **Austerity scenario** -- higher service level threshold, lower headcount.
- **Seasonal scenario** -- holiday-adjusted forecast with temporary staff.
- **Attrition scenario** -- accounts for expected agent turnover rates.

Compare scenarios side-by-side to make hiring and budget decisions. Each scenario shows the impact on service levels, cost, and FTE requirements.

### Output

| Output | Description |
|---|---|
| **FTE requirements** | Full-time equivalent headcount needed per week/month. |
| **Hiring timeline** | When to start hiring and training to meet future demand. |
| **Cost estimates** | Based on configured agent cost rates. |
| **Service level impact** | Projected service level at different staffing levels. |
| **Understaffed/overstaffed periods** | Identifies weeks where staffing gaps or excess exist. |

---

## Scheduling

Scheduling generates optimized agent schedules that balance service level targets, agent preferences, and business rules.

### Schedule Generation

1. **Select forecast group** -- choose which forecast group to schedule for.
2. **Define scheduling horizon** -- typically 1-4 weeks out.
3. **Configure optimization target**:
   - **Service Level** -- optimize to meet a percentage of contacts answered within threshold, per channel.
   - **Average Speed of Answer (ASA)** -- optimize to meet a target ASA, per channel.
4. **Run the optimizer** -- the system generates a schedule that minimizes staffing cost while meeting the target.

### Shift Profiles

Shift profiles are weekly schedule templates that define the allowable working patterns:

| Parameter | Description |
|---|---|
| **Shift start window** | Earliest and latest allowed start time (e.g., 7:00 AM - 9:00 AM). |
| **Shift duration** | Minimum and maximum shift length (e.g., 8-10 hours). |
| **Days on/off** | Number of working days per week and consecutive day-off requirements. |
| **Break rules** | Number, duration, and timing constraints for breaks (e.g., 15 min break after 2 hours, 30 min lunch between hours 4-5). |
| **Overtime** | Whether overtime is allowed, max overtime hours per week. |
| **Shift pattern** | Rotating, fixed, or flexible shift patterns. |

Multiple shift profiles can exist for different agent groups (full-time, part-time, flexible).

### Staffing Groups

Staffing groups link agents to forecast groups:

- A staffing group contains a set of agents who can handle contacts for a specific forecast group.
- Agents can belong to multiple staffing groups (cross-trained agents).
- Each staffing group references a shift profile that governs scheduling rules.
- Staffing groups determine which agents are available for which queues during scheduling.

### HR and Business Rules Compliance

The scheduler respects:

- **Minimum rest between shifts** -- configurable gap (e.g., 11 hours between shifts).
- **Maximum consecutive working days** -- prevent scheduling more than N days in a row.
- **Skill-based constraints** -- ensure agents with required skills are scheduled for specialized queues.
- **Time-off requests** -- approved time-off is blocked from scheduling.
- **Contractual hours** -- respect minimum and maximum weekly/monthly hours per agent.
- **Labor law compliance** -- country/region-specific labor regulations.
- **Overtime limits** -- maximum daily/weekly overtime hours.

### Schedule Publishing

After generation, schedules go through a review and publish workflow:

1. Scheduler reviews the generated schedule in the WFM console.
2. Scheduler can make manual adjustments (swap shifts, adjust break times, reassign agents).
3. Scheduler publishes the schedule.
4. Published schedules appear in the agent workspace (agents view their upcoming schedule).
5. Agents receive notifications of schedule changes.

### Agent Schedule View

Agents see their schedule in the workspace:
- **Calendar view** -- upcoming shifts with start/end times, break windows, and scheduled activities.
- **Today's timeline** -- visual bar showing the day's schedule with current position highlighted.
- **Next activity notification** -- "Break in 15 minutes."
- **Weekly view** -- upcoming week's schedule at a glance.
- Schedule view is read-only for agents.

---

## Time Off Management

### Allowances

- Set annual or monthly time-off allowances per agent or group.
- Different allowance pools for vacation, sick leave, personal days.
- Configurable by staffing group or individual agent.

### Accrual

- Hours accrued per pay period based on configurable rules.
- Accrual rates can vary by tenure, role, or employment type.
- Real-time balance tracking visible to agents and managers.

### Carryover

- Maximum carryover hours from one period to the next.
- Configurable expiration dates for carried-over hours.
- "Use it or lose it" policies supported.

### Request and Approval Workflow

1. Agent submits a time-off request from the workspace schedule view.
2. Request specifies dates, hours, and time-off type.
3. Manager reviews pending requests in the WFM console.
4. Manager approves or denies with optional comments.
5. Approved requests auto-update the schedule -- blocked from future scheduling.
6. Agent receives notification of approval/denial.

### CSV Upload

- Bulk import time-off balances and requests via CSV.
- Useful for initial setup or migration from another system.
- Supports batch updates to allowances and accrued balances.

---

## Overtime Management

### Rules

- Maximum overtime hours per day and per week.
- Approval requirements (auto-approved vs. manager-approved).
- Overtime rate multipliers for cost tracking.
- Cooldown periods between overtime assignments.

### Voluntary vs. Mandatory

| Type | Description |
|---|---|
| **Voluntary** | Agents opt-in to available overtime slots. System suggests eligible agents based on availability and skills. |
| **Mandatory** | Agents are assigned overtime based on business need. Follows rotation or seniority rules. |

### Scheduling

- System identifies understaffed periods from forecast vs. schedule comparison.
- Suggests agents for overtime based on availability, skills, and overtime limits.
- Overtime assignments respect shift profile rules and rest requirements.

### Cost Tracking

- Overtime hours tracked separately in reports.
- Cost calculated using configured overtime rate multipliers.
- Visible in capacity planning cost projections.

---

## Schedule Adherence

Schedule adherence monitors whether agents follow their published schedules in real time.

### Adherence Metrics

| Metric | Formula | Description |
|---|---|---|
| **Adherence percentage** | (Time in adherent status / Total scheduled time) x 100 | How well the agent followed the schedule. |
| **Conformance** | (Total time worked / Total scheduled time) x 100 | Whether the agent worked the expected total hours. |
| **Non-adherent time** | Total duration in non-adherent status during scheduled activity | Absolute time out of adherence. |
| **Out of adherence events** | Count of deviations from schedule | Number of times agent deviated. |

### How It Works

1. The system compares the agent's actual status (from the CCP) to their scheduled activity for each time interval.
2. Each scheduled activity maps to one or more acceptable agent statuses:
   - "Scheduled: Productive" maps to Available, On Contact, ACW.
   - "Scheduled: Break" maps to Break (custom status).
   - "Scheduled: Training" maps to Training (custom status).
3. If the agent's actual status does not match an acceptable status for the current scheduled activity, they are flagged as non-adherent.

### Real-Time Dashboard

Supervisors view adherence in real time:

- Agent list showing current status, scheduled activity, and adherence state (adherent / non-adherent).
- Color-coded indicators (green = adherent, red = non-adherent).
- Drill-down to individual agent timeline showing scheduled vs. actual throughout the day.
- Alerts when agents are non-adherent beyond a configurable threshold (e.g., non-adherent for more than 5 minutes).
- Team-level adherence percentage for at-a-glance monitoring.

### Historical Adherence Reports

- Daily, weekly, and monthly adherence reports.
- Filter by team, staffing group, or individual agent.
- Trend analysis to identify chronic adherence issues.
- Export for further analysis or performance reviews.

---

## Productivity Metrics

Beyond adherence, WFM tracks:

| Metric | Description |
|---|---|
| **Agent occupancy** | Percentage of available time spent handling contacts. |
| **Idle time** | Time in Available status with no contact. |
| **Productive time** | Time handling contacts (talk + hold + ACW). |
| **Shrinkage** | Time in non-productive statuses (breaks, training, meetings, offline). |
| **Schedule efficiency** | Ratio of required staff to scheduled staff. |

---

## Surge Management

Detect and respond to unexpected volume spikes:

- **Detection** -- real-time metrics identify surges via queue size, wait time spikes, and abandonment rate increases.
- **Dynamic staffing** -- extend current shifts, cancel scheduled breaks (with agent consent), activate on-call agents.
- **Voluntary overtime** -- offer overtime slots to available agents via the workspace.
- **Queue overflow** -- route excess contacts to backup queues, overflow teams, or alternate channels.
- **Automated responses** -- trigger callback offers or self-service deflection during sustained surges.

---

## Multi-Skill Scheduling

Schedule agents across multiple queues and skill sets:

- Agents assigned to multiple staffing groups (cross-trained).
- **Skill priority weighting** -- optimizer prioritizes primary skills while using secondary skills as needed.
- Schedule optimizer balances coverage across all skill groups.
- **Migration from single-skill** -- gradual rollout recommended. Start with a pilot group of cross-trained agents.
- **Forecast accuracy impact** -- multi-skill scheduling can affect forecast accuracy during transition as traffic patterns across queues change. Allow 2-4 weeks for models to adjust.

---

## Personas and Permissions

WFM functionality is role-gated via security profiles:

### Administrator

- Full access to all WFM features.
- Configures forecast groups, staffing groups, shift profiles.
- Manages WFM settings and permissions.
- Sets up time-off policies and overtime rules.

### Forecaster

- Creates, views, and edits forecasts.
- Applies manual overrides.
- Publishes forecasts for scheduling.
- Imports external forecast data.
- Views forecast accuracy metrics.

### Scheduler

- Creates and publishes schedules.
- Manages time-off requests (approve/deny).
- Makes manual schedule adjustments.
- Views adherence data.
- Configures overtime assignments.

### Capacity Planner

- Creates and manages capacity plans.
- Runs scenario comparisons (what-if analysis).
- Views long-term FTE projections.
- Analyzes cost impacts.

### Agent

- Views their own published schedule in the agent workspace.
- Sees upcoming shifts, breaks, and activities.
- Submits time-off requests.
- Opts in to voluntary overtime slots.
- Cannot view other agents' schedules or WFM configuration.

---

## Integration with Agent Workspace

Agents see their WFM schedule directly in the agent workspace:

- **Schedule view** -- calendar showing upcoming shifts with start/end times, break windows, and scheduled activities.
- **Today's timeline** -- visual bar showing the day's schedule with current position highlighted.
- **Next activity** -- notification of the next scheduled activity (e.g., "Break in 15 minutes").
- **Time-off requests** -- submit and track requests from the workspace.
- **Weekly view** -- upcoming week's schedule at a glance.

The schedule view is read-only for agents. Only schedulers and administrators can modify schedules.
