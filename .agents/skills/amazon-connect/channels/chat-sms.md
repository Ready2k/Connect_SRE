# Chat and SMS Channel

Amazon Connect supports real-time chat, SMS, and third-party messaging integrations. Agents handle chat contacts through the same CCP used for voice, with unified routing and reporting.

## Web Chat — Communications Widget

Connect provides a hosted, embeddable chat widget for websites and web applications. Up to 20 widgets can be created per instance.

**Setup:**
- Configure in the Connect console under "Communications widget"
- Generates a short JavaScript snippet to embed on your site
- Widget is hosted and served by AWS — no infrastructure to manage

**Customization:**
- Font family and size
- Primary color, background color, text color
- Widget button icon and position (bottom-right by default)
- Custom header text and subtitle
- Display name for bot and agent messages
- Company logo in the widget header
- Pre-chat form: collect customer name, email, or custom fields before the chat starts — data flows into contact attributes

**Security:**
- Widget is secured to your specific domain(s) via allowlisting
- Only renders on approved origins — prevents unauthorized embedding
- Supports JWT-based authentication for identifying logged-in customers
- HTTPS required on the hosting domain

**JWT authentication:**
- Pass a JWT token when initializing the widget to identify the customer
- JWT payload can include customer name, email, account ID — mapped to contact attributes
- Token is validated server-side by Connect
- Enables personalized greetings and routing based on authenticated identity
- Useful for logged-in customer portals where you already know who the user is

**Embedding — minimal code snippet:**

```html
<!-- Paste in your website's <head> or before </body> -->
<script type="text/javascript">
  (function(w, d, x, id){
    s=d.createElement('script');
    s.src='https://d3xxxxxxxxxxxx.cloudfront.net/amazon-connect-chat-interface-client.js';
    s.async=1;
    s.id=id;
    d.getElementsByTagName('head')[0].appendChild(s);
    w[x] = w[x] || function() { (w[x].ac = w[x].ac || []).push(arguments) };
  })(window, document, 'amazon_connect', 'amazon-connect-chat-widget');

  amazon_connect('styles', { openChat: { color: '#ffffff', backgroundColor: '#0052cc' }});
  amazon_connect('snippetId', 'YOUR_SNIPPET_ID');
</script>
```

**Widget sandbox attributes (for hyperlinks in interactive messages):**
```javascript
amazon_connect('updateSandboxAttributes',
  'allow-scripts allow-same-origin allow-popups allow-downloads allow-top-navigation-by-user-activation');
```

**Features:**
- Rich text messages, emojis
- File attachments (images, PDFs, etc.)
- Typing indicators
- Read receipts
- Message delivery status
- Persistent chat (continue previous conversations)
- Interactive messages (list pickers, quick replies, carousels)

## Chat Attachments

Enable agents and customers to share files during chat, email, and tasks.

**Enabling attachments:**
1. Open the Connect console → instance → **Data storage**
2. Under **Attachments**, choose **Edit**, select **Enable Attachments sharing**, then **Save**
3. Configure an S3 bucket for attachment storage (default: existing Connect bucket with new prefix)
4. Set up a CORS policy on the S3 bucket allowing `PUT` and `GET` from your domains
5. Optionally configure attachment scanning for compliance

**Supported file types:**
`.csv`, `.doc`, `.docx`, `.heic`, `.jfif`, `.jpeg`, `.jpg`, `.mov`, `.mp4`, `.pdf`, `.png`, `.ppt`, `.pptx`, `.rtf`, `.txt`, `.wav`, `.xls`, `.xlsx`
- Administrators can add custom file extensions via the admin website or API

**Size limits:**
- Default maximum: **20 MB** per attachment
- Configurable up to **100 MB** via admin website or API
- Maximum **35 attachments** per chat conversation
- S3 buckets with Object Lock are not supported

