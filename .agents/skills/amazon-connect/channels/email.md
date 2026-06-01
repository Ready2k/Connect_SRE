# Email Channel

Amazon Connect's email channel lets agents send and receive emails through the same CCP used for voice and chat. Built on Amazon SES for delivery, with full threading, templates, attachments, and Contact Lens analytics.

## Setup and Configuration

Email in Connect requires Amazon SES integration for sending and receiving.

**Domain setup:**
- Configure up to **5 custom domains** per Connect instance
- Domains must be verified in Amazon SES with DKIM + SPF records
- SES handles email delivery, bounce management, and reputation monitoring

**DKIM setup:**
1. Add your domain in the Connect console under email settings
2. Connect generates DKIM CNAME records (typically 3 records)
3. Add the CNAME records to your domain's DNS
4. Wait for DNS propagation and verification (can take up to 72 hours)
5. Once verified, the domain status changes to "Verified" in the console

**SPF setup:**
- Add an SPF TXT record to your domain's DNS: `v=spf1 include:amazonses.com ~all`
- This authorizes SES to send email on behalf of your domain
- Prevents your emails from being flagged as spam

**Custom MAIL FROM domain (optional):**
- Configure a custom MAIL FROM domain (e.g., `mail.example.com`) instead of the default SES domain
- Improves deliverability and brand consistency
- Requires an additional MX record and SPF record on the MAIL FROM subdomain

**Email addresses:**
- Create up to **100 email addresses** across your domains
- Common patterns: `support@example.com`, `sales@example.com`, `billing@example.com`
- Each address can be associated with a specific contact flow
- Multiple "from" addresses can be configured per queue — agents select which to send from
- Maximum email address length: **255 characters**
- Maximum display name length: **256 characters**

**Inbound routing:**
- Incoming emails hit SES, which triggers a Connect contact flow
- Contact flow applies routing logic (queue, priority, attributes)
- Email contacts land in agent queues alongside voice and chat

## Email Threading

Emails within the same conversation are threaded chronologically.

- Connect tracks threads via standard email headers (`In-Reply-To`, `References`)
- Agents see the full conversation history when handling a reply
- New emails from the same customer on the same subject are grouped into the thread
- Thread display is chronological — oldest at top, newest at bottom
- Agents can scroll through the entire conversation before responding
- Very long email threads may be truncated in the agent view for performance

## Agent Experience

**Rich text editor:**
- Agents compose replies using a full rich text editor in the CCP
- Formatting options: bold, italic, underline, bullet lists, numbered lists, hyperlinks
- HTML email output — customers receive properly formatted messages
- Default format: `text/html`; a `text/plain` version is also stored and available for flow blocks like "Get stored content"

**Templates:**
- Pre-built email templates for common responses
- Templates support dynamic variables (customer name, case ID, etc.)
- Admins create and manage templates in the Connect console
- Agents select a template and customize before sending
- Templates can include HTML formatting

**Signatures:**
- Configurable email signatures appended to outgoing messages
- Can be set per agent, per queue, or per routing profile
- Support HTML formatting (logo, links, disclaimers)

**Quick responses:**
- Pre-written snippets agents can insert into emails
- Different from templates — quick responses are partial content blocks, not full email bodies
- Useful for standard paragraphs, legal disclaimers, or common instructions

**Content protection:**
- Agents cannot manipulate or edit the customer's original content in replies
- Customer's message is quoted as-is in the reply thread
- Prevents accidental or intentional alteration of what the customer said

## Email Addresses — Recipients

**Per-email limits:**
- Up to **50 email addresses** total across To and CC per email message
- Inbound: any combination of 50 addresses across To and CC
- Outbound: only **1** address in To, up to **49** in CC
- Only **1** From address per email message
- **BCC is not supported** in Connect

**Maximum subject length:** 998 characters

## Auto-Responses

Configure automatic email replies for specific scenarios.

- Acknowledgment emails when a customer's email is received ("We got your message, a representative will respond within 24 hours")
- Out-of-hours auto-responses with expected response times
- Configured in contact flows using the "Send email" block or Lambda functions
- Auto-responses include thread headers so they appear in the correct conversation thread

