# Amazon Connect Default Flows -- Comprehensive Reference

Amazon Connect includes a set of default flows that handle common contact center scenarios out of the box. These flows trigger automatically during specific events (hold, transfer, queue, whisper, outbound calls) and can be customized or replaced.

---

## 1. Default Agent Hold

**Exact Name:** Default agent hold

**Flow Type:** Agent hold flow

**Description:**
This is the experience the agent receives when they are placed on hold. The flow loops a message to the agent at regular intervals so they know they are still on hold.

**Blocks (in order):**
1. **Loop prompts** -- Plays the text-to-speech message "You are on hold" to the agent every 10 seconds, repeating until hold ends.

**What the Agent Hears:**
The agent hears "You are on hold" repeated every 10 seconds while they remain on hold.

**What the Customer Hears:**
Nothing from this flow -- the customer has their own hold experience (see Default Customer Hold).

**When It Triggers:**
Automatically runs when an agent is placed on hold (e.g., during a conference or transfer scenario where the agent is held).

**Channel Support:**
- Voice: Yes
- Chat: Not applicable (hold is a voice concept)
- Task: Not applicable
- Email: Not applicable

**How to Customize:**
- Navigate to Routing > Flows > Default agent hold.
- Open the Loop prompts block to change the message or timing.
- The break time between messages can be set to a maximum of 10 seconds per prompt entry.
- To extend the interval beyond 10 seconds, add multiple prompts to the loop. For example, for 20 seconds between messages:
  - First prompt: "You are on hold" with break time = 10s
  - Second prompt: blank message with break time = 10s
- Save and Publish.

**Caveats and Limitations:**
- Break time maximum is 10 seconds per prompt entry. You must chain multiple prompts to get longer intervals.

**Tips:**
- To check if a default flow has been changed, use flow version control to view the original version of the flow.

---

## 2. Default Agent Transfer

**Exact Name:** Default agent transfer

**Flow Type:** Transfer flow (Agent transfer)

**Description:**
This is the flow the "from" agent experiences when they transfer a contact to another agent using quick connects. The agent hears a brief transfer message, and then the contact is transferred.

**Blocks (in order):**
1. **Play prompt** -- Plays the text-to-speech message "Transferring now" to the "from" agent.
2. **Transfer to agent** -- Transfers the contact to the destination agent.

**What the "From" Agent Hears:**
"Transferring now."

**What the "To" Agent Hears:**
The Default agent whisper flow runs for the receiving agent (plays the queue name).

**What the Customer Experiences:**
The customer is transferred and connected to the new agent.

**When It Triggers:**
Automatically runs when an agent initiates an agent-to-agent transfer via quick connects.

**Channel Support:**
- Voice: Yes
- Chat: The Transfer to Agent block is a beta feature and only works for voice interactions. To transfer a chat contact to another agent, you must use contact attributes to route contacts to a specific agent via a queue.
- Task: Not specified
- Email: Not specified

**How to Customize:**
- Navigate to Routing > Flows > Default agent transfer.
- Modify the Play prompt message or add additional blocks.
- Save and Publish.

**Caveats and Limitations:**
- The Transfer to Agent block is a beta feature and only works for voice interactions.
- For chat transfers to another agent, you must use the contact attributes method (route contacts to a specific agent queue) instead of the Transfer to Agent block.

**Tips:**
- To check if a default flow has been changed, use flow version control to view the original version of the flow.

---

## 3. Default Customer Queue

**Exact Name:** Default customer queue

**Flow Type:** Customer queue flow

**Description:**
This flow runs when a customer is placed in a queue waiting for an agent. It provides an initial greeting message followed by hold music, looping until an agent picks up.

**Blocks (in order):**
1. **Loop prompts** -- Contains:
   - A one-time voice prompt (text-to-speech): "Thank you for calling. Your call is very important to us and will be answered in the order it was received."
   - Queue music in .wav format (uploaded to the Connect instance).
2. The customer remains in this loop until their call is answered by an agent.

**What the Customer Hears:**
1. First, the greeting: "Thank you for calling. Your call is very important to us and will be answered in the order it was received."
2. Then, queue music plays on loop until an agent answers.

