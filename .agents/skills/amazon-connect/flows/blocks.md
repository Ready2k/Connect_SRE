# Amazon Connect Flow Blocks Reference

53 flow blocks organized by category. Voice ID blocks (Check Voice ID, Set Voice ID) are excluded — Voice ID reaches end of support May 2026. AWS lists 55 total blocks including those two.

## Quick Reference

| Category | Count | Blocks |
|----------|-------|--------|
| Interact | 10 | Play prompt, Get customer input, Store customer input, Loop prompts, Hold customer or agent, Get stored content, Connect assistant, Show view, Send message, Authenticate Customer |
| Set | 15 | Set contact attributes, Set customer queue flow, Set hold flow, Set whisper flow, Set disconnect flow, Set event flow, Set working queue, Set callback number, Set voice, Set logging behavior, Set recording and analytics behavior, Set recording analytics and processing behavior, Set routing criteria, Set Touchtone Buffer Behavior, Contact tags |
| Branch | 7 | Check contact attributes, Check hours of operation, Check queue status, Check staffing, Distribute by percentage, Check call progress, Get metrics |
| Integrate | 6 | Invoke AWS Lambda function, Customer profiles, Cases, Data Table, Create task, Create persistent contact association |
| Transfer & Disconnect | 7 | Transfer to queue, Transfer to agent (beta), Transfer to phone number, Transfer to flow, Disconnect/hang up, End flow/Resume, Resume contact |
| Flow Control | 4 | Invoke module, Return, Loop, Wait |
| Media & Streaming | 2 | Start media streaming, Stop media streaming |
| Outbound | 1 | Call phone number |
| Routing | 1 | Change routing priority/age |
| **Total** | **53** | |

---

## Interact

Blocks that interact with the contact (play audio, collect input, display views).


### Play prompt

**Description**: Plays an audio prompt, a text-to-speech message, or sends a chat response to customers and agents. For calls, you can use pre-recorded prompts (from the Connect library or uploaded), prompts stored in Amazon S3, or text-to-speech (plain text or SSML via Amazon Polly). For chats, only text prompts are supported -- audio options are not available.

**Channels**:
- Voice: Yes
- Chat: Yes (if configured for calls, routes to Error branch)
- Task: Yes (if configured for calls, routes to Error branch)
- Email: No (takes Success branch but has no effect)

Note: A callback contact without an agent or customer is routed to the Error branch.

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: Yes (library prompts only, not S3)
- Customer hold flow: No (use Loop prompts instead)
- Customer whisper flow: Yes (library prompts only, not S3)
- Outbound whisper flow: Yes (library prompts only, not S3)
- Agent hold flow: No (use Loop prompts instead)
- Agent whisper flow: Yes (library prompts only, not S3)
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes

**Properties**:
- **Prompt source -- Prompt library (audio)**: Select from pre-recorded prompts included with Connect or upload your own via the admin website. No bulk upload supported.
- **Prompt source -- S3 bucket audio file**: Specify an audio file path from an S3 bucket. Can be set manually, via attributes, via concatenation (e.g., personalize by language/LOB), or dynamically using user-defined contact attributes.
- **Prompt source -- Text-to-speech or chat text**: Enter plain text or SSML to be spoken as audio (via Amazon Polly) or sent as chat text. Supports contact attributes for dynamic text.
- **Skip or interrupt this prompt when touchtone buffering is enabled**: Checkbox. When selected and touchtone buffering is active: if the buffer already contains digits, the prompt is skipped entirely; if the buffer is empty, the prompt begins playing and can be interrupted by a keypress. When not selected (default), the prompt plays normally regardless of buffer state.

**Branches**:
- **Success**: The audio or text message was played/sent successfully.
- **Error**: Failed to play the audio or text message.
- **Okay**: Legacy branch on older block versions that lack an Error branch. Always taken at runtime. Updating the block configuration automatically adds an Error branch.

**Tips**:
- Supported audio format: .wav files, 8KHz, mono channel, U-Law encoding. Use third-party tools to convert.
- Maximum prompt size: less than 50MB and less than 5 minutes.
- For S3 prompts in opt-in Regions (e.g., Africa/Cape Town), the bucket must be in the same Region as your Connect instance.
- For best S3 performance, create the bucket in the same Region as your Connect instance.
- Text-to-speech/chat text maximum: 3,000 billed characters (6,000 total characters). Can use contact attributes.
- This block does not generate any data.
- Error scenarios: incorrect S3 path or bucket policy, incorrect audio format, file > 50MB or > 5 minutes, incorrect SSML, text > 6,000 characters, incorrect prompt ARN, callback contact without agent/customer.

---

### Get customer input

**Description**: Captures interactive and dynamic input from customers. Supports interruptible prompts with DTMF input (phone keypad) and Amazon Lex bots for voice-activated prompts. This block accepts only individual digits (0-9) and the special characters # and *. Multi-digit entries are not supported -- for multiple entries (e.g., credit card numbers), use the Store customer input block instead.

**Channels**:
- Voice: Yes
- Chat: Yes (only when Amazon Lex is used; otherwise takes Error branch)
- Task: No
- Email: No

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: Yes
- Customer hold flow: No
- Customer whisper flow: No
- Outbound whisper flow: Yes
- Agent hold flow: No
- Agent whisper flow: No
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes

**Properties**:

*Prompt Selection:*
- **Prompt library (audio)**: Choose from pre-recorded prompts or upload your own.
- **S3 bucket audio file**: Specify an audio file from S3 manually or dynamically.
- **Text-to-speech or chat text**: Enter plain text or SSML. Maximum 3,000 billed characters (6,000 total).

*DTMF Configuration:*
- **Set timeout**: How long to wait for the customer to respond (1-180 seconds). After this, a timeout error occurs. For Voice, this is the timeout until the first DTMF digit.
- **Add condition**: The digit value(s) to compare customer input against for branching.

*Amazon Lex Configuration:*
- **Select a Lex bot / Enter an ARN**: Choose or specify the Lex bot to use. Only built bots appear in the dropdown.
- **Session attributes**: Lex session attributes for the current contact session (e.g., max speech duration, start/end silence thresholds, barge-in, DTMF settings).
- **Intents**: Add intent names to branch on. Can be entered manually, searched, or selected from a dropdown filtered by locale.
- **Use sentiment override**: Branch based on sentiment score before the Lex intent. Negative sentiment is always evaluated first. Based on last utterance, not the entire conversation.
- **Initialize bot with message**: Pass the customer's initial message or a custom message to initialize the Lex bot.
  - *Use initial customer utterance (text-only)*: Serializes with `$.Media.InitialMessage`.
  - *Set manually*: Plain text or attribute references, max 1,024 characters.
  - *Set dynamically*: Any attribute with text value, max 1,024 characters.
- **Chat timeout**: How long until inactive customers timeout in a Lex interaction (min: 1 minute, max: 7 days).

*Voice Timeout Session Attributes (Lex):*
- **Max Speech Duration** (`x-amz-lex:audio:max-length-ms`): How long the customer speaks before input is truncated. Default: 12,000ms. Maximum: 15,000ms. Setting above 15,000ms routes to Error branch.
- **Start Silence Threshold** (`x-amz-lex:audio:start-timeout-ms`): How long to wait before assuming customer won't speak. Default: 3,000ms.
- **End Silence Threshold** (`x-amz-lex:audio:end-timeout-ms`): How long to wait after customer stops speaking. Default: 600ms.

*Barge-in (Lex V2):*
- Enabled globally by default; can be disabled in the Lex console. Modifiable via `x-amz-lex:allow-interrupt` session attribute.

*Barge-in (Lex Classic):*
- Disabled globally by default. Must set `x-amz-lex:barge-in-enabled` session attribute to enable.

*DTMF Session Attributes (Lex):*
- **End character** (`x-amz-lex:dtmf:end-character`): Ends the utterance. Default: #.
- **Deletion character** (`x-amz-lex:dtmf:deletion-character`): Clears accumulated DTMF digits and ends utterance. Default: *.
- **End timeout** (`x-amz-lex:dtmf:end-timeout-ms`): Idle time between digits before utterance is considered concluded. Default: 5,000ms.
- **Max DTMF digits per utterance** (`x-amz-lex:dtmf:max-length`): Maximum digits allowed. Default: 1,024 characters. Cannot be increased.

*Touchtone Buffering:*
- In DTMF mode: if the buffer contains a digit, dequeues a single digit and routes to matching branch immediately (skipping prompt). If empty, prompts as usual.
- In Lex mode: buffer is automatically cleared before bot interaction. Buffered digits are not used.

**Branches**:
- **Pressed [digit]** (DTMF conditions): Routes based on the specific digit the customer pressed.
- **[Intent name]** (Lex intents): Routes based on matched Lex intent.
- **Sentiment score** (Lex): Routes based on negative/positive sentiment thresholds.
- **Timeout**: No input provided within the configured timeout period.
- **Default**: Customer input doesn't match any DTMF condition, or no matching Lex intent.
- **Error**: Block execution fails, or Lex intent not fulfilled.

**Tips**:
- Session attributes have an order of precedence: (1) Lambda-provided overrides, (2) Console-provided in the block, (3) Service defaults.
- Prompt customers to end input with # and cancel with *. Without prompting for #, customers wait 5 seconds for Lex to stop waiting.
- Wildcards can be used in session attributes (e.g., `x-amz-lex:max-speech-duration-ms:*:*`). Wildcards apply across bots but NOT across blocks in a flow.
- If DTMF input is provided to a Lex bot, it's available as request attribute `x-amz-lex:dtmf-transcript` (max 1,024 characters).
- There is setup time between flows when using Transfer to flow. If the customer enters DTMF too quickly, digits may be dropped. Customer should wait for the prompt before entering input.
- If the initial message attribute is not included as part of the contact, the contact routes to the Error branch.
- This block does not generate any data.

---

### Store customer input

**Description**: Similar to Get customer input, but stores the input as a contact attribute (in the Stored customer input system attribute) and allows encryption. Plays a prompt to get a response from the customer, plays an interruptible audio prompt or text-to-speech, stores numerical input, and allows a custom terminating keypress. If during a call the customer doesn't enter any input, the contact is routed down the Success branch with a value of "Timeout" -- use a Check contact attributes block to detect this.

**Channels**:
- Voice: Yes
- Chat: No (Error branch)
- Task: No (Error branch)
- Email: No (Error branch)

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: Yes
- Outbound whisper flow: Yes
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes

**Properties**:
- **Prompt**: Select from the prompt library (audio), specify an S3 audio file, or use text-to-speech. Same options as the Play prompt block.
- **Maximum Digits**: Define the maximum number of digits a customer can enter.
- **Phone number**: Useful for queued callback scenarios.
  - *Local format*: Select a country; Connect auto-populates the country code for customers.
  - *International format*: Requires customers to enter their country code.
