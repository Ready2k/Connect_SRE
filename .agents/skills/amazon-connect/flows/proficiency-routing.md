# Proficiency-Based Routing

Route contacts to agents based on skill proficiencies (language, product expertise, etc.) using a step-by-step waterfall that progressively relaxes requirements.

## Setup Steps

1. **Create predefined attributes** — e.g., `Technology` with values like `AWS DynamoDB`, or use built-in `Connect:Language` (128 language values)
2. **Assign proficiencies to agents** — associate predefined attributes + proficiency level (1–5) per agent
3. **Set routing criteria** — use the `Set routing criteria` flow block (manual or dynamic via Lambda)
4. **Transfer to queue** — `Transfer to queue` block activates the routing criteria

## How It Works

When a contact enters a queue, Connect activates routing step 1:

1. Only agents matching the active step's requirements can be offered the contact
2. If no match is found before the step's expiration timer, Connect moves to the next step
3. Steps progressively relax requirements to widen the agent pool
4. When **all steps expire**, the contact falls back to longest-available agent in the queue
5. If a step has no expiration (`Never Expire`), it runs indefinitely — use for compliance/regulatory requirements

## Routing Criteria Structure

### Operators

| Operator | Usage |
|----------|-------|
| `AND` | Up to 8 attributes per AND condition |
| `OR` | Up to 3 OR conditions per step (dynamic only) |
| `NOT` | Exclude agents with specific proficiencies (dynamic only) |
| `>=` | Minimum proficiency level |
| `Range` | Min–max proficiency range (e.g., 1–3) |

- OR must be at the top level — you can nest AND inside OR, but not OR inside AND
- Cannot use the same attribute more than once in an expression (e.g., `connect:English(1-3) AND connect:English(5-5)` is invalid)

### Limits

- Max 8 attributes per AND condition
- Max 3 OR conditions per step
- Max 10 preferred agents per step
- Proficiency levels: 1–5
- Only `>=` comparison or `Range` (min/max)
- Unlimited routing criteria changes per contact (only latest 3 stored on contact record)

## Setting Routing Criteria

### Option 1: Manual (Flow Block UI)

Pick predefined attribute + value + proficiency level from dropdowns. Values can use JSONPath for dynamic resolution (e.g., `$.External.language`).

### Option 2: Dynamic (Lambda → JSON)

Invoke Lambda → return JSON → reference via `Set routing criteria` block with namespace `External` and key matching the Lambda response key.

### Lambda JSON Schema — AND Expression

```javascript
export const handler = async (event) => {
  return {
    MyRoutingCriteria: {
      Steps: [
        {
          Expression: {
            AndExpression: [
              {
                AttributeCondition: {
                  Name: "Language",
                  Value: "English",
                  ProficiencyLevel: 4,
                  ComparisonOperator: "NumberGreaterOrEqualTo",
                },
              },
              {
                AttributeCondition: {
                  Name: "Technology",
                  Value: "AWS Kinesis",
                  ProficiencyLevel: 2,
                  ComparisonOperator: "NumberGreaterOrEqualTo",
                },
              },
            ],
          },
          Expiry: { DurationInSeconds: 30 },
        },
        {
          Expression: {
            AttributeCondition: {
              Name: "Language",
              Value: "English",
              ProficiencyLevel: 1,
              ComparisonOperator: "NumberGreaterOrEqualTo",
            },
          },
          // No Expiry = never expires (last step)
        },
      ],
    },
  };
};
```

### Lambda JSON Schema — OR Expression

```javascript
export const handler = async (event) => {
  return {
    MyRoutingCriteria: {
      Steps: [
        {
          Expression: {
            OrExpression: [
              {
                AttributeCondition: {
                  Name: "Technology",
                  Value: "AWS Kinesis Firehose",
                  ProficiencyLevel: 2,
                  ComparisonOperator: "NumberGreaterOrEqualTo",
                },
              },
              {
                AttributeCondition: {
                  Name: "Technology",
                  Value: "AWS Kinesis",
                  ProficiencyLevel: 2,
                  ComparisonOperator: "NumberGreaterOrEqualTo",
                },
              },
            ],
          },
          Expiry: { DurationInSeconds: 30 },
        },
      ],
    },
  };
};
```

### Lambda JSON Schema — NOT + Range

