# Analytics Data Lake

The Amazon Connect analytics data lake provides a centralized query location for all Connect operational data, enabling analysis via Amazon Athena and visualization via Amazon QuickSight.

---

## Overview

The data lake is a zero-ETL solution. Amazon Connect automatically exports data to a managed data store, and you query it using standard SQL through Athena. No custom pipelines, Glue jobs, or data transformation code is required.

---

## Zero-ETL Architecture

- **No extraction code** -- Connect automatically exports data.
- **No transformation logic** -- Data is stored in a query-ready format.
- **No loading pipelines** -- No Glue crawlers, Glue jobs, or Step Functions needed.
- **No infrastructure management** -- AWS manages the underlying storage and catalog.

This eliminates the operational burden of maintaining data pipelines and reduces the time from data generation to query availability.

---

## Data Refresh

- Data is refreshed within **1 hour** of the contact or event completing.
- This is near real-time but not instant. For true real-time data, use Kinesis streaming or the agent event stream.
- Refresh is continuous; there is no manual trigger required.
- Contact records may be delivered more than once (at-least-once delivery). Updates (e.g., via `update-contact-attributes`) deliver a new record.

---

## Available Tables

The data lake includes the following tables. Each can be associated independently.

### Core Tables

| Table | DataSetId | Description |
|---|---|---|
| `contact_record` | `contact_record` | One row per contact segment with full CTR data. |
| `contact_statistic_record` | `contact_statistic_record` | Pre-computed contact statistics and boolean flags. |
| `contact_flow_events` | `contact_flow_events` | Flow and module execution events per contact. |
| `contact_lens_conversational_analytics` | `contact_lens_conversational_analytics` | Contact Lens analytics per analyzed contact. |
| `contact_evaluation_record` | `contact_evaluation_record` | One row per evaluation item (form/section/question). |
| `agent_queue_statistic_record` | `agent_queue_statistic_record` | Agent performance metrics per queue per interval. |
| `agent_statistic_record` | `agent_statistic_record` | Agent-level statistics per interval. |

### AI and Bot Tables

| Table | Description |
|---|---|
| `ai_agent` | AI agent invocation events (success, latency, helpfulness). |
| `ai_agent_knowledge_base` | Knowledge base references during AI sessions. |
| `ai_prompt` | AI prompt invocations (model, tokens, latency). |
| `ai_session` | AI session summaries (goal success, faithfulness, completeness). |
| `ai_tool` | AI tool invocations (accuracy scores, latency). |
| Bot analytics tables | Bot conversations, intents, slots. |

### Other Tables

| Table | Description |
|---|---|
| `agent_event` | Agent state transitions, configuration changes, contact associations. |
| `amazon_connect_resource_tags` | Resource tag snapshots for tag-based reporting. |
| `connect_test_case_execution_results` | Test case pass/fail results by execution method. |
| Cases tables | Case metadata, fields, associated contacts. |
| Configuration tables | Instance configuration data. |
| Forecasting tables | Short-term and long-term forecast data, intraday forecasts. |
| Outbound campaigns tables | Campaign event data. |
| Scheduling tables | Staff shifts, timeoffs, schedule metrics, schedule goals. |

---

## Key Table Schemas

### contact_record

