# Amazon Connect Testing Language Reference

**Version**: `2019-10-30`

The Testing Language is a JSON DSL for defining automated test cases for Amazon Connect contact flows. Tests simulate customer interactions and validate flow behavior without live calls.

## Structure

```
TestCase (JSON)
  ├── Version: "2019-10-30"
  ├── Metadata: { FlowId, FlowVersion }
  └── Observations[]
       ├── Identifier: unique ID
       ├── Event: { Type, Actor, Properties, MatchingCriteria }
       ├── Usage: { Type: "EXACTLY" }
       ├── Actions[]
       │    ├── Identifier: unique ID
       │    ├── Type: OverrideSystemBehavior | SendInstruction | Assert | TestControl
       │    ├── Parameters: { ... }
       │    └── Transitions: { NextAction }
       └── Transitions: { NextObservations[] }
```

## Top-Level Fields

### Version

Always `"2019-10-30"`:

```json
{
  "Version": "2019-10-30"
}
```

### Metadata

Identifies which flow to test:

```json
{
  "Metadata": {
    "FlowId": "arn:aws:connect:us-east-1:123456789012:instance/xxx/contact-flow/yyy",
    "FlowVersion": "1"
  }
}
```

### Observations

An ordered array of observation nodes. Each observation represents an expected event in the flow and the actions to take when that event occurs.

## Event Types

### TestInitiated

The entry point of the test. Always the first observation:

```json
{
  "Event": {
    "Type": "TestInitiated",
    "Actor": "System"
  }
}
```

### MessageReceived

An expected prompt/message from the flow to the customer:

```json
{
  "Event": {
    "Type": "MessageReceived",
    "Actor": "System",
    "Properties": {
      "ContentType": "text/plain"
    },
    "MatchingCriteria": {
      "Content": {
        "Similarity": {
          "Value": "Welcome to our support line. Press 1 for billing, press 2 for technical support.",
          "Threshold": 0.8
        }
      }
    }
  }
}
```

#### Similarity Matching

The `Similarity` matcher uses fuzzy matching to compare expected vs. actual prompts:

```json
{
  "Similarity": {
    "Value": "expected text content",
    "Threshold": 0.8
  }
}
```

- `Value` — the expected text content
- `Threshold` — similarity score between 0.0 and 1.0 (0.8 = 80% match required)

This allows tests to pass even when prompt text changes slightly (e.g., dynamic greetings, minor wording changes).

## Actors

| Actor | Description |
|---|---|
| `System` | The contact flow / Amazon Connect system |
| `Customer` | The simulated customer |
| `Agent` | The simulated agent |

## Usage

The `Usage` field controls how many times an observation can be matched:

```json
{
  "Usage": {
    "Type": "EXACTLY"
  }
}
```

Currently only `EXACTLY` is supported (the observation must be matched exactly once).

## Action Types

### OverrideSystemBehavior

Mock flow actions by substituting resources. This lets you control what the flow "sees" without needing real AWS resources.

```json
{
  "Identifier": "mock-hours",
  "Type": "OverrideSystemBehavior",
  "Parameters": {
    "ActionType": "CheckHoursOfOperation",
    "ResultOverride": {
      "Result": "InHours"
    }
  },
  "Transitions": {
    "NextAction": "send-dtmf"
  }
}
```

Common overrides:

| ActionType | ResultOverride | Description |
|---|---|---|
| `CheckHoursOfOperation` | `{ "Result": "InHours" }` or `{ "Result": "OutOfHours" }` | Mock business hours check |
| `InvokeLambdaFunction` | `{ "Result": "Success", "ExternalAttributes": {...} }` | Mock Lambda response |
| `GetCustomerInput` | `{ "Result": "Success" }` | Mock customer input collection |
| `TransferToQueue` | `{ "Result": "Success" }` | Mock queue transfer |
| `CheckContactAttributes` | `{ "Result": "Match" }` or `{ "Result": "NoMatch" }` | Mock attribute check |