**Storage architecture:**
- Uses two S3 locations: **staging** (pre-validation) and **final** (post-validation)
- Staging location validates file size and type before the file is available for download
- Recommended: set a 1-day lifecycle policy on the staging prefix to avoid storage costs
- Never change the lifecycle for the entire bucket — only the staging prefix

**Security profile permissions:**
- **View** — users can see file attachment settings
- **Edit** — users can modify attachment sizes and types
- **All** — both View and Edit

**Custom application APIs:**
- `StartAttachmentUpload` / `CompleteAttachmentUpload` / `GetAttachment` — Participant Service APIs for custom chat UIs
- `StartAttachedFileUpload` / `CompleteAttachedFileUpload` / `GetAttachedFile` / `BatchGetAttachedFileMetadata` / `DeleteAttachedFile` — Connect APIs for custom agent applications

## Chat Concurrency

Agents can handle multiple chat conversations simultaneously.

- Configured per **routing profile** — set the maximum concurrent chats per agent
- Maximum: **10 active chats** per agent (hard limit)
- Typical configuration: 2–5 simultaneous chats
- Chat does not block voice — agents can take a call while handling chats (if routing profile allows cross-channel concurrency)
- Each chat appears as a separate tab/contact in the CCP

## Rich Messaging — Interactive Messages

Interactive messages present structured content with selectable options. Powered by Amazon Lex and configured via a Lambda function.

**Template types:**

| Template | Description | Max Elements |
|----------|-------------|--------------|
| **List Picker** | List of selectable options with optional images per item | 10 elements (unlimited via action buttons) |
| **Quick Reply** | Inline horizontal buttons for simple choices | 10 for web chat, 5 for Apple Messages |
| **Panel** | Selectable options under one image (no per-item images) | 10 elements (unlimited via action buttons) |
| **Carousel** | Horizontally scrollable cards, each a list picker or panel | 5 cards |
| **Time Picker** | Appointment scheduling with date/time slots and location | 40 timeslots |

**List picker example (Lambda response):**
```json
{
  "templateType": "ListPicker",
  "version": "1.0",
  "data": {
    "replyMessage": {
      "title": "Thanks for selecting!"
    },
    "content": {
      "title": "What department do you need?",
      "subtitle": "Tap to select",
      "elements": [
        { "title": "Billing", "subtitle": "Payment questions" },
        { "title": "Technical Support", "subtitle": "Product issues" },
        { "title": "Sales", "subtitle": "New orders" }
      ]
    }
  }
}
```

**Quick reply example:**
```json
{
  "templateType": "QuickReply",
  "version": "1.0",
  "data": {
    "replyMessage": { "title": "Thanks for selecting!" },
    "content": {
      "title": "Which department would you like?",
      "elements": [
        { "title": "Billing" },
        { "title": "Cancellation" },
        { "title": "New Service" }
      ]
    }
  }
}
```

**Carousel example:**
```json
{
  "templateType": "Carousel",
  "version": "1.0",
  "data": {
    "content": {
      "title": "View our options",
      "elements": [
        {
          "templateIdentifier": "template0",
          "templateType": "Panel",
          "version": "1.0",
          "data": {
            "content": {
              "title": "Option A",
              "elements": [
                { "title": "Select A" },
                { "title": "Learn more" }
              ]
            }
          }
        }
      ]
    }
  }
}
```

**Carousel response format:**
```json
{
  "templateIdentifier": "template0",
  "listTitle": "Option A",
  "selectionText": "Select A"
}
```

**Carousel hyperlinks in elements:**
```json
{
  "title": "Learn More",
  "type": "hyperlink",
  "url": "https://www.example.com/details"
}
```

**Validation:**
- Total interactive message size must be less than **20 KB**
- String field limits are enforced by the client (truncated with ellipsis in the hosted widget)
- Images in interactive messages for Apple Messages must be S3 object URLs (max 200 KB, read access for `connect.amazonaws.com`)