**What the Agent Hears:**
Nothing from this flow.

**When It Triggers:**
Automatically runs when a customer is placed into a queue (after routing decisions in the inbound flow).

**Channel Support:**
- Voice: Yes
- Chat: NOT supported out of the box. The Loop prompts block only supports voice contacts. The flow will fail for chat contacts without modifications.
- Task: NOT supported out of the box. Will fail without modifications. AWS recommends creating a new flow that checks the channel and routes appropriately.
- Email: NOT supported out of the box. Will fail without modifications.

**How to Customize:**
1. Navigate to Routing > Flows > Default customer queue.
2. Open the Loop prompts block properties.
3. Use the dropdown to choose different music, or switch to Text to Speech and type a custom message.
4. Save and Publish. Connect starts playing the new message almost immediately (may take a few moments to fully take effect).

**Caveats and Limitations:**
- Does NOT support chat, tasks, or email contacts out of the box. It will fail for these channels without changes.
- The Loop prompts block only supports voice contacts.
- For non-voice channels, create a new flow that checks the channel first and routes accordingly.
- For tasks specifically, see AWS documentation on "How to send tasks to a queue."

**Tips:**
- You can add promotional or self-service messages to the queue prompt (e.g., "Did you know you can reset your own password at the login page?").
- Changes take effect almost immediately after publishing, though there may be a brief delay.

---

## 4. Default Customer Whisper

**Exact Name:** Default customer whisper

**Flow Type:** Customer whisper flow

**Description:**
This flow plays a brief notification sound to the customer when their call is connected to an agent. It uses the Set whisper flow block to play a "beep" sound, letting the customer know the connection has been made.

**Blocks (in order):**
1. **Set whisper flow** -- Plays a "beep" sound to the customer when the customer and agent are joined.

**What the Customer Hears:**
A "beep" sound indicating their call has been connected to an agent.

**What the Agent Hears:**
Nothing from this flow (the agent has their own whisper -- see Default Agent Whisper).

**When It Triggers:**
Automatically runs at the moment the customer is connected to an agent, just before the conversation begins.

**Channel Support:**
- Voice: Yes (default whisper plays automatically)
- Chat: NOT included by default. Chat conversations do not include a default whisper. You must explicitly add a Set whisper flow block in your inbound flow for chat to enable whispers.
- Task: Not specified
- Email: Not specified

**How to Customize:**
- Use the Set whisper flow block in your contact flow to override or disable the default customer whisper for voice conversations.
- Change the beep to a custom message or different audio.
- For chat, you must explicitly add a Set whisper flow block after the chat channel branch in your inbound flow.

**Caveats and Limitations:**
- Chat conversations do NOT include a default whisper. You must explicitly configure whispers for chat.
- Voice whispers play automatically; chat whispers require manual flow configuration.

**Tips:**
- You can disable the whisper entirely by using the Set whisper flow block with no content, which removes the brief delay before connection.

---

## 5. Default Agent Whisper

**Exact Name:** Default agent whisper

**Flow Type:** Agent whisper flow

**Description:**
This flow plays a message to the agent when they are connected to a customer. The message tells the agent which queue the customer was in, helping the agent understand the context of the incoming contact.

**Blocks (in order):**
1. **Set whisper flow** -- Plays the name of the queue to the agent using the system variable `$.Queue.Name`.

**What the Agent Hears:**
The name of the queue that the customer was waiting in (e.g., "Sales" or "Support"). This is retrieved from the system variable `$.Queue.Name`.

**What the Customer Hears:**
Nothing from this flow.

**When It Triggers:**
Automatically runs at the moment the agent is connected to a customer, just before the conversation begins.

**Channel Support:**
- Voice: Yes (default whisper plays automatically)
- Chat: NOT included by default. Chat conversations do not include a default whisper. You must explicitly add a Set whisper flow block in your inbound flow for chat to enable whispers. This is useful when agents manage multiple queues so they can see which queue the chat originated from.
- Task: Not specified
- Email: Not specified