| Column | Type | Description |
|---|---|---|
| `instance_id` | string | Connect instance ID. |
| `contact_id` | string | Contact ID. |
| `initial_contact_id` | string | First contact in the chain. |
| `previous_contact_id` | string | Contact before transfer. |
| `related_contact_id` | string | Related contact for linking. |
| `next_contact_id` | string | Next contact in chain. |
| `channel` | string | VOICE, CHAT, TASK, EMAIL. |
| `initiation_method` | string | INBOUND, OUTBOUND, TRANSFER, CALLBACK, QUEUE_TRANSFER, EXTERNAL_OUTBOUND, MONITOR, DISCONNECT, API. |
| `initiation_timestamp` | Timestamp | Contact start time. |
| `disconnect_timestamp` | Timestamp | Contact end time. |
| `disconnect_reason` | string | Reason for disconnect. |
| `queue_name` / `queue_id` / `queue_arn` | string | Queue info. |
| `queue_duration_ms` | bigint | Time spent waiting in queue (ms). |
| `queue_enqueue_timestamp` | Timestamp | When contact entered queue. |
| `agent_username` / `agent_id` / `agent_arn` | string | Agent info. |
| `agent_connected_to_agent_timestamp` | Timestamp | When agent connected. |
| `agent_interaction_duration_ms` | bigint | Agent interaction time (ms). |
| `agent_customer_hold_duration_ms` | bigint | Total hold time (ms). |
| `agent_number_of_holds` | bigint | Hold count. |
| `agent_longest_hold_duration_ms` | bigint | Longest hold (ms). |
| `agent_after_contact_work_duration_ms` | bigint | ACW time (ms). |
| `agent_after_contact_work_start/end_timestamp` | Timestamp | ACW window. |
| `agent_hierarchy_groups_level_1-5_name/arn/id` | string | Agent hierarchy (5 levels). |
| `agent_routing_profile_name/arn/id` | string | Agent routing profile. |
| `attributes` | map(string,string) | Contact attributes (key-value). |
| `customer_endpoint_type` / `customer_endpoint_address` | string | Customer phone/endpoint. |
| `system_endpoint_type` / `system_endpoint_address` | string | System endpoint. |
| `recording_location` / `recording_status` / `recording_type` | string | Recording info (S3 location, AVAILABLE/DELETED/NULL, AUDIO). |
| `references` | array(struct) | Attached references (URL, ATTACHMENT, NUMBER, STRING, DATE, EMAIL_MESSAGE). |
| `segment_attribute` | map(string,string) | Segment attributes (Subtype, Direction, etc.). |
| `agent_state_transitions` | array(struct) | State transition history. |
| `recordings` | array(struct) | Voice/screen recording details. |
| `ai_agents` | array(struct) | AI agent info (use_case, version, escalated). |
| `agent_pause_duration_ms` | bigint | Pause duration (tasks). |
| `quality_metrics_agent_audio` / `quality_metrics_customer_audio` | struct | Audio quality metrics. |
| Chat-specific columns | Various | `chat_contact_metrics_*`, `chat_agent_metrics_*`, `chat_customer_metrics_*` for message counts, response times, abandonment. |
| `data_lake_last_processed_timestamp` | Timestamp | Last processing time (not reliable for freshness). |

### contact_lens_conversational_analytics

| Column | Type | Description |
|---|---|---|
| `contact_id` | string | Contact ID. |
| `channel` | string | VOICE, CHAT. |
| `language_locale` | string | Analysis language. |
| `categories` | array(string) | Matched category labels. |
| `disconnect_timestamp` | Timestamp | Contact end time. |
| `greeting_time_agent_ms` | bigint | Agent first response time (chat). |
| `non_talk_time_total_ms` | bigint | Hold + silence >3s. |
| `talk_time_total_ms` / `talk_time_agent_ms` / `talk_time_customer_ms` | bigint | Talk time breakdown. |
| `total_conversation_duration_ms` | bigint | Start to last word spoken. |
| `talk_speed_agent_wpm` / `talk_speed_customer_wpm` | float | Words per minute. |
| `interruptions_time_total_ms` / `interruptions_time_agent_ms` / `interruptions_time_customer_ms` | bigint | Interruption durations. |
| `interruptions_total_count` / `interruptions_agent_count` / `interruptions_customer_count` | bigint | Interruption counts. |
| `sentiment_overall_score_agent` / `sentiment_overall_score_customer` | float | Overall sentiment scores. |
| `sentiment_interaction_score_customer_with_agent` / `sentiment_interaction_score_customer_without_agent` | float | Customer sentiment with/without agent. |
| `sentiment_end_score_agent` / `sentiment_end_score_customer` | float | End-of-call sentiment. |
| `response_time_average_agent_ms` / `response_time_average_customer_ms` | bigint | Chat response times. |
| `response_time_maximum_agent_ms` / `response_time_maximum_customer_ms` | bigint | Max chat response times. |

### contact_evaluation_record

