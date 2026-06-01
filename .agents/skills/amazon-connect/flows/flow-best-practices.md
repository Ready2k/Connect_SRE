# Amazon Connect Flows: Best Practices, Logging, and Initiation Methods

---

## Part 1: Best Practices for Flows

Source: https://docs.aws.amazon.com/connect/latest/adminguide/bp-contact-flows.html

---

### Attribute Naming Conventions

- Use consistent attribute naming conventions across all AWS services.
- Use camelCase for attribute names (e.g., `yourAttributeNames`) to avoid confusion when passing and referencing variables.
- Use standard naming conventions for attribute names. Do not use spaces or special characters that could impact downstream reporting processes such as AWS Glue crawlers.
- When setting **User Defined** or **External** values in dynamic attribute fields, use only alphanumeric characters (A-Z, 0-9) and periods. No other characters are allowed.

### Modular Flow Design

- Create modular flows. Make the flows as small as possible, then combine modular flows into an end-to-end contact experience.
- This helps keep flows manageable and avoids numerous regression testing cycles.

### Error Handling

- Ensure all error branches are routed to a block that effectively handles the error or terminates the contact.
- Ensure there are no infinite loops in the flow logic.
- Ensure that for each call, the flow connects the caller to an agent, bot, or transferred externally for further assistance.

### Logging and Sensitive Data

- Use a **Set logging behavior** block to enable or disable logging for segments of the flow where sensitive information is collected and cannot be stored in CloudWatch.

### Attribute References (Common Pitfalls)

- Ensure attributes used in the flow are set and referenced correctly.
- If there are periods prepended to the attribute names, you are likely using JSONPath (`$.`) format while also selecting a variable type from the pick list.
- Examples:
  - **Save text as attribute** with value `$.External.variableName` -- works as expected.
  - **Set dynamically** with value `variableName` -- works as expected.
  - **Set dynamically** with value `$.External.variableName` -- results in a prepended period (incorrect).

### Hours of Operation and Staffing

- Before transferring a call to an agent and putting that call in a queue, ensure that **Check hours of operation** and **Check staffing** blocks are used.
- These verify that the call is within working hours and that agents are staffed to service.

### Callbacks and Queue Management

- Ensure callbacks are offered before and after queue transfer by using **Check queue status** blocks.
- Include a condition for **Queue capacity** that is greater than X, where X is a number representing your expected queue capacity.
- If queue capacity exceeds the expected capacity:
  1. Use a **Get Customer Input** block to offer a callback. This retains the caller's position in the queue and calls them back when an agent is available.
  2. In the **Set callback number** block, choose the number to be used to call the customer back in the CCP. Use **System** > **Customer Number**, or a new number collected by a **Store Customer Input** block using **System** > **Stored customer input**.
  3. Add a **Transfer to queue** block. Configure it to **Transfer to callback queue** and configure the callback options to fit your specific use case.

### Queue Flow Prompts

- Use a **Loop prompts** block in your Customer queue flow to interrupt with a queued callback and external transfer option at regular intervals.

### Phone Numbers and External Transfers

- Ensure all countries referenced in external transfers or used for outbound dialing are added to the service quota for your account/instance.
- Ensure all numbers referenced in external transfers are in **E.164 format**.
  - Drop the national trunk prefix that you use when calling locally.
  - This prefix would be the leading `0` for most of Europe, `1` for the US. The prefix is replaced by the country code.
  - Example: UK mobile number `07911 123456` in E.164 format is `+44 7911 123456`.

---

## Part 2: Flow Logs (Generating, Enabling, Searching, and Alerting)

Source: https://docs.aws.amazon.com/connect/latest/adminguide/about-contact-flow-logs.html and sub-pages

---

### Overview

Amazon Connect flow logs provide real-time details about events in your flows as customers interact with them. You can also use flow logs to help debug flows during creation. If needed, you can always roll back to a previous version of a flow.

There are two types of logging for flows and bot interactions:

#### 1. Flow Logs (CloudWatch Log Group)

- Stored in an Amazon CloudWatch log group.
- Use cases:
  - Identifying bottlenecks in flow design.
  - Debugging flow issues in real-time.
  - Analyzing customer journey patterns.
- Flow logs help track customers between different flows by including the contact ID in each log entry. You can query the logs for the contact ID to trace the customer interaction through each flow.
- The CloudWatch log group is created automatically when **Enable flow logging** is selected for your instance on the Amazon Connect console.
- To actually enable logging, you also need to add a **Set logging behavior** block to your flow.

#### 2. Automated Interaction Logs (S3)

- Saved in an S3 bucket created when you select the following options on the Amazon Connect console:
  1. **Enable call recording** and create or select your S3 bucket on the **Data storage** page. The automated interaction log is stored in the same S3 location as call recordings.
  2. **Enable Automated Interaction Logs** on the **Flows** page. This enables logging of key interaction points such as flows, prompts, menus, and keypad selections. Available in S3 storage and on the **Contact details** page in the Connect admin website.
  3. **Enable Bot Analytics and Transcripts** on the **Flows** page. This ensures the log includes the Amazon Lex bot transcript.

---

### Storage for Flow Logs (CloudWatch)

- Flow logs are stored in an Amazon CloudWatch log group, in the **same AWS Region** as your Amazon Connect instance.
- The log group is created automatically when **Enable flow logging** is turned on for your instance.
- Log group naming convention: `/aws/connect/<instance-alias>`
- A log entry is added as each block in your flow is triggered.
- You can configure CloudWatch to send alerts when unexpected events occur during active flows.

**Important caveat**: If your CloudWatch log group is deleted, you need to **manually re-create** it. Otherwise, Amazon Connect will not publish any more logs.

#### Pricing

- You are **not charged** for generating flow logs.
- You **are charged** for using CloudWatch for generating and storing the logs.
- Free tier customers are charged only for usage that exceeds service quotas.
- See [Amazon CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/) for details.

---

### Enabling Flow Logs

#### Step 1: Enable Logging for Your Instance

1. Open the Amazon Connect console at https://console.aws.amazon.com/connect/.
2. On the instances page, choose the instance alias (this is also your instance name, which appears in your Amazon Connect URL).
3. In the navigation pane, choose **Flows**.
4. Select **Enable Flow logs** and choose **Save**.

**Tip**: Amazon Connect delivers flow logs **at least once**. They may be delivered again for multiple reasons, for example, a service retry due to an unavoidable failure.

#### Step 2: Add the Set Logging Behavior Block

- Logs are generated **only** for flows that include a **Set logging behavior** block with logging set to **enabled**.
- You control which flows, or parts of flows, logs are generated for by including multiple **Set logging behavior** blocks and configuring them as needed.

**Important behavior**: When you use a **Set logging behavior** block to enable or disable logging for a flow, logging is also enabled or disabled for any **subsequent flow** that a contact is transferred to, even if that flow does not include a **Set logging behavior** block. To avoid logging that persists between flows, enable or disable a **Set logging behavior** block as needed for that specific flow.

**Steps to enable/disable flow logs for a flow:**

1. In the flow designer, add a **Set logging behavior** block and connect it to another block in the flow.
2. Open the properties for the block. Choose **Enable** or **Disable**.
3. Choose **Save**.
4. If you add a **Set logging behavior** block to a flow that is already published, you must **publish it again** to start generating logs for it.

---

### Data in Flow Logs

- Log entries include:
  - Details about the **block** associated with the log entry.
  - The **contact ID**.
  - The **action taken** after the steps in the block were completed.
- Any contact interaction that occurs **outside** of the flow is **not logged** (e.g., time spent in a queue, interactions with an agent).
- You can set the properties of the block to **disable logging** during the parts of your flow that interact with or capture sensitive data or customers' personal information.
- If you use **Amazon Lex** or **AWS Lambda** in your flows, the logs show the entry and exit of the flow going to them, and include any information about the interaction that is sent or received during entry or exit.
- The logs include the **flow ID**, which stays the same when you change a flow. You can use the logs to compare interactions with different versions of the flow.

