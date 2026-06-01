# Amazon Connect Flow Designer Overview

## Flow Types

Amazon Connect provides ten distinct flow types, each tailored for a specific scenario in the contact routing lifecycle. Each type only exposes the blocks relevant to that scenario.

### Inbound Flow (Contact Flow)

The primary flow type. Runs when a customer initiates contact (phone call, chat, task). This is where you define the complete customer experience: greetings, menus, data lookups, routing decisions, and queue placement.

- Default: "Default customer queue flow" is used if no inbound flow is assigned to a phone number or chat endpoint.
- Every phone number or chat endpoint must be associated with an inbound flow.
- Works with voice, chat, and tasks.

### Campaign Flow

Manages what the customer experiences during an outbound campaign.

- Only works with outbound campaigns.
- Separate from outbound whisper flows.

### Customer Queue Flow

Runs while the customer is waiting in queue. Controls the hold experience: music, position announcements, estimated wait time, callback offers.

- Triggered after `Transfer to queue` places the contact in a queue.
- Can loop prompts, offer callbacks, or check queue metrics to make dynamic decisions.
- Set via the `Set customer queue flow` block in the inbound flow.
- Interruptible: can include actions such as offering a callback via the `Transfer to queue` block.
- Works with voice, chat, and tasks.

### Customer Hold Flow

Manages what the customer experiences while on hold (agent-initiated hold).

- One or more audio prompts can be played using the `Loop prompts` block.
- Works with voice only.

### Customer Whisper Flow

Plays a short message to the customer immediately before the agent connects. The customer hears this; the agent does not.

- Example: "This call may be recorded for quality purposes."
- Set via the `Set whisper flow` block (customer side).
- Default: "Default customer whisper" plays a beep.
- Works with voice and chat.

### Agent Hold Flow

Manages what the agent experiences when the customer is on hold.

- One or more audio prompts can be played using the `Loop prompts` block.
- Works with voice only.

### Agent Whisper Flow

Plays a short message to the agent immediately before they connect with the customer. The agent hears this; the customer does not.

- Example: "Incoming call from the billing queue."
- Set via the `Set whisper flow` block (agent side).
- Default: "Default agent whisper" plays a beep.
- Works with voice, chat, and tasks.

### Outbound Whisper Flow

Runs when an outbound call is placed (agent-initiated or via API). Controls what happens while the call is connecting and after the customer answers.

- Used for outbound campaigns, callbacks, and agent-initiated calls.
- Set at the queue level or via API.
- Can enable call recording using the `Set recording behavior` block.
- Works with voice and chat.

### Transfer to Agent Flow

Runs when a contact is transferred directly to a specific agent (not a queue). Associated with transfer-to-agent quick connects.

- Often plays messaging, then completes the transfer using the `Transfer to agent` block.
- Do not place sensitive information in this flow: during cold transfer, the transferring agent disconnects before transfer completes, and this flow runs for the caller.
- Works with voice, chat, and tasks.

### Transfer to Queue Flow

Runs when a contact is transferred to a different queue. Allows you to modify attributes, play prompts, or apply different routing logic before the contact enters the new queue.

- Associated with transfer-to-queue quick connects.
- Set via the `Transfer to queue` block.
- Works with voice, chat, and tasks.

## Default Flows

Every Amazon Connect instance comes with default flows that cannot be deleted. They serve as fallbacks when no custom flow is assigned. You can modify default flows, but the recommended practice is to create custom flows and reference them explicitly rather than relying on defaults.

Every instance includes 9 default flows that serve as automatic fallbacks. See [default-flows.md](default-flows.md) for full detail on each flow including blocks, triggers, channel support, customization steps, and caveats.

| Default Flow | Type | Trigger |
|---|---|---|
| Default agent hold | Agent Hold | Agent placed on hold |
| Default agent transfer | Transfer to Agent | Contact transferred to agent |
| Default customer queue | Customer Queue | Customer waiting in queue |
| Default customer whisper | Customer Whisper | Before agent connection (customer side) |
| Default agent whisper | Agent Whisper | Before customer connection (agent side) |
| Default customer hold | Customer Hold | Customer placed on hold |
| Default outbound | Outbound Whisper | Outbound call before agent connection |
| Default queue transfer | Transfer to Queue | Contact transferred between queues |
| Default prompts from Lex | N/A | Lex bot fallback prompts |

**Key caveat:** Default customer queue flow is **voice only** — fails for chat/task/email. Chat whispers require explicit Set whisper flow block.