**How to Customize:**
- Use the Set whisper flow block in your contact flow to override or disable the default agent whisper for voice conversations.
- Change the queue name announcement to a custom message with additional context.
- For chat, explicitly add a Set whisper flow block after the chat channel branch in your inbound flow, selecting "Default agent whisper" (or a custom whisper) in its properties.

**Caveats and Limitations:**
- Chat conversations do NOT include a default whisper. Must be configured explicitly.
- The queue name is read via text-to-speech, so unusual queue names may sound awkward.

**Tips:**
- To check if a default flow has been changed, use flow version control to view the original version.
- The system variable `$.Queue.Name` is documented under system attributes in the Connect admin guide.
- For chat, setting the default agent whisper is especially helpful when agents handle multiple queues, as it shows the originating queue name in the chat window.

---

## 6. Default Customer Hold

**Exact Name:** Default customer hold

**Flow Type:** Customer hold flow

**Description:**
This flow manages the customer's experience when they are placed on hold by an agent during a call. It plays hold music to the customer.

**Blocks (in order):**
1. **Loop prompts** (implied) -- Plays hold music/audio to the customer while they are on hold.

**What the Customer Hears:**
Hold music plays continuously while the customer is on hold.

**What the Agent Hears:**
Nothing from this flow (the agent has their own hold experience -- see Default Agent Hold).

**When It Triggers:**
Automatically runs when an agent puts the customer on hold during an active call.

**Channel Support:**
- Voice: Yes
- Chat: Not applicable (hold is a voice concept)
- Task: Not applicable
- Email: Not applicable

**How to Customize:**
- Navigate to Routing > Flows > Default customer hold.
- Modify the hold music or add text-to-speech messages.
- You can use "Save as" to create a copy, name it (e.g., "Customer hold message"), and then reference the custom flow in your contact flows.
- Save and Publish.

**Caveats and Limitations:**
- AWS documentation for this flow is minimal; it simply plays hold audio.

**Tips:**
- To check if a default flow has been changed, use flow version control to view the original version.
- Consider adding periodic messages between music segments (e.g., "Thank you for holding, an agent will be with you shortly") to improve the customer experience.

---

## 7. Default Outbound

**Exact Name:** Default outbound

**Flow Type:** Outbound whisper flow

**Description:**
This flow manages what the customer experiences as part of an outbound call, before being connected with an agent. It is an outbound whisper flow that optionally sets recording behavior and plays a notification about recording status.

**Blocks (in order):**
1. **Set recording behavior** (optional) -- Configures call recording settings.
2. **Play prompt** -- Plays the text-to-speech message: "This call is not being recorded."
3. The flow ends. The customer remains on the call after the flow completes.

**What the Customer Hears:**
"This call is not being recorded." (before being connected to the agent)

**What the Agent Hears:**
Nothing specific from this flow.

**When It Triggers:**
Automatically runs when an outbound call is placed from the Connect instance.

**How Outbound Flow Execution Works:**
- Before the call is made: All blocks before the first Play prompt are executed.
- After the customer picks up: The first Play prompt and all blocks after it are executed.

**Channel Support:**
- Voice: Yes
- Chat: Not applicable (outbound whisper is a voice concept)
- Task: Not applicable
- Email: Not applicable

**How to Customize:**
- Navigate to Routing > Flows > Default outbound.
- Change the Play prompt message (e.g., to "This call may be recorded for quality purposes").
- Modify the Set recording behavior block to enable or configure recording.
- Save and Publish.

**Caveats and Limitations:**
- Before using the Send message block in an outbound flow, see the AWS documentation section "Important information about using the Send message block in outbound flows" for recommended safeguards.
- The flow execution split (before vs. after customer picks up) is important to understand when designing custom outbound flows.

**Tips:**
- To check if a default flow has been changed, use flow version control to view the original version.
- Remember the execution split: blocks before the first Play prompt run before the call connects; blocks from the first Play prompt onward run after the customer answers.

---

## 8. Default Queue Transfer

**Exact Name:** Default queue transfer

**Flow Type:** Transfer flow (Queue transfer)

