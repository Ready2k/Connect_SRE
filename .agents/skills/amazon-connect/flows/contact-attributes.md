# Contact Attributes in Amazon Connect

Contact attributes are key-value pairs associated with a contact that carry data throughout the contact's lifecycle. They are the primary mechanism for passing information between flow blocks, Lambda functions, Lex bots, and the agent workspace.

## Attribute Types

### System Attributes

Automatically set by Amazon Connect. Read-only. Not all blocks support using system attributes (e.g., you cannot use a system attribute to store customer input).

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| AWS Region | `$.AwsRegion` | The AWS Region where the contact is handled (e.g., us-west-2, us-east-1). |
| Customer Number | `$.CustomerEndpoint.Address` | The customer's phone number (E.164 format), or email address for EMAIL channel. For outbound whisper, this is the number agents dialed. |
| Customer Display Name | `$.CustomerEndpoint.DisplayName` | The customer's name on the email they sent. |
| Customer Endpoint Type | `$.CustomerEndpoint.Type` | Type of customer endpoint. Valid value: `TELEPHONE_NUMBER`. |
| Customer ID | `$.CustomerId` | Customer identification number (e.g., from CRM). Used by Voice ID as `CustomerSpeakerId`. |
| System Number | `$.SystemEndpoint.Address` | The number the customer dialed (DID/TFN), or the email address the contact was sent to for EMAIL channel. |
| System Display Name | `$.SystemEndpoint.DisplayName` | The display name of the email address the customer sent to. |
| System Endpoint Type | `$.SystemEndpoint.Type` | Type of system endpoint. Valid value: `TELEPHONE_NUMBER`. |
| CC Email Address List | `$.AdditionalEmailRecipients.CcList` | Full list of CC'd email addresses on inbound email. |
| To Email Address List | `$.AdditionalEmailRecipients.ToList` | Full list of To email addresses on inbound email. |
| Customer Callback Number | Not applicable (no JSONPath) | Callback number (defaults to customer number). Set via `Set callback number` block. Not in contact records; copy to user-defined attribute to persist. |
| Stored Customer Input | `$.StoredCustomerInput` | Most recent input from `Store customer input` block. Not in contact records; copy to user-defined attribute to persist. |
| Queue Name | `$.Queue.Name` | Name of the queue the contact is assigned to. |
| Queue ARN | `$.Queue.ARN` | ARN of the queue. |
| Queue Outbound Caller ID | `$.Queue.OutboundCallerId.Address` | Outbound caller ID number defined for the queue. |
| Queue Outbound Caller ID Type | `$.Queue.OutboundCallerId.Type` | Type of outbound caller ID. Valid value: `TELEPHONE_NUMBER`. |
| Queue Outbound Number | (Available in outbound whisper flows only) | Outbound caller ID number for the selected queue. |
| Text to Speech Voice | `$.TextToSpeechVoiceId` | Current Amazon Polly voice ID. |
| Contact ID | `$.ContactId` | Unique identifier for the current contact. |
| Initial Contact ID | `$.InitialContactId` | ID of the original contact in a transfer chain. Same as ContactId for initial contacts. |
| Previous Contact ID | `$.PreviousContactId` | ID of the previous contact in a transfer chain. |
| Task Contact ID | `$.Task.ContactId` | Unique identifier for the task contact. |
| Channel | `$.Channel` | `VOICE`, `CHAT`, `TASK`, or `EMAIL`. |
| Instance ARN | `$.InstanceARN` | ARN of the Connect instance. |
| Initiation Method | `$.InitiationMethod` | How the contact was initiated: `INBOUND`, `OUTBOUND`, `TRANSFER`, `CALLBACK`, `QUEUE_TRANSFER`, `EXTERNAL_OUTBOUND`, `MONITOR`, `DISCONNECT`, `WEBRTC_API`, `API`. |
| Language Code | `$.LanguageCode` | Language/locale code (standard java.util.Locale, e.g., `en-US`, `ja-JP`). |
| Name | `$.Name` | The name of the task. |
| Description | `$.Description` | Description of the task. |
| References | `$.References.{ReferenceKey}.Value` and `$.References.{ReferenceKey}.Type` | Links to other documents related to a contact. |
| Tags | `$.Tags` | Tags used to organize, track, or control access. |