## Sample Flows

Amazon Connect provides sample flows that demonstrate common patterns. These cannot be edited directly; clone them to create editable copies.

| Sample Flow | Purpose |
|---|---|
| Sample inbound flow | First call experience, basic routing |
| Sample AB test | A/B contact distribution testing |
| Sample customer queue priority | Priority-based queue routing |
| Sample disconnect flow | Post-disconnect handling |
| Sample queue configurations | Different queue configuration patterns |
| Sample queue customer | Customer queue experience |
| Sample queued callback | Offering callbacks to customers in queue |
| Sample interruptible queue flow with callback | Interruptible queue with callback offer |
| Sample Lambda integration | Invoking Lambda functions from flows |
| Sample recording behavior | Configuring call recording |
| Sample note for screenpop | Passing screenpop data to agents |
| Sample secure input with agent | Secure customer data entry with an agent on the line |
| Sample secure input with no agent | Secure customer data entry without an agent |

To try a sample flow: claim a phone number, assign the sample flow, and call the number.

## Flow Modules

Flow modules are reusable, nestable sub-flows that work across all flow types.

### Creation and Usage

- Create a module: Routing > Contact flows > Modules > Create flow module.
- Add a description and up to 50 tags per module.
- Invoke from any flow using the `Invoke flow module` block (in the Integrate group).
- Modules end with the `Return` block, which passes control back to the calling flow.
- Modules can set contact attributes that the calling flow can read.

### Nesting

- Modules can invoke other modules, supporting up to **5 levels of nesting** with a stack limit to prevent recursive invocations.
- A module used as a tool can only invoke other modules also used as tools.

### Input, Output, and Custom Branches

- Modules support custom input/output schemas defined in the Settings tab.
- Input/output schemas default to Object type; properties support String, Number, Integer, Boolean, Object, Array, and Null types.
- Schemas can be defined via Designer mode or JSON schema mode.
- Up to **8 custom branches** per module.
- Module attributes: `$.Modules.Input`, `$.Modules.Result`, `$.Modules.ResultData`.
- Module attributes are not included in contact records, not passed to subsequent module invocations, and not available in the CCP.

### Versioning and Aliasing

- Module versions are immutable snapshots for consistency and reliability.
- Module aliases are descriptive names pointing to specific versions.
- `$.LATEST` alias automatically tracks the newest version.
- View specific versions or aliases in read-only mode.

### Limitations

- Modules do not allow overriding flow-local data of the invoking flow (External attributes, Lex attributes, Customer Profiles attributes, AI agents attributes, Queue metrics, Stored customer input).
- Flow attributes set within a module are not passed out of the module.
- If a module contains blocks not supported by the calling flow type, those blocks take the error branch.
- To pass data to/from a module, use attributes explicitly.

### Modules as Tools

Modules can be configured as tools for external invocation by systems like Connect AI agents (Q in Connect). This allows AI agents to use modules for actions like payment workflows and automated tasks. Supported blocks for tool modules include Cases, CheckContactAttributes, InvokeLambdaFunction, SetAttributes, CreateTask, DataTable, Loop, Return, and many others.

### Permissions

- **Contact flow modules** permissions in security profiles are required.
- Default: Admin and CallCenterManager profiles have module permissions.

## Flow Designer

The flow designer is a drag-and-drop canvas for building flows.

### Canvas Features

- Drag and drop blocks onto the canvas.
- Connect blocks by dragging from output branch circles to input connectors.
- Select multiple blocks with `Ctrl/Cmd + click` or by dragging a selection rectangle.
- Mini-map for navigating large flows.
- Block counter shows how many blocks are in the flow (warns at 200+ for export limits).
- Notes can be added to blocks for documentation.
- Custom block names for readability.
- Undo/redo history.
- Copy and paste flows or sections of flows.
- Auto-arrange blocks into a grid layout.
- All connectors must be connected to a block to publish.

### Block Categories

Blocks are organized into groups: Interact, Set, Branch, Integrate, Terminate, and others depending on flow type.

### Error Handling

Every block has at least a Success and Error branch. Always connect Error branches to meaningful fallback logic (play an apology prompt, transfer to queue, disconnect gracefully).

## Keyboard Shortcuts

### General