```javascript
export const handler = async (event) => {
  return {
    MyRoutingCriteria: {
      Steps: [
        {
          Expression: {
            NotAttributeCondition: {
              Name: "Language",
              Value: "English",
              ComparisonOperator: "Range",
              Range: {
                MinProficiencyLevel: 4.0,
                MaxProficiencyLevel: 5.0,
              },
            },
          },
          Expiry: { DurationInSeconds: 30 },
        },
      ],
    },
  };
};
```

## Step Statuses

| Status | Meaning |
|--------|---------|
| **Inactive** | Step is waiting — previous step hasn't expired yet |
| **Active** | Step is currently being evaluated for agent match |
| **Expired** | No agent matched during this step's duration |
| **Joined** | Agent successfully matched and joined the contact |
| **Interrupted** | Routing criteria was changed mid-step (e.g., via customer queue flow) |
| **Deactivated** | Contact disconnected — routing stopped |

## Preferred Agent Routing

Target specific agents by user ID instead of (or combined with) predefined attributes.

### When to Use

- Route returning customers to their last agent (use Customer Profiles `_last_agent_id`)
- Target a specific support team (up to 10 agents per step)
- Combine with attribute steps: step 1 = preferred agent (30s expiry), step 2 = attribute-based fallback

### Preferred Agent via Customer Profiles

1. Use `Customer profiles` block → search by `Phone = $.CustomerEndpoint.Address`
2. In `Set routing criteria` block → set preferred agent to `$.Customer.CalculatedAttributes._last_agent_id`
3. Set expiration timer for fallback

### Behavior When Preferred Agent Unavailable

The contact stays restricted to the preferred agent until the step expires, regardless of whether the agent is:
- Offline
- Busy with other contacts
- In a custom non-productive status
- Deleted from instance (userID still considered valid)

After expiry, contact falls to next step or longest-available agent.

## Preferred Agent vs Agent Queue

| | Set Routing Criteria (Preferred Agent) | Agent Queue |
|---|---|---|
| **Multiple agents** | Yes (up to 10) | No (1 agent) |
| **Fallback to pool** | Yes (on step expiry) | No |
| **Queue metrics** | Counted in standard queue | Separate agent queue |
| **Config format** | User ID (e.g., `janedoe`) | Agent ARN |
| **Best for** | Soft preference with fallback | Hard assignment, only that agent |

## Interaction with Other Routing Features

- **Queue priority and delay** operate normally alongside proficiency routing
- **Check staffing** works at queue level only — cannot filter by proficiency
- **Queue transfer before join** — routing criteria carries forward to new queue, restarts from step 1
- **Agent transfer (quick connect)** — use `Set routing criteria` in the transfer flow; previous contact's criteria does NOT carry to new segment
- **Agent queue** — routing criteria has no effect on contacts in agent queues
- **Agent rejection** — timer keeps running, rejected agent remains in the pool for subsequent matching
- **Short expiration warning** — setting `DurationInSeconds` too low can cause default queue-based routing to compete with proficiency routing

## Modifying Routing Criteria on Queued Contacts

- Use a **customer queue flow** to interrupt or update routing criteria on an already-queued contact
- Unlimited changes allowed (only latest 3 updates stored on the contact record)
- Active step gets status `Interrupted`, new criteria takes over

## Data Model References

Proficiency routing data appears in:
- **Contact records** — routing steps and statuses (see `analytics/contact-records.md`)
- **Agent event streams** — agent proficiency snapshot at join time (see `streaming/agent-event-streams.md`)
- **Contact event streams** — routing step transitions (see `streaming/eventbridge-events.md`)

## FAQ

**Are queues still needed?**
Yes. Routing criteria only activates when a contact is enqueued. Proficiencies add targeting within a queue.

**When to use proficiency vs separate queue?**
Business decision — consider how many queues you can consolidate by using proficiencies instead.

**Works across all channels?**
Yes — voice, chat, task, email.

**Can I search for agents by proficiency via API?**
No, not supported.

**What if a predefined attribute is deleted while in use?**
Active contacts with that attribute won't find matching agents. New contacts take the error branch on the `Set routing criteria` block.

**Are historical metrics available for proficiency routing?**
No. Use contact records, agent event streams, and contact event streams for analysis.

**Does the contact record include matched agent's proficiencies?**
No. The agent event stream has a snapshot of the agent's proficiencies at join time.

**Predefined attribute naming rules:**
Pattern: `^(?!(aws:|connect:))[\p{L}\p{Z}\p{N}_.:/=+-@']+$` — any letter, number, whitespace, or `_.:/=+-@'`, but cannot start with `aws:` or `connect:`.