#### Example Log Entry

The following example shows a **Set working queue** block of an inbound flow:

```json
{
    "ContactId": "11111111-2222-3333-4444-555555555555",
    "ContactFlowId": "arn:aws:connect:us-west-2:0123456789012:instance/nnnnnnnnnnn-3333-4444-5555-111111111111/contact-flow/123456789000-aaaa-bbbbbbbbb-cccccccccccc",
    "ContactFlowModuleType": "SetQueue",
    "Timestamp": "2021-04-13T00:14:31.581Z",
    "Parameters": {
        "Queue": "arn:aws:connect:us-west-2:0123456789012:instance/nnnnnnnnnnn-3333-4444-5555-111111111111/queue/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    }
}
```

**Fields:**
- `ContactId` -- The unique identifier for the contact.
- `ContactFlowId` -- The ARN of the flow, including instance ID and flow ID.
- `ContactFlowModuleType` -- The type of block that generated the log entry (e.g., `SetQueue`, `PlayPrompt`, etc.).
- `Timestamp` -- ISO 8601 timestamp of when the block was triggered.
- `Parameters` -- The parameters passed to/from the block. Content varies by block type.

---

### Searching Flow Logs

**Prerequisites**: Flow logging must be enabled first. Logs will be created for conversations that occur after logging is enabled.

**Steps to search flow logs:**

1. Open the Amazon CloudWatch console. Go to **Logs** > **Log groups**.
2. Choose the log group for your instance (e.g., `/aws/connect/mytest88`).
3. A list of log streams will be displayed.
4. To search all the log streams in the instance, choose **Search log group**.
5. In the search box, enter the string you want to search for (e.g., all or a portion of the contact ID).
6. After a couple of moments (longer depending on how big your log is), CloudWatch returns results.
7. You can open each event to see what happened (e.g., when a **Play prompt** block runs in a flow).

---

### Tracking Customers Between Multiple Flows

- In many cases, customers interact with multiple flows, being passed from one flow to another.
- Flow logs help track customers between different flows by including the **contact ID** in each log entry.
- When a customer is transferred to a different flow, the ID for the contact associated with their interaction is included with the log for the new flow.
- You can query the logs for the contact ID to trace the customer interaction through each flow.

**Important for high-volume contact centers**: There can be multiple streams for flow logs. If a contact is transferred to a different flow, the log may be in a **different stream**. To make sure you find all log data for a specific contact, search for the contact ID in the **entire CloudWatch log group** instead of in a specific log stream.

---

### Creating Alerts for Flow Log Events

- You can configure CloudWatch to define a **filter pattern** that looks for specific events in your flow logs and then creates an **alert** when an entry for that event is added to the log.
- Example: Set an alert for when a flow block goes down an **error path** as a customer interacts with the flow.
- Log entries are typically available in CloudWatch within a short time, giving you **near real-time** notification of events in flows.

---

## Part 3: Contact Initiation Methods and Flow Types

Source: https://docs.aws.amazon.com/connect/latest/adminguide/contact-initiation-methods.html

---

### Overview

Every contact in an Amazon Connect contact center is initiated by one of the following methods. The initiation method is stored in the `InitiationMethod` field of the contact record.

### All Initiation Methods