| Column | Type | Description |
|---|---|---|
| `evaluation_id` | string | Primary key. Unique evaluation ID. |
| `item_reference_id` | string | Primary key. Form/section/question reference. |
| `item_type` | string | Form, Section, sub-section, question, or deleted record. |
| `contact_id` | string | Evaluated contact. |
| `evaluation_submitted_timestamp` | Timestamp | When evaluation was submitted. |
| `score` | double | Score percentage for form/section/question. |
| `weighted_score` | double | Weighted contribution to form total. |
| `automatic_fail` | Boolean | Whether automatic fail was triggered. |
| `evaluator_id` | string | User ID of evaluator. |
| `numeric_answer` | double | Answer for numeric questions. |
| `answer_reference_id` | string | Answer for single-select questions. |
| `multi_select_answer_reference_ids` | array(string) | Answers for multi-select questions. |
| `date_time_answer` | Timestamp | Answer for date questions. |
| `evaluation_source` | string | Manual, assisted automation, or fully automatic. |
| `evaluation_type` | string | Standard or calibration. |
| `acknowledgement_status` | string | ACKNOWLEDGED or UNACKNOWLEDGED. |
| `automation_gen_ai_text_answer` | string | Gen AI text answer. |
| `automation_gen_ai_answer_justification` | string | Gen AI justification. |
| `is_automation_answer_accepted` | Boolean | Whether Gen AI answer was accepted. |

### contact_statistic_record

| Column | Type | Description |
|---|---|---|
| `contact_id` | string | Contact ID. |
| `channel` | string | VOICE, CHAT, TASK, EMAIL. |
| `queue_id` / `agent_id` | string | Queue and agent. |
| `initiation_method` | string | How contact was initiated. |
| `disconnect_timestamp` | Timestamp | Contact end. |
| `contact_flow_time_ms` | bigint | Time in contact flow. |
| `abandon_time_ms` | bigint | Wait time before abandonment. |
| `queue_time_ms` / `queue_answer_time_ms` | bigint | Queue wait times. |
| `handle_time_ms` | bigint | Agent interaction + hold + ACW. |
| `customer_hold_time_ms` | bigint | Hold time. |
| `agent_interaction_time_ms` | bigint | Agent interaction time. |
| `after_contact_work_time_ms` | bigint | ACW time. |
| Boolean flags | bigint | `is_connected`, `is_abandoned`, `is_handled`, `is_handled_incoming`, `is_handled_outbound`, `is_callback_handled`, `is_api_handled`, `is_put_on_hold`, `is_hold_disconnect`, `is_incoming`, `is_callback_contact`, `is_api_contact`, `is_queued`, `is_queued_and_handled`, `is_transferred_in`, `is_transferred_out`, `is_transferred_out_internal`, `is_transferred_out_external`, etc. |

### agent_queue_statistic_record

| Column | Type | Description |
|---|---|---|
| `user_id` | string | Agent user ID. |
| `routing_profile_id` | string | Routing profile. |
| `agent_hierarchy_level_1-5_id` | string | Hierarchy group IDs. |
| `interval_start_time` / `interval_end_time` | Timestamp | Interval window. |
| `queue_id` | string | Queue ID. |
| `channel` | string | VOICE, CHAT, TASK, EMAIL. |
| `queue_type` | string | STANDARD or AGENT. |
| `agent_non_response` | bigint | Contacts not answered by agent. |
| `contacts_offered` / `contacts_handled` | bigint | Contact counts. |
| `handle_time` | bigint | Average handle time. |
| `agent_incoming/outbound/callback/api_connecting_time` | bigint | Connecting times by type. |
| `incoming/outbound/callback/api_connecting_attempts` | bigint | Attempt counts by type. |

### agent_statistic_record

| Column | Type | Description |
|---|---|---|
| `user_id` | string | Agent user ID. |
| `interval_start_time` / `interval_end_time` | Timestamp | Interval window. |
| `online_time` | bigint | Time not in Offline status. |
| `error_time` | bigint | Time in error state. |
| `non_productive_time` | bigint | Time in custom status. |
| `agent_idle_time` | bigint | Available but not handling contacts. |
| `agent_on_contact_time` | bigint | Time on contacts (including hold + ACW). |
| `custom_state_time_01` through `custom_state_time_50` | bigint | Up to 50 custom agent states. |

