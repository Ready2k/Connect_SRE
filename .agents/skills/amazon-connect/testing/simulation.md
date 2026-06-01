# Testing and Simulation

Amazon Connect provides a visual test designer and simulation capabilities to validate contact flows, business logic, and routing behavior before deploying changes to production. Tests run within the Connect console without requiring live contacts or agents.

---

## Visual Test Designer

The test designer is available in the Amazon Connect console under **Routing > Tests** and provides a no-code interface for creating, executing, and reviewing test cases.

### Accessing the Test Designer

1. Open the Connect console.
2. Navigate to **Routing > Tests** to view the test case management page.
3. Choose **Create Test** to start a new test case.

---

## Simulation Concepts

Connect's simulation uses an event-driven trigger-response model that mirrors natural cause-and-effect reasoning patterns. This removes the need to know every internal interaction to validate the experience.

### Core Terminology

| Term | Definition |
|---|---|
| **Observations** | Each complete interaction that includes one observed event from the system and actions to validate or simulate behaviors. |
| **Events** | Expected behaviors from the system: a prompt, a bot message, or a Lambda call. |
| **Actions** | What the testing framework does in response to an event: sending DTMF, responding with text, asserting attribute values, or ending the test. |
| **Actors** | Roles played in the framework. For observing: System or Agent. For simulating: Customer, System, or Agent. |

### Interaction Groups

Each interaction group is a simulated interaction with the contact center, composed of three blocks:

#### Observe Block (Required)

Validates the expected interaction from the system. Four event types can be observed:

| Event Type | Description |
|---|---|
| **Test started** | The test simulation has begun. |
| **Message received** | A message/prompt was received from the system. |
| **Action triggered** | A system action was triggered (e.g., transfer to queue). |
| **Test completed** | The test has finished execution. |

**Matching criteria:**
- **Contains** -- the observed message contains the expected text.
- **Similarity match** -- the observed message is semantically similar to the expected text.

**Limitation:** Message received observation currently supports English only. Messages in other languages cause the observe block to fail.

**Action triggered configuration:**
- **Resource type** -- Queue, Lambda, Lex, Hours of Operation.
- **Target resource** -- the specific resource to observe.
- **Operation** -- the action type (e.g., Transfer to Queue).

#### Check Block (Optional)

Validates metadata during the interaction:

| Attribute Type | Description |
|---|---|
| **User-defined attributes** | Custom contact attributes set by flows. |
| **System attributes** | Built-in Connect attributes (queue, channel, etc.). |
| **Segment attributes** | Contact segment metadata. |

Multiple attributes can be validated in a single check block.

#### Action Block (Optional)

Performs actions in response to events. Four action types:

**1. Override Resources:**
Replace production resources with test alternatives during simulation:
- **Lambda** -- substitute a real Lambda with a test Lambda or override its response.
- **Lex** -- replace production bot with test bot.
- **Queue** -- substitute production queue with test queue.
- **Hours of Operation** -- override business hours for testing.

This prevents real data manipulation (e.g., preventing a Lambda that charges a credit card from executing in test).

**2. Override Actions:**
Override response values from related actions with predetermined values.

**3. Send Instructions:**
Simulate input to the contact center:
- **Text/Utterance** -- simulate customer speech or text input.
- **DTMF** -- simulate customer key presses.

**4. Test Control Actions:**
- **Log data** -- write data to the test execution log.
- **End test** -- terminate the test case execution at any point.

---

## Creating Test Cases

### Test Case Configuration

Each test case includes:

**Details Tab:**
- **Name** -- descriptive name for the test scenario.
- **Description** -- explanation of what the test validates.
- **Tags** -- key-value pairs for organization (e.g., Language: English, Env: Production).
- **ARN** -- auto-generated after creation.

**Settings Tab:**

| Setting | Description |
|---|---|
| **Channel** | Voice call or Chat. |
| **Starting point** | Contact flow or incoming phone number. |
| **Contact flow** | The specific flow to simulate. |
| **Contact data** | JSON object with initial contact attributes. |

**Design Tab:**
- Visual canvas for building interaction groups.
- Add new interactions with the **New interaction** button.
- Connect interaction groups in sequence for dependent validation.
- Leave interaction groups unconnected for independent validation.

### Interaction Group Sequencing

**Connected (sequential):**
- Each group depends on successful validation of the prior group.
- If a prior group fails to observe its expected event, subsequent groups do not execute.
- The test times out after 5 minutes with failure status.

**Unconnected (independent):**
- Triggered when a matching event occurs, regardless of other groups.
- Validates experiences that may occur in undetermined sequence.
- Useful for validating queue transfers that occur on both success and error paths.

### Test Case States

- **Draft** -- test case is being designed, not yet published.
- **Published** -- test case is ready for execution.
- **Saved** -- test case has been saved but may need publishing for execution.

---

## Executing Test Cases

When a test runs, a real contact is created to simulate the interaction. Interaction groups execute against this contact.

