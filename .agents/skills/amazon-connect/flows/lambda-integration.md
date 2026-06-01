# Lambda Integration in Amazon Connect Flows

## Overview

Amazon Connect flows can invoke AWS Lambda functions to perform data lookups, business logic, API calls, and integrations with external systems. The `Invoke AWS Lambda function` block (in the Integrate group) calls a Lambda function synchronously and makes the response available as contact attributes.

## Prerequisites

Before using Lambda in a flow, you must register the Lambda function with your Connect instance:

1. Go to Amazon Connect console > Your instance > Flows (under AWS Lambda section).
2. Use the **Function** dropdown to select the Lambda function to add.
3. Choose **Add Lambda Function**. Confirm the ARN is added under Lambda Functions.

The dropdown only lists functions in the same Region as your instance. To use a Lambda in a different Region or account:
- In the `Invoke AWS Lambda function` block, under **Select a function**, enter the Lambda ARN directly.
- Set up a resource-based policy on the Lambda:
  - Principal: `connect.amazonaws.com`
  - Source account: the account your instance is in
  - Source ARN: the ARN of your instance

Alternatively, use the `AssociateLambdaFunction` API.

## The Invoke AWS Lambda Function Block

### Configuration

- **Function ARN**: Select from registered functions, or enter an ARN manually (for cross-region/cross-account).
- **Timeout**: Maximum **8 seconds**. If the Lambda does not respond within the timeout, the Error branch is taken.
- **Response validation**: Choose **STRING_MAP** or **JSON** format for the response.
- **Function input parameters**: Key-value pairs sent as additional parameters alongside the standard event payload. Parameters can be:
  - **Set manually**: Static values.
  - **Set dynamically**: Reference contact attributes via JSONPath.
  - **JSON format**: Supports primitive types and nested JSON objects.

### Branches

- **Success**: Lambda returned a valid response.
- **Error**: Lambda timed out, threw an error, returned invalid format, or response exceeded 32 KB.

## Event Payload

When Connect invokes your Lambda function, it sends the following JSON event:

```json
{
  "Details": {
    "ContactData": {
      "Attributes": {
        "exampleAttributeKey1": "exampleAttributeValue1"
      },
      "Channel": "VOICE",
      "ContactId": "4a573372-1f28-4e26-b97b-XXXXXXXXXXX",
      "CustomerEndpoint": {
        "Address": "+1234567890",
        "Type": "TELEPHONE_NUMBER"
      },
      "CustomerId": "someCustomerId",
      "Description": "someDescription",
      "InitialContactId": "4a573372-1f28-4e26-b97b-XXXXXXXXXXX",
      "InitiationMethod": "INBOUND | OUTBOUND | TRANSFER | CALLBACK",
      "InstanceARN": "arn:aws:connect:aws-region:1234567890:instance/c8c0e68d-2200-4265-82c0-XXXXXXXXXX",
      "LanguageCode": "en-US",
      "MediaStreams": {
        "Customer": {
          "Audio": {
            "StreamARN": "arn:aws:kinesisvideo:...",
            "StartTimestamp": "1571360125131",
            "StopTimestamp": "1571360126131",
            "StartFragmentNumber": "100"
          }
        }
      },
      "Name": "ContactFlowEvent",
      "PreviousContactId": "4a573372-1f28-4e26-b97b-XXXXXXXXXXX",
      "Queue": {
        "ARN": "arn:aws:connect:...:instance/.../queue/...",
        "Name": "BasicQueue",
        "OutboundCallerId": {
          "Address": "+12345678903",
          "Type": "TELEPHONE_NUMBER"
        }
      },
      "References": {
        "key1": {
          "Type": "url",
          "Value": "urlvalue"
        }
      },
      "SystemEndpoint": {
        "Address": "+1234567890",
        "Type": "TELEPHONE_NUMBER"
      }
    },
    "Parameters": {
      "param1": "value1",
      "param2": "value2"
    }
  },
  "Name": "ContactFlowEvent"
}
```

### ContactData Fields