## Forwarding

Agents can forward emails to external addresses.

- Forward to colleagues, escalation teams, or external partners
- Forwarded email preserves the original thread and attachments
- The forwarded recipient can reply back into the Connect thread
- Useful for cross-team collaboration on complex cases

## Multiple "From" Addresses per Queue

A single queue can have multiple outbound email addresses configured.

- Agents select the appropriate "from" address when composing or replying
- Example: a "General Support" queue might send from `support@example.com`, `help@example.com`, or `info@example.com`
- The default "from" address is set at the queue level
- Routing rules can set the "from" address automatically based on contact attributes

## File Attachments

Email supports file attachments for both inbound and outbound messages.

**Size limits:**
- Maximum email body size: **5 MB**
- Maximum email body + attachments combined: **25 MB**
- Maximum **10 attachments** per email message
- Default per-file limit: **20 MB** (configurable up to **100 MB** via admin website or API)

**Supported file types:**
`.csv`, `.doc`, `.docx`, `.heic`, `.jfif`, `.jpeg`, `.jpg`, `.mov`, `.mp4`, `.pdf`, `.png`, `.ppt`, `.pptx`, `.rtf`, `.txt`, `.wav`, `.xls`, `.xlsx`
- Administrators can add custom file extensions via the admin website or API

**Inline images:**
- No limit on count, as long as total inline image size does not exceed **5 MB**
- Supported formats: `image/jpg`, `image/jpeg`, `image/png`, `image/gif`, `image/svg`, `image/webp`, `image/bmp`, `image/heif`, `image/heic`
- All inline images are Base64 encoded when stored

**Storage:**
- Attachments are stored in the Connect-managed S3 bucket
- Retention defined by your S3 lifecycle configuration
- You must configure an S3 bucket and CORS policy for email attachments — without this, the email channel will not work even if "Enable Attachments sharing" is selected
- Virus scanning is recommended via S3 event triggers (not built into Connect)

**CORS policy for attachments bucket:**
```json
[
  {
    "AllowedMethods": ["PUT", "GET"],
    "AllowedOrigins": ["https://www.example.com"],
    "AllowedHeaders": ["*"]
  }
]
```

## Contact Lens for Email

Contact Lens analytics apply to email contacts just as they do to voice and chat.

**Capabilities:**
- **Categorization:** Automatically classify emails by topic, intent, or issue type using rules
- **PII redaction:** Detect and redact sensitive information (SSN, credit card numbers, addresses) in email content
- **Summaries:** AI-generated summaries of email threads — useful for long multi-reply conversations
- **Sentiment analysis:** Assess customer sentiment from email text
- **Evaluation:** Include email contacts in agent quality evaluations

**Configuration:**
- Enable Contact Lens for email in the "Set recording and analytics behavior" flow block
- Redaction rules apply to stored transcripts and analytics output
- Results available in the Connect analytics dashboard and via APIs
- Up to 15 rules with Natural Language condition for email analysis event source

## Email Contact Lifecycle and Expiry

**Active email contact expiry:**
- Default: **14 days**
- Customizable up to **90 days** using the "Set contact attributes" flow block or the Expiry API
- Determines how long an email contact can remain active (waiting in queue or assigned to an agent) before expiring and closing automatically

| Stage | Description |
|-------|-------------|
| Received | SES receives the email, triggers Connect contact flow |
| Queued | Contact flow routes to a queue based on rules |
| Assigned | Agent accepts the email from their queue |
| Composing | Agent reads thread, drafts reply using rich text editor |
| Sent | Reply sent via SES, threaded with the original conversation |
| ACW | Agent completes after-contact work (notes, disposition) |
| Closed | Contact record finalized, analytics processed |

## Email APIs

### CreateEmailAddress

Provision a new email address for your Connect instance.

