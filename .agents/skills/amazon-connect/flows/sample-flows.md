# Amazon Connect Sample Flows — Complete Reference

Amazon Connect includes a set of sample flows that demonstrate common contact center patterns. They are designed to help you learn how to create your own flows that work in a similar way.

## How to Access Sample Flows

### To explore how the sample flows work

1. Claim a number if you haven't already: go to **Channels** > **Phone numbers** > **Claim a number**.
2. Choose the **DID** tab, then choose a number.
3. In **Flow / IVR** use the dropdown to choose the sample flow you want to try. Choose **Save**.
4. Call the number. The sample flow that you selected starts.

It is recommended to open the sample flow in the flow designer and follow along to see how it works while experiencing it.

### To open a sample flow in the flow designer

1. In Amazon Connect choose **Routing** > **Flows**.
2. On the **Flows** page, scroll down to the flows with names that start with **Sample**.
3. Choose the flow you want to view.

### To clone a sample flow

1. Open the sample flow in the flow designer.
2. Choose **Save As** to create a copy with a new name.
3. Modify the copy as needed for your use case.

---

## 1. Sample Inbound Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample inbound flow |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Serves as the default entry point for all inbound contacts. Routes contacts based on channel type and provides a menu of sample flow demonstrations. |

### How It Works

This sample flow is **automatically assigned to the phone number that you claimed** when you first set up flows. It is the default first-contact experience.

1. Uses the **Check contact attributes** block to determine if the contact is reaching out by **phone**, **chat**, or **task**.
2. **If the channel is chat or task**: The contact is transferred to the **Sample queue configurations flow**.
3. **If the channel is voice**: Based on user input, the contact is either:
   - Transferred to one of the other sample flows for demonstration, OR
   - A sample follow-up agent task is created for this contact.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Check contact attributes | Checks the Channel attribute to determine voice/chat/task |
| Transfer to flow | Transfers to Sample queue configurations (for chat/task) |
| Get customer input | Presents menu options for voice callers |
| Transfer to flow | Transfers to various sample flows based on input |
| Create task | Creates a follow-up agent task |

### Key Patterns Demonstrated

- Channel-based routing (voice vs. chat vs. task)
- Menu-driven IVR for voice contacts
- Transfer between flows
- Task creation from within a flow

### Customer Experience

- **Voice**: Hears a menu of options and can choose which sample flow to experience
- **Chat/Task**: Automatically routed to the queue configurations flow

### Prerequisites/Dependencies

- A claimed phone number
- All other sample flows (since this flow transfers to them)

---

## 2. Sample A/B Test Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample AB test |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates how to perform A/B call distribution based on percentage using the Distribute by percentage block. |

### How It Works

1. The **Play prompt** block uses **Amazon Polly** (text-to-speech) to say: *"Connect will now simulate rolling dice by using the Distribute randomly block. Now rolling."*
2. The contact reaches the **Distribute by percentage** block, which routes the customer randomly based on a percentage.
   - Simulates a dice roll, resulting in values between **2 to 12** with different percentages.
   - Example: 3% chance for "2", 6% chance for "3", and so on.
3. After the contact gets routed, the **Play prompt** tells the customer which number the dice rolled.
4. At the end, the **Transfer to flow** block transfers the customer back to the **Sample inbound flow**.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Play prompt | Amazon Polly TTS — announces the dice simulation |
| Distribute by percentage | Multiple branches with percentage weights (2-12, simulating dice probability) |
| Play prompt | Announces which number was rolled |
| Transfer to flow | Returns contact to Sample inbound flow |

### Key Patterns Demonstrated

- **A/B testing** / percentage-based routing
- Using the **Distribute by percentage** block for random distribution
- Amazon Polly text-to-speech integration
- Transferring back to a parent flow

### Customer Experience

- Hears a dice-rolling simulation announcement
- Is randomly routed to one of the percentage branches
- Hears which number was "rolled"
- Transferred back to the inbound flow

### Prerequisites/Dependencies

- Sample inbound flow (for return transfer)

---