**Platform-specific templates:**
- **Apple Form** — multi-page form with ListPicker, WheelPicker, DatePicker, Input page types
- **Apple Pay** — payment request via Apple Messages for Business
- **iMessage App** — custom iMessage app extension
- **WhatsApp List** — WhatsApp-native list format
- **WhatsApp Reply Button** — WhatsApp-native reply buttons

**Rich formatting in titles/subtitles:**
- Supports bold, italic, strikethrough, and hyperlinks in title and subtitle fields
- Uses markdown-like syntax rendered by the widget

## SMS Channel

Two-way SMS messaging through Amazon Connect, powered by Amazon Pinpoint SMS.

**Setup:**
1. Request a phone number or short code through Amazon Pinpoint SMS
2. Associate the SMS number with your Connect instance
3. Configure a contact flow for inbound SMS
4. Optionally integrate with Amazon Lex for automated responses

**SMS number types:**

| Type | Description | Throughput | Provisioning Time |
|------|-------------|------------|-------------------|
| **10DLC** (10-Digit Long Code) | Standard US number. Register brand + campaign in Pinpoint. Required for A2P SMS in US. | Up to 100 MPS | Days (after brand/campaign approval) |
| **Toll-Free** | Higher throughput than 10DLC. Requires toll-free verification. | Higher than 10DLC | Days–weeks |
| **Short Code** | 5-6 digit number. Highest throughput. Best for high-volume notifications. | Highest | 8–12 weeks |

**10DLC setup process:**
1. Register your brand in Amazon Pinpoint (company name, EIN, website)
2. Register a campaign (use case description, sample messages, message flow)
3. Wait for brand and campaign approval by carrier
4. Claim a 10DLC number in Pinpoint
5. Associate the number with your Connect instance
6. Map the number to an inbound contact flow

**Capabilities:**
- Two-way SMS — customers can initiate conversations and agents can reply
- Lex bot integration for automated self-service responses before agent handoff
- SMS messages routed through the same queues and routing profiles as chat
- Supports long messages (multi-segment SMS)
- Delivery receipts

**Message size limits:**
- Inbound SMS to agent or Lex: **1,024 characters**
- Outbound SMS from agent or Lex: **1,024 characters**

**Lex auto-response pattern:**
- Customer sends SMS
- Connect contact flow routes to a Lex bot
- Bot handles FAQs, appointment confirmations, status checks
- Escalates to a live agent when needed
- Agent sees the full Lex conversation history in the CCP

## Third-Party Messaging Integrations

Connect supports messaging platforms beyond native chat and SMS.

### Apple Messages for Business
- Integrate via Apple Business Register
- Connect receives messages as chat contacts
- Requires Apple Business account + Connect chat flow
- Supports rich messages: list pickers, time pickers, Apple Pay, forms
- Customer entry points: Maps, Safari, Spotlight search
- Message size limits: 1,024 chars inbound to Lex, 4,096 chars inbound to agent, 4,096 chars outbound
- Interactive message images must be S3 URLs (max 200 KB)
- Quick replies limited to 5 elements (Apple restriction)

### WhatsApp Business
- Register WhatsApp Business account via Meta Business Manager
- Configure in Connect admin console
- Map to inbound chat flow
- Supports rich messages (images, documents, location)
- Template messages required for outbound (24-hour session window)
- After 24 hours of inactivity, only pre-approved template messages can be sent
- Message size limits: 1,024 chars inbound to Lex, 4,096 chars inbound to agent, 4,096 chars outbound

**WhatsApp attachment limits:**

| Media Type | Supported Types | Max Size |
|------------|----------------|----------|
| Image | `.jpeg`, `.jpg`, `.jfif`, `.png` | 5 MB |
| Video | `.mp4`, `.3gp` | 16 MB |
| Document | `.txt`, `.pdf`, `.ppt`, `.pptx`, `.doc`, `.docx`, `.xls`, `.xlsx` | 20 MB |
| Audio | `.aac`, `.m4a`, `.mp3`, `.amr`, `.ogg` | 16 MB |
| Sticker | Not supported | — |