### Segment Attributes

System-defined key-value pairs stored on individual contact segments. User-defined segment attributes can also be created.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| connect:Subtype | `$.SegmentAttributes['connect:Subtype']` | Subtype of the channel used for the contact. |
| connect:Direction | `$.SegmentAttributes['connect:Direction']` | Direction of the contact (e.g., inbound or outbound). |
| connect:BlockReasonHeader | `$.SegmentAttributes['connect:BlockReasonHeader']` | Access to 603+ Network Blocked information (SIP redress header). |
| connect:CreatedByUser | `$.SegmentAttributes['connect:CreatedByUser']` | ARN of the user who created the task. |
| connect:AssignmentType | `$.SegmentAttributes['connect:AssignmentType']` | How a task is assigned (e.g., `SELF`). |
| connect:EmailSubject | `$.SegmentAttributes['connect:EmailSubject']` | Subject of an email contact. |
| connect:ScreenSharingDetails | `$.SegmentAttributes['connect:ScreenSharingDetails']` | Screen sharing activity info. Contains `ScreensharingActivated` (`TRUE`/`FALSE`). |
| connect:ContactExpiry | `$.SegmentAttributes['connect:ContactExpiry']` | Contact expiry details (`ExpiryDuration`, `ExpiryTimeStamp`) for Task and Email contacts. Type: valueMap. |
| connect:CustomerAuthentication | `$.SegmentAttributes['connect:CustomerAuthentication']` | Chat contact authentication details (IdentityProvider, ClientId, Status, AssociatedCustomerId, AuthenticationMethod). Type: ValueMap. |
| connect:ValidationTestType | `$.Segment.Attributes['connect:ValidationTestType']` | Testing/simulation type. Empty for non-simulated contacts. Value: `EXPERIENCE_VALIDATION`. |
| Client ID | `$.SegmentAttributes['connect:CustomerAuthentication']['ClientId']` | Amazon Cognito app client identifier. |
| Identity Provider | `$.SegmentAttributes['connect:CustomerAuthentication']['IdentityProvider']` | Identity provider used to authenticate. |
| Authentication Status | `$.SegmentAttributes['connect:CustomerAuthentication']['Status']` | `AUTHENTICATED`, `FAILED`, or `TIMEOUT`. |
| Associated Customer ID | `$.SegmentAttributes['connect:CustomerAuthentication']['AssociatedCustomerId']` | Customer identifier (custom or Customer Profile ID). |
| Authentication Method | `$.SegmentAttributes['connect:CustomerAuthentication']['AuthenticationMethod']` | `CONNECT` or `CUSTOM`. |
| Email Subject (segment) | `$.SegmentAttributes['connect:EmailSubject']` | Email subject for keyword inspection. |
| Amazon SES Spam Verdict | `$.SegmentAttributes['connect:X-SES-SPAM-VERDICT']` | SES spam scan result. Check for `FAILED` to route suspicious emails. |
| Amazon SES Virus Verdict | `$.SegmentAttributes['connect:X-SES-VIRUS-VERDICT']` | SES virus scan result. Check for `FAILED` to route suspicious emails. |
| User-defined segment attributes | `$.SegmentAttributes['Attribute_key_name']` | Custom segment attributes. Must be predefined. Optionally enforce valid values. |

### Views Attributes

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Action | `$.Views.Action` | Action taken by the user interacting with the view. Appears as flow branches from the `Show view` block. |
| View Result Data | `$.Views.ViewResultData` | Output data from the user's interaction with the view. |

### Capabilities Attributes

Support screen and video sharing capabilities.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Agent Screen Share | `$.Capabilities.Agent.ScreenShare` | Screen sharing capability enabled for the agent. |
| Agent Video | `$.Capabilities.Agent.Video` | Video sharing capability enabled for the agent. |
| Customer Screen Share | `$.Capabilities.Customer.ScreenShare` | Screen sharing capability enabled for the customer. |
| Customer Video | `$.Capabilities.Customer.Video` | Video sharing capability enabled for the customer. |

### Agent Attributes

Available only in agent whisper, customer whisper, agent hold, customer hold, outbound whisper, and transfer to agent flows. NOT available in customer queue, transfer to queue, or inbound flows.