## 3. Sample Customer Queue Priority Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample customer queue priority |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates how to raise or lower a contact's priority in a queue using the Change routing priority/age block. |

> **Note**: This sample flow is available in previous Amazon Connect instances. In new instances, this functionality is incorporated into the **Sample queue configurations flow**.

### How It Works

By default, the priority for new contacts is **5**. Lower values raise the priority of the contact. For example, a contact assigned a priority of **1** is routed first.

This sample shows two ways to raise or lower a customer's priority using the **Change routing priority/age** block:

#### Option 1: Raise the Priority

1. The **Get Customer Input** block prompts the customer to press **1** to move to the front of the queue.
2. If the customer presses 1, they go down the "Pressed 1" branch to the **Change routing priority/age** block.
3. This block changes their priority in the queue to **1** (highest priority).

#### Option 2: Change the Routing Age

1. The **Get Customer Input** block prompts the customer to press **2** to move behind existing contacts already in queue.
2. If the customer presses 2, they go down the "Pressed 2" branch to a different **Change routing priority/age** block.
3. This block increases their routing age by **10 minutes**, moving them ahead of others in the queue who have been waiting longer.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Get Customer Input | Prompts for 1 (front of queue) or 2 (change age) |
| Change routing priority/age | Option 1: Sets priority to 1 |
| Change routing priority/age | Option 2: Increases routing age by 10 minutes |

### Key Patterns Demonstrated

- **Queue priority manipulation** — setting explicit priority values
- **Routing age adjustment** — using time-based priority
- Two different approaches to queue prioritization
- Understanding that lower priority values = higher actual priority

### Customer Experience

- Prompted to choose between moving to front of queue or adjusting queue position
- Queue position changes based on selection

### Prerequisites/Dependencies

- A configured queue with contacts waiting (to see the effect)

---

## 4. Sample Disconnect Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample disconnect flow |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates post-disconnect handling for voice, chat, and task contacts with different behaviors per channel. |

### How It Works

This sample works with **voice**, **chat**, and **task** contacts, each handled differently.

#### Chat Contacts

1. The **Play prompt** block shows a text message that the agent has disconnected.
2. A **Wait** block sets the timeout period for **15 minutes**.
3. If the customer returns within 15 minutes, they are transferred to a queue to chat with another agent.
4. If the customer doesn't return, the timer expires and the chat disconnects.

#### Voice Contacts

1. Sets a user-defined attribute: `DisconnectFlowRun`. If it equals `Y`, disconnect.
2. Gets customer input — whether they were happy with the service.
3. Terminates the flow.

#### Task Contacts

1. Checks contact attributes — whether `Agent ARN` equals `NULL`.
2. Transfers to the agent's queue.
3. If at capacity, disconnects.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Check contact attributes | Determines channel type (voice/chat/task) |
| Play prompt | Shows disconnect message (chat) |
| Wait | 15-minute timeout for chat reconnection |
| Set contact attributes | Sets DisconnectFlowRun = Y (voice) |
| Get customer input | Satisfaction survey (voice) |
| Check contact attributes | Checks Agent ARN = NULL (task) |
| Transfer to queue | Routes to agent queue (task) |
| Disconnect | Terminates contact |

### Key Patterns Demonstrated

- **Per-channel disconnect handling** — different logic for voice, chat, and task
- **Chat reconnection window** — using Wait block for timed reconnection
- **Post-call survey** — gathering feedback after disconnect
- **User-defined attributes** — tracking flow execution state
- **Task reassignment** — routing orphaned tasks to queues

### Customer Experience

- **Chat**: Sees disconnect message, has 15 minutes to reconnect
- **Voice**: Asked about satisfaction before final disconnect
- **Task**: Automatically reassigned to agent queue if possible

### Prerequisites/Dependencies

- Referenced in ContactTraceRecord via `DisconnectReason`

---

## 5. Sample Queue Configurations Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample queue configurations |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates multiple queue management techniques: priority changes, wait time checks, and queued callback setup. |

### How It Works

This flow shows different ways you can put a customer in queue: change priority, determine wait time, and offer callback.