| Field | Description |
|-------|-------------|
| `Attributes` | User-defined contact attributes set earlier in the flow. May be empty. |
| `Channel` | `VOICE`, `CHAT`, or `TASK`. |
| `ContactId` | Unique ID for this contact. |
| `CustomerEndpoint.Address` | Customer's phone number (E.164) or chat endpoint. |
| `CustomerEndpoint.Type` | `TELEPHONE_NUMBER` or `CHAT`. |
| `CustomerId` | Customer identification number (if set). |
| `Description` | Task description (if applicable). |
| `InitialContactId` | The ID of the original contact (same as ContactId for initial contacts; differs for transfers). |
| `InitiationMethod` | `INBOUND`, `OUTBOUND`, `TRANSFER`, `CALLBACK`, `QUEUE_TRANSFER`, `API`. |
| `InstanceARN` | ARN of the Connect instance. |
| `LanguageCode` | Language/locale code (e.g., `en-US`). |
| `MediaStreams` | Kinesis Video Stream details if media streaming is active. |
| `Name` | Contact flow event name (`ContactFlowEvent`). |
| `PreviousContactId` | ID of previous contact in transfer chain. |
| `Queue` | Current queue (ARN, Name, OutboundCallerId). Null if not yet queued. |
| `References` | References attached to the contact (key-value with type). |
| `SystemEndpoint.Address` | The phone number the customer dialed (DID/TFN). |

### Parameters

The `Parameters` object contains key-value pairs configured in the `Invoke AWS Lambda function` block's "Function input parameters" section. These support JSON format including nested objects:

```json
{
  "Name": "Jane",
  "Age": 10,
  "isEnrolledInSchool": true,
  "hobbies": {
    "books": ["book1", "book2"],
    "art": ["art1", "art2"]
  }
}
```

## Response Format

Lambda must return one of two formats, configured in the block's **Response validation** setting.

### STRING_MAP (Flat Key-Value)

```javascript
exports.handler = async (event) => {
  const phoneNumber = event.Details.ContactData.CustomerEndpoint.Address;
  const customer = await lookupCustomer(phoneNumber);

  // Return flat key-value pairs (all values must be strings)
  return {
    customerName: customer.name,
    accountId: customer.accountId,
    tier: customer.tier,
    balance: String(customer.balance)
  };
};
```

All values must be strings. Numbers and booleans must be converted to strings. Output returned must be a flat object of key/value pairs with values that include only alphanumeric, dash, and underscore characters.

### JSON (Nested)

```javascript
exports.handler = async (event) => {
  const phoneNumber = event.Details.ContactData.CustomerEndpoint.Address;
  const customer = await lookupCustomer(phoneNumber);

  // Return nested JSON
  return {
    Name: {
      First: "John",
      Last: "Doe"
    },
    AccountId: "a12345689",
    OrderIds: ["x123", "y123"]
  };
};
```

Nested values are accessible via JSONPath: `$.External.Name.First`, `$.External.OrderIds[0]`.

**Note**: Referencing arrays is not supported directly in flow blocks. Arrays can only be used in another Lambda function.

### Python Example

```python
def lambda_handler(event, context):
    phone = event['Details']['ContactData']['CustomerEndpoint']['Address']
    customer_account_id = get_account_id_by_phone(phone)
    customer_balance = get_balance_by_account_id(customer_account_id)

    return {
        "AccountId": customer_account_id,
        "Balance": "$%s" % customer_balance
    }
```

### Response Limits

- **Maximum response size: 32 KB** of UTF-8 data. If the response exceeds this, the Error branch is taken.
- All top-level keys in STRING_MAP responses must be strings.
- The response must be valid JSON.

## Timeout and Retry Behavior

### Timeout

- **Maximum timeout per invocation: 8 seconds.** Configure in the block settings.
- **Total Lambda chain limit: 20 seconds.** If you invoke multiple Lambda functions in sequence within a single flow, the cumulative execution time must not exceed 20 seconds. After 20 seconds, subsequent Lambda invocations will fail.

### Retry

- Connect automatically retries Lambda invocations up to **3 times** on:
  - Throttling (429 / `TooManyRequestsException`)
  - Server errors (500-series)
- When a synchronous invocation returns an error, Connect retries up to 3 times, for a maximum of 8 seconds.
- At that point, the flow progresses down the Error branch.
- Retries do NOT occur on client errors (4xx other than 429) or on responses that are simply too large.

## Accessing Lambda Response in the Flow