```javascript
import { ConnectClient, CreateEmailAddressCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

const response = await client.send(new CreateEmailAddressCommand({
  InstanceId: instanceId,
  EmailAddress: "support@example.com",
  DisplayName: "Customer Support",
  Description: "Main support inbox",
}));
// response.EmailAddressId — unique identifier for this email address
// response.EmailAddressArn — ARN for IAM policies
```

### SearchEmailAddresses

Find email addresses configured in your instance.

```javascript
const response = await client.send(new SearchEmailAddressesCommand({
  InstanceId: instanceId,
  MaxResults: 25,
  SearchCriteria: {
    StringCondition: {
      FieldName: "emailAddress",
      Value: "support",
      ComparisonType: "CONTAINS",
    },
  },
}));
// response.EmailAddresses — array of matching email address objects
```

### SendOutboundEmail

Send an email from Connect without creating a full contact (e.g., notifications, receipts).

```javascript
const response = await client.send(new SendOutboundEmailCommand({
  InstanceId: instanceId,
  FromEmailAddress: {
    EmailAddressId: emailAddressId,
  },
  DestinationEmailAddress: {
    EmailAddressId: destinationEmailId,
    // or DisplayName + raw address
  },
  EmailMessage: {
    Subject: { Value: "Your order has shipped", Charset: "UTF-8" },
    Body: {
      Html: { Value: "<p>Your order #123 shipped today.</p>", Charset: "UTF-8" },
      Text: { Value: "Your order #123 shipped today.", Charset: "UTF-8" },
    },
  },
  // Optional: attach files via S3 references
}));
```

### StartEmailContact

Create a new inbound email contact that enters a contact flow.

```javascript
const response = await client.send(new StartEmailContactCommand({
  InstanceId: instanceId,
  ContactFlowId: contactFlowId,
  FromEmailAddress: {
    EmailAddress: "customer@example.com",
    DisplayName: "John Customer",
  },
  DestinationEmailAddress: "support@yourcompany.com",
  Name: "Email from John regarding billing",
  EmailMessage: {
    Subject: { Value: "Billing question", Charset: "UTF-8" },
    Body: {
      Text: { Value: "I have a question about my invoice.", Charset: "UTF-8" },
    },
  },
}));
// response.ContactId — the new contact's ID
```

### StartOutboundEmailContact

Proactively initiate an email contact that routes through a flow and assigns to an agent.

```javascript
const response = await client.send(new StartOutboundEmailContactCommand({
  InstanceId: instanceId,
  ContactFlowId: outboundFlowId,
  DestinationEmailAddress: {
    EmailAddress: "customer@example.com",
    DisplayName: "Jane Customer",
  },
  FromEmailAddress: {
    EmailAddressId: fromEmailAddressId,
  },
  EmailMessage: {
    Subject: { Value: "Follow-up on your recent case", Charset: "UTF-8" },
    Body: {
      Html: { Value: "<p>Hi Jane, following up on case #789...</p>", Charset: "UTF-8" },
    },
  },
}));
```

## Routing Behavior

- Email contacts enter queues and are routed via the same routing profiles as voice and chat
- Priority and delay settings apply — email can be lower priority than voice/chat
- Agents handle one email at a time by default (configurable concurrency)
- Email does not ring — it appears in the agent's queue and they accept it
- After-contact work (ACW) applies to email contacts

## Key Considerations

- **SES limits:** SES sending quotas apply — request increases for high-volume email operations
- **Bounce handling:** SES manages bounces and complaints; high bounce rates can affect your sending reputation
- **Encryption:** TLS in transit, S3 SSE at rest for stored emails and attachments
- **Compliance:** Email content can be redacted via Contact Lens for PCI/HIPAA compliance
- **Threading limits:** Very long email threads may be truncated in the agent view for performance
- **No BCC:** BCC is not supported in Connect — neither inbound visibility nor outbound sending
- **Spam filtering:** Inbound emails pass through SES spam/virus filtering before reaching Connect
- **Attachment requirement:** S3 bucket + CORS policy must be configured for email attachments — without this, the email channel will not function
- **Contact record retention:** 24 months from contact initiation
- **Message retention:** Defined by your S3 lifecycle configuration; downloadable via Connect's download feature