| Shortcut | Action |
|---|---|
| `Ctrl + /` | Open keyboard shortcuts panel |
| `Ctrl + C` / `Ctrl + V` | Copy / paste blocks |
| `Ctrl + Z` / `Ctrl + Y` | Undo / redo |
| `Ctrl + A` | Select all blocks |
| `Ctrl + S` | Save flow |
| `Delete` / `Backspace` | Delete selected blocks |
| `Ctrl + Alt + A` | Auto-arrange selected blocks (or all if all selected) |

### Canvas Navigation

| Shortcut | Action |
|---|---|
| `Home` | Jump to Entry block |
| `W`, `A`, `S`, `D` | Scroll through canvas (hold to move faster) |
| `Page Up` / `Page Down` | Step through items sequentially (row-wise) |
| Arrow keys | Navigate and select blocks |
| `Space` | Pick up / drop a block (then move with arrow keys) |

### Block Navigation

| Shortcut | Action |
|---|---|
| `K` | Cycle outgoing branches of a selected block |
| `L` | Select the cycled target block |
| `J` | Trace incoming branches to a block |

### Notes

| Shortcut | Action |
|---|---|
| `N` (after Home) | Create a new note |
| `Alt + N` | Fold / unfold selected note |
| `Enter` (note selected) | Begin editing note |

## Permissions

Flow management requires specific security profile permissions:

| Permission | Purpose |
|---|---|
| Flows - Create | Create and clone flows |
| Flows - Edit | Modify existing flows |
| Flows - Delete | Remove flows |
| Flows - Publish | Save and publish flows (making them live) |
| Flows - View | View flow list and details |
| Contact flow modules - Create/Edit/Delete/Publish/View | Separate permissions for modules |
| Numbers and flows - Prompts - Create/Edit/Delete | Manage prompts used in flows |

By default, Admin and CallCenterManager security profiles have these permissions.

## Prompts

Prompts are audio files or text-to-speech content used in flows.

### Creating Prompts

- Upload WAV files (8 kHz, 16-bit, mono PCM recommended for telephony; higher-rate files are downsampled to 8 kHz due to PSTN G.711 limitations).
- Record directly in the admin console via microphone (with crop and clear options).
- Use SSML or plain text for TTS prompts (configured per `Play prompt` or `Get customer input` block).
- Create prompts programmatically via the `CreatePrompt` API.
- Requires security profile permission: Numbers and flows > Prompts - Create.

### Prompt Limits

| Limit | Value |
|---|---|
| Maximum file size | 50 MB |
| Maximum duration | 5 minutes |
| Supported upload format | WAV |
| Bulk upload | Not supported (UI, API, or CLI) |

### Managing Prompts

- Manage in the admin console under Routing > Prompts.
- Prompts can be referenced by name or ARN in flow blocks.
- Filter prompts by Name, Description, and Tags.
- Copy full ARN with one click for use in dynamic prompt selection.
- Prompts can be tagged for organization and access control.
- Descriptions are recommended for accessibility.

### S3-Stored Prompts

- Dynamic content can be served from S3 via the `Get stored content` block.
- Useful for frequently changing prompts without re-uploading.

### Text-to-Speech

- Amazon Polly voices available for TTS.
- SSML tags supported for pronunciation, emphasis, pauses, etc.
- Dynamic text strings can reference contact attributes in Play prompt blocks.
- Voice and language selectable per block.

## Import and Export

Flows can be exported as JSON and imported into the same or different instances.

### Export

- Select a flow in the designer, choose Save > Export flow.
- Produces a JSON file in the Flow Language format.
- Files are created without a file extension by default.

### Export Limitations

- Flow must have **fewer than 200 blocks**.
- Total flow size must be **less than 1 MB**.
- Divide large flows into smaller ones to meet these requirements.

### Import

- Choose Save > Import flow in the flow designer.
- Can replace an existing flow or create a new one of the same type.
- The JSON is validated before import.
- Cannot import flows of different types (e.g., cannot import a customer queue flow into an inbound flow).

### Resource Resolution on Import

- Connect attempts to resolve resources (queues, prompts, Lambda ARNs) by ARN first, then by name.
- Same-instance imports resolve automatically.
- Cross-instance imports require ARN updates or matching resource names.
- Unresolved resources show warnings on the affected blocks.
- Flows can be saved with unresolved resources but can only be published if all required parameters are resolved.

### Flow Language Format

- Legacy flow format support for import ends **03/31/2026**.
- Copy/paste in the updated designer only works with the new flow language format.
- Stored offline flow configurations must be updated to the new format before the deadline.