### SendInstruction

Simulate customer input — DTMF tones, voice utterances, or chat text:

```json
{
  "Identifier": "press-1",
  "Type": "SendInstruction",
  "Parameters": {
    "InstructionType": "DTMF",
    "Value": "1"
  },
  "Transitions": {
    "NextAction": "assert-queue"
  }
}
```

Instruction types:

| InstructionType | Value | Description |
|---|---|---|
| `DTMF` | `"1"`, `"2"`, `"*"`, `"#"`, etc. | Simulate keypad press |
| `Utterance` | `"I need help with billing"` | Simulate voice input for Lex |
| `Text` | `"Hello, I need help"` | Simulate chat text input |

### Assert

Validate the current state of the contact at a specific point in the flow:

```json
{
  "Identifier": "check-queue",
  "Type": "Assert",
  "Parameters": {
    "Namespace": "$.Queue.Name",
    "Operator": "Equals",
    "Operand": "BillingQueue"
  },
  "Transitions": {
    "NextAction": "end-test"
  }
}
```

#### Namespace Paths

Assert can check any contact attribute namespace:

| Namespace Path | Description |
|---|---|
| `$.Queue.Name` | Current queue name |
| `$.Queue.ARN` | Current queue ARN |
| `$.Agent.FirstName` | Connected agent's first name |
| `$.Agent.LastName` | Connected agent's last name |
| `$.Agent.UserName` | Connected agent's username |
| `$.Attributes.{KEY}` | Contact attribute by key |
| `$.SystemEndpoint.Address` | Customer's phone number |
| `$.CustomerEndpoint.Address` | Customer's endpoint address |
| `$.Channel` | Contact channel (VOICE/CHAT/TASK) |
| `$.InitiationMethod` | How the contact was initiated |
| `$.SegmentAttributes.{KEY}` | Segment attribute by key |

#### Operators

| Operator | Description |
|---|---|
| `Equals` | Exact string match |
| `NotEquals` | String does not match |
| `Contains` | String contains substring |
| `GreaterThan` | Numeric greater than |
| `LessThan` | Numeric less than |
| `GreaterThanOrEqualTo` | Numeric >= |
| `LessThanOrEqualTo` | Numeric <= |

### TestControl

Control the test execution flow:

```json
{
  "Identifier": "end",
  "Type": "TestControl",
  "Parameters": {
    "Command": "EndTest"
  }
}
```

Commands:

| Command | Description |
|---|---|
| `EndTest` | End the test case (pass if all assertions passed) |

## Action Transitions

Each action has a `Transitions` object that specifies the next action to execute:

```json
{
  "Transitions": {
    "NextAction": "action-identifier"
  }
}
```

## Observation Transitions

Each observation has a `Transitions` object that specifies which observations can follow:

```json
{
  "Transitions": {
    "NextObservations": ["observation-2", "observation-3"]
  }
}
```

## Complete Example

This test case validates an IVR flow that:
1. Checks business hours
2. Plays a welcome message
3. Collects DTMF input (1 for billing)
4. Routes to the billing queue