### Direct Access (External Attributes)

After a successful Lambda invocation, response values are available as External attributes:

- `$.External.customerName`
- `$.External.accountId`
- `$.External.Name.First` (for nested JSON responses)

Use these in:
- `Check contact attributes` blocks for branching
- `Play prompt` blocks for dynamic TTS: "Hello, $.External.customerName"
- Other Lambda invocations as parameters

External attributes reference the most recently invoked Lambda. To use a response before another Lambda is invoked, save the values as contact attributes or pass them as parameters.

### Saving to Contact Attributes

Use the `Set contact attributes` block to copy External attributes to user-defined contact attributes:

- Source type: External
- Source attribute: `customerName`
- Destination key: `customerName`

This is recommended because:
- External attributes are overwritten by the next Lambda call.
- User-defined attributes persist in contact records.
- User-defined attributes are available in the CCP for screenpop.

### Parsing the Event in Lambda

#### Node.js

```javascript
exports.handler = function(event, context, callback) {
  // Access parameter from Invoke AWS Lambda function block
  let parameter1 = event['Details']['Parameters']['exampleParameterKey1'];

  // Access attribute from Set contact attributes block
  let attribute1 = event['Details']['ContactData']['Attributes']['exampleAttributeKey1'];

  // Access customer phone number from default data
  let phone = event['Details']['ContactData']['CustomerEndpoint']['Address'];

  // Apply business logic
  // ...
};
```

#### Python

```python
def lambda_handler(event, context):
    parameter1 = event['Details']['Parameters']['exampleParameterKey1']
    attribute1 = event['Details']['ContactData']['Attributes']['exampleAttributeKey1']
    phone = event['Details']['ContactData']['CustomerEndpoint']['Address']
    # Apply business logic
```

## Best Practices

### Play a Prompt Between Lambda Functions

If you chain multiple Lambda invocations, insert a `Play prompt` block between them:
- Provides feedback to the customer ("One moment while I look that up...")
- Helps stay within the 20-second total chain limit by giving each Lambda its own window.
- Prevents silence on the line during processing.
- By breaking up a chain with Play prompt blocks, you can invoke functions lasting longer than 20 seconds total.

### Error Handling

Always connect the Error branch to a meaningful fallback:

```javascript
exports.handler = async (event) => {
  try {
    const result = await riskyOperation();
    return { status: "success", data: result };
  } catch (error) {
    console.error("Lambda error:", error);
    // Return an error indicator instead of throwing
    // This takes the Success branch but lets you branch on status
    return { status: "error", errorMessage: error.message };
  }
};
```

Alternatively, throw an error to trigger the Error branch:

```javascript
exports.handler = async (event) => {
  const result = await riskyOperation();
  if (!result) {
    throw new Error("Customer not found");
  }
  return { customerName: result.name };
};
```

### Keep Lambda Functions Fast

- Connect flows are real-time voice interactions. Every second of Lambda execution is a second of silence (or prompt) for the customer.
- Aim for sub-1-second Lambda execution.
- Use provisioned concurrency for critical Lambdas to avoid cold starts.
- Cache frequently accessed data (DynamoDB DAX, ElastiCache, or in-memory caching for the Lambda execution environment).

### Logging

Log the incoming event for debugging:

```javascript
exports.handler = async (event) => {
  console.log("Connect event:", JSON.stringify(event, null, 2));

  const contactId = event.Details.ContactData.ContactId;
  const channel = event.Details.ContactData.Channel;
  const callerNumber = event.Details.ContactData.CustomerEndpoint.Address;
  const attributes = event.Details.ContactData.Attributes;
  const params = event.Details.Parameters;

  // Your logic here

  return { status: "ok" };
};
```

### Input Validation

Always validate incoming data:

```javascript
exports.handler = async (event) => {
  const contactData = event?.Details?.ContactData;
  if (!contactData) {
    throw new Error("Missing ContactData");
  }

  const phoneNumber = contactData.CustomerEndpoint?.Address;
  if (!phoneNumber) {
    return { status: "error", reason: "no_phone_number" };
  }

  // Continue with validated data
};
```

## Common Patterns

### Customer Lookup