1. The customer is put in the **BasicQueue**.
2. The **Default customer queue** flow is invoked, which runs a **Loop prompts** block playing: *"Thank you for calling. Your call is very important to us and will be answered in the order it was received."*
3. Hours of operation are checked with a **Check hours of operation** block.
4. The channel is checked with a **Check contact attributes** block:
   - **If chat**: Check time in queue. If less than 5 minutes, place in queue for agent. If more than 5 minutes, check channel again — if chat, place in queue for agent.
   - **If voice**: Route down the **No Match** branch to a **Play prompt** then **Get customer input** block.
5. In the **Get customer input** block (voice path), customer options:
   - **Press 1**: Move to the front of the queue
   - **Press 2**: Move to the end of the queue
6. Two **Change routing priority/age** blocks handle front-of-queue and back-of-queue placement.
7. A **Check queue status** block checks whether time in queue is less than **300 seconds**.
8. A **Play prompt** tells the customer the results.
9. Another **Check contact attributes** block checks the channel again (chat vs. voice/No Match).

#### Callback Path (Voice)

10. In another **Get customer input** block, customers are prompted: *"Press 1 to go into queue or 2 to enter a callback number."*
11. If customer presses **2**, routed to the **Store customer input** block.
12. The **Store customer input** block prompts the customer for their phone number.
13. The phone number is stored in the **Stored customer input** attribute by the **Set callback number** block.
14. A **Transfer to queue** block puts the customer in a callback queue with these settings:
    - **5 seconds** wait between callback initiation and enqueue
    - **1 callback attempt** if initial callback doesn't reach customer
    - If configured for 2 attempts: **10 minutes** between each attempt
    - No special callback queue — uses **BasicQueue** set at the beginning

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Set working queue | BasicQueue |
| Set customer queue flow | Default customer queue |
| Loop prompts | "Thank you for calling..." message |
| Check hours of operation | Validates business hours |
| Check contact attributes | Channel check (chat/voice/task) |
| Play prompt | Various status messages |
| Get customer input | Priority choice (1=front, 2=back) |
| Change routing priority/age | Move to front of queue |
| Change routing priority/age | Move to end of queue |
| Check queue status | Time in queue < 300 seconds |
| Get customer input | Queue vs. callback choice (1=queue, 2=callback) |
| Store customer input | Captures callback phone number |
| Set callback number | Stores number from customer input |
| Transfer to queue | Callback queue transfer with retry settings |

### Key Patterns Demonstrated

- **Queue priority manipulation** (front/back of queue)
- **Queue status checking** (wait time evaluation)
- **Hours of operation validation**
- **Multi-channel handling** (chat vs. voice paths)
- **Queued callback setup** — complete end-to-end callback flow
- **Callback retry configuration** (attempts, timing)
- **Loop prompts** for hold music/messages

### Customer Experience

- **Chat**: Placed in queue with wait time monitoring
- **Voice**: Given options to change queue position, check wait time, or request a callback
- **Callback**: Prompted for phone number, placed in callback queue

### Prerequisites/Dependencies

- BasicQueue must exist
- Hours of operation must be configured
- Default customer queue flow

---

## 6. Sample Queue Customer Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample queue customer |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates pre-queue validation checks including working queue assignment and hours of operation verification. |

### How It Works

1. The **Set working queue** block determines which queue to transfer the customer to.
2. The **Check hours of operation** block performs checks to avoid queuing the customer during non-working hours.
3. If within business hours and the queue can handle the call: customer is transferred to the queue.
4. If outside business hours: customer hears *"We are not able to take your call right now. Goodbye."* and is disconnected.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Set working queue | Assigns the target queue |
| Check hours of operation | Validates current time against business hours |
| Play prompt | "We are not able to take your call right now. Goodbye." |
| Transfer to queue | Moves customer into the queue |
| Disconnect | Ends the contact if outside hours |

### Key Patterns Demonstrated

- **Pre-queue validation** — checking hours before queuing
- **Working queue assignment**
- **Graceful rejection** — informing customer before disconnect
- Simple, minimal flow design

### Customer Experience

- If within hours: seamlessly placed in queue
- If outside hours: hears a polite message and is disconnected