In a Transfer to agent flow, agent attributes reflect the **target** agent, not the one who initiated the transfer.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Agent User Name | `$.Agent.UserName` | The username the agent uses to log in. |
| Agent First Name | `$.Agent.FirstName` | Agent's first name from their user account. |
| Agent Last Name | `$.Agent.LastName` | Agent's last name from their user account. |
| Agent ARN | `$.Agent.ARN` | ARN of the agent. |

### Queue Metrics Attributes

Returned by the `Get metrics` block. Returns null if no current activity.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Queue Name | `$.Metrics.Queue.Name` | Queue name for the metrics. |
| Queue ARN | `$.Metrics.Queue.ARN` | Queue ARN for the metrics. |
| Contacts in Queue | `$.Metrics.Queue.Size` | Number of contacts currently in the queue. |
| Oldest Contact Age | `$.Metrics.Queue.OldestContactAge` | Age (seconds) of the oldest contact in queue. |
| Estimated Wait Time (Queue) | `$.Metrics.Queue.EstimatedWaitTime` | Estimated wait time in seconds for the queue. |
| Agents Online | `$.Metrics.Agents.Online.Count` | Agents logged in and in any state other than offline. |
| Agents Available | `$.Metrics.Agents.Available.Count` | Agents whose state is set to Available. |
| Agents Staffed | `$.Metrics.Agents.Staffed.Count` | Agents in Available, ACW, or Busy states. |
| Agents in ACW | `$.Metrics.Agents.AfterContactWork.Count` | Agents currently in After Contact Work state. |
| Agents Busy | `$.Metrics.Agents.Busy.Count` | Agents currently active on a contact. |
| Agents Missed | `$.Metrics.Agents.Missed.Count` | Agents in Missed state (entered after a missed contact). |
| Agents Non-Productive | `$.Metrics.Agents.NonProductive.Count` | Agents in a non-productive (NPT) state. |

### Contact Metrics Attributes

Returned by the `Get metrics` block. Contact-level metrics.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Estimated Wait Time (Contact) | `$.Metrics.Contact.EstimatedWaitTime` | Estimated wait time in seconds for the current contact. |
| Position in Queue | `$.Metrics.Contact.PositionInQueue` | Contact's position in queue, accounting for channel and routing step. |

### Telephony Call Metadata Attributes

Additional information from telephony carriers. Availability varies by carrier and may result in empty values.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| P-Charge-Info | `$.Media.Sip.Headers.P-Charge-Info` | Party responsible for charges. |
| From | `$.Media.Sip.Headers.From` | Identity of the end user. |
| To | `$.Media.Sip.Headers.To` | Information about the called party. |
| ISUP-OLI | `$.Media.Sip.Headers.ISUP-OLI` | Originating Line Indicator (line type: PSTN, 800, wireless, payphone). |
| JIP | `$.Media.Sip.Headers.JIP` | Jurisdiction Indication Parameter (geographic location of caller/switch). |
| Hop-Counter | `$.Media.Sip.Headers.Hop-Counter` | Hop counter value. |
| Originating-Switch | `$.Media.Sip.Headers.Originating-Switch` | Originating switch identifier. |
| Originating-Trunk | `$.Media.Sip.Headers.Originating-Trunk` | Originating trunk identifier. |
| Call-Forwarding-Indicator | `$.Media.Sip.Headers.Call-Forwarding-Indicator` | Call forwarding / diversion header. Indicates domestic or international origin. |
| Calling-Party-Address | `$.Media.Sip.Headers.Calling-Party-Address` | Calling party number. NPAC dip shows true line type and native geographic switch. |
| Called-Party-Address | `$.Media.Sip.Headers.Called-Party-Address` | Called party number. |
| SIPREC Metadata | `$.Media.Sip.SiprecMetadata` | SIPREC metadata XML received by Contact Lens connector. |

### Chat Initial Message Attributes

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Initial Message | `$.Media.InitialMessage` | Initial message supplied by the customer on web chat or SMS. |

### Email Attributes

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Email Message (Plain text) | `$.Email.EmailMessage.Plaintext` | Plain text version of the email message (via `Get stored content` block). |

### User-Defined (Contact) Attributes