```javascript
const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const { DynamoDBDocumentClient, QueryCommand } = require("@aws-sdk/lib-dynamodb");

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  const phoneNumber = event.Details.ContactData.CustomerEndpoint.Address;

  const result = await docClient.send(new QueryCommand({
    TableName: "Customers",
    IndexName: "phone-index",
    KeyConditionExpression: "phoneNumber = :phone",
    ExpressionAttributeValues: { ":phone": phoneNumber }
  }));

  if (result.Items && result.Items.length > 0) {
    const customer = result.Items[0];
    return {
      found: "true",
      customerName: customer.name,
      accountId: customer.accountId,
      tier: customer.tier || "standard"
    };
  }

  return { found: "false" };
};
```

### Hours Override Check

```javascript
const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const { DynamoDBDocumentClient, GetCommand } = require("@aws-sdk/lib-dynamodb");

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

exports.handler = async (event) => {
  const result = await docClient.send(new GetCommand({
    TableName: "SystemConfig",
    Key: { configKey: "hoursOverride" }
  }));

  const override = result.Item;
  if (override && override.active) {
    return {
      overrideActive: "true",
      message: override.message || "We are currently closed for a scheduled maintenance."
    };
  }

  return { overrideActive: "false" };
};
```

### CRM Integration

```javascript
exports.handler = async (event) => {
  const phoneNumber = event.Details.ContactData.CustomerEndpoint.Address;
  const contactId = event.Details.ContactData.ContactId;

  const response = await fetch("https://api.crm.example.com/contacts/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${process.env.CRM_API_KEY}`
    },
    body: JSON.stringify({ phone: phoneNumber })
  });

  if (!response.ok) {
    return { found: "false" };
  }

  const data = await response.json();

  if (data.contacts && data.contacts.length > 0) {
    const contact = data.contacts[0];
    return {
      found: "true",
      crmId: contact.id,
      customerName: `${contact.firstName} ${contact.lastName}`,
      openCases: String(contact.openCaseCount),
      lastInteraction: contact.lastInteractionDate
    };
  }

  return { found: "false" };
};
```

### Tutorial: End-to-End Lambda Integration

A complete tutorial flow demonstrating Lambda integration:

1. **Set contact attributes**: Set `companyName` to a static value.
2. **Play prompt**: Greet the customer using TTS with the company name attribute.
3. **Invoke Lambda**: Pass `companyName` as a parameter. Lambda returns `customerBalance` and `websiteUrl`.
4. **Set contact attributes**: Copy `$.External.customerBalance` to `MyBalance` and `$.External.websiteUrl` to `MyURL`.
5. **Play prompt**: Read back the balance and website URL using SSML.
6. **Disconnect**: End the call.

Lambda code for the tutorial:

```javascript
exports.handler = async (event, context, callback) => {
  const customerNumber = event.Details.ContactData.CustomerEndpoint.Address;
  const companyName = event.Details.Parameters.companyName;

  const balance = await fetchBalance(customerNumber, companyName);
  const support = await fetchSupportUrl(companyName);

  const resultMap = {
    customerBalance: balance,
    websiteUrl: support
  };
  callback(null, resultMap);
};
```

## Lambda Permissions

### Resource-Based Policy

When you add a Lambda to your Connect instance via the console, Connect automatically adds a resource-based policy allowing invocation. For manual setup:

```
Principal: connect.amazonaws.com
Source Account: <your-account-id>
Source ARN: <your-connect-instance-arn>
Action: lambda:InvokeFunction
```

Use the AWS CLI `add-permission` command for cross-region or cross-account setups.

### Lambda Execution Role

The Lambda function's execution role needs permissions for whatever resources it accesses (DynamoDB, S3, Connect APIs, etc.). This is standard Lambda IAM configuration, not Connect-specific.

## Limits Summary

| Limit | Value |
|-------|-------|
| Maximum timeout per invocation | 8 seconds |
| Maximum cumulative Lambda chain duration | 20 seconds |
| Maximum response size | 32 KB (UTF-8) |
| Retry attempts on throttle/5xx | 3 |
| Response format | STRING_MAP or JSON |
| Concurrent Lambda limits | Standard AWS Lambda service quotas |
| Cross-region Lambda | Supported (enter ARN directly, configure resource-based policy) |
| Cross-account Lambda | Supported (enter ARN directly, configure resource-based policy) |