### Facebook Messenger
- Connect your Facebook Page to Amazon Connect
- Customer messages from Messenger route to agents
- Supports text, images, and quick replies
- Configured via the Connect console or APIs

**Integration architecture:**
- Third-party messages arrive via Amazon Connect APIs
- Contact flows handle routing logic identically to native chat
- Agents see a unified interface regardless of the originating channel
- Contact records and analytics capture the source channel

## Chat Message Streaming

Subscribe to real-time chat events for building custom integrations, analytics, or monitoring tools.

**Real-time streaming via APIs:**
- Subscribe to new chat contacts and message events
- Receive events as they happen (new message, participant joined/left, typing)
- Build custom dashboards, logging systems, or AI-powered assist tools

**Use cases:**
- Real-time supervisor monitoring of chat conversations
- Custom analytics pipelines for chat content
- AI agent-assist that reads messages and suggests responses
- Compliance logging and archival

**Event types:**
- `PARTICIPANT_JOINED` — agent or customer enters the chat
- `PARTICIPANT_LEFT` — agent or customer leaves
- `MESSAGE` — new message sent by any participant
- `EVENT` — typing indicator, read receipt, attachment
- `DISCONNECT` — chat session ended

## Persistent Chat

Allow customers to return to a previous conversation without losing context. Powered by `CreatePersistentContactAssociation`.

**How it works:**
- When a chat ends, create a persistent association using `CreatePersistentContactAssociation`
- When the customer returns, the widget loads the previous conversation history
- Context carries over — no need for the customer to re-explain their issue
- The new contact can route to the same agent (if available) or a different one

**Key details:**
- Association is tied to a source (e.g., customer ID, session token)
- History is displayed to the agent in the CCP
- Works with both the hosted widget and custom chat implementations
- Persistent associations have a configurable TTL
- Past transcript file size limit: **5 MB**
- Maximum past contacts traversed: **100**
- Rehydration types: `ENTIRE_PAST_SESSION` (full history) or `FROM_SEGMENT` (partial)

```javascript
import { ConnectClient, CreatePersistentContactAssociationCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

await client.send(new CreatePersistentContactAssociationCommand({
  InstanceId: instanceId,
  InitialContactId: initialContactId,
  RehydrationType: "ENTIRE_PAST_SESSION", // or FROM_SEGMENT
  SourceContactId: sourceContactId,
}));
```

## Multi-Party Chat

With enhanced contact monitoring enabled, chat supports multi-party conversations.

- Up to **6 participants** on a chat: customer + agent + 4 additional participants (other agents via quick connects)
- Up to **5 supervisors** can monitor a chat simultaneously
- Only **1 supervisor** can barge in on a given chat at a time
- 1 custom participant allowed per contact (e.g., a custom bot)
- Agents add participants using quick connects in the CCP

## Chat Transfer

Agents can transfer chat conversations to other agents or queues.

- **Warm transfer** — agent stays on chat, adds the target agent, briefs them, then leaves
- **Cold transfer** — agent transfers directly to a queue; customer may wait for a new agent
- Contact attributes and conversation history carry over to the receiving agent
- Transfer works across queues with different routing profiles

## Chat APIs

### StartChatContact

Initiate a new inbound chat contact programmatically (e.g., from a custom UI or backend trigger).

```javascript
import { ConnectClient, StartChatContactCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

const response = await client.send(new StartChatContactCommand({
  InstanceId: instanceId,
  ContactFlowId: contactFlowId,
  ParticipantDetails: {
    DisplayName: "Jane Customer",
  },
  Attributes: {
    customerName: "Jane",
    accountId: "12345",
  },
  // Optional: set chat duration (minutes)
  ChatDurationInMinutes: 1440, // 24 hours
}));

// response.ContactId — unique ID for this contact
// response.ParticipantId — customer's participant ID
// response.ParticipantToken — token for the customer to connect to the chat
```