**Description:**
This flow manages the agent's experience when they transfer a customer to another queue. It checks hours of operation and agent availability before completing the transfer.

**Blocks (in order):**
1. **Check hours of operation** -- Checks the hours of operation for the target queue.
   - **In hours** branch: Proceeds to Check staffing.
   - **Out of hours** branch: Plays a prompt and disconnects.
2. **Check staffing** -- Determines whether agents are available, staffed, or online in the target queue.
   - **True** (agents available): Proceeds to Transfer to queue.
   - **False** (no agents available): Plays a prompt and disconnects the call.
3. **Transfer to queue** -- Transfers the contact to the destination queue.

**What the Agent Experiences:**
The transfer is processed. If the transfer fails (out of hours or no agents), the flow plays a message and disconnects.

**What the Customer Experiences:**
The customer is transferred to the new queue and enters that queue's customer queue flow.

**When It Triggers:**
Automatically runs when an agent initiates a queue-to-queue transfer.

**Channel Support:**
- Voice: Yes
- Chat: Not explicitly specified, but queue transfers are supported for chat
- Task: Not explicitly specified
- Email: Not explicitly specified

**How to Customize:**
- Navigate to Routing > Flows > Default queue transfer.
- Modify the hours of operation check, staffing check logic, or the failure prompts.
- Add additional routing logic or fallback queues.
- Save and Publish.

**Caveats and Limitations:**
- If the target queue is out of hours or has no available agents, the call is disconnected after a prompt. There is no built-in fallback to another queue.

**Tips:**
- To check if a default flow has been changed, use flow version control to view the original version.
- Consider adding fallback logic (e.g., transfer to a voicemail queue or overflow queue) instead of disconnecting when no agents are available.

---

## 9. Default Prompts from Amazon Lex

**Exact Name:** Default prompts from Amazon Lex (not a Connect flow per se)

**Flow Type:** N/A -- These are Amazon Lex bot error-handling prompts, not a Connect flow.

**Description:**
When you add an Amazon Lex classic bot (not Amazon Lex V2) to your contact center, the bot includes default error-handling prompts. These are the messages the bot uses when it cannot understand the customer.

**Default Prompts:**
- "Sorry, can you please repeat that?"
- "Sorry, I could not understand. Goodbye."

**What the Customer Hears:**
The Lex bot's error messages when it fails to understand the customer's input.

**When It Triggers:**
When an Amazon Lex classic bot encounters an error or cannot match the customer's utterance to an intent.

**Channel Support:**
- Voice: Yes (via Lex bot integration)
- Chat: Yes (via Lex bot integration)
- Task: Not applicable
- Email: Not applicable

**How to Customize:**
1. In the Amazon Lex console, go to your bot.
2. On the Editor tab, choose Error Handling.
3. Change the text as needed.
4. Choose Save, then Build and Publish.

**Caveats and Limitations:**
- This applies only to Amazon Lex classic bots, NOT Amazon Lex V2.
- Changes are made in the Lex console, not in Amazon Connect.
- You must Build and Publish the bot for changes to take effect.

**Tips:**
- Customize these prompts to match your brand voice and provide helpful guidance to customers.

---

## 10. How to Change a Default Flow

**Page:** Change a default flow in your Connect Customer contact center

**Overview:**
You can override default flows by editing them directly, but AWS generally recommends creating new flows based on the defaults rather than editing the defaults directly. This gives you more control and preserves the original as a reference.

**Method 1: Edit the Default Flow Directly**
1. Navigate to Routing > Flows.
2. Choose the default flow you want to customize (e.g., Default customer queue).
3. Open the relevant block (e.g., Loop prompts) to modify its properties.
4. Change the message, music, or behavior as needed.
5. Save and Publish.
6. Changes take effect almost immediately (may take a few moments to fully propagate).

**Method 2: Copy the Default Flow Before Customizing (Recommended)**
1. Navigate to Routing > Flows.
2. Choose the default flow you want to customize.
3. In the upper right corner, choose the Save dropdown arrow, then select "Save as."
4. Assign a new name (e.g., "Customer hold message").
5. Make your customizations to the copy.
6. Add the new custom flow to your other flows so it runs instead of the default (e.g., reference it via a Set whisper flow block or Set customer queue flow block).

