# Data Streaming

Amazon Connect can stream contact records, agent events, and Customer Profiles data to Amazon Kinesis for real-time processing, analytics, and long-term retention beyond the 24-month in-instance limit.

## Enabling Data Streaming

Data streaming is configured from the **Data streaming** page in the Amazon Connect console (Amazon Connect > Instance > Data streaming).

### Console Steps
1. Open the Amazon Connect console at `https://console.aws.amazon.com/connect/`
2. On the instances page, choose the instance alias
3. In the navigation pane, choose **Data streaming**
4. Choose **Enable data streaming**
5. For **Contact records**: choose Kinesis Firehose (select existing or create new) or Kinesis Stream (select existing or create new)
6. For **Agent Events**: select an existing Kinesis Data Stream or create new
7. Choose **Save**

### Data Categories and Supported Destinations

| Data Category | Kinesis Data Firehose | Kinesis Data Stream |
|---|---|---|
| Contact records (CTRs) | Yes | Yes |
| Agent events | No | Yes (stream only) |
| Customer Profiles | No | Yes (stream only) |

- **Contact records** can go to either Firehose (for direct delivery to S3, Redshift, OpenSearch, etc.) or a Kinesis Data Stream (for custom consumers)
- **Agent events** and **Customer Profiles** support Kinesis Data Streams only — Firehose is not an option for these categories

## Contact Records Streaming

Contact records contain the metadata and details of every contact handled by your instance. By default, CTRs are available in the Connect instance for **24 months**. Streaming to Kinesis enables longer retention and integration with external analytics systems.

### What a Contact Record Includes
- **Contact identifiers**: ContactId, InitialContactId, PreviousContactId
- **Agent information**: ARN, timestamps (connect, disconnect), hierarchy groups, routing profile
- **Queue information**: ARN, name, enqueue/dequeue timestamps, duration
- **Recording location**: S3 bucket, key, type (audio/screen), status
- **Contact attributes**: All attributes set during the flow
- **Disconnect details**: Reason, timestamp, who disconnected (agent/customer/system)
- **Channel**: Voice, chat, task, email
- **Initiation method**: Inbound, outbound, transfer, callback, API, queue_transfer
- **Contact Lens metadata**: If Contact Lens is enabled, includes analysis results reference
- **Global Resiliency metadata**: ActiveRegion, OriginRegion, TrafficDistributionGroupId (if ACGR enabled)

### Delivery Behavior
- CTRs are emitted **after** the contact is fully completed (after ACW — After Contact Work)
- Records are delivered as JSON to the configured Kinesis stream or Firehose
- Each record is a self-contained JSON document
- Ordering: Records within a single contact are ordered, but records across contacts may arrive out of order
- Delivery: **At-least-once** — consumers must be idempotent to handle duplicates

## Agent Event Streaming

Agent events provide near-real-time visibility into agent activity. See [agent-event-streams.md](./agent-event-streams.md) for the full data model and event types.

### Event Types Published
- Agent login
- Agent logout
- Agent connects with a contact
- Agent status change (Available, Break, Training, etc.)

### Use Cases
- Build real-time dashboards displaying agent information and events
- Integrate with workforce management (WFM) solutions
- Configure alerting tools for custom notifications on specific agent activity
- Calculate ACW (After Contact Work) time

### Configuration
- Select a Kinesis Data Stream on the Data streaming page
- Agent events **cannot** be sent to Firehose
- Events stream in **near real-time** (not batched like CTRs)

## Customer Profiles Streaming

When Customer Profiles data streaming is enabled, profile changes (creates, updates, merges) are published to the configured Kinesis Data Stream. This is useful for keeping external systems synchronized with Connect's unified customer view.

## Server-Side Encryption with Customer-Managed KMS Keys

By default, Kinesis streams use AWS-managed encryption. To use a **customer-managed KMS key** (CMK), you must grant the Connect service-linked role permission to generate data keys.

### Step 1 — Get the Service-Linked Role ARN

The Connect service-linked role follows this pattern:
```
arn:aws:iam::<ACCOUNT_ID>:role/aws-service-role/connect.amazonaws.com/AWSServiceRoleForAmazonConnect_<SUFFIX>
```

Find it via **Console**: Amazon Connect console > Instance > Account overview > Distribution settings > Service-linked role.

Or via **CLI**:
```bash
aws iam list-roles --query "Roles[?contains(RoleName, 'AWSServiceRoleForAmazonConnect')].[Arn]" --output text
```

Or via the **DescribeInstance API**:
```bash
aws connect describe-instance --instance-id {{your_instance_id}}
# Save the ServiceRole value from the output
```

### Step 2 — Construct the KMS Key Policy Statement

Add a policy statement to your KMS key that grants the service-linked role `kms:GenerateDataKey` permission:

```json
{
  "Sid": "AllowConnectToGenerateDataKey",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::<ACCOUNT_ID>:role/aws-service-role/connect.amazonaws.com/AWSServiceRoleForAmazonConnect_<SUFFIX>"
  },
  "Action": "kms:GenerateDataKey",
  "Resource": "*"
}
```

### Step 3 — Apply the Policy to the KMS Key

```bash
# Get current policy
aws kms get-key-policy --key-id <KEY_ID> --policy-name default --output text > policy.json

# Edit policy.json to add the statement above

# Put updated policy
aws kms put-key-policy --key-id <KEY_ID> --policy-name default --policy file://policy.json
```

Or use the AWS KMS console, AWS CDK, or CloudFormation to update the key policy.

**Critical**: Update the KMS key permission **before** enabling streaming with a CMK. Without this permission, Connect cannot encrypt records before writing them to the Kinesis stream, and streaming will **fail silently**.