### agent_event

| Column | Type | Description |
|---|---|---|
| `event_id` | string | Unique event ID (part of composite PK with instance_id). |
| `event_timestamp` | Timestamp | When event occurred. |
| `event_type` | string | Type of agent event. |
| `current_agent_status_arn/name/type` | string | Current status details. |
| `current_configuration_username/first_name/last_name` | string | Agent identity. |
| `current_routing_profile_arn/name` | string | Routing profile. |
| `current_routing_profile_concurrency` | array(struct) | Concurrency settings. |
| `current_contacts` | array(struct) | Current contacts. |
| Previous state columns | Various | Mirror of current state for tracking changes. |

### amazon_connect_resource_tags

| Column | Type | Description |
|---|---|---|
| `resource_arn` | string | ARN of the tagged resource. |
| `tags` | map(string,string) | Tag key-value pairs. |
| `record_creation_timestamp` | Timestamp | When tags changed. |

---

## Athena Integration

### Setup

1. Navigate to **Analytics and optimization > Data lake** in the Amazon Connect console (or use CLI/CloudShell).
2. Enable the data lake for your instance.
3. Select which data types to include.
4. Specify the **Target AWS account ID** (can be same or different account).
5. Accept the RAM (Resource Access Manager) invitation in the consumer account.
6. In Lake Formation, create a database and resource link tables mapping to shared tables.
7. Query via Athena: `SELECT * FROM {{database_name}}.{{linked_table}} LIMIT 10`.

### Prerequisites

- Connect instance must be in a supported region.
- IAM permissions for Lake Formation, Athena, and S3.
- A Lake Formation admin must be configured in the account.
- Data lake administrator permissions in Lake Formation for the configuring user.

### CLI Setup

```bash
# Generate skeleton
aws connect batch-associate-analytics-data-set \
  --generate-cli-skeleton input > input_batch_association.json

# Associate tables
aws connect batch-associate-analytics-data-set \
  --cli-input-json file:///path/to/input_batch_association.json
```

Example JSON:
```json
{
  "InstanceId": "your_instance_id",
  "DataSetIds": [
    "contact_record",
    "contact_flow_events",
    "contact_statistic_record",
    "contact_lens_conversational_analytics",
    "agent_queue_statistic_record",
    "agent_statistic_record",
    "contact_evaluation_record"
  ],
  "TargetAccountId": "your_account_ID"
}
```

### Partitioning

Data is partitioned by date for efficient querying. Always include date filters in your queries to minimize scan costs.

### SQL Query Examples

```sql
-- Average handle time by queue for the last 7 days
SELECT
    queue_name,
    AVG(agent_interaction_duration_ms + agent_after_contact_work_duration_ms) AS avg_handle_time_ms,
    COUNT(*) AS contacts_handled
FROM contact_record
WHERE
    disconnect_timestamp >= CURRENT_DATE - INTERVAL '7' DAY
    AND agent_username IS NOT NULL
GROUP BY queue_name
ORDER BY avg_handle_time_ms DESC;

-- Abandonment rate by queue
SELECT
    cr.queue_name,
    SUM(cs.is_abandoned) AS abandoned,
    COUNT(*) AS total,
    ROUND(SUM(cs.is_abandoned) * 100.0 / COUNT(*), 2) AS abandon_rate_pct
FROM contact_statistic_record cs
JOIN contact_record cr ON cs.contact_id = cr.contact_id AND cs.instance_id = cr.instance_id
WHERE cs.disconnect_timestamp >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY cr.queue_name
ORDER BY abandon_rate_pct DESC;

-- Sentiment analysis by category
SELECT
    category,
    COUNT(*) AS contact_count,
    AVG(sentiment_overall_score_customer) AS avg_customer_sentiment
FROM contact_lens_conversational_analytics
CROSS JOIN UNNEST(categories) AS t(category)
WHERE disconnect_timestamp >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY category
ORDER BY contact_count DESC;

-- Agent performance summary
SELECT
    user_id,
    SUM(online_time) / 1000 / 60 AS online_minutes,
    SUM(agent_on_contact_time) / 1000 / 60 AS on_contact_minutes,
    SUM(agent_idle_time) / 1000 / 60 AS idle_minutes,
    ROUND(SUM(agent_on_contact_time) * 100.0 / NULLIF(SUM(online_time), 0), 2) AS occupancy_pct
FROM agent_statistic_record
WHERE interval_end_time >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY user_id
ORDER BY occupancy_pct DESC;
```