Custom key-value pairs you define. Set by the `Set contact attributes` block or via Lambda.

| JSONPath | Description |
|----------|-------------|
| `$.Attributes.{key}` | Any user-defined attribute. Key is the attribute name you chose. |

Examples:
- `$.Attributes.customerName`
- `$.Attributes.accountId`
- `$.Attributes.callerIntent`

### Flow Attributes

Temporary variables stored locally, restricted to the flow where they are set.

| JSONPath | Description |
|----------|-------------|
| `$.FlowAttributes.{key}` | Flow-scoped attribute. |

Key properties:
- Not visible outside the flow, not even when transferred to another flow.
- Can be up to 32 KB (maximum size of contact record attributes section).
- Not passed to Lambda unless explicitly configured as parameters in the `Invoke AWS Lambda function` block.
- Not passed to or out of modules.
- Do not appear in contact records or the CCP.
- Not accessible via `GetContactAttributes` API.
- Key and value appear in CloudWatch logs if flow logging is enabled.

### External (Lambda) Attributes

Returned by the most recent Lambda function invocation. Overwritten each time a new Lambda is invoked.

| JSONPath | Description |
|----------|-------------|
| `$.External.{key}` | A key from the Lambda response. |

Also accessible as: `$.LambdaInvocation.ResultData.{attributeName}`

Examples:
- `$.External.customerTier`
- `$.External.balance`
- `$.External.address.city` (nested JSON response)

External attributes are ephemeral. If you need them later in the flow (especially after another Lambda call), copy them to user-defined attributes using `Set contact attributes`.

Not included in contact records, not passed to the next Lambda invocation, not passed to the CCP for screenpop. Can be copied to user-defined attributes via `Set contact attributes` block.

### Amazon Lex Attributes

Set by Amazon Lex during a `Get customer input` interaction.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Intent Name | `$.Lex.IntentName` | The resolved intent name. |
| Intent Confidence Score | `$.Lex.IntentConfidence.Score` | Confidence score of the matched intent. |
| Slots | `$.Lex.Slots.{slotName}` | Value of a Lex slot. |
| Session Attributes | `$.Lex.SessionAttributes.{key}` | Lex session attributes (key-value map). |
| Sentiment Label | `$.Lex.SentimentResponse.Label` | Sentiment label from Amazon Comprehend (highest confidence). |
| Sentiment Scores | `$.Lex.SentimentResponse.Scores.Positive` / `.Negative` / `.Mixed` / `.Neutral` | Likelihood for each sentiment. |
| Dialog State | `$.Lex.DialogState` | Last dialog state from Lex. Value is `Fulfilled` if an intent was returned. |
| Alternate Intents | `$.Lex.AlternativeIntents.{x}.IntentName` / `.IntentConfidence.Score` / `.Slots` | List of alternate intents with confidence scores and slots. |

### Case Attributes

Used with Amazon Connect Cases.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Case ID | `$.Case.case_id` | Unique identifier (UUID format). |
| Case Reason | `$.Case.case_reason` | Reason for opening the case. |
| Created By | `$.Case.created_by` | Identity of the user who created the case. |
| Customer | `$.Case.customer_id` | Customer profile ID. |
| Date/Time Closed | `$.Case.last_closed_datetime` | Last time status was changed to closed. |
| Date/Time Opened | `$.Case.created_datetime` | When the case was opened. |
| Date/Time Updated | `$.Case.last_updated_datetime` | When the case was last updated. |
| Reference Number | `$.Case.reference_number` | 8-digit numeric reference (not guaranteed unique). |
| Status | `$.Case.status` | Current case status. |
| Summary | `$.Case.summary` | Summary of the case. |
| Title | `$.Case.title` | Title of the case. |

### Media Streams Attributes

Available when media streaming is active (after `Start media streaming` block).

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Customer Audio Stream ARN | `$.MediaStreams.Customer.Audio.StreamARN` | ARN of the Kinesis Video Stream for customer audio. |
| Customer Audio Start Timestamp | `$.MediaStreams.Customer.Audio.StartTimestamp` | When the customer audio stream started. |
| Customer Audio Stop Timestamp | `$.MediaStreams.Customer.Audio.StopTimestamp` | When the customer audio stream stopped. |
| Customer Audio Start Fragment Number | `$.MediaStreams.Customer.Audio.StartFragmentNumber` | Fragment number where streaming began. |