## Migration

When migrating flows between instances, regions, or environments:

### Manual Migration (Few Flows)

1. Export flows as JSON from the source instance.
2. Update all ARN references (Lambda functions, Lex bots, queues, prompts) to match the target instance.
3. Import into the target instance.
4. Test thoroughly: attribute references, Lambda integrations, and queue assignments.

### Programmatic Migration (Many Flows)

Use APIs for migrating tens or hundreds of flows:

1. **Source instance**:
   - `ListContactFlows`: Retrieve ARNs for flows to migrate.
   - `DescribeContactFlow`: Get flow details and content.
2. **Target instance**:
   - `CreateContactFlow`: Create flows in the target.
   - `UpdateContactFlowContent`: Update flow content.
3. Build an **ARN-to-ARN mapping** for queues, flows, and prompts between source and target instances.
4. Replace every ARN in the source flow with the corresponding target ARN.
5. `UpdateContactFlowContent` fails with `InvalidContactFlow` if ARNs are not updated.

## Flow Versioning

Flow versioning provides version control for published flows.

### Viewing Previous Versions

- Open a flow and use the **Latest: Published** dropdown to view previously published versions.
- For default flows, the oldest version matches the instance creation date.
- Each version can be opened in read-only mode to inspect all blocks and configurations.
- Users with tag-based access controls are restricted to Latest: Published and Latest: Saved versions.

### Rolling Back

1. Open the flow in the designer.
2. Choose the version to roll back to from the dropdown.
3. Choose **Publish** to push that version into production.

### Save Options

- **Save**: Save with the same name.
- **Save as**: Save as a new flow with a different name.
- **Publish**: Push the version into production immediately.

### Historical Changes

- Choose **View historical changes** at the bottom of the Flows page for a consolidated view of all changes across all flows.
- Filter by date or user name.

## Conversational AI Bots

Flows integrate with conversational AI through the `Get customer input` block:

- **Amazon Lex V2** (preferred): Supports multiple languages, streaming, and improved NLU.
- **Amazon Lex (Classic)**: Legacy support.
- The `Get customer input` block can be configured for DTMF, Lex, or both.
- Lex slot values are available as contact attributes: `$.Lex.{SlotName}`.
- Lex session attributes can pass context between the flow and the bot.

## Nova Sonic Speech-to-Speech

Amazon Nova Sonic enables speech-to-speech AI interactions in contact flows. Instead of the traditional IVR pipeline (TTS prompt -> speech recognition -> Lex NLU -> response TTS), Nova Sonic provides a single model that processes speech input and generates speech output directly.

- Configured as a speech model on a Conversational AI bot locale.
- Requires a Nova Sonic-compatible voice in the `Set voice` block with Generative speaking style.
- See `nova-sonic.md` for detailed configuration.

## Agent-Initiated Flows

Agents can trigger outbound flows:

- Outbound calls use the outbound whisper flow assigned to the queue.
- Quick connects can invoke transfer flows.
- The Connect Agent Workspace or CCP initiates the flow.
- Agent-initiated flows have access to the agent's contact attributes and the destination number.

## Callbacks

### Queued Callback

- Offered to customers waiting in queue via the `Create callback` block (inside a customer queue flow or transfer to queue flow).
- The customer provides a callback number (or uses the inbound number).
- The callback is placed in the queue at the same priority/position.
- When an agent becomes available, Connect dials the customer.
- Retry logic: configurable number of retry attempts and delay between retries.

### Customer-First Mode

- In customer-first callback mode, Connect dials the customer first.
- Only after the customer answers does Connect route to an available agent.
- Reduces agent idle time waiting for the customer to pick up.
- Configured in the callback block settings.

## Limits

| Limit | Value |
|---|---|
| Maximum blocks per flow | 250 (hard limit) |
| Maximum blocks for export | 200 |
| Maximum flow size for export | 1 MB |
| Maximum flows chained via Transfer to flow | 20 |
| Maximum flow execution time (voice) | 5 minutes |
| Maximum flow execution time (chat/task) | 7 days |
| Maximum flows per instance | 500 (soft limit, can be increased) |
| Maximum modules per instance | 200 (soft limit) |
| Maximum module nesting depth | 5 levels |
| Maximum custom branches per module | 8 |
| Maximum tags per module | 50 |
| Maximum Lambda chain duration | 20 seconds cumulative |
| Maximum Lambda timeout per invocation | 8 seconds |