### Running Tests

1. Choose **Run Test** from the test case page.
2. Monitor execution in real time on the results page.
3. View results in the **Test runs** tab.

### Execution Behavior

- Each interaction group executes exactly once.
- Connected groups execute in sequence -- each depends on the prior group succeeding.
- Unconnected groups execute independently when their matching event occurs.
- If an observe block fails to match, the test times out after 5 minutes.

### Execution Limits

| Limit | Value |
|---|---|
| **Concurrent tests** | Maximum 5 running simultaneously. Additional tests queue. |
| **Queue capacity** | Up to 100 test executions in queue (including 5 running). Requests beyond this are rejected. |
| **Test duration** | Maximum 5 minutes per test. Auto-timeout after 5 minutes. |
| **Record retention** | Tests before Feb 9, 2026: 30 days. Tests on/after that date: retained indefinitely. |

### Agent Queue Interaction Prevention

If a test is not ended before the simulated contact reaches a queue, it may connect to a live agent. Prevention strategies:

- **Proactive termination** -- use Action blocks to end tests before contacts reach agents.
- **Test queue substitution** -- use Action blocks to replace production queues with dedicated test queues.

### Viewing Results

**Test Runs Tab (per test case):**
- Lists all in-progress and completed runs.
- Shows outcome (Passed/Failed), date, and duration.

**Test Runs Tab (global):**
- Lists all test executions across all test cases in the instance.
- Shows only detail results for test cases the user created or has permission to view.

**Test Run Details:**
- Interaction block execution status for each group.
- Simulated contact ID (clickable to view Contact Detail page).
- Pass/fail status of each step.
- Expandable trace for each observe and action block.
- System entries: Initial Setup, Start, and Completed for visibility into system steps.

---

## Test and Simulation Dashboard

The dashboard provides aggregate analytics on test execution.

### Accessing the Dashboard

1. Navigate to **Analytics and optimization > Dashboards and reports**.
2. Choose **Test and simulation dashboard**.

### Dashboard Metrics

| Metric | Description |
|---|---|
| **Success rate** | Percentage of tests that passed. |
| **Failure rate** | Percentage of tests that failed. |
| **Execution duration** | Time taken for test runs. |
| **Failure breakdown** | Categorized failure reasons. |
| **Pass/fail trends** | Historical pass/fail rates over time. |
| **Recent executions** | Quick access to latest test results. |

### Required Permissions for Dashboard

- **Analytics and Optimization > Dashboards**: set to All.
- **Testing and Simulation > Test case**: set to View.

---

## Complete Simulation Example

### Scenario: Flight Booking Bot

A contact flow handles flight booking intents using an Amazon Lex bot with two intents: **book flight** and **agent escalation**. Success terminates the flow; escalation or no-intent transfers to a queue.

### Test Case Design

Five interaction groups -- first four connected in sequence (bot conversation), fifth unconnected (queue transfer validation).

**Interaction Group 1: Validate Bot Initial Message**

Observe block:
- Event type: Message received
- Actor: System
- Expected prompt: "hello welcome to anytravel you can say book a flight"
- Matching criteria: Similar

Action block:
- Action: Send instruction
- Actor: Customer
- Input type: Text/Utterance
- Input: "I want to book a flight"

**Interaction Group 2: Validate Origin City Collection**

Observe: "Where are you flying from?" (Similar match)
Action: Send instruction -- "Seattle"

**Interaction Group 3: Validate Destination City Collection**

Observe: "Where is your destination?" (Similar match)
Action: Send instruction -- "New York"

**Interaction Group 4: Validate Date Collection and Trigger Escalation**

Observe: "What is your departure date?" (Similar match)
Action: Send instruction -- "I need to connect to an agent"

**Interaction Group 5: Validate Transfer to Queue (Unconnected)**

Observe block:
- Event type: Action triggered
- Actor: System
- Resource type: Queue
- Target resource: BasicQueue
- Operation: Transfer to Queue

Action block:
- Action: Test commands
- Test control type: End test

This unconnected group validates queue transfer regardless of which Lex path triggers it (escalation intent, no match, or error).

### Execution and Results

1. Publish the test case.
2. Choose **Run test**.
3. Monitor results in real time.
4. Each interaction group shows pass/fail with expandable detail.
5. Contact ID links to the Contact Detail page where Contact Lens analysis is available if enabled.

---

## Chat Testing

Test chat flows with simulated chat contacts:

- Select **Chat** as the channel in test settings.
- Define chat messages the simulated customer sends via Send instruction actions.
- Test Lex bot interactions within chat flows.
- Validate chat-specific blocks (e.g., interactive messages, list pickers).
- Assert response messages and routing behavior.
- Same interaction group model applies to chat and voice.

---

## Business Condition Testing

Test flows under specific business conditions without waiting for those conditions to naturally occur:

| Condition | How to Simulate |
|---|---|
| After hours | Override Hours of Operation resource with test hours. |
| Holiday | Override Hours of Operation to simulate holiday schedule. |
| Full queue | Configure queue attributes or override queue resource. |
| Agent unavailable | Use test queue substitution with no agents. |
| Specific customer tier | Set contact data attributes to match tier criteria. |
| Failed Lambda | Override Lambda resource with test Lambda that returns error. |
| Lex bot failure | Override Lex resource with test bot. |

This is particularly valuable for testing edge cases and error handling paths that are difficult to trigger with live contacts.

---

## Permissions Required

### Security Profile Permissions

Testing and simulation requires permissions in the security profile under **Test Management > Test Cases**:

| Permission | Description |
|---|---|
| **View** | View existing test cases and results. |
| **Edit** | Modify test case definitions. |
| **Create** | Create new test cases. |
| **Remove** | Delete test cases. |
| **Execute** | Run test cases. |
| **Publish** | Publish test cases for execution. |

Admin security profiles have all testing and simulation permissions granted by default. Admins can grant permissions to onboard other user profiles.

---

## APIs

| API | Purpose |
|---|---|
| `CreateTestCase` | Create a new test case definition. |
| `UpdateTestCase` | Modify an existing test case. |
| `DescribeTestCase` | Get the full definition of a test case. |
| `DeleteTestCase` | Delete a test case. |
| `SearchTestCases` | Search for test cases by name, flow, or status. |
| `StartTestCaseExecution` | Execute a test case. |
| `StopTestCaseExecution` | Cancel a running test execution. |
| `GetTestCaseExecutionSummary` | Get pass/fail summary for an execution. |
| `ListTestCaseExecutions` | List all executions for a test case. |
| `ListTestCaseExecutionRecords` | Get detailed step-by-step execution records. |

### Example -- Create and Run a Test Case

```javascript
import {
  ConnectClient,
  CreateTestCaseCommand,
  StartTestCaseExecutionCommand,
  GetTestCaseExecutionSummaryCommand,
} from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

// Create a test case for after-hours routing
const { TestCaseId } = await client.send(new CreateTestCaseCommand({
  InstanceId: instanceId,
  Name: "After Hours - Voicemail Offered",
  Description: "Verifies that after-hours calls receive the closed message and voicemail option",
  ContactAttributes: {
    "SystemEndpoint": "+15551234567",
  },
  SimulatedTime: "2026-05-25T23:30:00Z", // 11:30 PM
  CustomerInputs: [
    { Type: "DTMF", Value: "1" }, // Press 1 for voicemail
  ],
  Assertions: [
    {
      Type: "FLOW_TRANSITION",
      ExpectedValue: "After Hours Flow",
    },
    {
      Type: "PROMPT_PLAYED",
      ExpectedValue: "We are currently closed",
    },
  ],
}));

// Execute the test
const { ExecutionId } = await client.send(new StartTestCaseExecutionCommand({
  InstanceId: instanceId,
  TestCaseId,
}));

// Check results (after execution completes)
const summary = await client.send(new GetTestCaseExecutionSummaryCommand({
  InstanceId: instanceId,
  TestCaseId,
  ExecutionId,
}));

console.log(`Result: ${summary.Status}`); // PASSED or FAILED
console.log(`Deviations: ${summary.DeviationCount}`);
```

---

## Best Practices

- **Create test cases for every flow** -- especially flows handling business-critical routing.
- **Test edge cases** -- after hours, holidays, full queues, Lambda failures, invalid inputs.
- **Run regression tests after flow changes** -- batch-execute all related test cases before publishing.
- **Use descriptive names** -- name test cases by the scenario they validate, not by internal IDs.
- **Use tags** -- organize test cases with key-value tags (e.g., Language, Environment, Feature).
- **End tests proactively** -- always include an End test action to prevent simulated contacts from reaching live agents.
- **Use test queue substitution** -- replace production queues with test queues to isolate simulations.
- **Monitor the dashboard** -- review pass/fail trends and failure breakdowns regularly.
- **Version control test cases** -- export test definitions and track changes alongside flow exports.

---

## Key Considerations

- **No live traffic impact** -- tests run in simulation mode and do not affect live contacts or agents (unless a simulated contact reaches a queue without being terminated).
- **Real resource invocations** -- Lambda functions and Lex bots are invoked for real during tests. Use resource overrides to prevent side effects in production systems.
- **Cost** -- test executions do not incur per-minute telephony charges, but Lambda and Lex invocations during tests are billed normally.
- **Concurrent limits** -- maximum 5 concurrent tests, 100 in queue.
- **Duration limit** -- 5 minutes per test, auto-timeout after that.
- **Language** -- observe block message matching currently supports English only.
- **Permissions** -- creating and running tests requires appropriate security profile permissions (View, Edit, Create, Remove, Execute, Publish).
- **Contact Lens integration** -- if Contact Lens is enabled on the flow, simulated contacts will be analyzed and results visible on the Contact Detail page.