### Customer Profiles Attributes

Used with Amazon Connect Customer Profiles. Total size limited to 14,000 characters (56 attributes at max 255 each) for the entire flow.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Profile ID | `$.Customer.ProfileId` | Unique identifier of a customer profile. |
| Profile ARN | `$.Customer.ProfileARN` | ARN of a customer profile. |
| First Name | `$.Customer.FirstName` | Customer's first name. |
| Middle Name | `$.Customer.MiddleName` | Customer's middle name. |
| Last Name | `$.Customer.LastName` | Customer's last name. |
| Account Number | `$.Customer.AccountNumber` | Unique account number. |
| Email Address | `$.Customer.EmailAddress` | Customer's email (general). |
| Phone Number | `$.Customer.PhoneNumber` | Customer's phone (general). |
| Additional Information | `$.Customer.AdditionalInformation` | Additional profile info. |
| Party Type | `$.Customer.PartyType` | Customer's party type. |
| Business Name | `$.Customer.BusinessName` | Name of customer's business. |
| Birth Date | `$.Customer.BirthDate` | Customer's birth date. |
| Gender | `$.Customer.Gender` | Customer's gender. |
| Mobile Phone Number | `$.Customer.MobilePhoneNumber` | Mobile phone number. |
| Home Phone Number | `$.Customer.HomePhoneNumber` | Home phone number. |
| Business Phone Number | `$.Customer.BusinessPhoneNumber` | Business phone number. |
| Business Email Address | `$.Customer.BusinessEmailAddress` | Business email. |
| Address | `$.Customer.Address1` through `$.Customer.Address4`, `$.Customer.City`, `$.Customer.County`, `$.Customer.Country`, `$.Customer.PostalCode`, `$.Customer.Province`, `$.Customer.State` | Generic address fields. |
| Shipping Address | `$.Customer.ShippingAddress1` through `$.Customer.ShippingAddress4`, `$.Customer.ShippingCity`, `$.Customer.ShippingCounty`, `$.Customer.ShippingCountry`, `$.Customer.ShippingPostalCode`, `$.Customer.ShippingProvince`, `$.Customer.ShippingState` | Shipping address fields. |
| Mailing Address | `$.Customer.MailingAddress1` through `$.Customer.MailingAddress4`, `$.Customer.MailingCity`, `$.Customer.MailingCounty`, `$.Customer.MailingCountry`, `$.Customer.MailingPostalCode`, `$.Customer.MailingProvince`, `$.Customer.MailingState` | Mailing address fields. |
| Billing Address | `$.Customer.BillingAddress1` through `$.Customer.BillingAddress4`, `$.Customer.BillingCity`, `$.Customer.BillingCounty`, `$.Customer.BillingCountry`, `$.Customer.BillingPostalCode`, `$.Customer.BillingProvince`, `$.Customer.BillingState` | Billing address fields. |
| Custom Attributes | `$.Customer.Attributes.{key}` | Key-value pair of custom profile attributes. |
| Object Attributes | `$.Customer.ObjectAttributes.{key}` | Key-value pair of custom object attributes. |
| Calculated Attributes | `$.Customer.CalculatedAttributes.{key}` | Key-value pair of calculated attributes. |
| Asset | `$.Customer.Asset.AssetId`, `.ProfileId`, `.AssetName`, `.SerialNumber`, `.ModelNumber`, `.ModelName`, `.ProductSKU`, `.PurchaseDate`, `.UsageEndDate`, `.Status`, `.Price`, `.Quantity`, `.Description`, `.AdditionalInformation`, `.DataSource`, `.Attributes.{key}` | Standard Asset object fields. |
| Order | `$.Customer.Order.OrderId`, `.ProfileId`, `.CustomerEmail`, `.CustomerPhone`, `.CreatedDate`, `.UpdatedDate`, `.ProcessedDate`, `.ClosedDate`, `.CancelledDate`, `.CancelReason`, `.Name`, `.AdditionalInformation`, `.Gateway`, `.Status`, `.StatusCode`, `.StatusUrl`, `.CreditCardNumber`, `.CreditCardCompany`, `.FulfillmentStatus`, `.TotalPrice`, `.TotalTax`, `.TotalDiscounts`, `.TotalItemsPrice`, `.TotalShippingPrice`, `.TotalTipReceived`, `.Currency`, `.TotalWeight`, `.BillingName`, `.BillingAddress1-4`, `.BillingCity`, `.BillingCounty`, `.BillingCountry`, `.BillingPostalCode`, `.BillingProvince`, `.BillingState`, `.ShippingName`, `.ShippingAddress1-4`, `.ShippingCity`, `.ShippingCounty`, `.ShippingCountry`, `.ShippingPostalCode`, `.ShippingProvince`, `.ShippingState`, `.Attributes.{key}` | Standard Order object fields. |
| Case (Profile) | `$.Customer.Case.CaseId`, `.ProfileId`, `.Title`, `.Summary`, `.Status`, `.Reason`, `.CreatedBy`, `.CreatedDate`, `.UpdatedDate`, `.ClosedDate`, `.AdditionalInformation`, `.DataSource`, `.Attributes.{key}` | Standard Case object fields. |