| # | Initiation Method | Description |
|---|-------------------|-------------|
| 1 | `INBOUND` | Customer initiated a voice (phone) contact |
| 2 | `OUTBOUND` | Agent initiated voice contact to external number via CCP |
| 3 | `TRANSFER` | Contact transferred by agent to another agent or queue via quick connects |
| 4 | `CALLBACK` | Customer contacted as part of a callback flow |
| 5 | `API` | Contact initiated via Connect API |
| 6 | `QUEUE_TRANSFER` | Customer transferred from one queue to another via a flow block |
| 7 | `DISCONNECT` | A Set disconnect flow block specifies which flow to run after disconnect |
| 8 | `WEBRTC_API` | Customer used communication widget for in-app voice/video call |
| 9 | `EXTERNAL_OUTBOUND` | Agent initiated voice contact with external participant via quick connect or flow block |
| 10 | `MONITOR` | Supervisor initiated monitor feature on agent contact |
| 11 | `AGENT_REPLY` | Agent replied to inbound email to create outbound email reply |
| 12 | `FLOW` | Email initiated by the Send message block |
| 13 | `CAMPAIGN_PREVIEW` | Contact initiated by outbound campaign using preview dialing mode |

---

### INBOUND

The customer initiated a voice (phone) contact with the contact center.

**Flow sequence for a simple inbound call (before caller connects to agent):**

1. **Inbound flow** -- Presented to the caller when the contact successfully connects with the phone number.
2. **Customer queue flow** -- Played to the customer if they are put in a queue during the transition in the Inbound flow.
3. **Agent whisper flow** -- Played to the agent after the agent becomes available and accepts the contact.
4. **Customer whisper flow** -- Played to the customer after the Agent whisper flow completes.

After both whisper flows are played successfully, the caller gets connected to the agent for interaction.

---

### OUTBOUND

An agent initiated voice (phone) contact to an external number using the CCP.

**Flow sequence:**

1. **Outbound whisper flow** -- Presented to the destination party as soon as they pick up the call.

After the Outbound whisper flow successfully completes, the agent and the contact are connected for interaction.

**Important detail**: Before the call is made, all the blocks before the first **Play prompt** are run. After the customer picks up, the first **Play prompt** and all the blocks after it are run.

The **Outbound flow** type is the only one involved in an outbound call initiated from Connect.

---

### TRANSFER

The contact was transferred by an agent to another agent or to a queue, using quick connects in the CCP. This results in a **new contact record** being created.

Before the agent transfers the contact, all the flows involved in an INBOUND contact are run.

#### Agent-to-Agent Transfer (Agent Quick Connect)

**Flow sequence:**

1. **Agent transfer flow** -- Played to the source agent after the transfer.
2. **Agent whisper flow** -- Played to the destination agent after they accept the call.
3. **Customer whisper flow** -- Played to the source agent.
4. **Customer hold flow** -- Played to the original inbound caller during the entire hold time.

After the source agent is connected with the destination agent, the source agent can:
- Choose **Join** -- Joins all parties (source agent, destination agent, customer) in a conference call.
- Choose **Hold all** -- Puts the destination agent and the customer on hold.
- Put destination agent on hold, so only the source agent can talk to the customer.
- Choose **End call** -- The source agent leaves the call but the destination agent and customer are directly connected and continue talking.

#### Agent-to-Queue Transfer (Queue Quick Connect)

**Flow sequence:**

1. **Queue transfer flow** -- Played to the source agent after the transfer.
2. **Agent whisper flow** -- Played to the destination agent (from the transferred queue) after they accept the call.
3. **Customer whisper flow** -- Played to the source agent.
4. **Customer hold flow** -- Played to the original inbound caller during the entire hold time.

After the source agent is connected with the destination agent, the source agent has the same options as above (Join, Hold all, Hold destination, End call).

---

### CALLBACK

The customer is contacted as part of a callback flow.

**Flow sequence:**

1. **Agent whisper flow** -- Played to the agent as soon as they accept the callback contact.
2. **Outbound whisper flow** -- Played to the customer after they accept the callback call.

After both flows are played, the agent and customer are connected and can interact.

---

### API

The contact was initiated with Amazon Connect by API. This could be:

1. An outbound contact created and queued to an agent using the `StartOutboundVoiceContact` API.
2. A live chat initiated by the customer where you called the `StartChatContact` API.
3. A task initiated by calling the `StartTaskContact` API.

**Example flow sequence (API-initiated outbound contact):**