### Prerequisites/Dependencies

- A configured queue
- Hours of operation set on the queue

---

## 7. Sample Queued Callback Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample queued callback |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Provides complete callback queue logic — checking wait times, offering callback option, and setting up the callback. |

> **Note**: This sample flow is available in previous Amazon Connect instances. In new instances, see examples of queued callback in the **Sample interruptible queue flow with callback** and **Sample queue configurations flow**.

### How It Works

1. After a voice prompt, a **working queue** is selected and its **queue status** is checked.
2. A voice prompt tells the customer if the wait time for the selected queue is **longer than 5 minutes**.
3. Customers are offered a choice:
   - **Wait in the queue**, OR
   - **Be placed into a callback queue**
4. If the customer decides to **wait in the queue**: The **Set customer queue flow** block places them in a queue flow that provides a callback option — specifically the **Sample interruptible queue flow with callback**.
5. If the customer chooses **callback**:
   - Their number is stored in the **Store customer input** block
   - Their callback number is set
   - They are transferred to the callback queue

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Play prompt | Initial greeting and wait time announcement |
| Set working queue | Selects target queue |
| Check queue status | Checks if wait time > 5 minutes |
| Get customer input | Wait vs. callback choice |
| Set customer queue flow | Sets to Sample interruptible queue flow |
| Store customer input | Captures callback phone number |
| Set callback number | Stores the callback number |
| Transfer to queue | Places in callback queue |

### Key Patterns Demonstrated

- **Queued callback end-to-end flow**
- **Wait time evaluation** before offering callback
- **Customer queue flow assignment** — changing the in-queue experience
- **Callback number collection and storage**
- Integration with the interruptible queue flow

### Customer Experience

- Informed of current wait time
- Given choice between waiting and receiving a callback
- If callback: prompted for phone number, then call ends and callback is scheduled

### Prerequisites/Dependencies

- Sample interruptible queue flow with callback
- A configured queue with routing profile
- For more info see: Set up queued callback, Transfer to queue block, Queued callbacks in real-time metrics

---

## 8. Sample Interruptible Queue Flow with Callback

| Property | Value |
|----------|-------|
| **Exact Name** | Sample interruptible queue flow with callback |
| **Flow Type** | Customer queue |
| **Purpose** | Manages the customer's in-queue experience with periodic interruptions offering a callback option. |

### How It Works

This flow manages what the customer experiences **while waiting in queue**. It uses **Check contact attributes** to determine if the customer is contacting by phone or chat, and routes accordingly.

- **If the channel is chat**: The customer is transferred to **Loop prompts** (standard hold messaging).
- **If the channel is voice**: The customer hears **looping audio** that **interrupts every 30 seconds** to give them two options from the **Get customer input** block:
  1. **Press 1**: Enter a callback number. The **Get customer input** block prompts for the phone number. Then the flow ends (callback is scheduled).
  2. **Press 2**: Ends the flow; the customer remains in the queue.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Check contact attributes | Channel check (chat vs. voice) |
| Loop prompts | Hold music/messaging for chat contacts |
| Get customer input | Interrupts every 30 seconds with callback option (voice) |
| Get customer input | Captures callback phone number |

### Key Patterns Demonstrated

- **Customer queue flow** (runs while contact is in queue, not before)
- **Interruptible hold experience** — breaking hold music with options
- **In-queue callback offering** — giving callback option after the customer is already waiting
- **30-second interrupt interval** — periodic check-ins with the customer
- **Channel-aware queue experience** — different hold experience for chat vs. voice

### Customer Experience

- **Chat**: Standard loop prompts while waiting
- **Voice**: Hold music interrupted every 30 seconds with option to request callback or continue waiting

### Prerequisites/Dependencies

- Must be assigned as a customer queue flow (not a standalone inbound flow)
- Typically used with Sample queued callback or Sample queue configurations flow

---

## 9. Sample Lambda Integration Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample Lambda integration |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates how to invoke a Lambda function for a data dip — retrieving external information about the customer based on their phone number. |

### How It Works