### Loop Attributes

Available with the Loop block when a LoopName is specified.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Index | `$.Loop.{loop_name}.Index` | Current index (starts from 0). Available with both Count and Array loops. |
| Element | `$.Loop.{loop_name}.Element` | Current element. Array-based loop only. |
| Elements | `$.Loop.{loop_name}.Elements` | Input elements. Array-based loop only. |

### Flow Modules Attributes

Input attributes are passed into a module. Output and Result attributes are returned from the most recent `Invoke Module` block. Overwritten with each module invocation.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Input | `$.Modules.Input` | Input data passed into the module (JSON object defined by module input schema). |
| Result | `$.Modules.Result` | Branch name returned from the module (excluding error branch). String. |
| Output | `$.Modules.ResultData` | Result data generated from module execution (JSON object defined by module output schema). |

Not included in contact records, not passed to subsequent module invocations, not available in CCP.

### Data Table Attributes

Returned by Data Table block operations.

#### Evaluate Data Table Values

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Query Result | `$.DataTables.{QueryName}.{AttributeName}` | Value of a specific attribute from a named query. |

#### List Data Table Values

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Data Table ID | `$.DataTableList.ResultData.dataTableId` | Unique identifier of the data table. |
| Lock Version | `$.DataTableList.ResultData.lockVersion.dataTable` | Lock version information. |
| Default Group | `$.DataTableList.ResultData.primaryKeyGroups.default[index]` | Records when no primary key group is configured. |
| Primary Key Groups | `$.DataTableList.ResultData.primaryKeyGroups.{GroupName}` | Records organized by primary value group name. |
| Specific Row | `$.DataTableList.ResultData.primaryKeyGroups.{GroupName}[index]` | Access a specific row (zero-based index). |
| Primary Key Value | `$.DataTableList.ResultData.primaryKeyGroups.{GroupName}[index].primaryKeys[index].attributeValue` | Primary key value in a specific row. |
| Attribute Value | `$.DataTableList.ResultData.primaryKeyGroups.{GroupName}[index].attributes[index].attributeValue` | Non-primary attribute value in a specific row. |

Maximum data limit for List namespace: 32 KB. Use backticks to wrap JSONPath references when accessing array elements in flow blocks.

### Apple Messages for Business Attributes

User-defined attributes for routing Apple Messages for Business customers.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| MessagingPlatform | `$.Attributes.MessagingPlatform` | Platform of origin. Value: `AppleBusinessChat`. |
| AppleBusinessChatCustomerId | `$.Attributes.AppleBusinessChatCustomerId` | Customer's opaque ID from Apple. Constant per AppleID + business. |
| AppleBusinessChatIntent | `$.Attributes.AppleBusinessChatIntent` | Intent/purpose of the chat. |
| AppleBusinessChatGroup | `$.Attributes.AppleBusinessChatGroup` | Department/group for routing. |
| AppleBusinessChatLocale | `$.Attributes.AppleBusinessChatLocale` | Language + region (e.g., `en_US`). |
| AppleFormCapability | `$.Attributes.AppleFormCapability` | Whether device supports forms (`true`/`false`). |
| AppleAuthenticationCapability | `$.Attributes.AppleAuthenticationCapability` | Whether device supports OAuth2 (`true`/`false`). |
| AppleTimePickerCapability | `$.Attributes.AppleTimePickerCapability` | Whether device supports time pickers (`true`/`false`). |
| AppleListPickerCapability | `$.Attributes.AppleListPickerCapability` | Whether device supports list pickers (`true`/`false`). |
| AppleQuickReplyCapability | `$.Attributes.AppleQuickReplyCapability` | Whether device supports quick replies (`true`/`false`). |