```json
{
  "Version": "2019-10-30",
  "Metadata": {
    "FlowId": "arn:aws:connect:us-east-1:123456789012:instance/xxx/contact-flow/main-ivr",
    "FlowVersion": "3"
  },
  "Observations": [
    {
      "Identifier": "test-start",
      "Event": {
        "Type": "TestInitiated",
        "Actor": "System"
      },
      "Usage": { "Type": "EXACTLY" },
      "Actions": [
        {
          "Identifier": "mock-hours-check",
          "Type": "OverrideSystemBehavior",
          "Parameters": {
            "ActionType": "CheckHoursOfOperation",
            "ResultOverride": {
              "Result": "InHours"
            }
          },
          "Transitions": { "NextAction": null }
        }
      ],
      "Transitions": {
        "NextObservations": ["welcome-prompt"]
      }
    },
    {
      "Identifier": "welcome-prompt",
      "Event": {
        "Type": "MessageReceived",
        "Actor": "System",
        "Properties": {
          "ContentType": "text/plain"
        },
        "MatchingCriteria": {
          "Content": {
            "Similarity": {
              "Value": "Welcome to our support line. Press 1 for billing, press 2 for technical support, or press 3 for all other inquiries.",
              "Threshold": 0.75
            }
          }
        }
      },
      "Usage": { "Type": "EXACTLY" },
      "Actions": [
        {
          "Identifier": "press-1-for-billing",
          "Type": "SendInstruction",
          "Parameters": {
            "InstructionType": "DTMF",
            "Value": "1"
          },
          "Transitions": { "NextAction": null }
        }
      ],
      "Transitions": {
        "NextObservations": ["billing-confirmation"]
      }
    },
    {
      "Identifier": "billing-confirmation",
      "Event": {
        "Type": "MessageReceived",
        "Actor": "System",
        "Properties": {
          "ContentType": "text/plain"
        },
        "MatchingCriteria": {
          "Content": {
            "Similarity": {
              "Value": "Transferring you to our billing department. Please hold.",
              "Threshold": 0.7
            }
          }
        }
      },
      "Usage": { "Type": "EXACTLY" },
      "Actions": [
        {
          "Identifier": "assert-billing-queue",
          "Type": "Assert",
          "Parameters": {
            "Namespace": "$.Queue.Name",
            "Operator": "Equals",
            "Operand": "BillingQueue"
          },
          "Transitions": {
            "NextAction": "assert-channel"
          }
        },
        {
          "Identifier": "assert-channel",
          "Type": "Assert",
          "Parameters": {
            "Namespace": "$.Channel",
            "Operator": "Equals",
            "Operand": "VOICE"
          },
          "Transitions": {
            "NextAction": "end-test"
          }
        },
        {
          "Identifier": "end-test",
          "Type": "TestControl",
          "Parameters": {
            "Command": "EndTest"
          }
        }
      ],
      "Transitions": {
        "NextObservations": []
      }
    }
  ]
}
```

## Running Tests via the SDK

```typescript
import { ConnectClient, StartContactFlowTestCommand, GetContactFlowTestResultCommand } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

// Start a test
const testRun = await client.send(new StartContactFlowTestCommand({
  InstanceId: 'instance-xxx',
  ContactFlowId: 'flow-xxx',
  TestCases: [
    {
      Name: 'billing-routing-test',
      TestCaseDefinition: JSON.stringify(testCaseJson),
    },
  ],
}));

console.log('Test Run ID:', testRun.TestRunId);

// Poll for results (in production, use EventBridge or Step Functions)
const result = await client.send(new GetContactFlowTestResultCommand({
  InstanceId: 'instance-xxx',
  TestRunId: testRun.TestRunId!,
}));

for (const testCase of result.TestCaseResults ?? []) {
  console.log(`${testCase.Name}: ${testCase.Status}`); // PASSED, FAILED, ERROR
  if (testCase.FailureDetails) {
    console.log('  Failure:', testCase.FailureDetails.Reason);
    console.log('  At observation:', testCase.FailureDetails.ObservationId);
  }
}
```

## Best Practices

1. **Use Similarity matching with reasonable thresholds** — prompts may change slightly between deployments. A threshold of 0.7-0.8 provides good balance.

2. **Mock external dependencies** — always use `OverrideSystemBehavior` for Lambda, hours-of-operation, and external lookups so tests are deterministic.

3. **Test both paths** — create separate test cases for InHours vs. OutOfHours, valid vs. invalid input, success vs. error Lambda responses.

4. **Assert queue assignment** — the most common validation is confirming the contact reaches the correct queue. Always assert `$.Queue.Name` or `$.Queue.ARN`.

5. **Keep tests focused** — each test case should validate one path through the flow. Combine multiple test cases in a single `StartContactFlowTest` call for comprehensive coverage.