1. A prompt tells the customer that a **data dip** is being performed.
2. The **Invoke AWS Lambda function** block triggers **sampleLambdaFlowFunction**.
   - This sample Lambda function determines the **location (US state)** of the phone number based on area code.
   - The function **times out in 4 seconds**.
   - If it times out, it plays a prompt: *"Sorry, we failed to find the state for your phone number's area code."*
3. The first **Check contact attributes** block checks the channel:
   - **If chat**: Returns a fun fact.
4. **If voice**: The second **Check contact attributes** block is triggered:
   - It checks the match conditions of **State**, which is an **external attribute**.
   - Uses an external contact attribute because it's getting data using a process external to Amazon Connect.
5. A prompt tells the customer it's returning them to **Sample inbound flow**, then starts the **Transfer to flow** block.
6. If the transfer fails, a prompt plays and the contact is disconnected.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Play prompt | "Performing data dip" announcement |
| Invoke AWS Lambda function | Calls sampleLambdaFlowFunction, 4-second timeout |
| Check contact attributes | Channel check (voice/chat/task) |
| Check contact attributes | Checks State external attribute with match conditions |
| Play prompt | Fun fact (chat) or state result (voice) |
| Play prompt | "Returning to Sample inbound flow" |
| Transfer to flow | Returns to Sample inbound flow |
| Play prompt | Error message if transfer fails |
| Disconnect | Ends contact on failure |

### Key Patterns Demonstrated

- **Lambda integration** — invoking external functions from a flow
- **Data dip** — looking up customer information in real-time
- **External attributes** — using data returned from Lambda as contact attributes
- **Timeout handling** — graceful fallback when Lambda times out
- **Channel-aware responses** — different content for chat vs. voice
- **Error handling** — managing transfer failures

### Customer Experience

- **Voice**: Hears announcement of data dip, then hears their state based on area code, then returned to inbound flow
- **Chat**: Receives a fun fact from the Lambda response

### Prerequisites/Dependencies

- **sampleLambdaFlowFunction** Lambda function must exist and be associated with the Connect instance
- Lambda function must be configured in Amazon Connect (Flows > AWS Lambda)
- For more info: "Store a value from a Lambda function as a contact attribute"

---

## 10. Sample Screenpop Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample note for screenpop |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates how to use Screenpop, a Contact Control Panel (CCP) feature, to load a web page with parameters based on contact attributes. |

### How It Works

In this sample flow, a **Set contact attributes** block is used to create an attribute from a text string. As an attribute, the text can be passed to the CCP to display a note to an agent.

The Screenpop feature in the CCP can load a web page with parameters based on the attributes set in the flow.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Set contact attributes | Creates an attribute from a text string for agent display |

### Key Patterns Demonstrated

- **Screenpop integration** — passing data to the agent's CCP
- **Contact attributes as data carriers** — using attributes to transmit information to the agent UI
- **Agent-facing data display** — showing contextual information when a call arrives
- **CCP customization** — extending the agent experience with flow-driven data

### Customer Experience

- Transparent to the customer — the screenpop is agent-facing only

### Agent Experience

- Agent sees a note or web page loaded in their CCP with parameters set by the flow
- Provides context about the contact before/during the interaction

### Prerequisites/Dependencies

- CCP must be configured to use Screenpop functionality
- The agent's CCP or custom CCP implementation must handle the screenpop attributes

---

## 11. Sample Secure Input with Agent

| Property | Value |
|----------|-------|
| **Exact Name** | Sample secure input with agent |
| **Flow Type** | Queue transfer |
| **Purpose** | Demonstrates how to collect sensitive customer data (e.g., credit card numbers) while the agent is on hold, using encryption. |

> **Note**: In a production environment, AWS recommends using encryption instead of this solution.

### How It Works

1. The flow begins by checking the customer's **channel**:
   - **If chat**: Customer is put in a queue.
2. **If voice**: The agent and customer are put in a **conference call**.
3. A **Play prompt** tells the customer that the agent will be put on hold while they enter their credit card information.
4. When the prompt finishes, the agent is put on hold using a **Hold customer or agent** block.
   - If an error occurs, a prompt plays that the agent was unable to be put on hold, and the flow ends.