- **Timeout before first entry**: How long to wait for the customer to start entering their reply (e.g., 20 seconds to get a credit card).
- **Timeout in between each entry**: How long to wait for the next input digit (min: 1 second, max: 20 seconds, default: 5 seconds).
- **Encrypt entry**: Encrypt the customer's entry (e.g., credit card information).
- **Specify terminating keypress**: Define a custom terminating keypress (up to 5 digits, using #, *, and 0-9). To use * as part of the terminating keypress, you must also choose Disable cancel key.
- **Disable cancel key**: By default, * deletes all prior DTMF input. When disabled, * is treated as any other key. Affects input sent to Lambda:
  - Selected: all characters including * are sent.
  - Not selected: only the * is sent.

*Touchtone Buffering:*
- Buffered digits are automatically used as input. If the buffer has enough digits to meet the configured maximum, the prompt is skipped entirely.
- If the buffer has fewer digits than the max, the block waits for remaining digits using the inter-digit timeout.
- Custom terminating keypresses are respected in the buffer.

**Branches**:
- **Success**: Customer input was successfully captured (note: a "Timeout" value may be stored if no input was entered).
- **Error**: Block execution failed.
- **Invalid number**: Customer entered an invalid number (applies when Phone number format is selected).

**Tips**:
- There is setup time between flows when using Transfer to flow. If the customer enters DTMF too quickly for a second flow, digits may be dropped. Customer should wait for the prompt.
- Use Check contact attributes after this block to check for timeout scenarios.
- Example with Disable cancel key: customer enters `1#2#3*4###` with `##` as terminator -- Lambda receives `1#2#3*4#`. Program Lambda to ignore the character before * to interpret as `1#2#4#`.

---

### Loop prompts

**Description**: Loops a sequence of prompts while a customer or agent is on hold or in a queue.

**Channels**:
- Voice: Yes
- Chat: No (Error branch)
- Task: No (Error branch)
- Email: No (Error branch)

**Flow Types**:
- Customer queue flow: Yes
- Customer hold flow: Yes
- Agent hold flow: Yes

**Properties**:
- **Prompts**: Add one or more prompts of the following types:
  - *Audio recording*: Select from the Connect prompt library.
  - *Text to Speech*: Enter plain text or SSML.
  - *S3 file path*: Specify an audio file from S3.
- **Interrupt**: Set the interval (in seconds) at which the prompt loop is interrupted for flow logic (e.g., offering a callback). The interrupt resets the loop based on the "Continue prompts during interrupt" setting.
- **Continue prompts during interrupt**: When NOT enabled, after the interrupt timeout, the flow executes the timeout branch logic and then restarts prompts from the beginning of the first prompt. When ENABLED, after the interrupt timeout: if the timeout branch has no audio-playing blocks, playback continues from where it was interrupted (seamless to customer); if the timeout branch includes audio blocks (Play prompt, Get customer input, etc.), the loop prompt is interrupted, timeout branch audio plays, then resumes at the start of the NEXT prompt in the sequence.

**Branches**:
- **Timeout**: Triggered when the interrupt interval elapses. Routes to timeout branch for flow logic (e.g., callback offers, queue position updates).
- **Error**: Block execution failed. Also triggered if a chat contact reaches this block.

**Tips**:
- The following blocks are NOT allowed before the Loop prompts block: Get customer input, Loop, Play prompt, Start media streaming, Stop media streaming, Store customer input, Transfer to phone number, Transfer to queue (including Transfer to callback queue).
- Always use an interruption period greater than 20 seconds. Connect does not support dequeuing a customer during the 20-second agent acceptance window -- shorter periods may cause contacts to go down the Error branch.
- The internal loop counter is persisted for the call, not the flow. If the flow is reused during a call, the counter is not reset.
- Some older flows have a version without an Error branch. In that case, a chat contact stops execution of the customer queue flow, and the chat is routed when the next agent becomes available.
- When used in a Queue flow, audio playback can be interrupted with a flow at preset times.

---

### Hold customer or agent

**Description**: Places a customer or agent on or off hold. Useful when, for example, you want to put the agent on hold while the customer enters credit card information. If triggered during a chat conversation, the contact routes to the Error branch.

Note: During a video call or screen sharing session, agents can see the customer's video/screen share even when the customer is on hold. It is the customer's responsibility to handle PII accordingly. Custom CCP and communication widget can be built to change this behavior.

**Channels**:
- Voice: Yes
- Chat: No (Error branch)
- Task: No (Error branch)
- Email: No (Error branch)

**Flow Types**:
- Inbound flow: Yes
- Outbound whisper flow: Yes
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes

**Properties**:
- **Hold option** (dropdown with three choices):
  - *Agent on hold*: The customer is on the call (agent is placed on hold).
  - *Customer on hold*: The agent is on the call (customer is placed on hold).
  - *Conference all*: Both agent and customer are on the call (no one is on hold).

**Branches**:
- **Success**: The hold/conference action completed successfully.
- **Error**: The action failed, or a non-voice contact reached this block.

**Tips**:
- Use in combination with Store customer input to securely collect sensitive data while the agent is on hold.
- During video/screen sharing, the agent can still see the customer's feed while the customer is on hold.

---

### Get stored content

**Description**: Retrieves stored data from your S3 bucket for use in flow branching decisions. Currently supports retrieving email message bodies in plain text format. Downloads the plain text version of the email message from S3 and stores it on the `$.Email.EmailMessage.Plaintext` flow attribute. Maximum supported size is 32 KB due to flow attribute limits. Email must be enabled for your Connect instance before using this option.

**Channels**:
- Voice: No
- Chat: No
- Task: No
- Email: Yes

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: Yes
- Customer hold flow: Yes
- Customer whisper flow: Yes
- Outbound whisper flow: Yes
- Agent hold flow: Yes
- Agent whisper flow: Yes
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes
- Disconnect flow: Yes

**Properties**:
- **Content Type**: Currently only "Email message (Plain text)" is available. Downloads the plain text version of the email from S3.

**Branches**:
- **Success**: Content was retrieved successfully and stored in the flow attribute.
- **Error**: Failed to retrieve the content.

**Tips**:
- Use with Check contact attributes block to inspect the email body (Namespace: Email, Key: Email Message) and add conditions for routing (e.g., route emails containing "Refund" to a specific queue). Note: keywords are case-sensitive.
- Use with Send message block to configure automated email responses after inspecting content.
- Maximum plain text email size: 32 KB. Larger emails route to the Error branch.
- Error scenarios: email size exceeds 32KB in plain text, S3 bucket policy not configured correctly, Connect lacks access to S3, or no plain text email message available on the contact.

---

### Connect assistant

**Description**: Associates a Connect assistant (Amazon Q in Connect) domain to a contact to enable real-time recommendations for agents. If you choose to customize your Connect AI agents, you need to create a Lambda and use the AWS Lambda function block instead.

**Channels**:
- Voice: Yes
- Chat: Yes
- Task: Yes
- Email: Yes

Note: Nothing happens if an outbound email is sent to this block, however you WILL be charged. Add a Check contact attributes block before this one to route tasks and outbound emails accordingly.

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: Yes
- Outbound whisper flow: Yes
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes

**Properties**:
- **Assistant domain ARN**: The full Amazon Resource Name (ARN) of the Connect assistant domain to associate to the contact.
- **Orchestration AI agent**: The AI agent to use for Agent Assistance.

**Branches**:
- **Success**: The assistant domain was associated to the contact successfully.
- **Error**: Failed to associate the assistant domain.

**Tips**:
- For voice/calls: You must enable Contact Lens real-time in the flow by adding a Set recording and analytics behavior block configured for Contact Lens real-time. The position of this block in the flow does not matter.
- Contact Lens is NOT required for using Connect AI agents with chats.
- Connect AI agents with Contact Lens real-time analytics recommend content related to customer issues detected during the current call.

---

### Show view

**Description**: Creates step-by-step workflow guides for agents in the Connect agent workspace, and interactive forms for customers within chat experiences. When a contact is routed to a flow with a Show view block, a UI page called a View renders on the agent workspace or within the customer's chat UI.

**Channels**:
- Voice: Yes (via guide flows initiated by Set event flow)
- Chat: Yes
- Task: Yes
- Email: Yes

**Flow Types**:
- Inbound flow: Yes
- Customer hold flow: No
- Customer whisper flow: No
- Outbound whisper flow: No
- Agent hold flow: No
- Agent whisper flow: No
- Transfer to agent flow: No
- Transfer to queue flow: No

**Properties**:
- **View**: Select the view resource to render. AWS managed views include:
  - *Detail view*: Display information and a list of actions. Common for screen-pops at call start.
  - *List view*: Display items as a list with titles, descriptions, and optional actions/links. Supports back navigation and persistent context header.
  - *Form view*: Input fields to gather data from customers/agents. Multiple sections with header, column or grid layout.
  - *Confirmation view*: Post-submission/action page with summary, next steps, prompts. Supports attribute bar, icon/image, headline, sub-headline, and back-to-home button.
  - *Cards view*: Present a list of topics to choose from when a contact is presented.
- **Version**: Select the view version (default: 1).
- **View data parameters**: Dynamically populated based on the selected view. For Form view, these include Sections, AttributeBar, Back, Cancel, Edit, ErrorText, Heading, Next, Previous, SubHeading, Wizard, etc. Each can be set:
  - *Set manually*: Enter text directly.
  - *Set dynamically*: Choose Namespace and Key for dynamic contact attributes.
  - *Set JSON*: Paste a JSON object for complex configurations. Supports "Apply Sample Data" for custom views.
- **This view has sensitive data**: When enabled, data submitted by a customer is not recorded in transcripts or contact records, and is not visible to agents by default. Recommended for credit card data, addresses, or other PII. Also turn off Set Logging Behavior to prevent sensitive data in flow logs.
- **Timeout**: How long the agent has to complete this step. If exceeded, routes to Timeout branch. The customer is already connected, so timeout does not affect customer experience.

**Branches**:
- **Conditional branches** (depend on selected view): E.g., for Form view: Back, Next, No Match. At runtime, routes based on agent's action on the view.
- **Error**: Failure to render the view or capture the view output action.
- **Timeout**: Agent did not complete the step within the configured timeout.

**Tips**:
- Build a flow module with Show view (sensitive data enabled), Lambda, and prompts for a reusable payment experience module.
- Required security profile permissions for agents: "Agent Applications - Custom views - All" to see guides.
- Required security profile permissions for managers/analysts: "Channels and flows - Views" to create guides.
- Data generated: `$.Views.Action` (the action taken on the view) and `$.Views.ViewResultData` (the output data). Reference these in subsequent blocks.
- When the block takes an error/timeout/no-match branch and you loop back, the flow can execute endlessly until chat timeout. Use a Loop block to limit retries.
- Custom (customer-managed) views are also supported in addition to AWS managed views.
- Configure dynamic references (e.g., `$.Channel`) in the UI builder for runtime population.

---

### Send message

**Description**: Sends a message to your customer based on a template or custom message you specify. Supports SMS, WhatsApp, and email messages. Can be used for automatic acknowledgements, automated responses, and survey messages.

Important: Before using for SMS, enable SMS messaging. Before using for WhatsApp, enable WhatsApp Business messaging.

**Channels**:
- Voice: Yes
- Chat: Yes
- Task: Yes
- Email: Yes

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: Yes
- Customer hold flow: Yes
- Customer whisper flow: Yes
- Outbound whisper flow: Yes
- Agent hold flow: Yes
- Agent whisper flow: Yes
- Transfer to agent flow: Yes
- Transfer to queue flow: Yes
- Disconnect flow: Yes

**Properties**:

*SMS Configuration:*
- **From**: Phone number to send from. Set manually (dropdown of claimed numbers) or dynamically (attribute pointing to phone number ARN).
- **To**: Customer's phone number. Set manually or dynamically (must be E.164 format).
- **Message**: Use template (choose from SMS templates) or Use text (plain text, set manually or dynamically). Max 1,024 characters including spaces. Supports links and emojis.
- **Flow**: The flow to handle the outbound contact. Set manually or dynamically (flow ARN).
- **Link to contact**: Option to link outbound SMS to the inbound contact. May want to disable to avoid repetitive associations.

*WhatsApp Configuration:*
- **From**: WhatsApp number imported into Connect instance. Set manually or dynamically.
- **To**: Customer's WhatsApp number. Set manually or dynamically (E.164 format).
- **Message template**: Required. Choose from WhatsApp templates (can contain plain text, interactive components, media). Outside the 24-hour customer service window, only template messages can be sent; subsequent Play Prompt messages will fail.
- **Flow**: The flow for the outbound contact. Set manually or dynamically.
- **Link to contact**: Option to link outbound WhatsApp contact to inbound contact.

*Email Configuration:*
- **From**: Email address to send from. Set manually (dropdown) or dynamically (e.g., Namespace: System, Key: System email address).
- **To**: Customer's email address. Set manually or dynamically (e.g., Namespace: System, Key: Customer endpoint address).
- **CC**: Single email address on cc line. Set manually (semicolon-separated list) or dynamically (e.g., Namespace: System, Key: CC Email Address List).
- **Message**: Use template (choose from email templates with subject and body) or Use text:
  - *Subject*: Up to 998 characters. Can be set dynamically (e.g., Namespace: Segment attribute, Key: Email Subject). Template subject is not included when replying to an inbound email.
  - *Message body*: Plain text, up to 5,000 characters. Set manually or dynamically via user-defined attribute.
- **Link to contact**: Option to link outbound email to inbound contact.

**Branches**:
- **Success**: Message was sent successfully.
- **Error**: Message sending failed.

**Tips**:
- CRITICAL: Do NOT use Send message with EMAIL type in the Default outbound flow -- this can cause infinite email loops. If you must, add a Check contact attributes block before it to verify `$.Channel` is not EMAIL and route EMAIL contacts away from the Send message block.
- Required security profile permissions: "Channels and flows > Phone numbers > View" (for SMS/WhatsApp), "Email addresses - View" (for email), "Content Management - Message templates - View" (for templates). Without these, you can still set properties dynamically.
- Error scenarios: incorrect system email address for From field, email sending service failure, template attributes could not be populated.
- WhatsApp: Outside the 24-hour customer service window, only template messages can be sent.

---

### Authenticate Customer

**Description**: Enables customers to authenticate during a chat. After successful sign-in and ID token retrieval from Amazon Cognito, Connect either updates an existing customer profile or creates a new one based on the identifier used. If the First Name field is present in the customer profile, the customer's display name is updated to that name.

Prerequisites: Customer authentication must be enabled for your Connect instance, a new Amazon Cognito user pool must be created with your identity provider, and Customer Profiles must be enabled.

**Channels**:
- Voice: No (Error branch)
- Chat: Yes
- Task: No (Error branch)
- Email: No (Error branch)

**Flow Types**:
- Inbound flow: Yes
- Customer queue flow: No
- Customer hold flow: No
- Customer whisper flow: No
- Outbound whisper flow: No
- Agent hold flow: No
- Agent whisper flow: No
- Transfer to agent flow: No
- Transfer to queue flow: No

**Properties**:
- **Amazon Cognito User Pool**: Select the associated user pool from the dropdown after associating it on the console page.
- **Amazon Cognito App Client**: Select the app client from the dropdown after selecting the user pool.
- **Customer Profiles Configuration**:
  - *Store by default template*: Ingests Amazon Cognito standard attributes into a unified standard profile object using the predefined Customer Profile object type. Uses phone number and email to map the customer to a profile.
  - *Enter a unique identifier*: Use a custom object type mapping (created in advance) for custom data mapping or key. Enter the mapping name.
- **Timeout**: How long until inactive customers who haven't signed in are routed to the Timeout branch. Minimum (default): 3 minutes. Maximum: 15 minutes.

**Branches**:
- **Success**: The customer was authenticated successfully.
- **Timeout**: The customer was inactive and did not sign in within the allocated time.
- **Opted out**: The customer chose not to sign in.
- **Error**: An error scenario occurred.

**Tips**:
- Enable flow logs in Amazon CloudWatch for real-time event details and debugging.
- Can also be used to authenticate customers during chats over Apple Messages for Business.
- This block does not generate any data.
- Error scenarios: Customer Profiles not enabled, unsupported chat subtype, incorrect authentication code, Amazon Cognito token endpoint errors (invalid_request, invalid_client, unauthorized_client), unsupported Region.

---

---

## Set

Blocks that set configuration, attributes, or behavior for the contact.

# Flow Blocks: Set / Configuration Category

---

### Set contact attributes

**Description**: Stores key-value pairs as contact attributes. You set a value that is later referenced in a flow. For example, create a personalized greeting for customers routed to a queue based on the type of customer account. You could also define an attribute for a company name or line of business to include in the text-to-speech strings said to a customer. Useful for copying attributes retrieved from external sources to user-defined attributes.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Attribute target** (where to set):
  - **Current contact**: Attributes are set on the contact this flow is running on. Accessible by other flows, modules, Lambdas, contact records, and the GetMetricDataV2 API.
  - **Related contact**: Attributes are associated with a new contact that contains a copy of the original contact properties (appears as `RelatedContactId` in the contact record).
  - **Flow**: Attributes are restricted to the flow in which they are configured (temporary/local variables).
    - Not visible outside the flow, not even when the contact is transferred to another flow.
    - Can be up to 32 KB (max size of the contact record attributes section).
    - Not passed to a Lambda unless explicitly configured as parameters in the Invoke AWS Lambda function block.
    - Not passed to modules. You can set a flow attribute within a module, but it won't be passed out of the module.
    - Don't appear in the contact record.
    - Don't appear to the agent in the CCP.
    - The `GetContactAttributes` API cannot expose them.
    - If logging is enabled, the key and value appear in the CloudWatch log.
- **Destination key**: The attribute name/key.
- **Value**: The attribute value (can be set manually or dynamically via JSONPath).
- **Namespace**: System, Agent, Queue, External, Lex, etc.

**Referencing attributes**:
- For attributes with special characters in their name (e.g., spaces), use brackets and single quotes: `$.Attributes.['user attribute name']`.
- Same namespace: use the attribute name or the Destination key.
- Different namespace: specify the JSONPath syntax to the attribute.
- Lambda: use `$.External.AttributeKey` format.
- Lex bot: use `$.Lex.IntentName` or `$.Lex.Slots.slotName` format.
- To use contact attributes to access other resources, set a user-defined attribute with the ARN of the resource as the value.

**Branches**:
- **Success**: Attribute was set successfully.
- **Error**: An error occurred (e.g., attributes exceed 32 KB).

**Tips**:
- When attributes for a contact exceed 32 KB, the contact is routed down the Error branch. Mitigations: remove unnecessary attributes by setting values to empty, or use flow attributes for data that doesn't need to persist.
- When using a user-defined destination key, you can name it anything but don't include `$` and `.` (period) characters -- they are used in JSONPath attribute paths.
- You can use this block to set the language attribute required for an Amazon Lex V2 bot (your language attribute must match the language model used to build the bot).
- Alternatively, use the Set voice block to set the language required for a Lex V2 bot.

---

### Set customer queue flow

**Description**: Specifies the flow to invoke when a customer is transferred to a queue. This determines what experience the customer has while waiting in queue.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Flow**: Select the customer queue flow to use. Can be set manually (choose from a list of Customer Queue type flows) or dynamically using contact attributes.

**Branches**:
- **Success**: The customer queue flow was set successfully.
- **Error**: An error occurred while setting the flow.

**Tips**:
- The selected flow must be of type "Customer Queue flow".
- Use contact attributes to set the flow dynamically if different customer segments need different queue experiences.

---

### Set hold flow

**Description**: Links from one flow type to another. Specifies the flow to invoke when a customer or agent is put on hold. If this block is triggered during a chat conversation, the contact is routed down the Error branch.

**Channels**: Voice (Yes), Chat (No -- Error branch), Task (No -- Error branch), Email (No -- Error branch)
**Flow Types**: Inbound flow, Customer Queue flow, Outbound whisper flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Flow**: Select the hold flow to use. Can be set manually (choose from a list of Agent Hold or Customer Hold type flows) or dynamically using contact attributes with namespace selection.

**Branches**:
- **Success**: The hold flow was set successfully.
- **Error**: An error occurred, or the block was triggered by a non-voice contact (chat, task, email).

**Tips**:
- Only supported for voice contacts. Chat, task, and email contacts route to the Error branch.
- You can set the hold flow dynamically using various attribute namespaces.

---

### Set whisper flow

**Description**: Overrides the default agent whisper or customer whisper flow. A whisper flow is what a customer or agent experiences when they are joined in a voice or chat conversation. For example, an agent whisper might display text telling the agent the customer's name, or a customer whisper might tell the customer the call is being recorded.

A whisper flow has these characteristics:
- It's a one-sided interaction: either the customer hears/sees it, or the agent does.
- It can be used to create personalized and automated interactions.
- It runs when a customer and agent are being connected.

For voice conversations, overrides the default agent whisper or customer whisper by linking to a different whisper flow or by disabling the whisper entirely. For outbound voice calls, it specifies the whisper played to the customer.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer Queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Whisper type**: Agent Whisper or Customer Whisper.
- **Flow**: Select the whisper flow. Can only select flows of type "Agent Whisper" or "Customer Whisper". Set manually or dynamically using contact attributes.
- **Disable whisper**: Option to disable a previously set agent or customer whisper (e.g., to eliminate connection latency perception in outbound campaigns).

**Branches**:
- **Success**: The whisper flow was set successfully.
- **Error**: An error occurred.

**Tips**:
- In a single block, you can set either a customer whisper or an agent whisper, but not both. Use multiple Set whisper flow blocks for both.
- A maximum of one agent whisper and one customer whisper can be played. If you use multiple Set whisper flow blocks, the most recently specified one for each type is played.
- Whispers must complete within 2 minutes. Otherwise, calls will be disconnected before being established.
- If agents appear stuck in "Connecting..." state before being forcefully disconnected, check that whisper flows complete within the 2-minute maximum.
- A whisper flow triggers after the agent accepts the contact (auto-accept or manual). Agent whisper runs first (before customer is taken out of queue), then customer whisper runs. Both complete before agent and customer can talk/chat.
- If an agent disconnects while agent whisper is running, the customer remains in queue to be re-routed.
- If a customer disconnects while customer whisper is running, the contact ends.
- If an agent/customer whisper flow includes blocks that chat doesn't support (e.g., Start/Stop media streaming, Set voice), chat skips those blocks and triggers an error branch but doesn't prevent flow progression.
- Whisper flows don't appear in transcripts.
- Chat conversations do not include a default whisper. You need to explicitly include a Set whisper flow block for default agent or customer whispers to play in chat.
- For chat contacts, when an outbound flow runs, a Play prompt block message will be displayed to both agent and customer.

---

### Set disconnect flow

**Description**: Specifies which flow to run after a disconnect event during a contact. A disconnect event is when: a chat or task is disconnected, a task is disconnected as a result of a flow action, or a task expires (default 7 days, configurable up to 90 days). When the disconnect event occurs, the corresponding flow runs.

Use cases:
- Run post-contact surveys (agent hangs up, disconnect flow runs, customer answers survey questions via Get customer input, answers uploaded via Lambda to external database).
- In chat scenarios, if a customer stops responding, use to decide whether to run a disconnect flow with a Wait block or end the conversation.
- In task scenarios where a task may not complete in 7 days, determine whether to re-queue or complete/disconnect the task.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Flow**: Select the disconnect flow to invoke. Can be set manually or dynamically using contact attributes.

**Branches**:
- **Success**: The disconnect flow was set successfully.
- **Error**: An error occurred.

**Tips**:
- It's not possible to play an audio prompt to the agent or invoke a flow when the customer disconnects. After the customer disconnects, the flow ends and the agent starts After Call Work (ACW) for that contact.
- For voice, the disconnect flow runs when the agent hangs up (while customer remains on the line).

---

### Set event flow

**Description**: Specifies which flow to run during a contact event. Supported events:
- **Default flow for agent UI**: Flow invoked when a contact comes into the Agent Workspace. Use to set up step-by-step guides for the agent.
- **Disconnect flow for agent UI**: Flow invoked when a contact that is open in the Agent Workspace ends. Use for step-by-step guides.
- **Flow at contact pause**: Flow invoked when a contact enters a paused state (Tasks).
- **Flow at contact resume**: Flow invoked when a contact resumes from a paused state (Tasks).

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Event type**: Select which event triggers the flow (Default flow for agent UI, Disconnect flow for agent UI, Flow at contact pause, Flow at contact resume).
- **Flow**: Select the flow to invoke for the chosen event. Can be set manually or dynamically.

**Branches**:
- **Success**: The event flow was set successfully.
- **Error**: An error occurred.

**Tips**:
- Primary use case is for step-by-step guided experiences in the Agent Workspace.
- Pause/resume events are specific to Tasks.

---

### Set working queue

**Description**: Specifies the queue to be used when Transfer to queue is invoked. A queue must be specified before invoking Transfer to queue except when used in a customer queue flow. It's also the default queue for checking attributes such as staffing, queue status, and hours of operation.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Queue**: Select the queue. Can be set manually (choose from dropdown) or dynamically.
  - **Set dynamically**: You must specify the queue ID (not the queue name). To find the queue ID, open the queue in the queue editor -- the ID is the last part of the URL after `/queue` (e.g., `aaaaaaaa-bbbb-cccc-dddd-111111111111`).

**Branches**:
- **Success**: The working queue was set successfully.
- **Error**: An error occurred.

**Tips**:
- When setting dynamically, always use the queue ID, not the queue name.
- Must be placed before a Transfer to queue block (unless in a Customer Queue flow).

---

### Set callback number

**Description**: Specifies the attribute to set the callback number for a customer.

**Channels**: Voice (Yes), Chat (No -- Invalid number branch), Task (No -- Invalid number branch), Email (No -- Invalid number branch)
**Flow Types**: Inbound flow, Customer Queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Phone number**: The callback number to set. Can be set manually or dynamically using contact attributes (commonly from a preceding Store customer input block).

**Branches**:
- **Success**: The callback number was set successfully.
- **Invalid number**: The customer entered a phone number that is not valid.
- **Not dialable**: Connect is unable to dial that number. For example, if your instance is not allowed to make calls to +447 prefix numbers, and the customer requested callback to a +447 prefix number -- even though the number is valid, Connect cannot call it.

**Tips**:
- The Store customer input block often comes before this block to capture the customer's callback number.
- Non-voice contacts (chat, task, email) route to the Invalid number branch.

---

### Set voice

**Description**: Sets the text-to-speech (TTS) language and voice to use for the contact flow. The default voice is Joanna (Conversational speaking style). You can override the speaking style to use Neural or Generative voices. After this block runs, any TTS invocation resolves to the selected voice. If triggered during a chat conversation, the contact goes down the Success branch with no effect on the chat experience.

**Channels**: Voice (Yes), Chat (No -- Success branch), Task (No -- Success branch), Email (No -- Success branch)
**Flow Types**: All flows

**Properties**:
- **Language**: Select the TTS language (e.g., en-US, ar-AE). Can be set dynamically. If set dynamically, voice must also be set dynamically.
- **Voice**: Select the Polly voice (e.g., Joanna, Ruth, Matthew). Can be set dynamically.
- **Override speaking style**: Enable to use Neural or Generative engine instead of Standard.
  - Neural voices: more lifelike pitch, inflection, intonation, and tempo.
  - Generative voices: most human-like, emotionally engaged, adaptive conversational voices.
- **Engine**: Standard, Neural, or Generative. Can be set dynamically. If voice is set dynamically and style is overridden, engine and style must also be dynamic.
- **Speaking style**: None, Conversational, or Newscaster. Conversational and Newscaster available for Matthew, Joanna (en-US), Lupe (es-US), Amy (en-GB) in neural engine.
- **Set language attribute**: Passes language code into the flow action. Required for Lex V2 bots with non-en-US languages.

**Branches**:
- **Success**: The voice was set successfully (also taken for chat/task/email with no effect).
- **Error**: The voice or engine is invalid, or the selected voice doesn't support the selected engine.

**Tips**:
- If you don't specify an engine, standard is used by default. Some voices (e.g., Ruth) don't support standard -- you must specify a supported engine or the block errors.
- For voices that support only neural, Override speaking style is automatically selected and cannot be cleared.
- Invalid language codes will not take the Error branch but may cause erroneous behavior with Lex V2 bots.
- If a play prompt is added after the Error branch, the voice defaults to Joanna/standard.
- If the defined speaking style is not supported by the defined voice, the "None" style is used.
- If language is set dynamically, voice must also be set dynamically.
- If voice is set dynamically with overridden speaking style, engine and style must also be set dynamically.
- Generative voices incur additional charges (see Amazon Polly Pricing). Included in Next Gen Amazon Connect pricing.
- For Lex V2 bots: your language attribute in Connect must match the language model used to build the bot. If using a non-en-US voice and you don't choose Set language attribute, the Get customer input block results in an error.
- Instances created before October 2018 that migrated to SLR need `polly:SynthesizeSpeech` permission for Generative engines.

---

### Set logging behavior

**Description**: Enables or disables flow logs so you can track events as contacts interact with flows. Flow logs are stored in Amazon CloudWatch.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Logging behavior**: Enable or Disable flow logging.

**Branches**:
- (No explicit branches documented -- block proceeds to the next connected block.)

**Tips**:
- Flow logs are stored in an Amazon CloudWatch log group.
- Useful for debugging and monitoring flow execution.
- When logging is enabled, flow attribute keys and values also appear in CloudWatch logs (be cautious with sensitive data in flow attributes).

---

### Set recording and analytics behavior

> **Note**: This block remains supported in existing flows for backwards compatibility, but it is replaced by "Set recording, analytics and processing behavior" for new flows or modifications.

**Description**: Sets options to record or monitor voice for agent and customer, enable automated interaction recording, enable screen recording, and set analytics behavior for contacts. Functionality includes:
- Configure what part of the call is recorded (agent, customer, or both). No additional charges.
- Enable automated interaction call recording (IVR/bot interactions). No additional charges.
- Enable screen recording of agents (requires setup). Additional charges apply.
- Configure Contact Lens analytics settings for chat and voice (language, redaction, generative AI capabilities). Additional charges apply.
- Enable Contact Lens conversational analytics on a contact.

**Channels**: Voice (Yes), Chat (Yes), Task (No -- Error branch), Email (No -- Error branch)
**Flow Types**: Inbound flow (Yes), Customer hold flow (No), Customer queue flow (Yes), Customer whisper flow (No), Outbound whisper flow (Yes), Agent hold flow (No), Agent whisper flow (No), Transfer to agent flow (Yes), Transfer to queue flow (Yes)

**Properties**:
- **Enable recording and analytics**:
  - **Voice**:
    - Agent and customer voice recording: Choose who to record.
    - Contact Lens speech analytics: Enable/disable speech analytics on recordings.
    - Automated interaction call recording: Enable recording during IVR/bot interactions.
  - **Screen**: Enable or disable agent screen recording.
  - **Chat**: Enable chat analytics (Contact Lens feature).
- **Configure analytics settings** (applies to Contact Lens conversational analytics):
  - **Language**: Set the language for speech-to-text transcript generation. Can be set dynamically based on customer language.
  - **Redaction**: Enable/disable redaction of sensitive data.
  - **Sentiment**: Enable/disable sentiment analysis.
  - **Contact Lens Generative AI capabilities**: Enable generative AI features (e.g., post-contact summaries).

**Branches**:
- **Success**: Recording/analytics behavior was set successfully.

**Tips**:
- Recommended to use this block in an inbound or outbound whisper flow for most accurate behavior. Using in a queue flow does not always guarantee calls are recorded (block might run after contact is joined to agent).
- You can change recording behavior mid-flow: add a second block to turn off agent and customer recording, then a third block to set new behavior (e.g., Agent only).
- Analytics settings are overwritten by each subsequent Set recording and analytics behavior block.
- For calls: unselecting "Enable speech analytics on agent and customer voice recordings" disables Contact Lens. If enabled in one block and disabled in a later block, analytics appear only during the enabled period.
- For automated interaction recording: recording starts when set to On. If set to Off later, recording is paused and can be resumed. Recording continues when transferred via Transfer to phone number block.
- For chat: real-time chat analysis starts as soon as any block enables it. No subsequent block disables real-time chat settings.
- If an agent puts a customer on hold, the agent is still recorded but the customer is not.
- If transferring a contact and you want to continue Contact Lens analytics, add another Set recording behavior block with Enable analytics turned on (transfer generates a second contact ID/record).
- When you enable conversational analytics, the flow type and block placement determine whether and when agents receive key highlights transcripts.
- To include Lex bot transcripts in Contact details and analytics dashboards: go to instance settings > Flows > Enable Bot Analytics and Transcripts.

---

### Set recording, analytics and processing behavior

**Description**: The newer replacement for "Set recording and analytics behavior." Supports two actions:
1. **Set message processor**: Configure a custom Lambda processor for in-flight chat messages.
2. **Set recording and analytics behavior**: Configure recording and analytics behavior for voice, chat, email, and screen recording.

**Channels**:
- Set message processing: Chat (Yes), Email (No), Tasks (No), Voice (No)
- Set recording and analytics behavior: Chat (Yes), Email (Yes), Tasks (Yes -- screen recording only), Voice (Yes)

**Flow Types**: All flow types except Journey flows.

**Properties**:
- **Action selection**: Choose between "Set message processor" or "Set recording and analytics behavior".
- **Set message processor** (Chat only):
  - **Enable processing**: Start or stop chat message processing.
  - **Function ARN**: Lambda function for message processing (must be integrated via `CreateIntegrationAssociation` API with MESSAGE_PROCESSOR IntegrationType).
  - **Processing failure handling**: Whether to deliver the original unprocessed message if processing fails.
- **Set recording and analytics behavior**:
  - **Channel selection**: Chat, Email, Screen recording, or Voice.
  - **Chat**:
    - Enable conversational analytics (Contact Lens).
    - Language, Conversational Analytics Redaction, In-flight Redaction, Sentiment, Generative AI capabilities.
  - **Email**:
    - Enable conversational analytics.
    - Language, Conversational Analytics Redaction, Generative AI capabilities.
    - Note: Sentiment analysis is not available for email.
  - **Voice**:
    - Agent and customer voice recording (choose who to record).
    - Contact Lens speech analytics on recordings.
    - Automated interaction call recording (IVR/bot interactions).
    - Language, Conversational Analytics Redaction, Sentiment, Generative AI capabilities.
  - **Screen recording**: Enable or disable agent screen recording.

**Branches**:
- **Success**: Configuration was applied successfully.
- **Error**: An error occurred.
- **Channel mismatch**: The media channel that began the contact differs from the channel selected in the block. For screen recording, taken when contact is not a voice contact.
- **In-flight redaction configuration failed** (Chat with Set recording and analytics action only): In-flight redaction failed to start/stop, but all other configurations updated correctly.

**Tips**:
- Recommended to use the recording portion in an inbound or outbound whisper flow for most accurate behavior. Other flow types may not guarantee recording if the block runs after the contact is joined to the agent.
- To configure both screen recording and channel recording/analytics, use two separate blocks in sequence -- one for screen recording, one for audio recording. Each block should be configured for only one recording type to avoid unexpected behavior.
- Analytics settings are overwritten by each subsequent block in the flow.
- For calls: disabling speech analytics in a later block stops analytics from that point. Post-call analytics require the latest block to have analytics enabled.
- For automated interaction recording: starts when On, pauses when Off, can be resumed. Continues during Transfer to phone number.
- For chat: real-time chat analysis starts as soon as any block enables it. No subsequent block disables real-time chat settings.
- Agent is still recorded when customer is on hold; customer is not.
- Transfers generate a new contact ID -- add another block with analytics enabled to continue Contact Lens on the new record.
- Block placement and flow type determine whether/when agents receive key highlights transcripts.

---

### Set routing criteria

> **Note**: Covered in detail in `proficiency-routing.md`. Brief reference included here.

**Description**: Sets routing criteria on a contact to define how it should be routed within its queue. Routing criteria is a sequence of one or more routing steps. Each step is a combination of requirements (predefined attribute conditions with proficiency levels) and an optional expiration duration. When all steps expire, the contact is offered to the longest available agent with the queue in their routing profile.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Set manually or dynamically**: Configure routing steps manually in the UI or dynamically via Lambda function output.
- **Routing steps**: Sequence of steps, each with:
  - **Requirements**: Predefined attribute conditions (Name, Value, ProficiencyLevel, ComparisonOperator). Supports AND (up to 8 attributes), OR (up to 3 conditions at top level), NOT operator, and range-based proficiency levels (1-5).
  - **Expiry**: Duration in seconds for each step (last step can be non-expiring).
- **Preferred agents**: Target up to 10 specific agents by user ID or username instead of/alongside predefined attributes.

**Branches**:
- **Success**: Routing criteria was set successfully.
- **Error**: An error occurred.

**Tips**:
- Must be used with Transfer to queue block -- the latter activates the routing criteria.
- Routing criteria does not take effect if the contact is transferred into an agent queue.
- When expiration time (DurationInSeconds) is set too short, it can prevent proper routing to the next most proficient agent when the first agent misses the call.
- Preferred agent targeting: contact is restricted to that agent until the step expires, regardless of whether the agent is online, busy, in a custom status, or even deleted from the instance.
- Routing criteria impacts queue metrics (SLA, queue time). A contact waiting for a specific agent won't be picked up by other available agents.
- Can combine preferred agent steps with predefined attribute steps in the same routing criteria.
- Can use Customer Profiles `_last_agent_id` calculated attribute to route to the last agent who handled the customer.
- OR expressions must be at the top level; you can place AND inside OR but not OR inside AND.
- Prerequisites: create predefined attributes, then assign proficiencies to agents using those attributes.

**Step statuses**: Inactive, Active, Expired, Joined, Interrupted, Deactivated.

---

### Set touchtone buffer behavior

**Description**: Enables or disables touchtone (DTMF) buffering for a contact. When enabled, customer keypad inputs (digits 0-9, #, *) are collected into a buffer of up to 30 characters as the customer presses them, even while prompts are still playing or between flow block transitions. This eliminates the common IVR problem of dropped digits when customers type ahead of prompts.

Two modes:
- **Enable Buffering**: Starts collecting DTMF input into the buffer. Buffered digits are consumed by the next Get customer input or Store customer input block.
- **Stop and Clear**: Stops buffering and clears any digits in the buffer. Optionally stores the buffered input before clearing, with support for encryption.

**Channels**: Voice (Yes), Chat (No -- Error branch), Task (No -- Error branch), Email (No -- Error branch)
**Flow Types**: Inbound flow, Customer queue flow, Outbound whisper flow, Transfer to agent flow, Transfer to queue flow

**Properties**:
- **Touchtone Buffer Behavior**: Enable or Stop and Clear.
- **Store input** (Stop and Clear mode only): Save current buffer contents to a contact attribute before clearing.
- **Encrypt input** (when Store input is enabled): Provide an encryption key to encrypt the stored value.

**Branches**:
- **Success**: The buffer behavior was set successfully.
- **Error**: An error occurred (e.g., non-voice contact, invalid encryption parameters with Stop and Clear + Store input).

**Interaction with other blocks**:
- **Play prompt**: Has a "Skip or interrupt this prompt when touchtone buffering is enabled" checkbox. When selected, if the buffer already has digits the prompt is skipped. If customer presses a key during the prompt, it's interrupted and the digit is added to the buffer.
- **Get customer input**: If buffer has a digit, the block dequeues and uses it automatically. If buffer is empty, customer is prompted normally. In Amazon Lex mode, the buffer is automatically cleared before bot interaction begins (buffered digits are NOT passed to the Lex bot).
- **Store customer input**: Dequeues up to the max number of digits specified. If buffer has enough digits, the prompt is skipped. If buffer has fewer than requested, inter-digit timeout allows real-time entry of remaining digits.

**Automatic clearing**: Buffer is cleared when:
- Digits are consumed (FIFO) by Get customer input or Store customer input.
- A Stop and Clear action is executed.
- Transferring to an agent or queue.
- Using Get customer input with Amazon Lex bots.
- The contact ends.

**Tips**:
- Use cases: allow customers to navigate multi-level IVR menus without waiting for prompts (type-ahead), capture account numbers/order IDs entered before the collection prompt plays.
- Buffer holds up to 30 characters maximum.
- Only supported for voice contacts.
- Represented as a `GetParticipantInput` action in Connect flow language with `EnableDTMFBuffer` parameter.

---

### Contact tags

**Description**: Creates and applies user-defined tags (key:value pairs) to contacts. You can create up to 6 user-defined tags. Tags can be referenced later in a flow and can also be removed if no longer relevant to the segment. Tags enable granular billing for a detailed view of Connect usage.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Action**: Tag contact or Untag contact.
- **Tag key**: The tag name (e.g., "Department").
- **Tag value**: The tag value (e.g., "Finance"). Can be set manually or dynamically using contact attributes.
- **Maximum**: Up to 6 user-defined tags per contact.

**Branches**:
- **Success**: Tags were applied/removed successfully.
- **Error**: An error occurred.

**Tips**:
- Used primarily for granular billing to get a detailed view of Connect usage by department, business unit, etc.
- See "Things to know about user-defined tags" in the granular billing documentation for how Connect processes user-defined tags.
- Tags can be removed in the flow using the Untag action if they are no longer relevant to the current segment.

---

## Branch

Blocks that make routing decisions based on conditions.

# Amazon Connect Flow Blocks — Branch Category

---

### Check contact attributes

**Description**: Branches based on a comparison to the value of a contact attribute. Supports checking user-defined attributes, system attributes, Lex attributes (intents, slots, sentiment), and queue metrics. Conditions are evaluated in the order they are listed; the first match wins.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Attribute to check**: Select the attribute namespace (User Defined, System, Agent, Queue metrics, Lex) and the specific attribute key
- **Conditions to check**: One or more comparison conditions evaluated in listed order; first match is followed
- **Dynamic conditions**: Conditions can reference dynamic values (e.g. `$.Attributes.verificationCode`)
- **Lex — Alternative Intents**: Branch on what the customer *might* have meant (alternate intent), not just the winning intent
- **Lex — Intent Confidence Score**: Confidence on a 0–1 scale (0 = not confident, 0.5 = 50%, 1 = 100%)
- **Lex — Intent Name**: The user intent returned by Amazon Lex
- **Lex — Sentiment Label**: The winning sentiment — POSITIVE, NEGATIVE, MIXED, or NEUTRAL
- **Lex — Sentiment Score**: Per-sentiment scores from Amazon Comprehend (Positive, Negative, Mixed, Neutral)
- **Lex — Session Attributes**: Key-value pairs representing session-specific context
- **Lex — Slots**: Key-value pairs of intent slots detected from user input

**Conditions/Operators**:
- Equals
- Is Greater Than
- Is Less Than
- Starts With
- Contains

**Branches**:
- **[Condition 1..N]**: One branch per condition you define; contact follows the first condition that matches
- **No Match**: When none of the defined conditions match the attribute value
- **Error**: (implicit) When the attribute cannot be retrieved or evaluated

**Tips**:
- Conditions are checked in the order they are listed — first match wins. Order matters.
- Does NOT support case-insensitive pattern matching. "green" will not match "Green"; you must include every permutation of upper/lower-case.
- To check for a NULL value, you must use a Lambda function — the block cannot check NULL natively.
- After a Get metrics block, use this block with "Queue metrics" attribute type to branch on returned metric values.

---

### Check hours of operation

**Description**: Checks whether a contact occurs within or outside of the defined hours of operation. Can reference hours defined directly on the block or, if none are specified, the hours associated with the contact's current queue. Supports override branches for special dates (e.g. holidays) in addition to the standard In hours / Out of hours paths.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Hours of operation**: Optionally specify an hours-of-operation schedule for this block. If not specified, the block uses the hours associated with the contact's current queue.
- **Optional branches — Check override**: Add named override branches that correspond to override entries in the hours of operation (e.g. holidays, extended hours). Each override gets its own output branch so you can route differently on special dates.

**Conditions/Operators**:
- N/A — this block evaluates the current date/time against the hours-of-operation schedule; no user-defined comparison operators.

**Branches**:
- **In hours**: The current date/time falls within the defined hours of operation
- **Out of hours**: The current date/time falls outside the defined hours of operation
- **[Override name]**: One branch per configured override (e.g. "Holiday", "Extended Hours") — matched when the current date/time hits an override entry
- **Error**: The hours of operation could not be determined (e.g. agent queue with no hours defined)

**Tips**:
- Agent queues (automatically created per agent) do not include hours of operation. If you check hours for an agent queue, the check fails and the contact is routed down the Error branch.
- If no hours of operation are specified on the block AND no queue is set, the block will error.
- Use overrides for holidays or special-date routing — each override gets its own branch so you can play custom messages before following the standard out-of-hours path.

---

### Check queue status

**Description**: Checks the status of a queue based on specified conditions and branches accordingly. Supports checking Time in Queue (how long the oldest contact has been waiting) and Queue Capacity (number of contacts currently waiting in the queue).

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Queue to check**: The queue whose status will be evaluated (set via the block or inherited from a Set working queue block)
- **Conditions to check — Time in Queue**: The amount of time the oldest contact has been in the queue before being routed to an agent or removed. Compared using numeric operators.
- **Conditions to check — Queue Capacity**: The number of contacts currently waiting in the queue. Compared using numeric operators.

**Conditions/Operators**:
- Is Greater Than (>)
- Is Less Than (<)
- Is Greater Than or Equal To (>=)
- Is Less Than or Equal To (<=)
- Is Equal To (=)

**Branches**:
- **[Condition 1..N]**: One branch per condition (e.g. "Time in Queue >= 120"). First matching condition wins.
- **No Match**: When none of the defined conditions match
- **Error**: When the queue status cannot be retrieved

**Tips**:
- The order in which you add conditions matters at runtime. Contacts are routed down the first matching condition.
- Be careful with overlapping conditions. For example, if you put "Time in Queue <= 90" first, it will match almost everything and subsequent conditions like "<= 9", "<= 12" etc. will never fire.
- Structure conditions from most restrictive to least restrictive to avoid unreachable branches.

---

### Check staffing

**Description**: Checks the current working queue (or a specified queue) for whether agents are available, staffed, or online. Use before transferring a call to verify that agents are present to service it. Typically paired with Check hours of operation.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Queue to check**: Select a specific queue or use the current working queue
- **Status to check**: Dropdown with three options:
  - **Available**: At least one agent in the queue has status "Available" (ready to take contacts)
  - **Staffed agents**: At least one agent is in "Available", "On call", or "After Contact Work" state
  - **Online agents**: At least one agent is in "Available", "Staffed", or a custom status state

**Conditions/Operators**:
- N/A — this block performs a boolean check (true/false) on the selected staffing status.

**Branches**:
- **True**: At least one agent matches the selected status criterion
- **False**: No agents match the selected status criterion
- **Error**: The queue is not set or the staffing status could not be determined

**Tips**:
- You MUST set a queue before using this block. Use a Set working queue block to set the queue first.
- If no queue is set, the contact is routed down the Error branch.
- When a contact is transferred from one flow to another, the queue set in the originating flow carries over to the next flow.
- Best practice: use Check hours of operation AND Check staffing together before transferring calls to a queue.

---

### Distribute by percentage

**Description**: Routes customers randomly based on a percentage. Useful for A/B testing. Internal logic generates a random number between 1-100 to determine which branch a contact follows. Does not use current or historical volume — allocation is purely random per contact.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer queue flow, Outbound Whisper flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Percentage allocations**: Define one or more named branches with a percentage (0-100). The remaining percentage automatically goes to the Default branch. Example: 20% = A, 40% = B, 40% remaining = Default.

**Conditions/Operators**:
- N/A — routing is based on random number generation against configured percentage thresholds, not comparison operators.

**Branches**:
- **[Custom branch 1..N]**: One branch per configured percentage bucket (e.g. "50% test")
- **Default**: Receives whatever percentage remains after all custom branches are allocated

**Tips**:
- Contacts are distributed randomly, so exact percentage splits may not occur — especially with small sample sizes.
- The block generates a random number 1-100 per contact. Example: with 20% A / 40% B / 40% Default, numbers 0-20 go to A, 21-60 go to B, 61-100 go to Default.
- This is a static allocation rule — it does not consider real-time traffic volume or historical patterns.

---

### Check call progress

**Description**: Engages with the output provided by an answering machine and provides branches to route the contact accordingly. Detects whether a call was answered by a live person, went to voicemail (with or without a beep), or could not be determined. Key block for customer-first callback use cases.

**Channels**: Voice only (Chat, Task, Email route to Error branch)
**Flow Types**: All flow types

**Properties**:
- **Wait time for answering machine detection**: Configure how long to wait for answering machine detection analysis (shown in the properties page)

**Conditions/Operators**:
- N/A — the block performs automated call-progress analysis (live voice vs. answering machine detection) and branches on the result.

**Branches**:
- **Call answered**: The call was answered by a live person
- **Voicemail (beep)**: The call went to voicemail and a beep was detected
- **Voicemail (no beep)**: The call went to voicemail but no beep was detected, OR the call went to voicemail but beep status is unknown
- **Not detected**: Could not determine whether a live voice or answering machine answered. Typical causes: long silences, excessive background noise.
- **Error**: Errors encountered after media was established on the call. Also triggered for non-voice channels (Chat, Task, Email).

**Tips**:
- Only supported on Voice channel. Chat, Task, and Email contacts are routed to the Error branch.
- Media must be established (call answered or answering machine picks up) before this block runs. If the call is rejected by the network or encounters a system error before media is established, the flow is not run at all.
- This block is key for customer-first callback use cases — use it to determine whether to leave a voicemail message or proceed with a live conversation.
- "Voicemail (no beep)" also covers the case where voicemail is detected but beep status is unknown.

---

### Get metrics

**Description**: Retrieves near real-time queue metrics (with a 5-10 second delay) for making granular routing decisions. By default returns metrics for the current queue aggregated across all channels. Can optionally filter by a specific queue, channel (Voice/Chat), or return contact-level metrics (position in queue, estimated wait time). Metrics are returned as attributes that can be referenced via JSONPath or the Check contact attributes block.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:
- **Queue**: Optionally specify a queue (defaults to current queue)
- **Channel filter**: Optionally filter by Voice, Chat, or other channel (defaults to all channels)
- **Returned metrics**:
  - Queue name
  - Queue ARN
  - Contacts in queue
  - Oldest contact in queue
  - Agents online
  - Agents available
  - Agents staffed
  - Agents after contact work
  - Agents busy (on contact)
  - Agents missed (agent non-response)
  - Agents non-productive
  - Queue estimated wait time
  - Contact estimated wait time
  - Contact position in queue

**Conditions/Operators**:
- N/A — this block retrieves metrics and stores them as attributes. Use a subsequent Check contact attributes block to branch on the values.

**Branches**:
- **Success**: Metrics were retrieved successfully and stored as contact attributes
- **Error**: Metrics could not be retrieved (e.g. no activity in the queue, empty real-time metrics report)

**Tips**:
- After this block, add a Check contact attributes block (set Attribute to check = "Queue metrics") to branch on the returned metric values.
- Dynamic attributes can only return metrics for ONE channel at a time. Use Set contact attributes to specify which channel before using dynamic attributes in this block.
- When setting a channel dynamically using text, enter "Voice" or "Chat" — the value is NOT case-sensitive.
- The block throws an Error when the Real-time metrics report returns empty metrics (no activity taking place). Handle the Error branch to avoid flow failures.
- For agent-based metrics (agents online, agents available, agents staffed): if there are no agents, no metrics are returned.
- Queue estimated wait time only returns a value when a single channel is specified.
- Metrics have a 5-10 second delay from real-time — they are near real-time, not instantaneous.

---

---

## Integrate

Blocks that integrate with external services and AWS services.

# Amazon Connect Flow Blocks: Integrate

---

### Invoke AWS Lambda function

**Description**: Calls AWS Lambda and returns data that can be used to set contact attributes via the Set contact attributes block.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: Inbound flow, Customer Queue flow, Customer Hold flow, Customer Whisper flow, Agent Hold flow, Agent Whisper flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:

*Select an action*: Choose between **Invoke Lambda** or **Load Lambda Result**.

#### Invoke Lambda

- **Execution mode**:
  - *Synchronous*: The contact is routed to the next block only after the Lambda invocation completes.
  - *Asynchronous*: The contact is routed to the next block without waiting for the Lambda to complete. You can configure a Wait block to wait for an asynchronously invoked Lambda.
- **Function**: Select a Lambda function from the drop-down list (must be added to the instance first).
- **Timeout**: Maximum wait time before Lambda times out. Maximum of 8 seconds for Synchronous mode, 60 seconds for Asynchronous mode. If the invocation is throttled, the request is retried. Also retried on general service failure (500 error). Connect retries up to three times, for maximum until timeout specified. After that, the contact is routed down the Error branch.
- **Response validation**: The Lambda function response format. Must be set when configuring the block.
  - *STRING_MAP*: Lambda returns a flat object of key/value pairs of the string type.
  - *JSON*: Lambda returns any valid JSON including nested JSON.

#### Load Lambda Result

- **Lambda Invocation RequestId**: The requestId of the Lambda when run in Asynchronous mode. `$.LambdaInvocation.InvocationId` contains the requestId of the most recent asynchronously run Lambda.
  - Namespace: Lambda Invocation
  - Key: Invocation ID

**Branches**:
- **Success**: Lambda invocation completed successfully.
- **Error**: Lambda invocation failed (timeout, throttling after retries, or service error).
- **Timeout** (Synchronous mode only): Lambda invocation timed out.

**Tips**:
- To use an AWS Lambda function in a flow, first add the function to your instance (see Add a Lambda function to your Connect instance).
- After you add the function to your instance, you can select the function from the "Select a function" drop-down list in the block.
- If the Lambda invocation gets throttled, the request is retried. It is also retried on general service failure (500 error).
- When configured for Asynchronous execution mode, the block has Success and Error branches. When configured for Synchronous execution mode, it also has a Timeout branch.

---

### Customer profiles

**Description**: Enables you to retrieve, create, and update a customer profile. You can retrieve profiles using up to five search identifiers. You can retrieve a Customer Profile's object and calculated attributes (requires a profile ID). You can associate the contact (voice, chat, tasks) to an existing customer profile. When customer profile data is retrieved, Response fields are stored in contact attributes, allowing use in subsequent blocks. Response fields can also be referenced via JSONPath: `$.Customer.<field>` (e.g., `$.Customer.City`, `$.Customer.Asset.Status`).

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flow types

**Properties**:

*Select an action*: Choose from **Get Profile**, **Create Profile**, **Update Profile**, **Get Profile Object**, **Get Calculated Attributes**, **Associate Contact to Profile**, **Check Segment Membership**, or **Get Profile Recommendations**.

#### Get Profile

- **Search identifiers**: At least one required, up to five total.
- **Logical operator**: If multiple search identifiers are provided, you must provide one logical operator: AND or OR, applied across all identifiers (e.g., a AND b AND c, or x OR y OR z).
- **Response fields**: Define attributes to persist in subsequent blocks, stored in contact attributes under the Customer namespace.

#### Create Profile

- **Request fields**: Specify the attributes to populate during profile creation (e.g., PhoneNumber, custom attributes like "Language").
- **Response fields**: Define attributes to persist in subsequent blocks, stored in contact attributes.

#### Update Profile

- **Prerequisite**: Must use a Get Profile block before Update Profile to locate the specific profile to update.
- **Request fields / Request field values**: Provide the attributes and values to update.
- **Response fields**: Define attributes to persist in subsequent blocks.

#### Get Profile Object

- **Mandatory Profile ID**: Required. Use a preceding Get Profile block or manually input.
- **Object type**: Indicate the object type from which to retrieve information.
- **Retrieval option**: Choose either "Use latest profile object" (always retrieves most recent) or "Use search identifier" (search using provided identifier).
- **Response fields**: Define attributes to persist in subsequent blocks.

#### Get Calculated Attributes

- **Mandatory Profile ID**: Required. Use a preceding Get Profile block or manually input.
- **Response fields**: Options are the Calculated Attribute definitions defined for your Customer Profiles domain. If the definition uses a threshold, the value is Boolean (True/False). Otherwise, returns numeric or string.
- **Required permissions**: `ListCalculatedAttributeDefinitions` and `GetCalculatedAttributeForProfile` in AmazonConnectServiceLinkedRolePolicy or AmazonConnectServiceCustomerProfileAccess.

#### Check Segment Membership

- **Mandatory Profile ID**: Required. Use a preceding Get Profile block.
- **Segment**: Select manually or set dynamically using an attribute that refers to the customer segment's identifier (SegmentDefinitionName).
- **Required permissions**: `ListSegmentDefinitions`, `GetSegmentMembership`, `BatchGetProfile`, and `BatchGetCalculatedAttributeForProfile`.
- If checking membership for a Spark SQL-powered segment, the segment checked is the last snapshot created (not real-time). Use `lastComputedAt` to verify freshness.

#### Associate Contact to Profile

- **Mandatory Profile ID**: Required. Use a preceding Get Profile block.
- **Contact ID**: Must provide a value for Contact ID.
- **Required permissions**: `ListCalculatedAttributeDefinitions` and `GetCalculatedAttributeForProfile`, plus Customer Profiles View permission in security profile.

#### Get Profile Recommendations

- **Required permissions**: `GetProfileRecommendations` in AmazonConnectServiceLinkedRolePolicy or AmazonConnectServiceCustomerProfileAccess.

**Branches**:

*Get Profile*:
- **Success**: One profile was found. Response fields are stored to contact attributes.
- **Error**: An error was encountered while trying to find the profile (system error or misconfiguration).
- **Multiple Found**: Multiple profiles were found.
- **None Found**: No profile was found.

*Create Profile*:
- **Success**: A profile is successfully created. Response fields are stored in contact attributes.
- **Error**: An error occurred during profile creation (system error or misconfiguration).

*Update Profile*:
- **Success**: The profile has been successfully updated. Response fields are stored in contact attributes.
- **Error**: An error occurred during the attempt to update the profile (system error or misconfiguration).

*Get Profile Object*:
- **Success**: The profile object is successfully located. Response fields are stored in contact attributes.
- **Error**: An error occurred during the attempt to retrieve the profile object (system error or misconfiguration).
- **None Found**: No object is found.

*Get Calculated Attributes*:
- **Success**: A calculated attribute is found. Response fields are stored in contact attributes.
- **Error**: An error occurred while attempting to retrieve the calculated attribute (system error or misconfiguration).
- **None Found**: No calculated attribute is found.

*Check Segment Membership*:
- **In Segment**: The profile belongs to the customer segment.
- **Not in Segment**: The profile does not belong to the customer segment.
- **Error**: An error occurred while attempting to check segment membership (system error or misconfiguration).

*Associate Contact to Profile*:
- **Success**: Associated the contact to profile.
- **Error**: An error was encountered while attempting to associate the contact to profile (system error or misconfiguration).

**Tips**:
- Before using this block, make sure Customer Profiles is enabled for your Connect instance.
- A contact is routed down the Error branch when: Customer Profiles is not enabled, request data values are not valid (cannot be over 255 characters), the Customer Profiles API request has been throttled, or Customer Profiles is having availability issues.
- The total size of Customer Profiles contact attributes is limited to 14,000 characters (56 attributes assuming max size of 255 each) for the entire flow. This includes all values persisted as Response fields in Customer Profiles blocks during the flow.
- Use a Play Prompt block after retrieving a profile to provide a personalized call or chat experience.
- Use a Check Contact Attributes block after retrieving profile data to route a contact conditional on the value.
- For Update Profile, always use a Get Profile block first to locate the specific profile.
- For Get Profile Object and Get Calculated Attributes, a Profile ID is mandatory -- use a preceding Get Profile block.

---

### Cases

**Description**: Gets, updates, and creates cases. Searches for cases linked to a contact. You can link a contact to a case, and then the contact will be recorded in the Activity feed of the case. When the agent accepts a contact that is linked to a case, the case automatically opens as a new tab in the agent application. While you can link contacts to multiple cases, there is a limit of five new case tabs automatically opening in the agent application (the five most recently updated cases).

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:

*Select an action*: Choose from **Get Case**, **Get Case ID**, **Update Case**, or **Create Case**.

#### Get Case

- **Link contact to case**: Yes/No. If Yes, choose Current contact or Related contact.
- **Search criteria**: At least one required. Can use attribute in the Cases namespace or set manually.
- **Get last updated case**: Option to get only the last updated case for any search criteria.
- **Response fields**: Persist case fields in the case namespace for use in subsequent blocks. Can use attribute in Cases namespace or set manually.
- **Customer ID**: Can be configured using Customer Profile ARN (Type: Customer, Attribute: Profile ARN).
- Search functions: Contains for text fields, EqualTo for number/boolean, greater than or equal to for date fields. Single-select field type is also supported.

#### Get Case ID

- **Link contact to case**: Yes/No. If Yes, choose Current contact or Related contact.
- **Contact to search**: Fetch a case linked to another contact in the current contact's contact chain. Options: Current contact, Initial contact, Task contact, Previous contact, Related contact.
- If a case is found, the case ID is persisted in the case namespace for use in other blocks.

#### Update Case

- **Link contact to case**: Yes/No. If Yes, choose Current contact or Related contact.
- **Prerequisite**: Must use a Get Case block before Update Case to find the case to update.
- **Case ID**: Required to identify which case to update (unique identifier, only field allowed here).
- **Request fields**: At least one update to a Request field is required. Can use attribute in Cases namespace or set manually.

#### Create Case

- **Link contact to case**: Yes/No. If Yes, choose Current contact or Related contact.
- **Template**: Must provide a case template (e.g., General Inquiry).
- **Required fields**: Fields required by the template appear in the Required fields section. Values must be assigned to create a case.
- **Customer ID**: Must specify the customer. Recommended to add a Customer Profiles block before to get/create a customer profile. Use Profile ARN (Type: Customer, Attribute: Profile ARN). If setting manually, provide full ARN: `arn:aws:profile:{{region}}:{{account}}:domains/{{domain}}/profiles/{{profileId}}`.
- **Request fields**: Can specify values for non-required fields.
- After creating a case, the case ID is persisted in the case namespace for use in other blocks.

**Branches**:

*Get Case*:
- **Success**: The case was found.
- **Contact not linked**: The case was found but the contact was not linked (partial success/failure). Only appears if Link contact to case is set to Yes.
- **Multiple found**: Multiple cases found with the search criteria.
- **None found**: No cases found with the search criteria.
- **Error**: An error was encountered while trying to find the case (system error or misconfiguration).

*Get Case ID*:
- **Success**: The case was found. If link contact was specified, the contact was also successfully linked.
- **Contact not linked**: The case was found but the contact was not linked (partial success/failure). Only appears if Link contact to case is set to Yes.
- **Multiple found**: Multiple cases found with the search criteria.
- **None found**: No cases found with the search criteria.
- **Error**: An error was encountered (system error or misconfiguration).

*Update Case*:
- **Success**: The case was updated, and the contact was linked to the case.
- **Contact not linked**: The case was updated but the contact was not linked (partial success/failure). Only appears if Link contact to case is set to Yes.
- **Error**: The case was not updated. The contact was not linked as the case was not updated.

*Create Case*:
- **Success**: The case was created, and the contact was linked to the case.
- **Contact not linked**: The case was created but the contact was not linked (partial success/failure). Only appears if Link contact to case is set to Yes.
- **Error**: The case was not created. The contact was not linked as the case was not created.

**Tips**:
- Be sure to enable Connect Cases before using this block. Otherwise, you cannot configure its properties.
- Check the Cases service quotas and request increases. The quotas apply when this block creates cases.
- You can specify up to 10 Response fields on a Cases block. If you specify more than 10 and publish the flow, the error "Invalid or missing parameter data" is displayed.
- To get cases for a given customer, add a Customer Profiles block before the Cases block.
- For custom fields, the syntax uses a UUID to represent the field. Find the UUID on the custom field details page (last portion of the URL).
- For system fields, use the syntax `$.Case.<fieldId>` (e.g., `$.Case.status`).
- Use a Play Prompt block after Get Case to read case status to the customer via IVR without requiring an agent.

---

### Data Table

**Description**: Enables you to evaluate, list, or write data from data tables within your contact flows. This block helps with dynamic decision-making, personalized customer experiences, and data management by interacting with structured data stored in Connect data tables.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:

*Select an action*: Choose between **Read from data table** (Evaluate or List) or **Write to data table**.

*Define data table*: Choose "Set manually" to directly select a data table from the dropdown. Once selected, the interface automatically populates available attributes from that table.

#### Evaluate Data Table Values

- **Action**: Read from data table > Evaluate Data Table values.
- **Queries**: Up to 5 queries per block. At least one query is required.
  - **Query Name** (Required): Descriptive name for the query. Must be unique throughout the entire flow (not just within the block).
  - **Primary Attributes**: Automatically populated from the selected table's schema. All primary attribute fields are required. These act as filters to identify specific rows. Uses exact matching.
  - **Query Attributes**: Automatically populated dropdown with all available attributes. Select one or more attributes to be returned and made available in the flow.
- **Accessing retrieved data**: Use namespace format `$.DataTables.{{QueryName}}.{{AttributeName}}`. Use brackets and single quotes for attribute names with special characters: `$.DataTables.CustomQuery['my attribute name with spaces']`.
- Data table values of type list are not supported.
- Subsequent data table blocks will clear previous queries from the data tables namespace.
- Query results are only available in the flow that contains the data table flow block.

#### List Data Table Values

- **Action**: Read from data table > List Data Table values.
- **Primary Value Groups**: Up to 5 groups. Each group defines filtering criteria.
  - **Group Name** (Required): Descriptive name. Must be unique throughout the entire flow.
  - **Primary Attributes**: Automatically populated from table schema. All required. Uses exact matching.
- Returns entire records (all attributes), not just selected attributes. If no primary value group is configured, the entire table is loaded within a 32KB limit.
- **Accessing retrieved data**:
  - Data table ID: `$.DataTableList.ResultData.dataTableId`
  - Lock version: `$.DataTableList.ResultData.lockVersion.dataTable`
  - Specific row by index: `$.DataTableList.ResultData.primaryKeyGroups.{{GroupName}}[{{index}}]`
  - Primary key value: `$.DataTableList.ResultData.primaryKeyGroups.{{GroupName}}[{{index}}].primaryKeys[{{index}}].attributeValue`
  - Attribute value: `$.DataTableList.ResultData.primaryKeyGroups.{{GroupName}}[{{index}}].attributes[{{index}}].attributeValue`
  - When no primary key group is configured, results are under a "default" group name.
  - Use backticks to wrap JSONPath references when accessing array elements in flow blocks.

#### Write to Data Table

- **Action**: Write to data table.
- **Input method**: Input tab (structured form) or Raw JSON tab (advanced).
- **Primary Value Groups**: At least one required. No fixed limit on number of groups.
  - **Group Name** (Required): Must be unique throughout the entire flow.
  - **Primary Attributes**: Automatically populated from table schema. All required. These determine which record to create or update.
  - **Configure Attributes to Write**:
    - **Attribute Name** (Required): Select from dropdown of available attributes. Can add multiple attributes.
    - **Attribute Value Configuration**: Choose "Set attribute value" (specify value -- static text, contact attributes, or system variables) or "Use default value" (uses the default from the data table schema).
  - **Configure Lock Version**: Controls concurrent write operations.
    - *Use Latest*: Always writes to the most recent version. Suitable for most use cases.
    - *Set dynamically*: Specify version number dynamically at runtime via Lambda or module.
- **Upsert behavior**: If a record with matching primary attributes exists, it is updated; otherwise, a new record is created.
- **Attribute limit**: Total of 25 attributes across all primary value groups in a single block. Counting rules:
  - Group with no "Attributes to write": count of primary attribute values counts toward limit.
  - Group with "Attributes to write": count of attributes to write counts toward limit (primary attributes not counted).

**Branches**:
- **Success**: The data table operation completed successfully.
- **Error**: The data table operation failed.

**Tips**:
- Use cases include configuration retrieval, dynamic routing decisions, and status checks.
- Query names (Evaluate) and Group names (List/Write) must be unique across the entire contact flow, not just within a single block.
- For Evaluate, at least one query must be configured; all primary attributes are mandatory.
- For List, if no primary value group is configured, the entire table loads within a 32KB limit.
- For Write, the total sum of counted attributes across all primary value groups must not exceed 25.
- Retrieved values can be referenced in Check Contact Attributes, Set Contact Attributes, Play Prompt, and Invoke Lambda Function blocks.
- If the query returns no results or the attribute is not found, the reference will be empty or null.
- Subsequent data table blocks will clear previous queries from the data tables namespace.

---

### Create task

**Description**: Creates a new task manually or by using a task template. Sets the task attributes. Initiates a flow to start the task immediately or schedules it for a future date and time.

**Channels**: Voice, Chat, Task, Email
**Flow Types**: All flows

**Properties**:

*Select creation method*: Choose between **Create manually** or **Use template**.

#### Create Manually

- **Task name**: Set manually or dynamically.
- **Description**: Set manually or dynamically.
- **Contact flow**: Select the flow to run for the task.
- **Schedule date and time**: Optionally schedule the task for a future date and time.
- **Link to contact**: Option to automatically link the task to the current contact.
- All settings can be specified manually or dynamically.

#### Use Template

- **Template**: Select from previously created task templates.
- **Flow**: If the selected template does not include a flow, you must specify the flow for the task to run.
- Fields populated by the template cannot be overwritten.

**Branches**:
- **Success**: Task was created successfully. Responds with the contact ID of the newly created task.
- **Error**: Task was not created.

**Tips**:
- If your Connect instance was created on or before October 2018, the contact is routed down the Error branch unless you create an IAM policy with `connect:StartTaskContact` permission and attach it to the Connect service role.
- The newly created task runs the flow specified in the Flow section of the block, or the flow configured by the selected task template. You can reference the contact ID of the newly created task in subsequent blocks using Namespace: System, Value: Task Contact id.
- When scheduling a task with "Set date and time using attribute": values for date fields must be in Unix timestamp (Epoch seconds). Most likely you will use a User-defined attribute for the Namespace. When the date and time have passed, contacts are always routed down the Error branch -- keep the Epoch seconds updated to a valid future date and time.
- Use the "Link to contact" option to automatically link the task to the contact.
- Check the service quotas for tasks and API throttling, and request increases if needed. The quotas apply when this block creates tasks.

---

### Create persistent contact association

**Description**: Enables persistent chat experience on the current chat. This allows you to select the required rehydration mode, enabling conversations with contacts to continue where they left off.

**Channels**: Chat only (Voice and Task route to Error branch)
**Flow Types**: Inbound flow, Customer Queue flow, Customer Hold flow, Customer Whisper flow, Outbound Whisper flow, Agent Hold flow, Agent Whisper flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Rehydration mode**: Select the rehydration type to configure how past chat conversations are restored.
  - *Entire past conversation*: Rehydrates the entire past chat conversation.
  - *From specific segment*: Rehydrates from a specific segment of a past chat conversation.

**Branches**:
- **Success**: Persistent contact association was created successfully.
- **Error**: Failed to create the persistent contact association. Also triggered when used on Voice or Task channels.

**Tips**:
- To enable persistent chat, you can either add the Create persistent contact association block to your flow OR provide the previous `contactId` in the `SourceContactId` parameter of the StartChatContact API, but not both. You can enable persistence of a `SourceContactID` on a new chat only once.
- Recommended to use this block (rather than the API) when using the following features: Connect chat widget, Apple Messages for Business.
- You can configure persistent chats to rehydrate the entire past chat conversation or rehydrate from a specific segment.
- Voice and Task channels are not supported and will route to the Error branch.

---

## Transfer, Disconnect, Flow Control, Media, Outbound & Routing

# Amazon Connect Flow Blocks — Transfer, Disconnect, Flow Control, Media, Outbound & Routing

---

## Transfer and Disconnect

---

### Transfer to queue

**Description**: Transfers the current contact to the destination queue. The behavior depends on context:
- When used in a Customer Queue flow, it transfers a contact already in a queue to another queue.
- When used in a callback scenario, Amazon Connect calls the agent first. After the agent accepts the call in the CCP, Connect calls the customer.
- In all other cases, it places the current contact in a queue and ends the current flow.
- This block cannot be used in a callback scenario when using the chat channel. If attempted, the Error branch is followed and an error is created in the CloudWatch log.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: Inbound flow, Customer queue flow, Transfer to agent flow, Transfer to queue flow

**Properties**:

*Transfer to queue tab:*
- When contacts are **not in any queue yet**: Simply places contacts in the destination queue. You must use a Set working queue block before this block.
- When contacts are **already in a queue**: Moves contacts from one queue to another. You can manually set the destination queue or set it dynamically.

*Transfer to Callback tab:*
- **Initial delay**: Specify how much time must pass between a callback contact being initiated in the flow and the customer being put in queue for the next available agent.
- **Maximum number of retries**: The maximum number of retry attempts after the initial callback. For example, if set to 1, Connect tries at most 2 times (initial + 1 retry). Double-check this value -- accidentally entering a high number (e.g., 20) results in unnecessary agent work and too many calls for the customer.
- **Minimum time between attempts**: How long to wait before trying again if the customer doesn't answer.
- **Set working queue**: Transfer a callback to a different queue. Useful if you set up a special queue just for callbacks. If you want to specify this property, you must add a Set customer callback number block before this block. If not set, Connect uses the queue previously set in the flow.
- **Set creation flow**: Select the flow to run when a callback contact is created. Requirements: (1) Flow type must be Contact flow (inbound). (2) Must contain a Transfer to queue block to queue the contact. Optional configurations include: evaluating contact attributes with Check contact attributes to detect duplicates or resolved issues; adding a Set customer queue flow block to specify the customer queue flow; using Get metrics + GetCurrentMetricData to send advance SMS notifications.
- **Caller ID number to display**: The phone number shown to customers when they receive the callback. Set manually (select from claimed numbers) or set dynamically (via contact attributes). Must be a valid phone number claimed in your instance. Takes precedence over the outbound phone number configured on the queue.

**Branches**:

*Transfer to queue mode:*
- **At capacity**: The destination queue cannot accept additional contacts (current count exceeds maximum contacts allowed). Contact remains in current working queue.
- **Error**: Transfer fails for reasons other than capacity (invalid queue ARN, queue doesn't exist, queue disabled for routing). Contact remains in current working queue.

*Transfer to queue in Customer Queue flow (contact already in queue):*
- **Success**: Contact successfully transferred to the destination queue.
- **At capacity**: Destination queue full. Contact remains in current working queue.
- **Error**: Transfer fails for non-capacity reasons. Contact remains in current working queue.

*Transfer to callback mode:*
- **Success**: Callback successfully scheduled and contact transferred to specified queue.
- **Error**: Callback scheduling failed.

**Tips**:
- When used in a Customer Queue flow, you must add a Loop prompts block before this block.
- To use this block in most flows, you must add a Set working queue block first. Two exceptions: (1) When used in a Customer Queue flow. (2) When making an outbound campaign that points to an Inbound flow -- the queue is already set via campaign configuration.
- Queue-to-queue transfers can be done only 11 times because there is a maximum limit of 12 contacts in a contact chain. Every transfer adds a new contact to the chain.
- The block checks queue capacity by comparing the current number of contacts in the queue to the Maximum contacts in queue limit. If no limit is set, the queue is limited to the concurrent contacts service quota for the instance.

---

### Transfer to agent (beta)

**Description**: Ends the current flow and transfers the customer to an agent. This block is a beta feature and works only for voice interactions. If the agent is already with someone else, the contact is disconnected. If the agent is in After Contact Work, they are automatically removed from ACW at the time of transfer. AWS recommends using the Set working queue block for agent-to-agent transfers instead, as it supports omnichannel transfers (voice and chat).

**Channels**: Voice (Yes), Chat (No - Error branch), Task (No - Error branch), Email (No - Error branch)

**Flow Types**: Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- This block does not have any configurable properties.

**Branches**:
- This block does not have any branches. It displays the status "Transferred" and is a terminal block.

**Tips**:
- This is a beta block -- prefer using Set working queue for agent-to-agent transfers as it supports all channels (voice, chat, task).
- If used with chat or task channels, the contact is routed down the Error branch.
- If the target agent is unavailable (on another call), the contact is disconnected -- there is no queue or retry mechanism.

---

### Transfer to phone number

**Description**: Transfers the customer to a phone number external to your Amazon Connect instance.

**Channels**: Voice (Yes), Chat (No - Error branch), Task (No - Error branch), Email (No - Error branch)

**Flow Types**: Inbound flow, Customer Queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Country code**: Select the country code for the destination phone number.
- **Phone number**: The external phone number to transfer the call to. Can be set manually or dynamically.
- **Set timeout**: The number of seconds to wait for the external party to answer before timing out (e.g., 30 seconds).
- **Resume flow after disconnect**: When set to Yes, returns the caller to your instance and resumes the flow after the transferred call ends. Only works if the external party disconnects -- if the customer disconnects, the whole call disconnects.
- **Send DTMF**: Useful to bypass DTMF menus of the external party. For example, enter "1,1,362" to automatically press those digits. A comma pauses for 750ms.
- **Caller ID number**: Choose a number from your instance to appear as the caller ID. If not specified, the caller's own caller ID is passed through to the external party.
- **Caller ID name**: Set a caller ID name, but there is no guarantee it will appear correctly to the customer. Per SIP protocol RFC3261, the following characters are reserved and must not be used: ; / ? : @ & = + $ , -- using them may cause outbound calls to fail or the caller ID name to display inaccurately.

**Branches**:
- **Success**: The call was successfully transferred.
- **Call Failed**: The outbound call to the external number failed.
- **Timeout**: The external party did not answer within the specified timeout period.
- **Error**: Any other error occurred during the transfer.

**Tips**:
- Submit a service quota increase request to allow your business to make outbound calls to the specified country. Calls to countries not on the allowlist will fail.
- If the country you want is not listed, submit a request using the Amazon Connect service quotas increase form.
- You can choose to end the flow when the call is transferred, or choose Resume flow after disconnect to return the caller after the transferred call ends.
- In Australia: The caller ID must be an Amazon Connect-provided DID (Direct Inward Dialing) number. Toll-free or non-Connect numbers may cause local telephony suppliers to reject outbound calls due to anti-fraud requirements.
- In the UK: The caller ID must be a valid E.164 phone number. Missing phone numbers may cause rejections due to local anti-fraud requirements.
- If using Amazon Connect outside the United States, it is recommended to select a Caller ID number from your instance. Otherwise, local regulations may cause telephony providers to block or redirect non-Amazon Connect phone numbers, resulting in rejected calls, poor audio quality, delay, latency, or incorrect caller ID display.

---

### Transfer to flow

**Description**: Ends the current flow and transfers the customer to a different flow.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: Inbound flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Flow**: Select the destination flow from a dropdown box. Can be set manually or dynamically. Only published flows appear in the dropdown list.

**Branches**:
- **Error**: The specified flow is not valid, or it is not a valid flow type (must be Inbound, Transfer to Agent, or Transfer to Queue flow).

**Tips**:
- Only published flows appear in the dropdown list for selection.
- The destination flow must be of a valid type: Inbound flow, Transfer to Agent flow, or Transfer to Queue flow.

---

### Disconnect / hang up

**Description**: Disconnects the contact. This is a terminal block that ends the call, chat, task, or email interaction.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: Inbound flow, Customer queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- This block does not have any configurable properties.

**Branches**:
- This block does not have any branches. It is a terminal block.

**Tips**:
- This is a terminal block used to end a contact interaction at the end of a flow.
- Use this block when you want to definitively end the contact's session.

---

### End flow / Resume

**Description**: Ends the current flow without disconnecting the contact. This is a terminal flow block that enables you to end a paused flow and return the contact without terminating the overall interaction. However, if placed in an inbound flow or disconnect flow, it functions identically to the Disconnect block and terminates the contact.

Common use cases:
- Often used for the Success branch of the Transfer to queue block. The flow doesn't end until the call is picked up by an agent.
- Used when a Loop prompts block is interrupted, to return the customer to the Loop prompts block.
- Used to end a paused flow and return the contact without terminating the overall interaction (e.g., pausing and resuming tasks).

**Channels**: Voice, Chat, Task, Email

**Flow Types**: All flows. However, if placed in an inbound flow or disconnect flow, it functions identically to the Disconnect block and terminates the contact.

**Properties**:
- This block does not have any configurable properties.

**Branches**:
- This block does not have any branches. It is a terminal block.

**Tips**:
- If placed in an inbound flow or disconnect flow, this block functions identically to the Disconnect block and terminates the contact.
- Use this block when you want to end the flow execution but keep the contact's session alive (e.g., while they wait in a queue).
- Useful for pausing and resuming tasks without disconnecting the contact.

---

### Resume contact

**Description**: Resumes a task contact from a paused state. This enables agents to free up an active slot so they can receive more critical tasks when their current task is stalled -- for example, because of a missing approval or waiting on external input.

**Channels**: Voice (No - Error branch), Chat (No - Error branch), Task (Yes), Email (No - Error branch)

**Flow Types**: All flow types

**Properties**:
- This block does not have any additional configurable properties beyond the standard block settings.

**Branches**:
- **Success**: The task was successfully resumed from its paused state.
- **Error**: An error occurred while attempting to resume the contact (e.g., the contact is not a task, or the task is not in a paused state).

**Tips**:
- When designing a flow to resume unassigned, paused tasks that are dequeued, be sure to add a Transfer to queue block to the flow to queue the task after resuming. Otherwise, the task will stay in a de-queued state.
- This block only works with Task contacts. Voice, Chat, and Email contacts will be routed to the Error branch.

---

## Flow Control

---

### Invoke module

**Description**: Calls a published module, which enables you to create reusable sections of a contact flow. Modules are shared building blocks that can be invoked from multiple flows.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: All flow types. If your module contains blocks that are not supported by the specific flow type, this incompatibility might cause interruptions in the flow execution.

**Properties**:
- **Module**: Select the published module to invoke. Can be set manually or dynamically.

**Branches**:
- **Success**: The module completed execution successfully and returned to the calling flow.
- **Error**: An error occurred during module execution (e.g., invalid module, module not published, or runtime error within the module).

**Tips**:
- Only published modules can be selected for invocation.
- If your module contains blocks not supported by the specific flow type it is called from, this may cause interruptions in flow execution.
- Modules enable reusable flow logic -- use them to avoid duplicating common flow patterns across multiple flows.

---

### Return (from module)

**Description**: Marks the terminal action or terminal step of a flow module. Use this block to exit the flow module after it has run successfully, then continue running the flow in which the module is referenced.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: Flow modules only. This block is not available in any other type of flow (not in Inbound, Customer Queue, Customer Hold, Customer Whisper, Outbound Whisper, Agent Hold, Agent Whisper, Transfer to Agent, or Transfer to Queue flows).

**Properties**:
- This block does not require any configuration. It is a terminal block for a flow module.

**Branches**:
- This block does not have any branches. No conditions are supported. It is a terminal block.

**Tips**:
- This block is only available when editing flow modules -- it will not appear in the block dock for any other flow type.
- The block is stored as an `EndFlowModuleExecution` action in the Amazon Connect Flow Language.
- Because this is a terminal block, there are no error scenarios that the flow may encounter when this block runs.
- No data is generated by this block.

---

### Loop

**Description**: Loops over the same blocks for a configured number of iterations through the Looping branch. After the loop is completed, the Complete branch is followed. If the provided input is incorrect, the Error branch is followed. This block is often used with a Get customer input block -- for example, if the customer doesn't succeed in entering their account number, you can loop to give them another opportunity.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: All flows

**Properties**:
- **Select an action**: Choose from two options:
  - **Set number of loops**: Loop for a specified count.
    - If the provided input is not a valid number, the Error branch is taken.
    - If Loop Name is provided, you can access the current index through `$.Loop.<yourLoopName>.Index` (starts from 0).
  - **Set array for looping**: Provide an array or list to loop through each element.
    - The block loops for the number of elements in the input.
    - Loop Name is required when looping over an array.
    - Accessible variables:
      - `$.Loop.<yourLoopName>.Index` -- Current index (starts from 0)
      - `$.Loop.<yourLoopName>.Element` -- Current looping element
      - `$.Loop.<yourLoopName>.Elements` -- The provided input array
    - Error branch is taken if an invalid array is provided.
- **Loop Name**: An optional (required for array looping) name for the loop. Must be unique -- no other loop should be active with the same loop name.

**Branches**:
- **Looping**: The contact follows this branch for each iteration of the loop.
- **Complete**: The contact follows this branch after all loop iterations are finished.
- **Error**: The contact follows this branch if the provided input is incorrect (invalid number or invalid array).

**Tips**:
- If you enter 0 for the loop count, the Complete branch is followed the first time this block runs.
- If a loop name is provided, it must be unique -- no other loop should be active with the same loop name.
- Use the Loop block with Get customer input for retry patterns (e.g., giving customers multiple attempts to enter account numbers).

---

### Wait

**Description**: Pauses the flow for a specified wait time or until a specified event occurs. For example, if a contact stops responding to a chat, the block pauses the contact flow for the specified wait time (Timeout), then branches accordingly (such as to disconnect).

**Channels**: Voice (Yes - but only in Inbound flow when the "Keep running while waiting" option or the "Set event-based wait" option is selected), Chat (Yes), Task (Yes - always branches to Time Expired or Error; never branches to Bot participant disconnected or Participant not found; the Participant Type setting does not affect this behavior), Email (Yes)

**Flow Types**: Inbound flow, Customer Queue flow

**Properties**:
- **Participant Type**: Runs the Wait block for the specified participant type.
  - **Default**: A customer contact.
  - **Bot**: A custom participant, such as a third-party bot.
- **Timeout**: Run this branch if the customer hasn't sent a message after a specified amount of time. Maximum is 7 days.
  - Manually set timeout: Provide Number and Units.
  - Dynamically set timeout: The unit of measurement is in seconds.
- **Customer return** (optional, Default participant type only): Route the contact down this branch when the customer returns and sends a message. You can route the customer to the previous (same) agent, previous (same) queue, or override and set a new working queue or agent.
- **Set Event based Wait** (optional, Default participant type only): Specify a Lambda to wait for its completion and route the contact down the Lambda Return branch when the Lambda execution completes.
- **Keep running while waiting** (optional, Default participant type only): Temporarily route the contact down the Continue branch while waiting on the block.

**Branches**:

*With Participant Type = Default:*
- **Time Expired**: The specified timeout has elapsed.
- **Customer return** (optional): The customer returned and sent a message.
- **Lambda return** (optional): The specified Lambda execution completed.
- **Continue** (optional): Temporary branch for running blocks while waiting.
- **Error**: An error occurred.

*With Participant Type = Bot:*
- **Bot participant disconnected**: The custom participant (e.g., third-party bot) has successfully disconnected from the contact.
- **Participant not found**: No custom participant was found to be associated with the contact.
- **Time Expired**: The timeout specified has elapsed before the custom participant disconnected.
- **Error**: An error occurred.

**Tips**:
- You can configure the Wait block to wait for a Lambda invoked using the Invoke AWS Lambda function block in Asynchronous execution mode. Select Set Event based Wait and provide the RequestId of the Lambda invocation. If the wrong Invocation ID is provided, it continues to wait until the Set timeout.
- You cannot have nested Wait blocks (e.g., a Wait block inside the Continue branch of another Wait block). This results in the error: "Unsupported Action In Wait Action's Continue Branch."
- You can configure the Wait block to run other blocks while waiting. For example, add a Play prompt block to the Continue branch to play audio while waiting for Lambda execution.
- You can add multiple Wait blocks to your flows for cascading timeout behavior. For example: if the customer comes back in 5 minutes, connect to the same agent; if not back after 5 minutes, send a "We missed you" text; if back in 12 hours, put in a priority queue but don't route to the same agent.

---

## Media and Streaming

---

### Start media streaming

**Description**: Captures what the customer hears and says during a contact. You can then perform analysis on the audio streams to determine customer sentiment, use the audio for training purposes, or identify and flag abusive callers.

**Channels**: Voice (Yes), Chat (No - Error branch), Task (No - Error branch), Email (No - Error branch)

**Flow Types**: Inbound flow, Customer Queue flow, Agent Whisper flow, Customer Whisper flow, Outbound Whisper flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Media stream direction**: Two options:
  - **From the customer**: Capture audio from the customer (what the customer says).
  - **To the customer**: Capture audio sent to the customer (what the customer hears).

**Branches**:
- **Success**: Media streaming started successfully.
- **Error**: An error occurred while starting media streaming (e.g., live media streaming not enabled, or triggered during a chat conversation).

**Tips**:
- You must enable live media streaming in your instance to successfully capture customer audio. See the Amazon Connect documentation for setup instructions.
- Customer audio is captured until a Stop media streaming block is invoked, even if the contact is passed to another flow.
- You must use a Stop media streaming block to stop media streaming.
- If this block is triggered during a chat conversation, the contact is routed down the Error branch.

---

### Stop media streaming

**Description**: Stops capturing customer audio after it was started with a Start media streaming block. You must use this block to stop media streaming.

**Channels**: Voice (Yes), Chat (No - Error branch), Task (No - Error branch), Email (No - Error branch)

**Flow Types**: Inbound flow, Customer Queue flow, Customer Whisper flow, Outbound Whisper flow, Agent Whisper flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- This block does not have any configurable properties.

**Branches**:
- **Success**: Media streaming stopped successfully.
- **Error**: An error occurred while stopping media streaming (e.g., triggered during a chat conversation).

**Tips**:
- You must enable live media streaming in your instance to successfully capture customer audio.
- Customer audio is captured until a Stop media streaming block is invoked, even if the contact is passed to another flow.
- If this block is triggered during a chat conversation, the contact is routed down the Error branch.
- Always pair Start media streaming with Stop media streaming to properly manage audio capture lifecycle.

---

## Outbound and Routing

---

### Call phone number

**Description**: Used to place an outbound call from an Outbound Whisper flow. Outbound whisper flows run in Amazon Connect immediately after an agent accepts the call during direct dial and callback scenarios.

**Channels**: Voice (Yes), Chat (No), Task (No), Email (No)

**Flow Types**: Outbound Whisper flow

**Properties**:
- **Caller ID number**: The phone number to display as the caller ID when placing the outbound call. Two options:
  - **Select a number from your instance**: Choose from a dropdown of available phone numbers claimed for your instance.
  - **Use Attribute**: Set dynamically using a contact attribute (e.g., Namespace = User-defined, Attribute = MainPhoneNumber).
- If no caller ID is specified, the caller ID number defined for the queue is used when the call is placed.

**Branches**:
- **Success**: The outbound call was successfully initiated.
- There is no Error branch. If a call is not successfully initiated, the flow ends and the agent is placed in AfterContactWork (ACW).

**Tips**:
- To use a custom caller ID, you must open an AWS Support ticket to enable this feature.
- Only published flows can be selected as the outbound whisper flow for a queue.
- When there is an error with a call initiated by this block, the call is disconnected and the agent is placed in AfterContactWork (ACW).
- There is no error branch -- if the call fails, the flow simply ends and the agent goes to ACW.

---

### Change routing priority / age

**Description**: Changes a customer's position in the queue. For example, move the contact to the front of the queue or to the back of the queue.

**Channels**: Voice, Chat, Task, Email

**Flow Types**: Inbound flow, Customer queue flow, Transfer to Agent flow, Transfer to Queue flow

**Properties**:
- **Set priority**: Change the contact's priority relative to other contacts in the queue.
  - Default priority for new contacts: 5
  - Range of valid values: 1 (highest priority) to 9223372036854775807 (lowest priority). If you enter a number larger than the max, the flow will fail when published.
- **Adjust by time**: Add or subtract seconds or minutes from the amount of time the current contact has spent in queue. Contacts are routed on a first-come, first-served basis, so changing their perceived time in queue also changes their position.
  - How it works: Connect takes the actual "time in queue" for the contact and adds the specified seconds. The additional seconds make the contact appear artificially older, causing the routing system to perceive this contact's time in queue as longer than it actually is, which affects its position in the ranked list.

**Branches**:
- **Success**: The routing priority or age was successfully changed.

**Tips**:
- When using this block, it takes at least 60 seconds for a change to take effect for contacts already in queue.
- If you need a change in a contact's priority to take effect immediately, set the priority before putting the contact in queue (i.e., before using a Transfer to queue block).
- You can use negative time adjustments to move contacts toward the back of the queue.