### Outbound Campaign Attributes

Data from Amazon Pinpoint segments. Reference via `$.Attributes.{attribute_from_segment}`.

Examples:
- `$.Attributes.FirstName`
- `$.Attributes.ItemDescription`

### Connect AI Agents Attribute

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| SessionArn | `$.Wisdom.SessionArn` | ARN of a Connect AI agents session. Pass to Lambda for API actions like `UpdateSession`. |

## How to Set Contact Attributes

### In the Flow Designer

Use the **Set contact attributes** block:

1. Add the block to your flow.
2. Configure the attribute:
   - **Namespace**: User defined, External, System, etc.
   - **Destination key**: The attribute name (e.g., `callerIntent`).
   - **Value**: Can be:
     - **Set manually**: A static string value.
     - **Set dynamically**: A reference to another attribute using JSONPath (e.g., `$.External.tier`).

### From Lambda

Return attributes from Lambda, then use `Set contact attributes` to save them:

```javascript
// Lambda returns:
return {
  customerName: "Jane Doe",
  accountId: "ACC-12345"
};
```

In the flow after the Lambda block, add `Set contact attributes`:
- Source type: External
- Source attribute: `customerName`
- Destination key: `customerName`

Alternatively, update contact attributes directly via the `UpdateContactAttributes` API in Lambda:

```javascript
const { ConnectClient, UpdateContactAttributesCommand } = require("@aws-sdk/client-connect");

const client = new ConnectClient({});

exports.handler = async (event) => {
  const { ContactId, InstanceARN } = event.Details.ContactData;
  const instanceId = InstanceARN.split("/").pop();

  await client.send(new UpdateContactAttributesCommand({
    InstanceId: instanceId,
    InitialContactId: ContactId,
    Attributes: {
      customerName: "Jane Doe",
      accountId: "ACC-12345"
    }
  }));

  return { status: "ok" };
};
```

## How to Reference Contact Attributes

### In Play Prompt (TTS)

Use JSONPath directly in the text:

```
Hello, $.Attributes.customerName. Your account number is $.Attributes.accountId.
```

The flow engine substitutes the attribute values at runtime.

### In Check Contact Attributes (Branching)

1. Add the `Check contact attributes` block.
2. Set the **Attribute to check**: Use the JSONPath (e.g., `$.Attributes.callerIntent`).
3. Add conditions:
   - Equals `billing` -> route to billing queue
   - Equals `support` -> route to support queue
   - No match -> default branch

### In Lambda Parameters

In the `Invoke AWS Lambda function` block, add function input parameters:
- Key: `accountId`
- Value: `$.Attributes.accountId`

These appear in `event.Details.Parameters.accountId` in the Lambda function.

### In Lex Session Attributes

Pass contact attributes to Lex as session attributes in the `Get customer input` block:
- Source: `$.Attributes.customerName`
- Lex session attribute key: `customerName`

## JSONPath Syntax Reference

Amazon Connect uses a subset of JSONPath for attribute references:

| Syntax | Meaning |
|--------|---------|
| `$.Attributes.{key}` | User-defined contact attribute |
| `$.FlowAttributes.{key}` | Flow-scoped attribute (not persisted) |
| `$.External.{key}` | Lambda response attribute |
| `$.LambdaInvocation.ResultData.{key}` | Lambda response (alternative syntax) |
| `$.Lex.IntentName` | Lex intent name |
| `$.Lex.Slots.{slotName}` | Lex slot value |
| `$.Lex.SessionAttributes.{key}` | Lex session attribute |
| `$.Lex.IntentConfidence.Score` | Lex intent confidence |
| `$.Lex.SentimentResponse.Label` | Lex sentiment label |
| `$.Lex.AlternativeIntents.{x}.IntentName` | Alternative intent name |
| `$.Queue.Name` | Current queue name |
| `$.Queue.ARN` | Current queue ARN |
| `$.SystemEndpoint.Address` | System endpoint (dialed number) |
| `$.CustomerEndpoint.Address` | Customer endpoint (caller number) |
| `$.Channel` | Contact channel |
| `$.ContactId` | Contact ID |
| `$.InitialContactId` | Initial contact ID |
| `$.PreviousContactId` | Previous contact ID |
| `$.InstanceARN` | Instance ARN |
| `$.InitiationMethod` | Initiation method |
| `$.LanguageCode` | Language code |
| `$.AwsRegion` | AWS Region |
| `$.Metrics.Queue.Size` | Queue size metric |
| `$.Metrics.Queue.OldestContactAge` | Oldest contact age |
| `$.Metrics.Queue.EstimatedWaitTime` | Queue estimated wait time |
| `$.Metrics.Agents.Available.Count` | Available agents count |
| `$.Metrics.Contact.EstimatedWaitTime` | Contact estimated wait time |
| `$.Metrics.Contact.PositionInQueue` | Contact position in queue |
| `$.MediaStreams.Customer.Audio.StreamARN` | Media stream ARN |
| `$.MediaStreams.Customer.Audio.StartTimestamp` | Media stream start timestamp |
| `$.MediaStreams.Customer.Audio.StopTimestamp` | Media stream stop timestamp |
| `$.MediaStreams.Customer.Audio.StartFragmentNumber` | Media stream start fragment |
| `$.Agent.UserName` | Agent username |
| `$.Agent.FirstName` | Agent first name |
| `$.Agent.LastName` | Agent last name |
| `$.Agent.ARN` | Agent ARN |
| `$.Customer.ProfileId` | Customer profile ID |
| `$.Customer.FirstName` | Customer first name |
| `$.Customer.LastName` | Customer last name |
| `$.Case.case_id` | Case ID |
| `$.Case.status` | Case status |
| `$.SegmentAttributes['connect:Subtype']` | Segment subtype |
| `$.SegmentAttributes['connect:Direction']` | Segment direction |
| `$.Views.Action` | View action |
| `$.Views.ViewResultData` | View result data |
| `$.Loop.{name}.Index` | Loop index |
| `$.Modules.Input` | Module input |
| `$.Modules.Result` | Module result |
| `$.Modules.ResultData` | Module output |
| `$.DataTables.{QueryName}.{AttributeName}` | Data table query result |
| `$.Wisdom.SessionArn` | AI agents session ARN |
| `$.Media.Sip.Headers.{header}` | SIP telephony metadata |
| `$.Media.InitialMessage` | Chat initial message |
| `$.Email.EmailMessage.Plaintext` | Email plain text |

## Attribute Limits

| Limit | Value |
|-------|-------|
| Maximum number of user-defined attributes per contact | 200 |
| Maximum attribute key length | 256 characters |
| Maximum attribute value length | 32,768 characters |
| Maximum total attributes size | 32 KB |
| Attribute key allowed characters | Alphanumeric, hyphens, periods, underscores |
| Maximum Customer Profiles attributes per flow | 14,000 characters (56 attributes at 255 chars each) |
| Maximum Data Table List namespace size | 32 KB |
| Maximum flow attributes size | 32 KB |
| Maximum Lambda response size | 32 KB |

## Best Practices

- **Copy External to Contact attributes** immediately after Lambda invocation if you need the values later. External attributes are overwritten by the next Lambda call.
- **Use Flow attributes** for sensitive data (credit card numbers) that should not persist in contact records or be visible in the CCP.
- **Use meaningful attribute names**: `customerTier` not `ct`, `accountStatus` not `as`.
- **Keep attribute values small**: The 32 KB total limit is shared across all attributes on the contact.
- **Do not store sensitive data in attributes** unless encrypted. Contact attributes appear in contact records, CloudWatch Logs (if flow logging is enabled), and the agent workspace.
- **Use contact tags** (via `Contact tags` block) for categorization and search; use attributes for data that drives flow logic.
- **Referencing arrays** is not supported directly in flow blocks. Arrays can only be used in Lambda functions.