5. The customer's input is stored using the **Store Customer Input** block.
   - This block **encrypts** the sensitive customer information using a **signing key** that must be uploaded in **.pem format**.
6. After the customer's data is collected, the agent and customer are put back on the call using the **Conference All** option in another **Hold customer or agent** block.
7. The error branch runs if there's an error while capturing the customer's data.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Check contact attributes | Channel check (chat vs. voice) |
| Transfer to queue | Queue placement for chat contacts |
| Play prompt | Instructs customer that agent will be on hold |
| Hold customer or agent | Puts agent on hold |
| Store Customer Input | Captures and encrypts credit card data with .pem signing key |
| Hold customer or agent | Conference All — reconnects agent and customer |
| Play prompt | Error message if hold fails |

### Key Patterns Demonstrated

- **Secure data collection** — collecting sensitive info while agent cannot hear
- **Agent hold during data entry** — privacy protection pattern
- **Encryption with signing key** — .pem key-based encryption of DTMF input
- **Conference call management** — hold and reconnect patterns
- **Error handling** — graceful fallback on hold failure
- **Queue transfer flow type** — runs during queue-to-agent transfer

### Customer Experience

- Informed that agent will be on hold
- Enters credit card number via DTMF keypad
- Agent reconnects after data is captured

### Agent Experience

- Placed on hold during sensitive data entry
- Reconnected after customer finishes entering data
- Cannot hear or see the sensitive input

### Prerequisites/Dependencies

- **Encryption key** must be uploaded in **.pem format** in Amazon Connect
- Flow type is **Queue transfer** (not standard inbound)
- For production use, AWS recommends using full encryption

---

## 12. Sample Secure Input with No Agent

| Property | Value |
|----------|-------|
| **Exact Name** | Sample secure input with no agent |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates how to capture and encrypt sensitive customer data in an IVR flow without any agent involvement. |

### How It Works

1. Begins by checking the contact's **channel**:
   - **If chat**: A prompt plays saying this doesn't work with chat, and the contact is transferred to the **Sample inbound flow**.
2. **If voice**: The **Store customer input** block prompts the customer to enter their credit card number.
   - The block **stores and encrypts** the data using a **signing key** uploaded in **.pem format**.
3. In the **Set contact attributes** block, the encrypted card number is set as a contact attribute.
4. After the card number is successfully set, the customer is transferred back to the **Sample inbound flow**.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Check contact attributes | Channel check (chat vs. voice) |
| Play prompt | "This doesn't work with chat" message |
| Transfer to flow | Returns chat contacts to Sample inbound flow |
| Store customer input | Captures and encrypts credit card number with .pem signing key |
| Set contact attributes | Stores encrypted card number as contact attribute |
| Transfer to flow | Returns to Sample inbound flow after successful capture |

### Key Patterns Demonstrated

- **IVR-based secure data collection** — no agent involvement
- **Encryption at capture** — encrypting data immediately during DTMF input
- **Contact attributes for encrypted data** — storing encrypted values for downstream use
- **Channel validation** — gracefully handling unsupported channels
- **Agentless secure input** — complete self-service sensitive data collection

### Customer Experience

- **Voice**: Prompted to enter credit card number, then returned to main menu
- **Chat**: Told feature is unavailable for chat, returned to inbound flow

### Prerequisites/Dependencies

- **Encryption key** must be uploaded in **.pem format**
- Sample inbound flow (for transfer back)

---

## 13. Sample Recording Behavior Flow

| Property | Value |
|----------|-------|
| **Exact Name** | Sample recording behavior |
| **Flow Type** | Flow (inbound) |
| **Purpose** | Demonstrates how to configure call and chat recording/monitoring with the Set recording behavior block for different channels. |

### How It Works

The flow starts by checking the **channel** of the contact:

- **If task**: Transferred to the Sample inbound flow.
- **If chat**: A prompt explains that the **Set recording block** enables managers to monitor chat conversations.
  - To *record* chats, you only need to specify an **Amazon S3 bucket** where the conversation will be stored.
  - To *monitor* chats, the **Set recording block** is configured to record both the **Agent and Customer**.