### StartOutboundChatContact

Proactively reach out to a customer via chat (e.g., order update, appointment reminder).

```javascript
const response = await client.send(new StartOutboundChatContactCommand({
  InstanceId: instanceId,
  ContactFlowId: outboundFlowId,
  DestinationEndpoint: {
    Type: "CONNECT_PHONENUMBER", // or other endpoint types
    Address: "+14155551234",
  },
  ParticipantDetails: {
    DisplayName: "Support Team",
  },
}));
```

### SendChatIntegrationEvent

Inject events into a chat contact from an external system (e.g., a CRM sending a notification into an active chat).

```javascript
const response = await client.send(new SendChatIntegrationEventCommand({
  SourceId: "external-crm-system",
  DestinationId: destinationId,
  Event: {
    Type: "MESSAGE",
    Content: JSON.stringify({
      Content: "Your order #456 has shipped!",
      ContentType: "text/plain",
    }),
  },
  Subtype: "connect:sms", // or other subtypes
}));
```

### GetTranscript

Retrieve the transcript of a chat conversation (via Participant Service).

```javascript
import { ConnectParticipantClient, GetTranscriptCommand } from "@aws-sdk/client-connectparticipant";

const client = new ConnectParticipantClient({ region: "us-east-1" });

const response = await client.send(new GetTranscriptCommand({
  ConnectionToken: connectionToken,
  // Optional filters
  MaxResults: 100,
  SortOrder: "ASCENDING",
}));

// response.Transcript — array of chat message items
// response.NextToken — pagination token
```

### CreateParticipant

Add a custom participant (e.g., a bot) to an active chat contact.

```javascript
const response = await client.send(new CreateParticipantCommand({
  InstanceId: instanceId,
  ContactId: contactId,
  ParticipantDetails: {
    DisplayName: "AI Assistant",
    ParticipantRole: "CUSTOM_BOT",
  },
}));

// response.ParticipantId
// response.ParticipantCredentials.ParticipantToken
```

## Routing and Queue Behavior

- Chat contacts are routed through the same routing profiles and queues as voice
- Agents can handle multiple concurrent chats (configurable concurrency per routing profile)
- Default chat concurrency is typically 2-5 simultaneous chats (max 10)
- Chat does not block voice — agents can take a call while handling chats (if configured)
- Queue priority and routing logic apply identically to chat contacts

## Chat Timeouts and Lifecycle

| Timeout | Default | Configurable | Purpose |
|---------|---------|-------------|---------|
| Chat duration | Up to 7 days (including wait time) | Yes (via `ChatDurationInMinutes`) | Maximum lifetime of a chat session |
| Customer idle | 15 minutes | Yes (via contact flow) | Disconnect if customer stops responding |
| Agent idle | None | Custom via Lambda | Optional agent inactivity detection |
| After-contact work | Same as voice ACW | Yes | Time for agent to wrap up after chat ends |
| Lex bot timeout | 10 seconds | No | Max time for Lex to respond to customer prompt |

## Key Considerations

- **Encryption:** All chat messages encrypted in transit (TLS) and at rest
- **Transcripts:** Full chat transcripts stored in S3 (configure in instance settings)
- **Contact Lens:** Chat analytics available — sentiment, categorization, PII redaction
- **Lex integration:** Bots can handle initial interactions before agent handoff
- **Transfer:** Agents can transfer chats to other agents or queues (warm or cold)
- **Attachments:** Supported in chat — default 20 MB limit, configurable up to 100 MB, 35 attachments per conversation
- **Contact record retention:** 24 months from contact initiation for all chat subtypes (SMS, WhatsApp, Apple Messages)
- **Websocket connections:** Maximum 5 open websocket connections per chat participant
