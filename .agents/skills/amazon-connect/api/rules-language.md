# Amazon Connect Rules Function Language Reference

**Version**: `2022-11-25`

The Rules Function Language is a JSON DSL used to define programmatic conditions for Amazon Connect automation rules. Rules are created via the `CreateRule` API and trigger actions based on contact analytics, metrics, evaluations, and case events.

## Structure

```
RuleFunction (JSON string)
  └── Top-level Operator (AND / OR)
       └── Operands[] (array of conditions)
            └── Each operand: Operator + Operands (nested)
                 └── Leaf: ComparisonValue path + comparison value
```

Every rule function is a single JSON object with a top-level `AND` or `OR` operator containing an array of operand conditions.

## Operators

| Operator | Description | Leaf/Branch |
|---|---|---|
| `AND` | All operands must be true | Branch |
| `OR` | At least one operand must be true | Branch |
| `CONTAINS_ANY` | Value contains any of the specified strings | Leaf |
| `EQUALS` | Value equals the specified string | Leaf |
| `NumberLessOrEqualTo` | Numeric value <= threshold | Leaf |
| `NumberGreaterOrEqualTo` | Numeric value >= threshold | Leaf |

## Trigger Event Sources

Rules are triggered by one of 12 event sources:

| Event Source | Description |
|---|---|
| `OnPostCallAnalysisAvailable` | Contact Lens post-call analysis is complete |
| `OnRealTimeCallAnalysisAvailable` | Contact Lens real-time analysis segment available |
| `OnPostChatAnalysisAvailable` | Contact Lens post-chat analysis is complete |
| `OnEmailAnalysisAvailable` | Contact Lens email analysis is complete |
| `OnMetricDataUpdate` | A metric threshold is breached |
| `OnContactEvaluationSubmit` | An evaluation form is submitted |
| `OnCaseCreate` | A case is created |
| `OnCaseUpdate` | A case field is updated |
| `OnSlaBreach` | An SLA is breached |
| `OnZendeskTicketCreate` | A Zendesk ticket is created (via integration) |
| `OnZendeskTicketStatusUpdate` | A Zendesk ticket status changes |
| `OnSalesforceCaseCreate` | A Salesforce case is created (via integration) |

## ComparisonValue Paths

### Post-Call Analysis Paths (20+)

#### Transcript Matching

| Path | Type | Description |
|---|---|---|
| `$.ContactLens.PostCall.ExactMatch.Transcript` | String | Exact string match in transcript |
| `$.ContactLens.PostCall.SemanticMatch.Transcript` | String | Semantic/meaning-based match in transcript |
| `$.ContactLens.PostCall.SemanticMatch.Phrase` | String | Semantic match against a specific phrase |
| `$.ContactLens.PostCall.PatternMatch.Transcript` | PatternMatch | Pattern-based match (see PatternMatch operands) |

#### Sentiment

| Path | Type | Description |
|---|---|---|
| `$.ContactLens.PostCall.Sentiment.State` | String | Overall sentiment: `POSITIVE`, `NEGATIVE`, `NEUTRAL`, `MIXED` |
| `$.ContactLens.PostCall.Sentiment.OverallScore` | Number | Overall sentiment score (-5.0 to 5.0) |
| `$.ContactLens.PostCall.Sentiment.Score.Beginning` | Number | Sentiment score for the first quarter |
| `$.ContactLens.PostCall.Sentiment.Score.End` | Number | Sentiment score for the last quarter |

#### Talk Metrics

| Path | Type | Description |
|---|---|---|
| `$.ContactLens.PostCall.NonTalkTime.TotalTimeSecs` | Number | Total silence duration in seconds |
| `$.ContactLens.PostCall.NonTalkTime.LongestTimeSecs` | Number | Longest single silence period |
| `$.ContactLens.PostCall.Interruptions.Instances` | Number | Number of interruption instances |
| `$.ContactLens.PostCall.TalkTime.TotalTimeSecs` | Number | Total talk time in seconds |
| `$.ContactLens.PostCall.Loudness.HighestLoudnessScore` | Number | Peak loudness score |

#### Agent Metrics