---

## QuickSight Integration

1. Create a QuickSight data source pointing to the Athena database.
2. Build datasets from the data lake tables.
3. Create analyses and dashboards with filters, calculations, and visualizations.
4. Use QuickSight SPICE to cache data for faster dashboard performance.

---

## Cross-Account Access via Resource Links

### What Are Resource Link Tables?

Resource link tables are cross-account Athena table references that allow you to access the data lake tables from another AWS account or workgroup.

### Setup Flow

1. In the Connect console, add a data share specifying the target account ID.
2. An AWS RAM invitation is created for the consumer account.
3. Accept the RAM invitation in the consumer account (expires after 12 hours if not accepted).
4. In the consumer account's Lake Formation, create resource link tables pointing to the shared tables.
5. Grant SELECT permissions via Lake Formation to specific IAM roles/users.

### Important Notes

- Initial RAM request is created only for the first share; subsequent shares reuse accepted RAM.
- Lake Formation optimizes by reusing existing accepted RAM requests when possible.
- Revoke access to remove visibility to the data.

---

## Data Retention

The data lake maintains a **rolling 25-month window** of accessible data. The cutoff date updates at 12 AM UTC.

Each table uses a designated timestamp field for age calculations:

| Table | Age Timestamp Column |
|---|---|
| `agent_queue_statistic_record` | `interval_end_time` |
| `agent_statistic_record` | `interval_end_time` |
| `contact_evaluation_record` | `evaluation_submitted_timestamp` |
| `contact_flow_events` | `start_timestamp` |
| `contact_lens_conversational_analytics` | `disconnect_timestamp` |
| `contact_statistic_record` | `disconnect_timestamp` |
| `contact_record` | `disconnect_timestamp` |
| `staff_shift_activities` | `last_updated_timestamp` |
| `staff_shifts` | `last_updated_timestamp` |
| `staff_timeoffs` | `last_updated_timestamp` |
| `staff_timeoff_intervals` | `last_updated_timestamp` |
| `short_term_forecasts` | `creation_timestamp` |
| `long_term_forecasts` | `creation_timestamp` |
| `outbound_campaign_events` | `campaign_event_timestamp` |
| `schedule_metrics` | `last_updated_timestamp` |
| `schedule_goals` | `last_updated_timestamp` |
| `bot_conversations` | `bot_conversation_end_timestamp` |
| `bot_intents` | `bot_conversation_end_timestamp` |
| `bot_slots` | `bot_conversation_end_timestamp` |
| `intraday_forecasts` | `creation_timestamp` |

For retention beyond 25 months, configure Kinesis Data Streams or Kinesis Data Firehose to export contact records and analytics to your own S3 bucket.

---

## APIs

| API | Description |
|---|---|
| `BatchAssociateAnalyticsDataSet` | Associate data types with the data lake for a target account. |
| `BatchDisassociateAnalyticsDataSet` | Remove data type associations. |
| `ListAnalyticsDataAssociations` | List current data type associations. |

---

## Cost Considerations

- **Data lake storage** -- Included with Amazon Connect at no additional charge.
- **Athena queries** -- Standard Athena pricing applies (per TB scanned). Use partitioning and columnar filtering to minimize costs.
- **QuickSight** -- Standard QuickSight pricing for users and SPICE capacity.
- **Lake Formation** -- No additional charge for Lake Formation itself.

---

## Limitations

- Data is read-only. You cannot write to or modify data lake tables.
- Query performance depends on data volume and complexity. Use date partitioning.
- The data lake does not include real-time streaming data. For sub-minute latency, use Kinesis.
- Cross-region data lake access is not supported. The data lake exists in the same region as the Connect instance.
- Maximum concurrent Athena queries follow standard Athena service limits.
- New features may add fields/values to tables; build applications to ignore unknown fields.
- Contact records may be delivered more than once due to updates.
