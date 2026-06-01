# Contact Flow Logging

## Overview

Contact flow logging records the execution path of every contact through a flow, including which blocks were executed, what decisions were made, and what errors occurred. Logs are written to Amazon CloudWatch Logs and are essential for debugging flow issues, tracing contact failures, and auditing flow behavior.

---

## Enabling Flow Logging

### Method 1: Set Logging Behavior Block

Add a **Set logging behavior** block at the beginning of your flow:

- **Log behavior**: Enable or Disable
- Place it before any other blocks to capture the full execution path

### Method 2: Enable via API

Set the `CONTACTFLOW_LOGS` attribute using `UpdateContactFlowContent` or by setting a contact attribute in the flow:

```json
{
  "Key": "CONTACTFLOW_LOGS",
  "Value": "true"
}
```

### Instance-Level Default

You can also enable flow logging at the instance level in the Amazon Connect console under **Contact flows** settings. This enables logging for all flows in the instance.

---

## CloudWatch Log Group

Flow logs are written to the following CloudWatch log group:

```
/aws/connect/{instance-id}
```

This log group is created automatically when flow logging is first enabled. Each log stream within the group corresponds to a flow execution.

---

## Log Format

Each log entry is a JSON object with the following fields:

| Field | Description |
|-------|-------------|
| `ContactId` | Unique identifier for the contact |
| `ContactFlowId` | ARN of the contact flow |
| `ContactFlowName` | Human-readable flow name |
| `ContactFlowModuleId` | ARN of the flow module (if executing within a module) |
| `Action` | The block type that was executed |
| `Parameters` | Input parameters for the block |
| `ExternalResults` | Results from external calls (Lambda responses, etc.) |
| `Timestamp` | ISO 8601 timestamp of the log entry |

---

## Sample Log Entry

```json
{
  "ContactId": "abc12345-def6-7890-abcd-ef1234567890",
  "ContactFlowId": "arn:aws:connect:us-east-1:123456789012:instance/inst-id/contact-flow/flow-id",
  "ContactFlowName": "MainInboundFlow",
  "ContactFlowModuleId": null,
  "Action": "InvokeLambdaFunction",
  "Parameters": {
    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:LookupCustomer",
    "TimeLimit": "8000"
  },
  "ExternalResults": {
    "customerName": "Jane Smith",
    "accountStatus": "active",
    "tier": "premium"
  },
  "Timestamp": "2025-03-15T14:30:22.456Z"
}
```

---

## What Gets Logged

- **Block entry and exit**: Every block the contact passes through
- **Lambda invocations**: Function ARN, input parameters, and full response payload
- **Error branches taken**: When a block follows the Error branch, the reason is logged
- **Attribute values set**: When a "Set contact attributes" block runs, the key-value pairs appear in Parameters
- **Condition evaluations**: Which branch was taken in "Check contact attributes" blocks
- **Queue transfers**: Target queue ARN and transfer result
- **Flow module invocations**: Entry into and exit from reusable flow modules

## What Does NOT Get Logged

- **Sensitive customer input**: DTMF input captured by "Store customer input" blocks with encryption enabled is not logged in plaintext
- **Audio content**: Voice audio and recordings are not part of flow logs
- **Agent actions outside flows**: Agent desktop actions, hold/mute, after-contact work
- **Whisper flow details**: Whisper flows log at a reduced level

---

## PII Considerations

Contact attributes containing PII **will appear in flow logs**. If your flow sets attributes like customer name, phone number, or account number, those values are written to CloudWatch Logs in plaintext.

Mitigations:

- **Encrypt sensitive input**: Use the "Store customer input" block with encryption enabled for DTMF input containing PII (see `flows/encryption.md`)
- **Avoid storing PII in attributes**: Look up sensitive data in Lambda and return only non-sensitive identifiers
- **Set log retention policies**: Reduce the window during which PII is accessible in logs
- **Restrict log access**: Use IAM policies to limit who can read CloudWatch Logs for the Connect log group

---

## Log Retention

CloudWatch Logs retains flow logs **indefinitely** by default. This can lead to both cost accumulation and compliance concerns.

Set a retention policy in the CloudWatch console or via API:

```javascript
const { CloudWatchLogsClient, PutRetentionPolicyCommand } = require("@aws-sdk/client-cloudwatch-logs");

const client = new CloudWatchLogsClient({ region: "us-east-1" });

await client.send(new PutRetentionPolicyCommand({
  logGroupName: "/aws/connect/your-instance-id",
  retentionInDays: 90  // Options: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653
}));
```

---

## Troubleshooting with Logs

### Find Which Block a Contact Failed At

```
fields @timestamp, Action, Parameters, @message
| filter ContactId = "abc12345-def6-7890-abcd-ef1234567890"
| sort @timestamp asc
```

The last entry before the error or the entry with an Error branch action reveals where the flow failed.

### Trace Lambda Invocation Errors

```
fields @timestamp, Action, Parameters.FunctionArn, ExternalResults, @message
| filter Action = "InvokeLambdaFunction"
| filter @message like /Error/
| sort @timestamp desc
| limit 50
```

Cross-reference with the Lambda function's own CloudWatch log group (`/aws/lambda/{function-name}`) for the full error stack trace.

### Debug Attribute Values at Each Step

```
fields @timestamp, Action, Parameters
| filter ContactId = "abc12345-def6-7890-abcd-ef1234567890"
| filter Action = "SetAttributes" or Action = "CheckAttribute"
| sort @timestamp asc
```

This shows every attribute set or checked during the contact's flow execution, helping identify where an unexpected value was introduced.

### Filter by ContactId for End-to-End Trace

For a complete picture of a single contact's journey through the flow:

```
fields @timestamp, ContactFlowName, Action, Parameters, ExternalResults
| filter ContactId = "abc12345-def6-7890-abcd-ef1234567890"
| sort @timestamp asc
| limit 200
```

This produces a chronological trace of every block the contact traversed, including flow module transitions.

---

## Cost

CloudWatch Logs pricing applies to flow logs:

- **Ingestion**: Per GB of log data ingested
- **Storage**: Per GB-month of log data stored
- **Queries**: Logs Insights charges per GB of data scanned

High-volume instances (thousands of contacts per hour) can generate significant log volume. Set retention policies and consider sampling (enabling logging for a subset of flows) if cost is a concern.