- **If voice**: A **Get customer input** block prompts the customer to enter a number for who they want to record. Their entry triggers the **Set recording behavior** block with the appropriate configuration.

The flow ends with the customer being transferred back to the **Sample inbound flow**.

### Blocks Used

| Block | Configuration |
|-------|--------------|
| Check contact attributes | Channel check (voice/chat/task) |
| Transfer to flow | Task contacts → Sample inbound flow |
| Play prompt | Explains chat monitoring capability |
| Set recording behavior | Chat: records Agent and Customer |
| Get customer input | Voice: prompts for recording target selection |
| Set recording behavior | Voice: configured based on customer input |
| Transfer to flow | Returns to Sample inbound flow |

### Key Patterns Demonstrated

- **Recording configuration** — setting up call recording within a flow
- **Chat monitoring** — enabling supervisor monitoring of chat conversations
- **Recording vs. monitoring distinction** — recording needs S3 bucket, monitoring needs Set recording block
- **Per-channel recording settings** — different recording configs for voice and chat
- **Customer-driven recording selection** — letting the caller choose what gets recorded (demo purposes)

### Customer Experience

- **Voice**: Prompted to select recording target, then returned to inbound flow
- **Chat**: Informed about monitoring capability
- **Task**: Silently redirected to inbound flow

### Prerequisites/Dependencies

- Amazon S3 bucket configured for recording storage (for chat recording)
- Sample inbound flow (for return transfer)
- For more info see: "When, what, and where for contact recordings", "Enable contact recording", "Enable enhanced multi-party contact monitoring", "Review recorded conversations"

---

## Flow Relationship Map

```
Sample Inbound Flow (entry point)
  |
  |-- [chat/task] --> Sample Queue Configurations
  |                      |
  |                      |-- [voice callback] --> Transfer to callback queue
  |                      |-- [voice priority] --> Change routing priority/age
  |                      |-- [in-queue] --> Default Customer Queue (Loop prompts)
  |
  |-- [voice menu] --> Sample A/B Test --> (returns to Inbound)
  |                --> Sample Lambda Integration --> (returns to Inbound)
  |                --> Sample Recording Behavior --> (returns to Inbound)
  |                --> Sample Screenpop
  |                --> Sample Secure Input (with agent)
  |                --> Sample Secure Input (no agent) --> (returns to Inbound)
  |                --> Sample Queue Customer
  |                --> Sample Customer Queue Priority
  |
  |-- [disconnect] --> Sample Disconnect Flow
  |
  |-- [in-queue experience] --> Sample Interruptible Queue Flow with Callback
  |
  |-- [callback] --> Sample Queued Callback --> Sample Interruptible Queue Flow
```

---

## Summary Table

| # | Flow Name | Type | Primary Pattern |
|---|-----------|------|-----------------|
| 1 | Sample inbound flow | Flow (inbound) | Channel routing, IVR menu, entry point |
| 2 | Sample AB test | Flow (inbound) | Percentage-based A/B distribution |
| 3 | Sample customer queue priority | Flow (inbound) | Queue priority and routing age manipulation |
| 4 | Sample disconnect flow | Flow (inbound) | Per-channel disconnect handling |
| 5 | Sample queue configurations | Flow (inbound) | Queue management, priority, callbacks |
| 6 | Sample queue customer | Flow (inbound) | Pre-queue validation, hours check |
| 7 | Sample queued callback | Flow (inbound) | End-to-end callback queue setup |
| 8 | Sample interruptible queue flow with callback | Customer queue | In-queue callback interrupts |
| 9 | Sample Lambda integration | Flow (inbound) | Lambda data dip, external attributes |
| 10 | Sample note for screenpop | Flow (inbound) | CCP screenpop with contact attributes |
| 11 | Sample secure input with agent | Queue transfer | Encrypted input with agent on hold |
| 12 | Sample secure input with no agent | Flow (inbound) | Agentless encrypted IVR input |
| 13 | Sample recording behavior | Flow (inbound) | Recording and monitoring configuration |