**Caveats and Limitations:**
- Editing a default flow directly affects all contacts that use it across your instance.
- There is no "reset to default" button -- use flow version control to view the original version.

**Tips:**
- AWS recommends copying the default flow and giving it a custom name rather than editing the original.
- Use flow version control to view the original version of any default flow if you need to compare or revert.

---

## 11. Set Default Whisper Flow for Chat

**Page:** Set the default whisper flow in Connect Customer for a chat conversation

**Overview:**
Chat conversations do NOT include a default whisper automatically (unlike voice). You must explicitly add a Set whisper flow block in your inbound contact flow for chat whispers to play.

**Step-by-Step Instructions:**
1. Go to Routing > Flows, and choose your inbound flow (e.g., Sample inbound flow).
2. Add a **Set whisper flow** block after the chat channel has branched (use a Check contact attributes or similar block to branch by channel).
3. In the Set whisper flow block properties, choose the flow you want to play as the default for chat conversations. For example:
   - Choose "Default agent whisper" to show agents the name of the originating queue in the chat window.
4. Save and Publish.

**When to Use This:**
- When agents handle multiple queues and need to know which queue a chat came from.
- When you want customers to receive a notification or message when connected to an agent via chat.

**Channel-Specific Behavior:**
- Voice: Whispers play automatically via the default whisper flows. No extra configuration needed.
- Chat: Whispers do NOT play automatically. You must explicitly add Set whisper flow blocks in your contact flow.

**Caveats and Limitations:**
- If you do not explicitly set a whisper flow for chat, no whisper will play -- there is no automatic fallback.
- The Set whisper flow block must be placed after the channel branch in your flow.
- You can set both agent and customer whispers for chat by adding separate Set whisper flow blocks.

**Tips:**
- Setting the default agent whisper for chat is especially useful when agents manage multiple queues, as it displays the originating queue name in the chat window.

---

## Summary Table

| Default Flow | Flow Type | Voice | Chat | Task | Email | Auto-Triggers When |
|---|---|---|---|---|---|---|
| Default agent hold | Agent hold | Yes | N/A | N/A | N/A | Agent placed on hold |
| Default agent transfer | Agent transfer | Yes | Beta only | -- | -- | Agent-to-agent transfer via quick connects |
| Default customer queue | Customer queue | Yes | Fails | Fails | Fails | Customer enters a queue |
| Default customer whisper | Customer whisper | Yes | Manual setup required | -- | -- | Customer connected to agent |
| Default agent whisper | Agent whisper | Yes | Manual setup required | -- | -- | Agent connected to customer |
| Default customer hold | Customer hold | Yes | N/A | N/A | N/A | Customer placed on hold |
| Default outbound | Outbound whisper | Yes | N/A | N/A | N/A | Outbound call placed |
| Default queue transfer | Queue transfer | Yes | -- | -- | -- | Agent transfers to another queue |

**Legend:** "Fails" = flow will error without modifications. "Manual setup required" = must explicitly add Set whisper flow block. "N/A" = concept does not apply to channel. "--" = not explicitly documented.

---

## General Tips (Applicable to All Default Flows)

1. **Version Control:** Use flow version control to view the original version of any default flow. This helps you compare changes or understand the baseline behavior.

2. **Copy Before Editing:** AWS recommends using "Save as" to copy a default flow before customizing it. This preserves the original and gives you a clean reference.

3. **Chat Whispers:** Chat does NOT get automatic whispers. You must explicitly add Set whisper flow blocks in your inbound flow after branching by channel.

4. **Customer Queue and Non-Voice:** The Default customer queue flow only supports voice. For chat, tasks, and email, create a custom flow that checks the channel first.

5. **Publish to Activate:** All changes to default flows require publishing. Changes take effect almost immediately but may need a few moments to fully propagate.

6. **Outbound Flow Execution Split:** In outbound flows, blocks before the first Play prompt run before the call connects; blocks from the first Play prompt onward run after the customer answers.