| Path | Type | Description |
|---|---|---|
| `$.ContactLens.PostCall.Agent.CustomerHoldDurationSecs` | Number | Total hold duration |
| `$.ContactLens.PostCall.Agent.LongestHoldDurationSecs` | Number | Longest single hold |
| `$.ContactLens.PostCall.Agent.NumberOfHolds` | Number | Number of hold events |
| `$.ContactLens.PostCall.Agent.AgentInteractionDurationSecs` | Number | Agent interaction duration |
| `$.ContactLens.PostCall.Agent.AfterContactWorkDurationSecs` | Number | ACW duration |
| `$.ContactLens.PostCall.Agent.NonTalkTimePct` | Number | Percentage of non-talk time |
| `$.ContactLens.PostCall.Agent.CustomerHoldDurationPct` | Number | Hold time as percentage of call |
| `$.ContactLens.PostCall.Agent.RoutingProfile.ARN` | String | Agent's routing profile ARN |
| `$.ContactLens.PostCall.Agent.HierarchyGroup.ARN` | String | Agent's hierarchy group ARN |
| `$.ContactLens.PostCall.Agent.AgentId` | String | Agent user ID |

#### Queue & Contact Metadata

| Path | Type | Description |
|---|---|---|
| `$.ContactLens.PostCall.Queue.QueueId` | String | Queue ID the contact was routed to |
| `$.ContactLens.PostCall.InitiationMethod` | String | How the contact was initiated |
| `$.ContactLens.PostCall.DisconnectReason` | String | Why the contact disconnected |
| `$.ContactLens.PostCall.PotentialDisconnectIssue` | String | Potential disconnect issue detected |

#### Dynamic Attributes

| Path | Type | Description |
|---|---|---|
| `$.ContactLens.PostCall.ContactAttribute.{KEY}` | String | Contact attribute by key name |
| `$.ContactLens.PostCall.SegmentAttributes.UserDefined.{KEY}` | String | User-defined segment attribute |
| `$.ContactLens.PostCall.AiAgent.IdWithVersion` | String | AI agent ID and version |

## FilterClause

Filters narrow the scope of transcript analysis:

### ParticipantRole

Filter transcript matching to a specific participant:

```json
{
  "ParticipantRole": "CUSTOMER"
}
```

Values: `CUSTOMER`, `AGENT`, `ANY`

### PostCallContactPeriodSeconds

Limit analysis to the first or last N seconds of the call:

```json
{
  "PostCallContactPeriodSeconds": {
    "First": 60
  }
}
```

or

```json
{
  "PostCallContactPeriodSeconds": {
    "Last": 120
  }
}
```

### PatternMatchLanguageFilter

Restrict pattern matching to specific languages (11 supported):

```json
{
  "PatternMatchLanguageFilter": ["en-US", "es-US"]
}
```

Supported languages: `en-US`, `en-GB`, `en-AU`, `en-IN`, `es-US`, `fr-CA`, `fr-FR`, `de-DE`, `it-IT`, `ja-JP`, `pt-BR`

## PatternMatch Operands

PatternMatch supports four operand types:

### PLAIN

Simple string match:

```json
{
  "Operator": "CONTAINS_ANY",
  "Operands": [
    {
      "Type": "PLAIN",
      "Value": "cancel my account"
    }
  ]
}
```

### LIST

Array of strings (any match triggers):

```json
{
  "Operator": "CONTAINS_ANY",
  "Operands": [
    {
      "Type": "LIST",
      "Value": [
        { "Type": "PLAIN", "Value": "cancel" },
        { "Type": "PLAIN", "Value": "close my account" },
        { "Type": "PLAIN", "Value": "terminate service" }
      ]
    }
  ]
}
```

### PROXIMITY

Words within a specified distance of each other:

```json
{
  "Operator": "CONTAINS_ANY",
  "Operands": [
    {
      "Type": "PROXIMITY",
      "Value": {
        "Distance": 5,
        "IsWithin": true
      }
    }
  ]
}
```

- `Distance` — maximum number of words between the target words
- `IsWithin` — `true` if words must be within distance, `false` if they must be farther apart

### NUMERICAL

Numeric comparison within transcript:

```json
{
  "Operator": "CONTAINS_ANY",
  "Operands": [
    {
      "Type": "NUMERICAL",
      "Value": {
        "Decimal": 100.0
      }
    }
  ]
}
```

## Negate Flag

Any condition can be negated with the `Negate` flag:

```json
{
  "Operator": "CONTAINS_ANY",
  "Operands": [...],
  "Negate": true
}
```

This inverts the condition — true becomes false and vice versa.

## Complete Example

This rule triggers on post-call analysis when:
1. The customer mentioned "cancel" or "close account" AND
2. The customer sentiment score at the end was negative AND
3. The call had more than 2 holds

```json
{
  "Version": "2022-11-25",
  "Operator": "AND",
  "Operands": [
    {
      "Operator": "CONTAINS_ANY",
      "ComparisonValue": "$.ContactLens.PostCall.SemanticMatch.Transcript",
      "Operands": [
        { "Type": "PLAIN", "Value": "cancel my account" },
        { "Type": "PLAIN", "Value": "close my account" },
        { "Type": "PLAIN", "Value": "terminate my service" }
      ],
      "FilterClause": {
        "ParticipantRole": "CUSTOMER",
        "PostCallContactPeriodSeconds": {
          "Last": 300
        }
      }
    },
    {
      "Operator": "NumberLessOrEqualTo",
      "ComparisonValue": "$.ContactLens.PostCall.Sentiment.Score.End",
      "Operands": [-2.0]
    },
    {
      "Operator": "NumberGreaterOrEqualTo",
      "ComparisonValue": "$.ContactLens.PostCall.Agent.NumberOfHolds",
      "Operands": [3]
    }
  ]
}
```

## Using Rules via the SDK

```typescript
import { ConnectClient, CreateRuleCommand } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

await client.send(new CreateRuleCommand({
  InstanceId: 'instance-xxx',
  Name: 'churn-risk-detection',
  TriggerEventSource: {
    EventSourceName: 'OnPostCallAnalysisAvailable',
  },
  Function: JSON.stringify({
    Version: '2022-11-25',
    Operator: 'AND',
    Operands: [
      {
        Operator: 'CONTAINS_ANY',
        ComparisonValue: '$.ContactLens.PostCall.SemanticMatch.Transcript',
        Operands: [
          { Type: 'PLAIN', Value: 'cancel my account' },
          { Type: 'PLAIN', Value: 'switching to competitor' },
        ],
        FilterClause: {
          ParticipantRole: 'CUSTOMER',
        },
      },
      {
        Operator: 'NumberLessOrEqualTo',
        ComparisonValue: '$.ContactLens.PostCall.Sentiment.OverallScore',
        Operands: [-1.0],
      },
    ],
  }),
  Actions: [
    {
      ActionType: 'CREATE_TASK',
      CreateTaskAction: {
        Name: 'Churn Risk Follow-up',
        Description: 'Customer expressed intent to cancel with negative sentiment',
        ContactFlowId: 'flow-xxx',
      },
    },
    {
      ActionType: 'SEND_NOTIFICATION',
      SendNotificationAction: {
        DeliveryMethod: 'EMAIL',
        Subject: 'Churn Risk Alert',
        Content: 'A customer expressed cancellation intent. Review the contact.',
        ContentType: 'PLAIN_TEXT',
        Recipient: {
          UserTags: { Department: 'Retention' },
        },
      },
    },
  ],
  PublishStatus: 'PUBLISHED',
}));
```

## Rule Action Types

Rules can trigger these action types:

| Action Type | Description |
|---|---|
| `ASSIGN_CONTACT_CATEGORY` | Assign a category label to the contact |
| `CREATE_TASK` | Create a follow-up task contact |
| `CREATE_CASE` | Create a case in Amazon Connect Cases |
| `UPDATE_CASE` | Update fields on an existing case |
| `SEND_NOTIFICATION` | Send email/push notification |
| `GENERATE_EVENT_BRIDGE_EVENT` | Emit an EventBridge event |
| `END_ASSOCIATED_TASKS` | End tasks associated with the contact |
| `SUBMIT_AUTO_EVALUATION` | Auto-submit an evaluation form |
| `ASSIGN_SLA` | Assigns an SLA definition to a case. Parameters: `SlaId`. |