## Stream Processing Patterns

### Pattern 1: Lambda Consumer
- Attach a Lambda function as a Kinesis Data Stream consumer
- Lambda auto-scales with shard count
- Best for: lightweight transformations, routing to DynamoDB, sending notifications
- Configure batch size, starting position, and error handling in the event source mapping

### Pattern 2: KCL Application (Kinesis Client Library)
- Run a long-lived application using the Kinesis Client Library
- Best for: high-throughput processing, complex aggregations, stateful processing
- KCL handles shard management, checkpointing, and load balancing

### Pattern 3: Firehose to S3 (Recommended for Archival)
1. Stream CTRs to **Kinesis Data Firehose**
2. Firehose delivers to **S3** with partitioning by date
3. Apply **S3 lifecycle rules** for tiered storage (Standard → IA → Glacier)
4. Query archived records with **Athena** using a Glue catalog table

### Pattern 4: Firehose to Analytics
- Firehose can deliver directly to Redshift, OpenSearch, Splunk, or HTTP endpoints
- Built-in buffering, compression, and format conversion

## Error Handling

### At-Least-Once Delivery
- Kinesis provides at-least-once delivery — consumers must handle **duplicate records**
- Use ContactId + timestamp as an idempotency key for deduplication

### Lambda Consumer Error Handling
- Configure `MaximumRetryAttempts` and `BisectBatchOnFunctionError` in the event source mapping
- Use a **dead letter queue** (SQS or SNS) via `OnFailure` destination for records that exhaust retries
- Set `MaximumRecordAgeInSeconds` to skip stale records and prevent iterator age growth

### Kinesis Stream Errors
- Monitor `GetRecords.IteratorAgeMilliseconds` — high values indicate consumers falling behind
- Monitor `WriteProvisionedThroughputExceeded` — indicates shard capacity exceeded; reshard to add capacity
- Connect's service-linked role needs `kinesis:PutRecord` and `kinesis:PutRecords` on the target stream (granted automatically when configured via console)

### Firehose Error Handling
- Firehose stores failed records in a configured **S3 error bucket**
- Monitor `DeliveryToS3.DataFreshness` for delivery lag
- Configure retry duration for transient destination failures

## Monitoring Streaming Health

### CloudWatch Metrics for Kinesis Data Streams
- `IncomingRecords` — number of records put into the stream
- `IncomingBytes` — bytes put into the stream
- `GetRecords.IteratorAgeMilliseconds` — consumer lag (should stay low)
- `ReadProvisionedThroughputExceeded` — consumer hitting read limits
- `WriteProvisionedThroughputExceeded` — Connect hitting write limits

### CloudWatch Metrics for Firehose
- `DeliveryToS3.Success` — successful deliveries to S3
- `DeliveryToS3.DataFreshness` — age of oldest undelivered record
- `IncomingRecords` / `IncomingBytes` — volume metrics

### Alarms to Set
- Iterator age > threshold → consumer is falling behind
- Write throughput exceeded → need more shards
- Delivery freshness > threshold → Firehose delivery issues
- Error count > 0 on dead letter queue → records failing processing

## Retention and Archival

| Storage Location | Retention |
|---|---|
| Connect instance (native) | 24 months |
| Kinesis Data Stream | Configurable (1–365 days, or unlimited with enhanced fan-out) |
| Kinesis Firehose to S3 | Indefinite (managed by S3 lifecycle rules) |

## APIs and Configuration

### Console-Only Configuration
- Data streaming is enabled/disabled via the Connect console Data streaming page
- There is no direct API to toggle data streaming on/off

### AssociateInstanceStorageConfig API
- Used programmatically to associate storage configurations (including Kinesis streams) with a Connect instance
- Relevant for infrastructure-as-code deployments

```
AssociateInstanceStorageConfig
  InstanceId: string (required)
  ResourceType: string (required) — CONTACT_TRACE_RECORDS, AGENT_EVENTS, etc.
  StorageConfig: object (required)
    StorageType: KINESIS_STREAM | KINESIS_FIREHOSE
    KinesisStreamConfig:
      StreamArn: string (required)
    KinesisFirehoseConfig:
      FirehoseArn: string (required)
```

### Related APIs
- `DescribeInstanceStorageConfig` — view current storage config
- `UpdateInstanceStorageConfig` — change the target stream/firehose
- `DisassociateInstanceStorageConfig` — remove a storage config
- `ListInstanceStorageConfigs` — list all storage configs for an instance

### Kinesis/Firehose Resource Management
- Kinesis streams and Firehose delivery streams are managed via their respective AWS SDKs
- `KinesisClient` from `@aws-sdk/client-kinesis`
- `FirehoseClient` from `@aws-sdk/client-firehose`

## Key Considerations

- **Ordering**: Records within a single contact are ordered, but records across contacts may arrive out of order
- **Duplicates**: At-least-once delivery — consumers should be idempotent
- **Latency**: CTRs stream after contact completion (after ACW); agent events stream in near-real-time
- **Cross-region**: The Kinesis stream must be in the **same region** as the Connect instance
- **Permissions**: The Connect service-linked role needs `kinesis:PutRecord` and `kinesis:PutRecords` on the target stream (granted automatically when configured via console)
- **Shard sizing**: Plan shard count based on expected contact volume — each shard handles 1 MB/s or 1,000 records/s write, 2 MB/s read
- **Firehose buffering**: Firehose buffers before delivery — configure buffer size (1–128 MB) and interval (60–900 seconds) based on freshness needs
- **KMS cost**: Using a customer-managed KMS key incurs KMS API call charges for every record encrypted/decrypted