1. **Inbound flow** -- Provided in the API request, played to the customer after the outbound contact is successfully initiated via `StartOutboundVoiceContact`.
2. **Customer queue flow** -- Played to the customer while waiting in queue for an agent (depending on Inbound flow configuration).
3. **Agent whisper flow** -- Played to the agent when the available agent accepts the call.
4. **Customer whisper flow** -- Played to the customer.

After both whisper flows play successfully, the caller is connected to the agent.

---

### QUEUE_TRANSFER

While the customer was in one queue (listening to a Customer queue flow), they were transferred into another queue using a flow block.

**Flow involved:**
- **Customer queue flow** only. No additional flows are involved.

---

### DISCONNECT

When a **Set disconnect flow** block runs, it specifies which flow to run after a disconnect event during a contact.

**Flow involved:**
- You can specify only an **Inbound flow** in this block.
- Since it occurs after the disconnect event, no additional flow is presented to the customer.

---

### WEBRTC_API

The contact used the communication widget to make an in-app voice/video call to an agent. This initiation method uses the same flow types as INBOUND:

1. **Inbound flow**
2. **Customer queue flow**
3. **Agent whisper flow**
4. **Customer whisper flow**

---

### EXTERNAL_OUTBOUND

An agent initiated a voice (phone) contact with an external participant by using either a quick connect in the CCP or a flow block.

**No flow type is associated with this initiation method.**

---

### MONITOR

A supervisor initiated the monitor feature on a contact connected to an agent. The supervisor can silently monitor the agent and customer, or barge the conversation.

**No flow type is associated with this initiation method.**

---

### AGENT_REPLY

An agent has replied to an inbound email contact to create an outbound email reply.

**Flow involved:**
- **Outbound whisper flow** type is played.

---

### FLOW

An email was initiated by the **Send message** block.

**Flow involved:**
- **Outbound whisper flow** type is played.

---

### CAMPAIGN_PREVIEW

The contact was initiated by an outbound campaign using preview dialing mode. The agent previews customer information before the call is placed.

---

### Overriding Default Contact Flows

For all initiation methods discussed above, if you do not specify flows for **Agent whisper flow**, **Customer whisper flow**, **Customer queue flow**, or **Outbound whisper flow**, then the **default flow** of that type runs instead.

To override the defaults and use your own flows, use the following blocks:
- **Set customer queue flow** -- Overrides the default Customer queue flow.
- **Set hold flow** -- Overrides the default Customer hold flow.
- **Set whisper flow** -- Overrides the default Agent whisper and Customer whisper flows.

---

### Summary: Initiation Method to Flow Type Mapping

| Initiation Method | Inbound Flow | Customer Queue Flow | Agent Whisper Flow | Customer Whisper Flow | Outbound Whisper Flow | Agent Transfer Flow | Queue Transfer Flow | Customer Hold Flow |
|---|---|---|---|---|---|---|---|---|
| INBOUND | Yes | Yes | Yes | Yes | - | - | - | - |
| OUTBOUND | - | - | - | - | Yes | - | - | - |
| TRANSFER (Agent) | - | - | Yes | Yes | - | Yes | - | Yes |
| TRANSFER (Queue) | - | - | Yes | Yes | - | - | Yes | Yes |
| CALLBACK | - | - | Yes | - | Yes | - | - | - |
| API | Yes | Yes | Yes | Yes | - | - | - | - |
| QUEUE_TRANSFER | - | Yes | - | - | - | - | - | - |
| DISCONNECT | Yes | - | - | - | - | - | - | - |
| WEBRTC_API | Yes | Yes | Yes | Yes | - | - | - | - |
| EXTERNAL_OUTBOUND | - | - | - | - | - | - | - | - |
| MONITOR | - | - | - | - | - | - | - | - |
| AGENT_REPLY | - | - | - | - | Yes | - | - | - |
| FLOW | - | - | - | - | Yes | - | - | - |
| CAMPAIGN_PREVIEW | - | - | - | - | - | - | - | - |
