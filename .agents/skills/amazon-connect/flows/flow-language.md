# Amazon Connect Flow Language — Complete Reference

Source: https://docs.aws.amazon.com/connect/latest/devguide/flow-language.html

---

# Part 1: Concepts & Structure

## Connect Customer Flow Language

The Flow language is a JSON-based representation of a series of flow actions, and the criteria for moving between them.

Uses:
- Efficiently update flows migrating from one instance to another
- Write flows rather than drag blocks onto the flow designer

---

## Concepts

### Contact

Flows can be run in context of a contact. In this case, they are referred to as *flows*.

### Participant

Flows can additionally be run in a participant context. This allows participant actions — such as playing prompts or getting customer input — to be run. Certain types of flows, such as "No participants remaining" disconnect flows and Workitem flows, don't have a participant associated.

### Action Types

Flow actions have the following implicit types:

1. **Contact actions** — Attempted only when the flow is run in context of a contact. They generally result in contact data being manipulated.
2. **Flow control actions** — Used only to determine the path through a flow. No side effects. Generally work in every circumstance.
3. **Interactions** — Have side effects, but don't require a contact or a participant (e.g., invoking Lambda). Generally work in every circumstance.
4. **Participant actions** — Attempted only when the flow is run in context of a participant. Result in an action the participant experiences (playing a prompt, disconnecting).

---

## Example Flow

```json
{
    "Version": "2019-10-30",
    "StartAction": "12345678-1234-1234-1234-123456789012",
    "Metadata": {
        "EntryPointPosition": { "x": 88, "y": 100 },
        "ActionMetadata": {
            "12345678-1234-1234-1234-123456789012": {
                "Position": { "x": 270, "y": 98 }
            },
            "abcdef-abcd-abcd-abcd-abcdefghijkl": {
                "Position": { "x": 545, "y": 92 }
            }
        }
    },
    "Actions": [
        {
            "Identifier": "12345678-1234-1234-1234-123456789012",
            "Type": "MessageParticipant",
            "Transitions": {
                "NextAction": "abcdef-abcd-abcd-abcd-abcdefghijkl",
                "Errors": [],
                "Conditions": []
            },
            "Parameters": {
                "Text": "Thanks for calling the sample flow!"
            }
        },
        {
            "Identifier": "abcdef-abcd-abcd-abcd-abcdefghijkl",
            "Type": "DisconnectParticipant",
            "Transitions": {},
            "Parameters": {}
        }
    ]
}
```

**Key fields:**
- `Version`: Currently only `"2019-10-30"` is supported
- `StartAction`: Identifier of the first Action to run
- `Metadata`: Object that may be filled in with data as desired (positions, etc.)
- `Actions`: List of Action objects. A single flow may have no more than 250 Actions

---

## Actions — Structure

### Identifier

A string unique among all Actions within the same Flow. Up to 50 characters, can include any characters (including unicode and spaces).

**Disallowed characters:** `% : ( \ / ) = $ , ; [ ] { }`

**Disallowed strings:** `__proto__`, `constructor`, `__defineGetter__`, `__defineSetter__`, `toString`, `hasOwnProperty`, `isPrototypeOf`, `propertyIsEnumerable`, `toLocaleString`, `valueOf`

### Type

A string identifying the type of action (e.g., `MessageParticipant`, `DisconnectParticipant`, `UpdateContactAttributes`).

### Parameters

An object defining the customizable behavior of an Action block. Format differs per Action type.

### Transitions

An object defining the behavior for choosing the next Action after the current Action completes.

**Fields:**

- **NextAction**: Identifier of the Action to run if no error or condition is preferentially chosen
- **Errors**: List of error objects, each with `ErrorType` (string) and `NextAction` (identifier)
- **Conditions**: Ordered list of condition checks evaluated against the Action's result. First true Condition wins.

Each Condition object:
- `NextAction`: Identifier of Action to run if this Condition evaluates to true
- `Condition`: Object with `Operator` and `Operands`

### The Condition Object

- **Operator**: String indicating which comparison operator to apply
- **Operands**: List of operands. May be strings or nested Condition objects depending on Operator
- Nesting limit: 5 levels deep, max 50 sub-Conditions total

### List of Operators

| Operator | Description | Operand Type | Count |
|---|---|---|---|
| Equals | True if string exactly equals result | String | One |
| TextStartsWith | True if result begins with specified string | String | One |
| TextEndsWith | True if result ends with specified string | String | One |
| TextContains | True if result contains the string at least once | String | One |
| NumberGreaterThan | True if result > specified value (numeric) | String | One |
| NumberGreaterOrEqualTo | True if result >= specified value (numeric) | String | One |
| NumberLessThan | True if result < specified value (numeric) | String | One |
| NumberLessOrEqualTo | True if result <= specified value (numeric) | String | One |

**Example Condition** (returns true if result starts with "ABC"):
```json
{
    "Operator": "TextStartsWith",
    "Operands": ["ABC"]
}
```

---

## Parameter Restrictions

- **Must be defined statically**: JSONPath cannot be used at all
- **Must be defined statically or as a single valid JSONPath identifier**: If JSONPath is used, it must be the entire value (no `"My name is $.Name"`). JSONPath must be valid (e.g., `$.Attributes.stuff` is valid, `$.BadValue` is not)
- **May be defined statically or dynamically**: Anything goes. `"My name is $.Name"` is fine

---

# Part 2: Contact Actions (27 actions)

---

## CompleteOutboundCall

**Type:** `CompleteOutboundCall`

**Description:** When a flow is run before an outbound call is made, this action calls the outbound destination. If not used, the first participant action implicitly completes the outbound call.

**Parameters:**
```
"CallerId": { Optional, override caller ID. Ignored when using VoiceConnectors
    "Number": Caller ID number. Static or single valid JSONPath.
}
"VoiceConnector": { Optional
    "VoiceConnectorType": Only "ChimeConnector". Static only.
    "VoiceConnectorArn": ARN of Voice Connector. Static or dynamic.
    "FromUser": User making the call. Static or dynamic.
    "ToUser": User receiving the call. Static or dynamic.
    "UserToUserInformation": Optional SIP user-to-user info. Static or dynamic.
}
"ConnectionTimeLimitSeconds": Optional, Voice Connector only. Integer 1-600. Static or dynamic.
```

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Only when contact is making an outbound call but has not yet called the outbound number.

**UI Block:** Call phone number

---

## CreateCase

**Type:** `CreateCase`

**Description:** Creates a new case using an existing case template.

**Parameters:**
```json
{
    "LinkContactToCase": "true" or "false",
    "CaseTemplateId": "templateId aligned with existing case templateName",
    "CaseRequestFields": "Optional map of case fields. Keys from Cases domain. Values static or dynamic."
}
```

**Results/Conditions:** None

**Errors:**
- `ContactNotLinked` — Contact was not linked after case creation
- `NoMatchingError` — System error or misconfiguration

**Restrictions:** Any flow type, any channel

**UI Block:** Cases

---

## CreateTask

**Type:** `CreateTask`

**Description:** Creates a new task to run an assigned flow.

**Parameters:**
```json
{
    "ContactFlowId": "Flow ID or ARN. Static or single valid JSONPath.",
    "Attributes": { "Optional. Key: Value, static or dynamic." },
    "Name": "Task name (string)",
    "Description": "Optional. Task description (string)",
    "References": { "Optional. Type: Value, static or dynamic." },
    "DelaySeconds": "Optional. Integer 1-518400 (6 days). Cannot be used with ScheduledTime.",
    "ScheduledTime": "Optional. Date/time. Cannot be used with DelaySeconds.",
    "TaskTemplateId": "Optional. Static only."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** All channels, all flow types

**UI Block:** Create task

---

## CreateWisdomSession

**Type:** `CreateWisdomSession`

**Description:** Associates a Wisdom domain to a contact to enable real-time recommendations.

**Parameters:**
```json
{
    "WisdomAssistantArn": "ARN for Wisdom Assistant. Static or dynamic."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Voice channel only. All flow types.

**UI Block:** Amazon Q in Connect

---

## DequeueContactAndTransferToQueue

**Type:** `DequeueContactAndTransferToQueue`

**Description:** Combination of Dequeue + TransferContactToQueue. Removes contact from queue, creates new contact segment, places into specified queue (queue-to-queue transfer). Fails if contact is not queued, is being joined to agent, or is connected to agent.

**Parameters:**
```json
{
    "QueueId": "Optional. Queue ID or ARN. Cannot be used with AgentId. Static or single JSONPath.",
    "AgentId": "Optional. Agent ID or ARN. Cannot be used with QueueId. Static or single JSONPath."
}
```

**Results/Conditions:** None

**Errors:**
- `QueueAtCapacity` — Destination queue is at capacity
- `NoMatchingError`

**Restrictions:** Customer queue flow only

**UI Block:** Transfer to queue (when used in Customer queue flow)

---

## EndFlowModuleExecution

**Type:** `EndFlowModuleExecution`

**Description:** Ends the current module execution without disconnecting the contact.

**Parameters:** None (empty object)

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Flow modules only

**UI Block:** Return Block

---

## GetCase

**Type:** `GetCase`

**Description:** Searches all existing cases with the provided customer ID. Add request fields to filter. Specify response fields to persist in context.

**Parameters:**
```json
{
    "LinkContactToCase": "true or false",
    "GetLastUpdatedCase": "true or false — get only last updated case",
    "CustomerId": "Customer's Id to search cases",
    "CaseRequestFields": "Optional map. Keys from Cases domain. Static or dynamic.",
    "CaseResponseFields": ["Optional list of field names to persist in case namespace"]
}
```

**Results/Conditions:** None

**Errors:**
- `NoMatchingError` — System error or misconfiguration
- `ContactNotLinked` — Contact was not linked after case retrieval
- `MultipleFound` — Multiple cases found
- `NoneFound` — No cases found

**Restrictions:** Any flow type, any channel

**UI Block:** Cases

---

## InvokeFlowModule

**Type:** `InvokeFlowModule`

**Description:** Invokes a reusable flow module.

**Parameters:**
```json
{
    "FlowModuleId": "Flow module ID or ARN. Static or dynamic."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** All channels, Inbound flow types only

**UI Block:** Invoke module

---

## StartOutboundChatContact

**Type:** `StartOutboundChatContact`

**Description:** Initiates an outbound chat contact. Only SMS chats supported.

**Parameters:**
```json
{
    "SourceEndpoint": {
        "Address": "ConnectPhoneNumberArn",
        "Type": "CONNECT_PHONENUMBER_ARN"
    },
    "DestinationEndpoint": {
        "Address": "E164 phone number",
        "Type": "TELEPHONE_NUMBER"
    },
    "ContactFlowArn": "Flow ARN for the outbound chat",
    "ContactSubtype": "connect:SMS",
    "InitialSystemMessage": {
        "Content": "Optional initial message"
    },
    "RelatedContact": "Optional. Only 'CURRENT' supported."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:**
- Only `connect:SMS` as ContactSubtype
- Only `CONNECT_PHONENUMBER_ARN` as SourceEndpoint Type
- Only `TELEPHONE_NUMBER` as DestinationEndpoint Type

**UI Block:** Send message

---

## TagContact

**Type:** `TagContact`

**Description:** Sets a collection of user-defined tags on the current contact. All-or-nothing operation.

**Parameters:**
```json
{
    "Tags": {
        "Key1": "Value1"
    }
}
```
Keys and values may be static or dynamic.

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Any flow type, any channel

**UI Block:** Contact tags

---

## TransferContactToAgent

**Type:** `TransferContactToAgent`

**Description:** Ends the current flow and transfers to an agent. If agent is busy, contact is disconnected. Voice only.

**Parameters:** None

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Transfer to agent and transfer to queue flows only

**UI Block:** Transfer to agent

---

## TransferContactToQueue

**Type:** `TransferContactToQueue`

**Description:** Places a contact not already in a queue into the contact's TargetQueue. Fails if contact is already queued/routing/connected.

**Parameters:** None

**Results/Conditions:** None

**Errors:**
- `QueueAtCapacity` — Destination queue at capacity
- `NoMatchingError`

**Restrictions:** Inbound contact flows and transfer flows only. Not whisper, customer queue, or hold flows.

**UI Block:** Transfer to queue

---

## UnTagContact

**Type:** `UnTagContact`

**Description:** Removes a collection of user-defined tags from the current contact. Cannot remove system tags.

**Parameters:**
```json
{
    "TagKeys": ["Key1"]
}
```
Keys can only be set statically.

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** All channels, all flow types

**UI Block:** Contact tags

---

## UpdateCase

**Type:** `UpdateCase`

**Description:** Updates an existing case by ID.

**Parameters:**
```json
{
    "LinkContactToCase": "true or false",
    "CaseId": "Unique identifier of the case",
    "CaseRequestFields": "Optional map. Keys from Cases domain. Static or dynamic."
}
```

**Results/Conditions:** None

**Errors:**
- `ContactNotLinked` — Contact not linked after case update
- `NoMatchingError`

**Restrictions:** Any flow type, any channel

**UI Block:** Cases

---

## UpdateContactAttributes

**Type:** `UpdateContactAttributes`

**Description:** Sets a collection of contact attributes on current or related contact. All-or-nothing.

**Parameters:**
```json
{
    "Attributes": {
        "Key": "Value"
    },
    "TargetContact": "Current or Related (static only)"
}
```
Keys and values may be static or dynamic.

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Any flow type, any channel

**UI Block:** Set contact attributes

---

## UpdateContactCallbackNumber

**Type:** `UpdateContactCallbackNumber`

**Description:** Updates the callback number used by CreateCallbackContact. Defaults to customer caller ID if never set.

**Parameters:**
```json
{
    "CallbackNumber": "Must be a single valid JSONPath reference. Cannot be static."
}
```

**Results/Conditions:** None

**Errors:**
- `InvalidCallbackNumber` — Not a valid E.164 phone number
- `CallbackNumberNotDialable` — Not dialable by the instance

**Restrictions:** Contact flows, transfer flows, customer queue flows. Not whispers or hold flows.

**UI Block:** Set callback number

---

## UpdateContactData

**Type:** `UpdateContactData`

**Description:** Sets a collection of Connect-defined attributes on the specified contact. All-or-nothing.

**Parameters:**
```json
{
    "Name": "Optional. Contact name. Static or dynamic.",
    "Description": "Optional. Contact description.",
    "LanguageCode": "Optional. Language for current contact.",
    "CustomerId": "Optional. Customer ID associated with contact.",
    "References": { "Optional. Type: Value, static or dynamic." },
    "IsVoiceIdStreamingEnabled": "Optional. 'TRUE' or 'FALSE'.",
    "IsVoiceAuthenticationEnabled": "Optional. 'TRUE' or 'FALSE'.",
    "IsFraudDetectionEnabled": "Optional. 'TRUE' or 'FALSE'.",
    "VoiceAuthenticationThreshold": "Optional. 0-100.",
    "VoiceAuthenticationResponseTime": "Optional. 5-10.",
    "FraudDetectionThreshold": "Optional. 0-100.",
    "WatchlistId": "Optional. 0-100.",
    "WisdomSessionArn": "Optional. Session ARN.",
    "TargetContact": "Required. 'Current' or 'Related'."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** All channels, all flow types

**UI Block:** Set contact attributes

---

## UpdateContactEventHooks

**Type:** `UpdateContactEventHooks`

**Description:** Sets one or more contact event hooks (flows associated with contact events).

**Valid event hooks:**
- AgentHold
- AgentWhisper
- CustomerHold
- CustomerQueue
- CustomerRemaining
- CustomerWhisper
- DefaultAgentUI
- DisconnectAgentUI
- PauseContact
- ResumeContact

**Parameters:**
```json
{
    "EventHooks": {
        "EventType": "FlowId or ARN"
    }
}
```
Only one entry per map. Keys must be static.

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** All flow types

**UI Blocks:** Set customer queue flow, Set event flow, Set hold flow, Set whisper flow

---

## UpdateContactMediaProcessing

**Type:** `UpdateContactMediaProcessing`

**Description:** Configure custom Lambda processor for in-flight chat messages.

**Parameters:**
```json
{
    "ChatProcessor": {
        "ProcessingEnabled": "True or False (static)",
        "LambdaProcessorARN": "ARN of Lambda function (static)",
        "ChatProcessorSettings": {
            "DeliverUnprocessedMessages": "True or False (static)"
        }
    }
}
```

**Results/Conditions:** None

**Errors:**
- `NoMatchingError` — Must always be defined
- `ChannelMismatch` — Channel mismatch (only chat supported)

**UI Block:** Set recording, analytics and processing behavior

---

## UpdateContactMediaStreamingBehavior

**Type:** `UpdateContactMediaStreamingBehavior`

**Description:** Enables or disables contact media streaming for a set of participants.

**Parameters:**
```json
{
    "MediaStreamingState": "Enabled or Disabled (static)",
    "Participants": [
        {
            "ParticipantType": "Customer (static only)",
            "MediaDirections": ["From", "To"]
        }
    ],
    "MediaStreamType": "Audio (static only)"
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Contact flows, customer queue flows, transfer flows, whisper flows. Not hold flows. Voice channel only.

**UI Block:** Start/Stop media streaming

---

## UpdateContactRecordingAndAnalyticsBehavior

**Type:** `UpdateContactRecordingAndAnalyticsBehavior`

**Description:** Sets contact recording behavior including analysis behavior and which participants to record. Newer version with channel-specific configuration.

**Parameters:**
```json
{
    "ChatBehavior": {
        "ChatAnalyticsBehavior": {
            "Enabled": "True/False (static)",
            "AnalyticsLanguage": "xx-XX format (dynamic OK)",
            "ConversationalAnalyticsRedactionConfiguration": {
                "Enabled": "True/False (static)",
                "RedactionResults": "RedactedAndOriginal or RedactedOnly (dynamic OK)",
                "RedactionMaskMode": "EntityType or PII (static)",
                "RedactionEntities": ["list of entity types (static)"]
            },
            "InFlightChatRedactionConfiguration": {
                "Enabled": "True/False (static)",
                "RedactionMaskMode": "EntityType or PII (static)",
                "RedactionEntities": ["list (static)"],
                "DeliverUnprocessedMessages": "True/False (static)"
            },
            "AnalyticsModes": ["ContactLens"],
            "SentimentConfiguration": { "Enabled": "True/False (static)" },
            "SummaryConfiguration": { "SummaryModes": ["PostContact", "AutomatedInteraction"] }
        }
    },
    "VoiceBehavior": {
        "VoiceRecordingBehavior": {
            "RecordedParticipants": ["Agent", "Customer"],
            "IVRRecordingBehavior": "Enabled or Disabled (static)"
        },
        "VoiceAnalyticsBehavior": {
            "Enabled": "True/False (static)",
            "AnalyticsLanguage": "xx-XX (static)",
            "ConversationalAnalyticsRedactionConfiguration": {
                "Enabled": "True/False (static)",
                "RedactionResults": "RedactedAndOriginal or RedactedOnly",
                "RedactionMaskMode": "EntityType or PII (static)",
                "RedactionEntities": ["list (static)"]
            },
            "AnalyticsModes": ["RealTime", "AutomatedInteraction"],
            "SentimentConfiguration": { "Enabled": "True/False (static)" },
            "SummaryConfiguration": { "SummaryModes": ["PostContact", "AutomatedInteraction"] }
        }
    },
    "ScreenRecordingBehavior": {
        "ScreenRecordedParticipants": ["Agent"]
    }
}
```

Only ONE channel behavior object per configuration. ScreenRecordingBehavior can be independent.

**Valid RedactionEntities:** BANK_ACCOUNT_NUMBER, BANK_ROUTING, CREDIT_DEBIT_NUMBER, CREDIT_DEBIT_CVV, CREDIT_DEBIT_EXPIRY, INTERNATIONAL_BANK_ACCOUNT_NUMBER, PIN, SWIFT_CODE, CA_HEALTH_NUMBER, UK_NATIONAL_HEALTH_SERVICE_NUMBER, CA_SOCIAL_INSURANCE_NUMBER, SSN, UK_NATIONAL_INSURANCE_NUMBER, PASSPORT_NUMBER, DRIVER_ID, IN_AADHAAR, NAME, AGE, EMAIL, PHONE, ADDRESS, US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER, UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER, IN_PERMANENT_ACCOUNT_NUMBER, IN_NREGA, AWS_ACCESS_KEY, AWS_SECRET_KEY, IP_ADDRESS, MAC_ADDRESS, PASSWORD, URL, USERNAME, LICENSE_PLATE, VEHICLE_IDENTIFICATION_NUMBER, IN_VOTER_NUMBER, DATE_TIME, AGENT_DISPLAY_NAME, CUSTOMER_DISPLAY_NAME, ATTACHMENT_NAME

**Entities NOT supported for chat in-flight redaction:** IN_PERMANENT_ACCOUNT_NUMBER, IN_NREGA, IN_VOTER_NUMBER, IN_AADHAAR, DATE_TIME, CUSTOMER_DISPLAY_NAME, AGENT_DISPLAY_NAME, ATTACHMENT_NAME

**Results/Conditions:** None

**Errors:**
- `NoMatchingError` — Must always be defined
- `ChannelMismatch` — Channel mismatch. Must always be defined.
- `InFlightRedactionConfigurationFailed` — If chat behavior with in-flight redaction fails

**UI Block:** Set recording, analytics and processing behavior

---

## UpdateContactRecordingBehavior

**Type:** `UpdateContactRecordingBehavior`

**Description:** Sets contact recording behavior including analysis behavior and which participants to record (legacy version).

**Parameters:**
```json
{
    "RecordingBehavior": {
        "RecordedParticipants": ["Agent", "Customer"],
        "ScreenRecordedParticipants": ["Agent"],
        "IVRRecordingBehavior": "Enabled or Disabled (static)"
    },
    "AnalyticsBehavior": {
        "Enabled": "True/False (static)",
        "AnalyticsLanguage": "xx-XX format (static)",
        "AnalyticsRedactionBehavior": "Enabled or Disabled",
        "AnalyticsRedactionResults": "RedactedAndOriginal or RedactedOnly (dynamic OK)",
        "AnalyticsRedactionMaskMode": "EntityType or PII (static)",
        "AnalyticsRedactionEntities": ["list of entities"],
        "ChannelConfiguration": {
            "Chat": { "AnalyticsModes": ["ContactLens"] },
            "Voice": { "AnalyticsModes": ["RealTime"] }
        },
        "SummaryConfiguration": { "SummaryModes": ["PostContact"] },
        "SentimentConfiguration": { "Enabled": "True/False (static)" }
    }
}
```

AnalyticsBehavior can only be set if RecordedParticipants contains both Agent and Customer.

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Contact flows, transfer flows, outbound whispers, customer queue flows. Not agent/customer whispers or hold flows. Analytics is voice channel only.

**UI Block:** Set recording and analytics behavior

---

## ResumeContact

**Type:** `ResumeContact`

**Description:** Resumes a contact from a paused state.

**Parameters:** None

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** None — can be used everywhere

---

## UpdateContactRoutingBehavior

**Type:** `UpdateContactRoutingBehavior`

**Description:** Updates the contact's routing details. Can move contact forward or backward in queue, or specify queue priority.

**Parameters:**
```json
{
    "QueuePriority": "Integer > 0 (lower = higher priority). Static. Cannot be used with QueueTimeAdjustmentSeconds.",
    "QueueTimeAdjustmentSeconds": "Integer (larger = routed sooner). Static. Cannot be used with QueuePriority."
}
```

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Inbound contact flows only

**UI Block:** Change routing priority / age

---

## UpdateContactTargetQueue

**Type:** `UpdateContactTargetQueue`

**Description:** Sets the contact's TargetQueue used by all other queue-checking instructions and TransferContactToQueue.

**Parameters:**
```json
{
    "QueueId": "Optional. Queue ID or ARN. Cannot be used with AgentId. Static or single JSONPath.",
    "AgentId": "Optional. Agent ID or ARN. Cannot be used with QueueId. Static or single JSONPath."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Inbound contact flows and transfer flows only

**UI Block:** Set working queue

---

## UpdateContactTextToSpeechVoice

**Type:** `UpdateContactTextToSpeechVoice`

**Description:** Updates the Amazon Polly voice used by text-to-speech. Defaults to Joanna if never run.

**Parameters:**
```json
{
    "TextToSpeechVoice": "Amazon Polly voice name. Static or dynamic.",
    "TextToSpeechEngine": "Engine for the voice. Static or dynamic.",
    "TextToSpeechStyle": "None, Conversational, or Newscaster. Static or dynamic."
}
```

**Results/Conditions:** Error if voice/engine invalid or voice doesn't support engine

**Errors:** `NoMatchingError` — Must always be defined

**Restrictions:** All flow types, all channels

**UI Block:** Set voice

---

## UpdatePreviousContactParticipantState

**Type:** `UpdatePreviousContactParticipantState`

**Description:** Prevents previous participants from observing the contact. Common uses: disconnecting the agent that initiates a transfer, or putting agent on hold during secure input collection.

**Parameters:**
```json
{
    "PreviousContactParticipantState": "AgentOnHold | CustomerOnHold | OffHold (voice only)"
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Inbound contact flows and transfer flows only

**UI Block:** Hold customer or agent

---

# Part 3: Flow Control Actions (15 actions)

---

## CheckHoursOfOperation

**Type:** `CheckHoursOfOperation`

**Description:** Returns whether the specified hours of operation is in hours or out of hours, allowing comparisons.

**Parameters:**
```json
{
    "HoursOfOperationId": "Optional. ID or ARN. Static or dynamic. If not specified, uses TargetQueue's hours."
}
```

**Results/Conditions:** True or False. Must have Condition for Equals True and Equals False, no other conditions.

**Errors:** `NoMatchingError`

**Restrictions:** Inbound flows, transfer flows, customer queue flows. Not hold or whisper flows.

**UI Block:** Check hours of operation

---

## CheckMetricData

**Type:** `CheckMetricData`

**Description:** Shortcut action to load metric data for a queue and allow comparisons. Avoids needing separate GetMetricData + Compare.

**Parameters:**
```json
{
    "MetricType": "NumberOfAgentsAvailable | NumberOfAgentsStaffed | NumberOfAgentsOnline | OldestContactInQueueAgeSeconds | NumberOfContactsInQueue (static only)",
    "QueueId": "Optional. Queue ID or ARN. Dynamic OK.",
    "AgentId": "Optional. Agent ID or ARN. Dynamic OK. If neither specified, uses TargetQueue."
}
```

**Results/Conditions:** Number representing metric value. If MetricType is NumberOfAgents*, only "NumberGreaterThan 0" condition supported. Otherwise Equals and Number* operands allowed.

**Errors:**
- `NoMatchingError`
- `NoMatchingCondition` — Only if MetricType is OldestContactInQueueAgeSeconds or NumberOfContactsInQueue

**Restrictions:** Flows, queue/agent transfers, customer queue flows. Not whisper or hold flows.

**UI Blocks:** Check staffing, Check queue status

---

## CheckOutboundCallStatus

**Type:** `CheckOutboundCallStatus`

**Description:** Engages with answering machine output, provides routing branches.

**Parameters:** None (empty object)

**Results/Conditions:**
- `CallAnswered` — Answered by person
- `VoicemailBeep` — Voicemail with beep detected
- `VoicemailNoBeep` — Voicemail, no beep detected
- `NotDetected` — Could not determine (silence, background noise)

Only `Equals` operator supported.

**Errors:** `NoMatchingError`

**Restrictions:** Outbound campaigns only

**UI Block:** Check call progress

---

## CheckVoiceId

**Type:** `CheckVoiceId`

**Description:** Checks enrollment status, voice authentication, or fraud detection results from Voice ID.

**Parameters:**
```json
{ "CheckVoiceIdOption": "enrollmentStatus | voiceAuthentication | fraudDetection" }
```

**Results/Conditions by option:**

**enrollmentStatus:**
- Enrolled, Not enrolled, Opted out

**voiceAuthentication:**
- Authenticated, Not authenticated, Inconclusive, Not enrolled, Opted out

**fraudDetection:**
- High risk, Low risk, Inconclusive

**Errors:** `NoMatchingError`

**Restrictions:** Voice channel only. Error branch taken for chat/task.

**UI Block:** Check Voice ID

---

## Compare

**Type:** `Compare`

**Description:** Allows comparisons against the specified value.

**Parameters:**
```json
{
    "ComparisonValue": "Any single JSONPath identifier valid for flow data object"
}
```

**Results/Conditions:** The value specified, usable for conditions.

**Errors:** `NoMatchingCondition`

**Restrictions:** Available in every flow type

**UI Block:** Check contact attributes

---

## DistributeByPercentage

**Type:** `DistributeByPercentage`

**Description:** Returns a random number 1-100 for percentage-based routing.

**Parameters:** None (empty object)

**Results/Conditions:** Number 1-100 random. Must be a chain of NumericLessThan comparisons with each subsequent value = previous + desired percentage, max 100.

**Errors:** `NoMatchingCondition` — Default option in flow editor

**Restrictions:** Inbound flows, transfer flows, customer queue flows. Not hold or whisper flows.

**UI Block:** Distribute by percentage

---

## EndFlowExecution

**Type:** `EndFlowExecution`

**Description:** Finishes flow without explicitly disconnecting participant. Participant may be disconnected by contact logic after.

**Parameters:** None

**Results/Conditions:** None

**Errors:** None (always terminal)

**Restrictions:** Whisper flows and customer queue flows only. Not flows, hold, or transfer.

**UI Block:** End flow / Resume

---

## GetMetricData

**Type:** `GetMetricData`

**Description:** Loads real-time queue metrics and makes them available on flow run data.

**Parameters:**
```json
{
    "QueueId": "Optional. Queue ID or ARN. Dynamic OK.",
    "AgentId": "Optional. Agent ID or ARN. Dynamic OK.",
    "QueueChannel": "Optional. 'Voice' or 'Chat'. Dynamic OK. If not specified, all channels."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Available in every flow type

**UI Block:** Get queue metrics

---

## Loop

**Type:** `Loop`

**Description:** When the same action runs multiple times, returns "ContinueLooping" N times, then "DoneLooping" once, then resets.

**Parameters:**
```json
{
    "LoopCount": "0-100. Static or dynamic."
}
```

**Results/Conditions:** Must have Condition for Equals ContinueLooping and Equals DoneLooping, no other conditions.

**Errors:** None

**Restrictions:** Every flow type

**UI Block:** Loop

---

## StartVoiceIdStream

**Type:** `StartVoiceIdStream`

**Description:** Sends audio to Voice ID for caller verification and fraud detection as soon as call is connected.

**Parameters:** None (empty object)

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Voice channel only. Error branch for chat/task. Not hold flows.

**UI Block:** Set Voice ID

---

## TransferToFlow

**Type:** `TransferToFlow`

**Description:** Execution jumps to a different flow and continues from that flow's beginning.

**Parameters:**
```json
{
    "ContactFlowId": "Flow ID or ARN. Static or single valid JSONPath."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Inbound flows and transfer flows only. Not hold, customer queue, or whisper flows.

**UI Block:** Transfer to flow

---

## UpdateFlowAttributes

**Type:** `UpdateFlowAttributes`

**Description:** Sets a collection of attributes on the current flow. These are NOT carried over to subsequent flows. All-or-nothing.

**Parameters:**
```json
{
    "FlowAttributes": {
        "Type": {
            "FlowAttribute": "Value"
        }
    }
}
```

**Results/Conditions:** None

**Errors:** None

**Restrictions:** All channels, all flow types

**UI Block:** Set contact attributes

---

## UpdateFlowLoggingBehavior

**Type:** `UpdateFlowLoggingBehavior`

**Description:** Enables or disables flow logging. Behavior remains for rest of contact segment and is inherited by new segments.

**Parameters:**
```json
{
    "FlowLoggingBehavior": "Enabled or Disabled (static only)"
}
```

**Results/Conditions:** None

**Errors:** None

**Restrictions:** Every flow type

**UI Block:** Set logging behavior

---

## UpdateRoutingCriteria

**Type:** `UpdateRoutingCriteria`

**Description:** Sets the routing criteria for the contact with step-based routing.

**Parameters:**
```json
{
    "RoutingCriteria": {
        "Steps": [
            {
                "Expression": {
                    "AttributeCondition": {
                        "Name": "Predefined attribute name (1-64 chars)",
                        "Value": "Predefined attribute value (1-64 chars)",
                        "ProficiencyLevel": "Float: 1.0, 2.0, 3.0, 4.0, 5.0",
                        "ComparisonOperator": "NumberGreaterOrEqualTo"
                    },
                    "AndExpression": ["List of attribute conditions AND-ed together"]
                },
                "Expiry": {
                    "DurationInSeconds": "Static only"
                }
            }
        ]
    }
}
```

When all steps exhausted, contact is offered to any agent in the queue.

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** All channels. Inbound flow, Customer Queue flow, Transfer to Agent flow, Transfer to Queue flow only.

**UI Block:** Set routing criteria

---

## Wait

**Type:** `Wait`

**Description:** Pauses the flow for a specified duration or until a specified event, whichever is first.

**Parameters:**
```json
{
    "TimeoutSeconds": "Static (positive integer, max 604800 = 7 days) or single JSONPath.",
    "Events": "Optional list: 'CustomerReturned', 'BotParticipantDisconnected'. Static only."
}
```

**Results/Conditions:** If event interrupts, result = event name. If timeout, result = "WaitCompleted". Only `Equals` operator. WaitCompleted always required, every specified event also required as condition operand.

**Errors:**
- `NoMatchingError`
- `ParticipantNotFound` — For BotParticipantDisconnected event

**Restrictions:** Every flow type, chat channel only

**UI Block:** Wait

---

# Part 4: Interactions (8 actions)

---

## AssociateContactToCustomerProfile

**Type:** `AssociateContactToCustomerProfile`

**Description:** Associate a contact to a customer profile. Customer Profiles must be enabled.

**Parameters:**
```json
{
    "ProfileRequestData": {
        "ProfileId": "Profile being associated",
        "ContactId": "ContactId being associated"
    },
    "ProfileResponseData": {}
}
```
Both ProfileId and ContactId required.

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**UI Block:** Customer profiles block

---

## CreateCallbackContact

**Type:** `CreateCallbackContact`

**Description:** Creates a new callback contact. Uses contact's CustomerCallbackNumber if no customer number specified. If ContactFlowId specified, InitialCallDelaySeconds is ignored.

**Parameters:**
```json
{
    "QueueId": "Optional. Queue ID or ARN. Static or single JSONPath.",
    "AgentId": "Optional. Agent ID or ARN. Static or single JSONPath.",
    "InitialCallDelaySeconds": "Integer > 0, max 259200 (3 days). Static.",
    "MaximumConnectionAttempts": "Integer > 0. Static.",
    "RetryDelaySeconds": "Integer > 0, max 259200 (3 days). Static.",
    "ContactFlowId": "Optional. Flow ID or ARN. Static or single JSONPath.",
    "CallerId": "Optional. Phone number claimed in instance. Static or single JSONPath."
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Contact flows, transfer flows, customer queue flows. Not whisper or hold flows.

**UI Block:** Set callback number

---

## CreateCustomerProfile

**Type:** `CreateCustomerProfile`

**Description:** Create a customer profile. Customer Profiles must be enabled.

**Parameters:**
```json
{
    "ProfileRequestData": {
        "FirstName": "Optional",
        "MiddleName": "Optional",
        "LastName": "Optional",
        "PhoneNumber": "Optional",
        "EmailAddress": "Optional",
        "AccountNumber": "Optional",
        "AdditionalInformation": "Optional",
        "PartyType": "Optional",
        "BusinessName": "Optional",
        "BirthDate": "Optional",
        "Gender": "Optional",
        "MobilePhoneNumber": "Optional",
        "HomePhoneNumber": "Optional",
        "BusinessPhoneNumber": "Optional",
        "BusinessEmailAddress": "Optional",
        "Address1-4, City, County, Country, PostalCode, Province, State": "Optional",
        "ShippingAddress1-4, ShippingCity...ShippingState": "Optional",
        "MailingAddress1-4, MailingCity...MailingState": "Optional",
        "BillingAddress1-4, BillingCity...BillingState": "Optional",
        "Attributes.x": "Optional custom attributes"
    },
    "ProfileResponseData": {
        "Same fields as above — optional, specify which to return"
    }
}
```

Profile ID persisted under `$.Customer.ProfileId`.

**Results/Conditions:** None. Response attributes available under `$.Customer` path.

**Errors:** `NoMatchingError`

**UI Block:** Customer profiles block

---

## InvokeLambdaFunction

**Type:** `InvokeLambdaFunction`

**Description:** Invokes an AWS Lambda function with optional parameters. Lambda receives copy of flow run data if contact exists.

**Parameters:**
```json
{
    "LambdaFunctionARN": "ARN. Static or dynamic.",
    "InvocationTimeLimitSeconds": "Integer > 0, max 8. Static.",
    "InvocationType": "SYNCHRONOUS | ASYNCHRONOUS",
    "LambdaInvocationAttributes": { "Key": "Value — static or dynamic" },
    "ResponseValidation": {
        "ResponseType": "STRING_MAP or JSON. Static."
    }
}
```

STRING_MAP: Lambda must return flat key/value pairs of strings.
JSON: Lambda can return any valid JSON including nested.

**Results/Conditions:** None. Response attributes available under `$.External` path.

**Errors:** `NoMatchingError`

**Restrictions:** All channels, all flow types

**UI Block:** AWS Lambda function

---

## GetCustomerProfile

**Type:** `GetCustomerProfile`

**Description:** Retrieve a customer profile by search identifier(s), up to five. Customer Profiles must be enabled.

**Parameters:**
```json
{
    "ProfileRequestData": {
        "IdentifierName": "Name for single-identifier search",
        "IdentifierValue": "Value for single-identifier search",
        "SearchCriteria": [
            { "IdentifierName": "Name", "IdentifierValue": "Value" }
        ],
        "LogicalOperator": "AND or OR (required with SearchCriteria)"
    },
    "ProfileResponseData": {
        "FirstName, LastName, PhoneNumber, EmailAddress, etc.": "Optional fields to return"
    }
}
```

At least one search identifier required. Use either IdentifierName/Value or SearchCriteria.

**Results/Conditions:** None. Response under `$.Customer` path.

**Errors:**
- `MultipleFoundError` — Multiple profiles found
- `NoneFoundError` — No profiles found
- `NoMatchingError`

**UI Block:** Customer profiles block

---

## GetCustomerProfileObject

**Type:** `GetCustomerProfileObject`

**Description:** Retrieve a customer profile object (Asset, Order, Case) by type, based on recency or search identifier.

**Parameters:**
```json
{
    "ProfileRequestData": {
        "ProfileId": "Required. Profile owning the object.",
        "ObjectType": "Required. Type of object.",
        "IdentifierName": "Optional. Search identifier name.",
        "IdentifierValue": "Optional. Search identifier value.",
        "UseLatest": "true/false"
    },
    "ProfileResponseData": {
        "AssetAssetId, AssetProfileId, AssetAssetName, AssetSerialNumber...": "Optional Asset fields",
        "OrderOrderId, OrderProfileId, OrderCreatedDate, OrderStatus...": "Optional Order fields",
        "CaseCaseId, CaseTitle, CaseStatus...": "Optional Case fields",
        "ObjectAttributes.x": "Optional custom attributes"
    }
}
```

ProfileId and ObjectType required. Either UseLatest or IdentifierName+Value required.

**Results/Conditions:** None. Response under `$.Customer` path.

**Errors:**
- `NoneFoundError`
- `NoMatchingError`

**UI Block:** Customer profiles block

---

## GetCalculatedAttributesForCustomerProfile

**Type:** `GetCalculatedAttributesForCustomerProfile`

**Description:** Retrieve calculated attributes for a customer profile.

**Parameters:**
```json
{
    "ProfileRequestData": {
        "ProfileId": "Required. Profile owning the calculated attribute."
    },
    "ProfileResponseData": {
        "CalculatedAttributes._average_hold_time": "Optional",
        "CalculatedAttributes._frequent_caller": "Optional",
        "CalculatedAttributes.x": "Optional custom calculated attributes"
    }
}
```

**Results/Conditions:** None. Response under `$.Customer` path.

**Errors:**
- `NoneFoundError`
- `NoMatchingError`

**UI Block:** Customer profiles block

---

## UpdateCustomerProfile

**Type:** `UpdateCustomerProfile`

**Description:** Update a customer profile previously created or retrieved in the flow.

**Parameters:**
```json
{
    "ProfileRequestData": {
        "FirstName, MiddleName, LastName, PhoneNumber, EmailAddress...": "All optional",
        "Address fields, Shipping fields, Mailing fields, Billing fields": "All optional",
        "Attributes.x": "Optional custom attributes"
    },
    "ProfileResponseData": {
        "Same fields as request — optional, specify which to return"
    }
}
```

**Results/Conditions:** None. Response under `$.Customer` path.

**Errors:** `NoMatchingError`

**UI Block:** Customer profiles block

---

# Part 5: Participant Actions (6 actions)

---

## ConnectParticipantWithLexBot

**Type:** `ConnectParticipantWithLexBot`

**Description:** Connects the participant with an Amazon Lex bot. When interaction is over, Intent and Slots are available to the flow.

**Parameters:**
```json
{
    "PromptId": "Optional. Prompt ID or ARN. Static or single JSONPath. Cannot use with Text/SSML.",
    "Text": "Optional. Text to send. Static or dynamic. Cannot use with PromptId/SSML.",
    "SSML": "Optional. SSML to send. Static or dynamic. Cannot use with Text/PromptId.",
    "Media": {
        "Uri": "Location of message",
        "SourceType": "S3 only",
        "MediaType": "Audio only"
    },
    "LexV2Bot": {
        "AliasArn": "Alias ARN. Static or dynamic."
    },
    "LexBot": {
        "Name": "Bot name",
        "Region": "AWS region",
        "Alias": "Bot alias"
    },
    "LexSessionAttributes": { "Key": "Value — static or dynamic" },
    "LexInitializationData": {
        "InitialMessage": "Optional. Serialized to $.Media.InitialMessage (chat only)"
    },
    "LexTimeoutSeconds": {
        "Text": "Number — timer length for chat"
    }
}
```

Provide either LexBot or LexV2Bot.

**Results/Conditions:** Result is the bot Intent. Only `Equals` operator supported.

**Errors:**
- `NoMatchingCondition` — No condition was true
- `NoMatchingError` — Error with no other match
- `InputTimeLimitExceeded` — No response before LexTimeoutSeconds

**Restrictions:** All channels. Contact flows, transfer flows, customer queue flows. Not whisper or hold flows.

**UI Block:** Get customer input

---

## DisconnectParticipant

**Type:** `DisconnectParticipant`

**Description:** Disconnects the participant from the contact and stops the flow.

**Parameters:** None

**Results/Conditions:** None

**Errors:** None

**Restrictions:** All channels. Contact flows, transfer flows, customer queue flows.

**UI Block:** Disconnect / hang up

---

## GetParticipantInput

**Type:** `GetParticipantInput`

**Description:** Gathers customer input (DTMF for voice, entered string for other channels). Supports encryption, validation, storage, custom DTMF terminator.

**Parameters:**
```json
{
    "PromptId": "Optional. Prompt ID or ARN. Static or single JSONPath.",
    "Text": "Optional. Static or dynamic.",
    "SSML": "Optional. Static or dynamic.",
    "Media": {
        "Uri": "Location",
        "SourceType": "S3",
        "MediaType": "Audio"
    },
    "InputTimeLimitSeconds": "Integer > 0. Static. Timeout until first DTMF digit (voice).",
    "StoreInput": "True or False. Static.",
    "InputValidation": {
        "PhoneNumberValidation": {
            "NumberFormat": "Local or E164. Static.",
            "CountryCode": "Two-letter code. Required if Local. Static."
        },
        "CustomValidation": {
            "MaximumLength": "Number. Static or dynamic."
        }
    },
    "InputEncryption": {
        "EncryptionKeyId": "Key identifier. Static or dynamic.",
        "Key": "PEM public key. Static or dynamic."
    },
    "DTMFConfiguration": {
        "InputTerminationSequence": "Up to 5 digits as terminator",
        "DisableCancelKey": "True or False — disables * cancel",
        "InterdigitTimeLimitSeconds": "1-20 seconds between digits. Static or dynamic."
    }
}
```

InputValidation required if and only if StoreInput is True. InputEncryption only with CustomValidation. PhoneNumberValidation and CustomValidation are mutually exclusive.

**Results/Conditions:**
- If StoreInput True: No conditions supported
- If StoreInput False or not defined: Result is participant input. Only `Equals` operator, single character (0-9, *, #)

**Errors:**
- `NoMatchingCondition` — Only if StoreInput is False
- `NoMatchingError` — Must always be defined
- `InvalidPhoneNumber` — Only if StoreInput True with PhoneNumberValidation
- `InputTimeLimitExceeded` — No response before timeout

**Restrictions:** Voice channel only. Contact flows, transfer flows, customer queue flows. Not whisper or hold flows.

**UI Block:** Get customer input

---

## MessageParticipant

**Type:** `MessageParticipant`

**Description:** Sends a message to the participant. Audio prompt or TTS for voice, text message for other channels.

**Parameters:**
```json
{
    "PromptId": "Optional. Prompt ID or ARN. Static or single JSONPath. Cannot use with Text/SSML.",
    "Text": "Optional. Static or dynamic. Cannot use with PromptId/SSML.",
    "SSML": "Optional. Static or dynamic. Cannot use with Text/PromptId.",
    "Media": {
        "Uri": "Location",
        "SourceType": "S3",
        "MediaType": "Audio"
    }
}
```

**Results/Conditions:** None

**Errors:** `NoMatchingError`

**Restrictions:** Contact flows, transfer flows, whisper flows, customer queue flows. Not hold flows. PromptId and SSML are voice-only. Other channels support Text only.

**UI Block:** Play

---

## MessageParticipantIteratively

**Type:** `MessageParticipantIteratively`

**Description:** Loops a sequence of prompts while customer/agent is on hold or in queue. Can be interrupted by timeout.

**Parameters:**
```json
{
    "Messages": [
        { "Text": "Optional TTS text" },
        { "PromptId": "Prompt ID or ARN" },
        { "SSML": "Optional SSML" },
        { "Media": { "Uri": "...", "SourceType": "S3", "MediaType": "Audio" } }
    ],
    "InterruptFrequencySeconds": "Optional. Time before action completes with MessagesInterrupted."
}
```

**Results/Conditions:** When timeout elapses, result = "MessagesInterrupted". Only `Equals` operator with MessagesInterrupted.

**Errors:** `NoMatchingError`

**Restrictions:** Customer Queue, Customer Hold, Agent Hold flows only. PromptId is voice-only. Chat channel takes error branch immediately.

**UI Block:** Loop prompt

---

## ShowView

**Type:** `ShowView`

**Description:** Initiates a UI-based workflow for step-by-step guides in the Connect agent workspace.

**Parameters:**
```json
{
    "ViewResource": {
        "Id": "View Resource ID",
        "Version": "View Resource version"
    },
    "InvocationTimeLimitSeconds": 400,
    "ViewData": {
        "Description": "Optional map of data passed to the View. Static or dynamic."
    },
    "SensitiveDataConfiguration": {
        "HideResponseOn": ["TRANSCRIPT"]
    }
}
```

**Results/Conditions:** Result is the user's selection in the View. Available conditions depend on the View resource.

**Errors:**
- `NoMatchingError`
- `NoMatchingCondition`
- `TimeLimitExceeded` — No response before InvocationTimeLimitSeconds

**Restrictions:** Chat channel only. Inbound flows and customer queue flows only. Limit combined inputs + contact attributes to 16KB.

**UI Block:** Show View

---

# Appendix: Action Type Quick Reference

## Contact Actions (27)

| Action Type | UI Block | Channel | Key Flow Types |
|---|---|---|---|
| CompleteOutboundCall | Call phone number | Voice | Outbound flows |
| CreateCase | Cases | All | All |
| CreateTask | Create task | All | All |
| CreateWisdomSession | Amazon Q in Connect | Voice | All |
| DequeueContactAndTransferToQueue | Transfer to queue | All | Customer queue only |
| EndFlowModuleExecution | Return Block | All | Flow modules only |
| GetCase | Cases | All | All |
| InvokeFlowModule | Invoke module | All | Inbound only |
| StartOutboundChatContact | Send message | SMS | All |
| TagContact | Contact tags | All | All |
| TransferContactToAgent | Transfer to agent | Voice | Transfer flows |
| TransferContactToQueue | Transfer to queue | All | Inbound, transfer |
| UnTagContact | Contact tags | All | All |
| UpdateCase | Cases | All | All |
| UpdateContactAttributes | Set contact attributes | All | All |
| UpdateContactCallbackNumber | Set callback number | All | Flow, transfer, CQ |
| UpdateContactData | Set contact attributes | All | All |
| UpdateContactEventHooks | Set whisper/hold/queue flow | All | All |
| UpdateContactMediaProcessing | Set recording behavior | Chat | All |
| UpdateContactMediaStreamingBehavior | Start/Stop media streaming | Voice | Flow, CQ, transfer, whisper |
| UpdateContactRecordingAndAnalyticsBehavior | Set recording, analytics | All | Flow, transfer, CQ |
| UpdateContactRecordingBehavior | Set recording behavior | All | Flow, transfer, outbound whisper, CQ |
| ResumeContact | — | All | All |
| UpdateContactRoutingBehavior | Change routing priority | All | Inbound only |
| UpdateContactTargetQueue | Set working queue | All | Inbound, transfer |
| UpdateContactTextToSpeechVoice | Set voice | All | All |
| UpdatePreviousContactParticipantState | Hold customer or agent | Voice | Inbound, transfer |

## Flow Control Actions (15)

| Action Type | UI Block | Channel | Key Flow Types |
|---|---|---|---|
| CheckHoursOfOperation | Check hours of operation | All | Inbound, transfer, CQ |
| CheckMetricData | Check staffing / queue status | All | Flow, transfer, CQ |
| CheckOutboundCallStatus | Check call progress | Voice | Outbound campaigns |
| CheckVoiceId | Check Voice ID | Voice | All |
| Compare | Check contact attributes | All | All |
| DistributeByPercentage | Distribute by percentage | All | Inbound, transfer, CQ |
| EndFlowExecution | End flow / Resume | All | Whisper, CQ only |
| GetMetricData | Get queue metrics | All | All |
| Loop | Loop | All | All |
| StartVoiceIdStream | Set Voice ID | Voice | All except hold |
| TransferToFlow | Transfer to flow | All | Inbound, transfer |
| UpdateFlowAttributes | Set contact attributes | All | All |
| UpdateFlowLoggingBehavior | Set logging behavior | All | All |
| UpdateRoutingCriteria | Set routing criteria | All | Inbound, CQ, transfer |
| Wait | Wait | Chat | All |

## Interactions (8)

| Action Type | UI Block | Key Details |
|---|---|---|
| AssociateContactToCustomerProfile | Customer profiles | Requires ProfileId + ContactId |
| CreateCallbackContact | Set callback number | InitialCallDelay, MaxAttempts, RetryDelay |
| CreateCustomerProfile | Customer profiles | All profile fields optional |
| InvokeLambdaFunction | AWS Lambda function | 8s timeout max, STRING_MAP or JSON response |
| GetCustomerProfile | Customer profiles | Up to 5 search identifiers |
| GetCustomerProfileObject | Customer profiles | Assets, Orders, Cases |
| GetCalculatedAttributesForCustomerProfile | Customer profiles | Calculated attributes |
| UpdateCustomerProfile | Customer profiles | Update previously created/retrieved profile |

## Participant Actions (6)

| Action Type | UI Block | Channel | Key Details |
|---|---|---|---|
| ConnectParticipantWithLexBot | Get customer input | All | Lex V1/V2, Intent conditions |
| DisconnectParticipant | Disconnect / hang up | All | Terminal action |
| GetParticipantInput | Get customer input | Voice | DTMF, encryption, validation |
| MessageParticipant | Play | All | TTS/SSML (voice), Text (other) |
| MessageParticipantIteratively | Loop prompt | Voice | Queue/hold flows only |
| ShowView | Show View | Chat | Step-by-step guides, 16KB limit |
# Connect Flow Language — Part 2: Flow Control, Interactions, Participant Actions

Complete reference for three action categories in the Amazon Connect Customer Flow Language.

---

## Category 1: Flow Control Actions

Flow control actions don't have side effects and are only used to determine the path through a flow. They don't need a contact or participant to succeed. They control flow behavior by enabling/disabling features (such as logging) or by choosing a branch when the flow runs.

---

### 1.1 CheckHoursOfOperation

**Action Type:** `CheckHoursOfOperation`

**Description:** Returns whether the specified hours of operation object (or the hours of operation object associated with the current queue if no hours of operation is referenced) is in hours or out of hours as its result, allowing comparisons against it.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `HoursOfOperationId` | String (ID or ARN) | Optional | An hours of operation ID or ARN. Must be either fully static or fully dynamic. If not specified, the TargetQueue's hours of operation for the contact are used. |

```json
{
  "HoursOfOperationId": "string"
}
```

**Transitions / Conditions:**

- Result is **True** or **False** based on whether the hours of operation is in hours or out of hours.
- There must be a Condition for Equals **True** and a Condition for Equals **False**, and no other conditions.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** Available in inbound flows, transfer flows, and customer queue flows. Not available in hold flows or whisper flows.

**UI Block:** [Check hours of operation](https://docs.aws.amazon.com/connect/latest/adminguide/check-hours-of-operation.html)

---

### 1.2 CheckMetricData

**Action Type:** `CheckMetricData`

**Description:** A shortcut single action to avoid using GetMetricData and Compare for a set of simple metrics. Loads the specified metric data for the specified queue, and allows comparisons to the loaded value.

**Parameters:**

| Parameter | Type | Required | Valid Values | Description |
|-----------|------|----------|--------------|-------------|
| `MetricType` | String (enum) | Required | `NumberOfAgentsAvailable`, `NumberOfAgentsStaffed`, `NumberOfAgentsOnline`, `OldestContactInQueueAgeSeconds`, `NumberOfContactsInQueue` | The metric to check. Dynamic values are NOT supported. |
| `QueueId` | String (ID or ARN) | Optional | — | A queue ID or queue ARN. May not be specified if AgentId is specified. Dynamic values supported. |
| `AgentId` | String (ID or ARN) | Optional | — | An agent ID or agent ARN, representing an agent queue. May not be specified if QueueId is specified. Dynamic values supported. If neither this nor QueueId are specified, the contact TargetQueue is used. |

```json
{
  "MetricType": "NumberOfContactsInQueue",
  "QueueId": "arn:aws:connect:...",
  "AgentId": "arn:aws:connect:..."
}
```

**Transitions / Conditions:**

- Result is a **number** representing the metric value.
- If MetricType is `NumberOfAgents*`, the only supported condition is `NumberGreaterThan 0`.
- Otherwise, `Equals` and any `Number*` operands are allowed.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |
| `NoMatchingCondition` | If no other Condition matches (only supported if MetricType is `OldestContactInQueueAgeSeconds` or `NumberOfContactsInQueue`) |

**Restrictions:** Available in flows, queue and agent transfers, and customer queue flows. Not available in any whisper or hold flows.

**UI Block:** [Check staffing](https://docs.aws.amazon.com/connect/latest/adminguide/check-staffing.html), [Check queue status](https://docs.aws.amazon.com/connect/latest/adminguide/check-queue-status.html)

---

### 1.3 CheckOutboundCallStatus

**Action Type:** `CheckOutboundCallStatus`

**Description:** Engages with the output provided by an answering machine, and provides branches to route the contact accordingly.

**Parameters:** None (empty parameter object).

```json
{}
```

**Transitions / Conditions:**

| Result Value | Description |
|-------------|-------------|
| `CallAnswered` | The call has been answered by a person |
| `VoicemailBeep` | Connect identifies voicemail and detects a beep |
| `VoicemailNoBeep` | Connect identifies voicemail but doesn't detect a beep, or beep is unknown |
| `NotDetected` | Connect could not determine voicemail vs. live voice (long silences, excessive background noise) |

- Only the `Equals` operator is supported.
- Only `CallAnswered`, `VoicemailBeep`, `VoicemailNoBeep`, and `NotDetected` are valid operands.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no condition matches |

**Restrictions:** Works with Connect outbound campaigns ONLY.

**UI Block:** [Check call progress](https://docs.aws.amazon.com/connect/latest/adminguide/check-call-progress.html)

---

### 1.4 CheckVoiceId

**Action Type:** `CheckVoiceId`

**Description:** Checks the enrollment status, voice authentication, or fraud detection results of the voice analysis returned by Voice ID.

**Parameters:**

| Parameter | Type | Required | Valid Values |
|-----------|------|----------|--------------|
| `CheckVoiceIdOption` | String (enum) | Required | `enrollmentStatus`, `voiceAuthentication`, `fraudDetection` |

```json
{
  "CheckVoiceIdOption": "enrollmentStatus"
}
```

**Transitions / Conditions:**

When `CheckVoiceIdOption` = **enrollmentStatus**:

| Result | Description |
|--------|-------------|
| `Enrolled` | Caller is enrolled in voice authentication |
| `Not enrolled` | Caller has not been enrolled |
| `Opted out` | Caller has opted out of voice authentication |

Not charged for checking enrollment status.

When `CheckVoiceIdOption` = **voiceAuthentication**:

| Result | Description |
|--------|-------------|
| `Authenticated` | Authentication score >= threshold (default 90 or custom) |
| `Not authenticated` | Authentication score < threshold |
| `Inconclusive` | Unable to analyze caller's speech (usually < 10 seconds of audio) |
| `Not enrolled` | Caller not enrolled |
| `Opted out` | Caller opted out |

Not charged if result is Inconclusive, Not enrolled, or Opted out.

When `CheckVoiceIdOption` = **fraudDetection**:

| Result | Description |
|--------|-------------|
| `High risk` | Risk score meets or exceeds threshold |
| `Low risk` | Risk score below threshold |
| `Inconclusive` | Unable to analyze caller's voice for fraud detection |

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no condition matches |

**Restrictions:** Voice channel only. Chat or task channels take the Error branch.

**UI Block:** [Check Voice ID](https://docs.aws.amazon.com/connect/latest/adminguide/check-voice-id.html)

---

### 1.5 Compare

**Action Type:** `Compare`

**Description:** Allows comparisons against the specified value.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ComparisonValue` | JSONPath | Required | Any single JSONPath identifier that is valid for the flow data object |

```json
{
  "ComparisonValue": "$.Attributes.myAttribute"
}
```

**Transitions / Conditions:**

- The value specified for comparison. This can be used for conditions.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingCondition` | If no Condition matches |

**Restrictions:** Available in every type of flow.

**UI Block:** [Check contact attributes](https://docs.aws.amazon.com/connect/latest/adminguide/check-contact-attributes.html)

---

### 1.6 DistributeByPercentage

**Action Type:** `DistributeByPercentage`

**Description:** Returns a random number between 1 and 100 (inclusive) as its result, allowing comparisons against it.

**Parameters:** None (empty parameter object).

```json
{}
```

**Transitions / Conditions:**

- Result is a number between 1 and 100, inclusive, chosen randomly.
- Comparisons must be a chain of `NumericLessThan` comparisons, with each subsequent comparison checking the previous value plus the desired percentage.
- No comparison may check a value larger than 100.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingCondition` | If no Condition matches (this is the default option in the flow editor) |

**Restrictions:** Available in inbound flows, transfer flows, and customer queue flows. Not available in hold flows or whisper flows.

**UI Block:** [Distribute by percentage](https://docs.aws.amazon.com/connect/latest/adminguide/distribute-by-percentage.html)

---

### 1.7 EndFlowExecution

**Action Type:** `EndFlowExecution`

**Description:** Finishes flow, but does not explicitly disconnect the participant. The participant may be disconnected by contact logic after this. For example, if a flow ends before the contact is put into queue, ending the flow results in the contact being ended.

**Parameters:** None (empty parameter object).

```json
{}
```

**Transitions / Conditions:** None. No conditions are supported.

**Errors:** None. This is always a terminal action.

**Restrictions:** Available only in whisper flows and customer queue flows. Not available in flows, hold flows, or transfer flows.

**UI Block:** [End flow / Resume](https://docs.aws.amazon.com/connect/latest/adminguide/end-flow-resume.html)

---

### 1.8 GetMetricData

**Action Type:** `GetMetricData`

**Description:** Loads real-time queue metrics for the queue specified by queue ID, agent ID (for agent queues), or the target queue, and makes them available on the flow run data.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `QueueId` | String (ID or ARN) | Optional | A queue ID or ARN. May not be specified if AgentId is specified. Dynamic values supported. |
| `AgentId` | String (ID or ARN) | Optional | An agent ID or ARN, representing an agent queue. May not be specified if QueueId is specified. Dynamic values supported. |
| `QueueChannel` | String (enum) | Optional | `Voice` or `Chat`. Can be set dynamically. Determines the channel for which metrics are returned. If not specified, metrics are returned for all channels. |

```json
{
  "QueueId": "arn:aws:connect:...",
  "AgentId": "arn:aws:connect:...",
  "QueueChannel": "Voice"
}
```

**Transitions / Conditions:** None. No conditions are supported.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** Available in every type of flow.

**UI Block:** [Get queue metrics](https://docs.aws.amazon.com/connect/latest/adminguide/get-queue-metrics.html)

---

### 1.9 Loop

**Action Type:** `Loop`

**Description:** When the same action (the same Action Identifier) is run multiple times, this block returns "ContinueLooping" a number of times equal to the specified loop count, then "DoneLooping" once, then resets.

**Parameters:**

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `LoopCount` | Number | Required | 0-100 inclusive | Number of times to loop. Must be either fully static or fully dynamic. |

```json
{
  "LoopCount": 5
}
```

**Transitions / Conditions:**

| Result | Description |
|--------|-------------|
| `ContinueLooping` | The loop should continue |
| `DoneLooping` | The loop should finish |

- Must have a Condition for Equals `ContinueLooping` and for Equals `DoneLooping`, and no other Conditions.

**Errors:** None.

**Restrictions:** Supported in every type of flow.

**UI Block:** [Loop](https://docs.aws.amazon.com/connect/latest/adminguide/loop.html)

---

### 1.10 StartVoiceIdStream

**Action Type:** `StartVoiceIdStream`

**Description:** Sends audio to Connect Voice ID to verify the caller's identity and match against fraudsters in watchlist, as soon as the call is connected to a flow.

**Parameters:** None (empty parameter object).

```json
{}
```

**Transitions / Conditions:** None. No conditions are supported.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no condition matches |

**Restrictions:** Voice channel only. Chat or task channels take the Error branch. Not supported in hold flows.

**UI Block:** [Set Voice ID](https://docs.aws.amazon.com/connect/latest/adminguide/set-voice-id.html)

---

### 1.11 TransferToFlow

**Action Type:** `TransferToFlow`

**Description:** Execution jumps to a different flow, and continues running at that flow's beginning.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ContactFlowId` | String (ID or ARN) | Required | A flow ID or flow ARN. Must be either fully static or a single valid JSONPath identifier. |

```json
{
  "ContactFlowId": "arn:aws:connect:us-east-1:123456789012:instance/.../contact-flow/..."
}
```

**Transitions / Conditions:** None.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** Available in inbound flows and transfer flows. Not available in hold flows, customer queue flows, or whisper flows.

**UI Block:** [Transfer to flow](https://docs.aws.amazon.com/connect/latest/adminguide/transfer-to-flow.html)

---

### 1.12 UpdateFlowAttributes

**Action Type:** `UpdateFlowAttributes`

**Description:** Sets a collection of attributes on the current flow. These attributes are NOT carried over to subsequent flows. Either all attributes are set or none are set (atomic operation).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `FlowAttributes` | Object (Map<String, FlowAttribute>) | Required | Keys are of type String, Values are of type FlowAttribute |

```json
{
  "FlowAttributes": {
    "Type": {
      "FlowAttribute": "Value"
    }
  }
}
```

**Transitions / Conditions:** None. No conditions are supported.

**Errors:** None.

**Restrictions:** Supported on all channels and in all flow types.

**UI Block:** [Set contact attributes](https://docs.aws.amazon.com/connect/latest/adminguide/set-contact-attributes.html)

---

### 1.13 UpdateFlowLoggingBehavior

**Action Type:** `UpdateFlowLoggingBehavior`

**Description:** Enables or disables flow logging. If this is a flow, the behavior remains unless overridden for the rest of the contact segment. It is automatically inherited by new segments in the chain.

**Parameters:**

| Parameter | Type | Required | Valid Values | Description |
|-----------|------|----------|--------------|-------------|
| `FlowLoggingBehavior` | String (enum) | Required | `Enabled`, `Disabled` | Dynamic values are NOT supported. |

```json
{
  "FlowLoggingBehavior": "Enabled"
}
```

**Transitions / Conditions:** None. No conditions are supported.

**Errors:** None.

**Restrictions:** Available in every type of flow.

**UI Block:** [Set logging behavior](https://docs.aws.amazon.com/connect/latest/adminguide/set-logging-behavior.html)

---

### 1.14 UpdateRoutingCriteria

**Action Type:** `UpdateRoutingCriteria`

**Description:** Sets the routing criteria for the contact.

**Parameters:**

```json
{
  "RoutingCriteria": {
    "Steps": [
      {
        "Expression": {
          "AttributeCondition": {
            "Name": "string (1-64 chars)",
            "Value": "string (1-64 chars)",
            "ProficiencyLevel": 1.0,
            "ComparisonOperator": "NumberGreaterOrEqualTo"
          },
          "AndExpression": []
        },
        "Expiry": {
          "DurationInSeconds": 30
        }
      }
    ]
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `RoutingCriteria` | Object | Required | JSON object containing routing criteria |
| `RoutingCriteria.Steps` | Array | Required | List of routing steps. When no agent found in a step within its duration, moves to next step sequentially. When all steps exhausted, offered to any agent in queue. May be static or dynamic. |
| `Steps[].Expression` | Object | Required | Tagged union specifying the expression for a routing step |
| `Steps[].Expression.AttributeCondition` | Object | Optional | Predefined attribute condition |
| `Steps[].Expression.AttributeCondition.Name` | String | Required | Name of predefined attribute (1-64 chars) |
| `Steps[].Expression.AttributeCondition.Value` | String | Required | Value of predefined attribute (1-64 chars) |
| `Steps[].Expression.AttributeCondition.ProficiencyLevel` | Float | Required | Valid values: `1.0`, `2.0`, `3.0`, `4.0`, `5.0` |
| `Steps[].Expression.AttributeCondition.ComparisonOperator` | String | Required | Valid value: `NumberGreaterOrEqualTo` |
| `Steps[].Expression.AndExpression` | Array | Optional | List of routing expressions (attribute conditions) which will be AND-ed together |
| `Steps[].Expiry` | Object | Optional | Expiration settings for a routing step |
| `Steps[].Expiry.DurationInSeconds` | Number | Required | Seconds to wait before expiring the routing step. Can only be set statically. |

**Transitions / Conditions:** None. No conditions are supported.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** Supported on all channels. Only in Inbound flow, Customer Queue flow, Transfer to Agent flow, and Transfer to Queue flow types.

**UI Block:** [Set routing criteria](https://docs.aws.amazon.com/connect/latest/adminguide/set-routing-criteria.html)

---

### 1.15 Wait

**Action Type:** `Wait`

**Description:** Pauses the flow for a specified duration, or until a specified event happens, whichever happens first.

**Parameters:**

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `TimeoutSeconds` | Number or JSONPath | Required | Positive integer, max 604800 (7 days) | Time to wait before finishing with "WaitCompleted". Can be statically defined or a single valid JSONPath identifier. |
| `Events` | Array of Strings | Optional | Must be defined statically | List of events that can trigger an interrupt. Supported: `CustomerReturned`, `BotParticipantDisconnected`. |

```json
{
  "TimeoutSeconds": 300,
  "Events": ["CustomerReturned", "BotParticipantDisconnected"]
}
```

**Transitions / Conditions:**

| Result | Description |
|--------|-------------|
| `WaitCompleted` | Time elapsed without interruption |
| `CustomerReturned` | Customer returned event fired |
| `BotParticipantDisconnected` | Bot participant disconnected event fired |

- Only `Equals` operator supported.
- `WaitCompleted` is always required as a condition operand.
- Every specified event must also be present as a condition operand.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |
| `ParticipantNotFound` | Supported event: `BotParticipantDisconnected` |

**Restrictions:** Supported in every type of flow, but only on the **chat channel**.

**UI Block:** [Wait](https://docs.aws.amazon.com/connect/latest/adminguide/wait.html)

---

## Category 2: Interaction Actions

Interaction actions have side effects, but they don't require a contact or a participant. They include actions such as invoking an AWS Lambda function. They generally work in every circumstance.

---

### 2.1 AssociateContactToCustomerProfile

**Action Type:** `AssociateContactToCustomerProfile`

**Description:** Associate a contact to a customer profile. Customer Profiles must be enabled for the Connect instance.

**API Reference:** [AddProfileKey](https://docs.aws.amazon.com/customerprofiles/latest/APIReference/API_AddProfileKey.html)

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ProfileRequestData.ProfileId` | String | Required | Profile being associated |
| `ProfileRequestData.ContactId` | String | Required | ContactId being associated |

```json
{
  "ProfileRequestData": {
    "ProfileId": "string",
    "ContactId": "string"
  },
  "ProfileResponseData": {}
}
```

**Transitions / Conditions:** None. Conditions are not supported.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**UI Block:** [Customer profiles block](https://docs.aws.amazon.com/connect/latest/adminguide/customer-profiles-block.html)

---

### 2.2 CreateCallbackContact

**Action Type:** `CreateCallbackContact`

**Description:** Creates a new callback contact. If no customer number is specified and this runs in context of a contact, the contact's CustomerCallbackNumber is used. If you specify a ContactFlowId, the InitialCallDelaySeconds parameter is ignored.

**Parameters:**

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `QueueId` | String (ID or ARN) | Optional | Fully static or single JSONPath | Queue for the callback. Falls back to contact's current TargetQueue. May not be specified if AgentId is specified. |
| `AgentId` | String (ID or ARN) | Optional | Fully static or single JSONPath | Agent queue. May not be specified if QueueId is specified. |
| `InitialCallDelaySeconds` | Integer | Required | > 0, <= 259200 (3 days), static | Minimum time to wait before routing the callback. Gives customer time to end existing contact. |
| `MaximumConnectionAttempts` | Integer | Required | > 0, static | Max attempts to connect callback if not answered. |
| `RetryDelaySeconds` | Integer | Required | > 0, <= 259200 (3 days), static | Minimum wait between unanswered callback attempts. |
| `ContactFlowId` | String (ID or ARN) | Optional | Fully static or single JSONPath | Flow to execute post-creation. If specified, InitialCallDelaySeconds is ignored. |
| `CallerId` | String | Optional | Fully static or single JSONPath | Phone number for the callback (what customer sees). Must be a valid phone number claimed in the instance. |

```json
{
  "QueueId": "arn:aws:connect:...",
  "InitialCallDelaySeconds": 30,
  "MaximumConnectionAttempts": 3,
  "RetryDelaySeconds": 600,
  "ContactFlowId": "arn:aws:connect:...",
  "CallerId": "+15551234567"
}
```

**Transitions / Conditions:** None. No conditions are supported.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** Supported in contact flows, transfer flows, and customer queue flows. Not supported in whisper flows or hold flows.

**UI Block:** [Set callback number](https://docs.aws.amazon.com/connect/latest/adminguide/set-callback-number.html)

---

### 2.3 CreateCustomerProfile

**Action Type:** `CreateCustomerProfile`

**Description:** Create a customer profile. Customer Profiles must be enabled for the Connect instance.

**API Reference:** [CreateProfile](https://docs.aws.amazon.com/customerprofiles/latest/APIReference/API_CreateProfile.html)

**Parameters:**

`ProfileRequestData` and `ProfileResponseData` both accept the same set of optional fields:

| Field Category | Fields |
|---------------|--------|
| **Name** | `FirstName`, `MiddleName`, `LastName` |
| **Contact Info** | `PhoneNumber`, `EmailAddress`, `MobilePhoneNumber`, `HomePhoneNumber`, `BusinessPhoneNumber`, `BusinessEmailAddress` |
| **Business** | `AccountNumber`, `AdditionalInformation`, `PartyType`, `BusinessName`, `BirthDate`, `Gender` |
| **Primary Address** | `Address1`-`Address4`, `City`, `County`, `Country`, `PostalCode`, `Province`, `State` |
| **Shipping Address** | `ShippingAddress1`-`ShippingAddress4`, `ShippingCity`, `ShippingCounty`, `ShippingCountry`, `ShippingPostalCode`, `ShippingProvince`, `ShippingState` |
| **Mailing Address** | `MailingAddress1`-`MailingAddress4`, `MailingCity`, `MailingCounty`, `MailingCountry`, `MailingPostalCode`, `MailingProvince`, `MailingState` |
| **Billing Address** | `BillingAddress1`-`BillingAddress4`, `BillingCity`, `BillingCounty`, `BillingCountry`, `BillingPostalCode`, `BillingProvince`, `BillingState` |
| **Custom** | `Attributes.x` (custom key-value pairs) |

All fields are optional. Newly created profile ID is persisted under `$.Customer.ProfileId`.

```json
{
  "ProfileRequestData": {
    "FirstName": "John",
    "LastName": "Doe",
    "PhoneNumber": "+15551234567",
    "Attributes.x": "custom_value"
  },
  "ProfileResponseData": {
    "FirstName": "",
    "LastName": "",
    "PhoneNumber": ""
  }
}
```

**Transitions / Conditions:** None. If no error, response attributes are available under `$.Customer` path.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**UI Block:** [Customer profiles block](https://docs.aws.amazon.com/connect/latest/adminguide/customer-profiles-block.html)

---

### 2.4 InvokeLambdaFunction

**Action Type:** `InvokeLambdaFunction`

**Description:** Invokes an AWS Lambda function with optional parameters. The Lambda function also receives a copy of the flow run data if there is an associated contact.

**Parameters:**

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `LambdaFunctionARN` | String (ARN) | Required | Static or dynamic | The ARN of the Lambda function to invoke |
| `InvocationTimeLimitSeconds` | Integer | Required | > 0, <= 8, static | Seconds to wait for a Lambda response |
| `InvocationType` | String (enum) | Required | `SYNCHRONOUS`, `ASYNCHRONOUS` | Specifies the invocation type |
| `LambdaInvocationAttributes` | Object (Map) | Optional | Keys/values static or dynamic | Additional data to send to the Lambda function |
| `ResponseValidation.ResponseType` | String (enum) | Required | `STRING_MAP`, `JSON`, static | If `STRING_MAP`, Lambda must return flat key/value string pairs. If `JSON`, Lambda can return any valid JSON including nested. |

```json
{
  "LambdaFunctionARN": "arn:aws:lambda:us-east-1:123456789012:function:myFunction",
  "InvocationTimeLimitSeconds": 8,
  "InvocationType": "SYNCHRONOUS",
  "LambdaInvocationAttributes": {
    "customKey": "customValue"
  },
  "ResponseValidation": {
    "ResponseType": "STRING_MAP"
  }
}
```

**Transitions / Conditions:** None. If no error, response attributes are available under `$.External` path.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** None. Supported by all channels and in all types of flows.

**UI Block:** [AWS Lambda function](https://docs.aws.amazon.com/connect/latest/adminguide/invoke-lambda-function-block.html)

---

### 2.5 GetCustomerProfile

**Action Type:** `GetCustomerProfile`

**Description:** Retrieve a customer profile based on any search identifier, up to five total. Customer Profiles must be enabled.

**API Reference:** [SearchProfiles](https://docs.aws.amazon.com/customerprofiles/latest/APIReference/API_SearchProfiles.html)

**Parameters:**

At least one search identifier must be present. Use either single-identifier or multi-identifier search:

**Single identifier:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ProfileRequestData.IdentifierName` | String | Required (if not using SearchCriteria) | Name to search for profiles |
| `ProfileRequestData.IdentifierValue` | String | Required (if not using SearchCriteria) | Value to search for profiles |

**Multiple identifiers:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ProfileRequestData.SearchCriteria` | Array of `{IdentifierName, IdentifierValue}` | Required (if not using single identifier) | List of search criteria |
| `ProfileRequestData.LogicalOperator` | String (enum) | Required with SearchCriteria | `AND` or `OR` |

`ProfileResponseData` accepts the same field set as CreateCustomerProfile (all optional). Profile ID is persisted under `$.Customer.ProfileId`.

```json
{
  "ProfileRequestData": {
    "SearchCriteria": [
      { "IdentifierName": "_phone", "IdentifierValue": "+15551234567" },
      { "IdentifierName": "_email", "IdentifierValue": "john@example.com" }
    ],
    "LogicalOperator": "OR"
  },
  "ProfileResponseData": {
    "FirstName": "",
    "LastName": "",
    "AccountNumber": ""
  }
}
```

**Transitions / Conditions:** None. If no error, response attributes available under `$.Customer` path.

**Errors:**

| Error | Description |
|-------|-------------|
| `MultipleFoundError` | Multiple profiles found for the search key |
| `NoneFoundError` | No profiles found for the search key |
| `NoMatchingError` | If no other Error matches |

**UI Block:** [Customer profiles block](https://docs.aws.amazon.com/connect/latest/adminguide/customer-profiles-block.html)

---

### 2.6 GetCustomerProfileObject

**Action Type:** `GetCustomerProfileObject`

**Description:** Retrieve a customer profile object of the desired type, based on recency or any search identifier. Customer Profiles must be enabled.

**API Reference:** [ListProfileObjects](https://docs.aws.amazon.com/customerprofiles/latest/APIReference/API_ListProfileObjects.html)

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ProfileRequestData.ProfileId` | String | Required | Profile owning the object |
| `ProfileRequestData.ObjectType` | String | Required | Type of object being retrieved |
| `ProfileRequestData.UseLatest` | Boolean | Conditional | true/false. Required if not using IdentifierName/Value |
| `ProfileRequestData.IdentifierName` | String | Conditional | Name of search identifier. Required if not using UseLatest |
| `ProfileRequestData.IdentifierValue` | String | Conditional | Value of search identifier. Required if not using UseLatest |

`ProfileResponseData` supports these object-specific fields (all optional):

**Asset fields:** `AssetAssetId`, `AssetProfileId`, `AssetAssetName`, `AssetSerialNumber`, `AssetModelNumber`, `AssetModelName`, `AssetProductSKU`, `AssetPurchaseDate`, `AssetUsageEndDate`, `AssetStatus`, `AssetPrice`, `AssetQuantity`, `AssetDescription`, `AssetAdditionalInformation`, `AssetDataSource`, `AssetAttributes.x`

**Order fields:** `OrderOrderId`, `OrderProfileId`, `OrderCustomerEmail`, `OrderCustomerPhone`, `OrderCreatedDate`, `OrderUpdatedDate`, `OrderProcessedDate`, `OrderClosedDate`, `OrderCancelledDate`, `OrderCancelReason`, `OrderName`, `OrderAdditionalInformation`, `OrderGateway`, `OrderStatus`, `OrderStatusCode`, `OrderStatusUrl`, `OrderCreditCardNumber`, `OrderCreditCardCompany`, `OrderFulfillmentStatus`, `OrderTotalPrice`, `OrderTotalTax`, `OrderTotalDiscounts`, `OrderTotalItemsPrice`, `OrderTotalShippingPrice`, `OrderTotalTipReceived`, `OrderCurrency`, `OrderTotalWeight`, `OrderBillingName`, `OrderBillingAddress1`-`4`, `OrderBillingCity`, `OrderBillingCounty`, `OrderBillingCountry`, `OrderBillingPostalCode`, `OrderBillingProvince`, `OrderBillingState`, `OrderShippingName`, `OrderShippingAddress1`-`4`, `OrderShippingCity`, `OrderShippingCounty`, `OrderShippingCountry`, `OrderShippingPostalCode`, `OrderShippingProvince`, `OrderShippingState`, `OrderAttributes.x`

**Case fields:** `CaseCaseId`, `CaseProfileId`, `CaseTitle`, `CaseSummary`, `CaseStatus`, `CaseReason`, `CaseCreatedBy`, `CaseCreatedDate`, `CaseUpdatedDate`, `CaseClosedDate`, `CaseAdditionalInformation`, `CaseDataSource`, `CaseAttributes.x`

**Generic:** `ObjectAttributes.x`

Auto-persisted IDs:
- Asset ID -> `$.Customer.Asset.AssetId`
- Order ID -> `$.Customer.Order.OrderId`
- Case ID -> `$.Customer.Case.CaseId`

```json
{
  "ProfileRequestData": {
    "ProfileId": "profile-id-123",
    "ObjectType": "Order",
    "UseLatest": true
  },
  "ProfileResponseData": {
    "OrderOrderId": "",
    "OrderStatus": "",
    "OrderTotalPrice": ""
  }
}
```

**Transitions / Conditions:** None. If no error, response available under `$.Customer` path.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoneFoundError` | No profile objects found |
| `NoMatchingError` | If no other Error matches |

**UI Block:** [Customer profiles block](https://docs.aws.amazon.com/connect/latest/adminguide/customer-profiles-block.html)

---

### 2.7 GetCalculatedAttributesForCustomerProfile

**Action Type:** `GetCalculatedAttributesForCustomerProfile`

**Description:** Retrieve calculated attributes for a customer profile. Customer Profiles must be enabled.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ProfileRequestData.ProfileId` | String | Required | Profile owning the calculated attribute |

`ProfileResponseData` fields (all optional):

| Field | Description |
|-------|-------------|
| `CalculatedAttributes._average_hold_time` | Built-in: average hold time |
| `CalculatedAttributes._frequent_caller` | Built-in: frequent caller flag |
| `CalculatedAttributes.x` | Any custom calculated attribute |

```json
{
  "ProfileRequestData": {
    "ProfileId": "profile-id-123"
  },
  "ProfileResponseData": {
    "CalculatedAttributes._average_hold_time": "",
    "CalculatedAttributes._frequent_caller": "",
    "CalculatedAttributes.custom_attr": ""
  }
}
```

**Transitions / Conditions:** None. If no error, response available under `$.Customer` path.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoneFoundError` | No profiles found |
| `NoMatchingError` | If no other Error matches |

**UI Block:** [Customer profiles block](https://docs.aws.amazon.com/connect/latest/adminguide/customer-profiles-block.html)

---

### 2.8 UpdateCustomerProfile

**Action Type:** `UpdateCustomerProfile`

**Description:** Update a customer profile that was previously created or retrieved in the flow. Customer Profiles must be enabled.

**API Reference:** [UpdateProfile](https://docs.aws.amazon.com/customerprofiles/latest/APIReference/API_UpdateProfile.html)

**Parameters:**

`ProfileRequestData` and `ProfileResponseData` accept the same field set as CreateCustomerProfile (all optional):

- Name fields: `FirstName`, `MiddleName`, `LastName`
- Contact: `PhoneNumber`, `EmailAddress`, `MobilePhoneNumber`, `HomePhoneNumber`, `BusinessPhoneNumber`, `BusinessEmailAddress`
- Business: `AccountNumber`, `AdditionalInformation`, `PartyType`, `BusinessName`, `BirthDate`, `Gender`
- Primary Address: `Address1`-`4`, `City`, `County`, `Country`, `PostalCode`, `Province`, `State`
- Shipping Address: `ShippingAddress1`-`4`, `ShippingCity`, `ShippingCounty`, `ShippingCountry`, `ShippingPostalCode`, `ShippingProvince`, `ShippingState`
- Mailing Address: `MailingAddress1`-`4`, `MailingCity`, `MailingCounty`, `MailingCountry`, `MailingPostalCode`, `MailingProvince`, `MailingState`
- Billing Address: `BillingAddress1`-`4`, `BillingCity`, `BillingCounty`, `BillingCountry`, `BillingPostalCode`, `BillingProvince`, `BillingState`
- Custom: `Attributes.x`

Profile ID persisted under `$.Customer.ProfileId`.

```json
{
  "ProfileRequestData": {
    "FirstName": "Jane",
    "LastName": "Doe",
    "Attributes.loyalty_tier": "Gold"
  },
  "ProfileResponseData": {
    "FirstName": "",
    "LastName": ""
  }
}
```

**Transitions / Conditions:** None. If no error, response available under `$.Customer` path.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**UI Block:** [Customer profiles block](https://docs.aws.amazon.com/connect/latest/adminguide/customer-profiles-block.html)

---

## Category 3: Participant Actions

Participant actions are attempted only when the flow runs in context of a participant. They generally result in an action that the participant experiences, such as playing a prompt or disconnecting.

---

### 3.1 ConnectParticipantWithLexBot

**Action Type:** `ConnectParticipantWithLexBot`

**Description:** Connects the participant with the specified Amazon Lex bot. When the interaction is over, the Intent and Slots of the bot are available to the flow during its run.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PromptId` | String (ID or ARN) | Optional | Prompt to play while gathering input. May not be specified if Text or SSML is specified. Static or single JSONPath. |
| `Text` | String | Optional | Text to send to participant. May not be specified if PromptId or SSML is specified. Static or dynamic. |
| `SSML` | String | Optional | SSML to send to participant. May not be specified if Text or PromptId is specified. Static or dynamic. |
| `Media` | Object | Optional | External media source |
| `Media.Uri` | String | Required (in Media) | Location of the message |
| `Media.SourceType` | String | Required (in Media) | Only supported: `S3` |
| `Media.MediaType` | String | Required (in Media) | Only supported: `Audio` |
| `LexV2Bot` | Object | Required | LexV2 bot details |
| `LexV2Bot.AliasArn` | String (ARN) | Required | Alias ARN of the LexV2 bot. Static or dynamic. |
| `LexSessionAttributes` | Object (Map) | Optional | Session attributes passed to Lex. Keys/values static or dynamic. |
| `LexInitializationData` | Object | Optional | Initialization data to prime the bot. Only supported for Chat channel (not Voice). |
| `LexInitializationData.InitialMessage` | String | Optional | Initial message parsed to Lex. Always serialized to `$.Media.InitialMessage` (resolves to customer's initial chat message). |
| `LexTimeoutSeconds` | Object | Optional | Lex timer configuration |
| `LexTimeoutSeconds.Text` | Number | Optional | Timer length for chat channel in seconds |

**Note:** If the initial message attribute is not included as part of the contact, the Get customer input block takes the error branch. Use Check contact attributes block prior to verify the initial message is available for different messaging types (web chat, SMS, Apple Messages for Business).

**Full JSON Example:**

```json
{
  "Parameters": {
    "PromptId": "arn:aws:connect:...:prompt/...",
    "Text": "How can I help you?",
    "SSML": "<speak>How can I help you?</speak>",
    "Media": {
      "Uri": "s3://bucket/audio.wav",
      "SourceType": "S3",
      "MediaType": "Audio"
    },
    "LexV2Bot": {
      "AliasArn": "arn:aws:lex:us-east-1:123456789012:bot-alias/BOTID/ALIASID"
    },
    "LexSessionAttributes": {
      "key1": "value1"
    },
    "LexInitializationData": {
      "InitialMessage": "$.Media.InitialMessage"
    },
    "LexTimeoutSeconds": {
      "Text": 300
    }
  },
  "Identifier": "unique-action-id",
  "Type": "ConnectParticipantWithLexBot",
  "Transitions": {
    "NextAction": "next-action-id",
    "Errors": [
      { "NextAction": "error-action-id", "ErrorType": "InputTimeLimitExceeded" },
      { "NextAction": "error-action-id", "ErrorType": "NoMatchingError" },
      { "NextAction": "default-action-id", "ErrorType": "NoMatchingCondition" }
    ]
  }
}
```

**Transitions / Conditions:**

- If Lex interaction succeeds, the result is the **Intent** of the bot.
- Conditions are supported, but only the `Equals` operator is supported.
- `NextAction`: Identifier of the action to run after this action if no error or condition is preferentially chosen.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingCondition` | No specified condition evaluated to True |
| `NoMatchingError` | Error occurred and no other error matched |
| `InputTimeLimitExceeded` | No response before configured LexTimeoutSeconds |

**Restrictions:** Supported by all channels. Available only in contact flows, transfer flows, and customer queue flows. Not available in whisper flows or hold flows.

**UI Block:** [Get customer input](https://docs.aws.amazon.com/connect/latest/adminguide/get-customer-input.html)

---

### 3.2 DisconnectParticipant

**Action Type:** `DisconnectParticipant`

**Description:** Disconnects the participant from the contact and stops this flow from running.

**Parameters:** None. No parameters expected.

```json
{}
```

**Transitions / Conditions:** None. Conditions are not supported.

**Errors:** None.

**Restrictions:** Supported for all channels. Available in contact flows, transfer flows, and customer queue flows.

**UI Block:** [Disconnect / hang up](https://docs.aws.amazon.com/connect/latest/adminguide/disconnect-hang-up.html)

---

### 3.3 GetParticipantInput

**Action Type:** `GetParticipantInput`

**Description:** Gathers customer input (DTMF collection for voice contacts, or an entered string for other channels). Supports optional encryption, validation, storing to "LastParticipantInput", custom DTMF terminators, and more.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PromptId` | String (ID or ARN) | Optional | Prompt to play. May not be specified if Text or SSML specified. Static or single JSONPath. |
| `Text` | String | Optional | Text to send. May not be specified if PromptId or SSML specified. Static or dynamic. |
| `SSML` | String | Optional | SSML to send. May not be specified if Text or PromptId specified. Static or dynamic. |
| `Media` | Object | Optional | External media source |
| `Media.Uri` | String | Required (in Media) | Location of the message |
| `Media.SourceType` | String | Required (in Media) | Only supported: `S3` |
| `Media.MediaType` | String | Required (in Media) | Only supported: `Audio` |
| `InputTimeLimitSeconds` | Integer | Required | Timeout until first DTMF digit (Voice). Must be static, > 0. |
| `StoreInput` | String (enum) | Required | `True` or `False`. Must be static. |
| `InputValidation` | Object | Conditional | Required if and only if StoreInput is True |
| `InputValidation.PhoneNumberValidation` | Object | Optional | May not be specified if CustomValidation is specified |
| `InputValidation.PhoneNumberValidation.NumberFormat` | String (enum) | Required (in PhoneNumberValidation) | `Local` or `E164`. Static only. |
| `InputValidation.PhoneNumberValidation.CountryCode` | String | Conditional | Required if NumberFormat is `Local`. Two-letter country code. Static only. |
| `InputValidation.CustomValidation` | Object | Optional | May not be specified if PhoneNumberValidation is specified |
| `InputValidation.CustomValidation.MaximumLength` | Number | Required (in CustomValidation) | Maximum length of input. Static or dynamic. |
| `InputEncryption` | Object | Optional | May only be specified if CustomValidation is provided |
| `InputEncryption.EncryptionKeyId` | String | Required (in InputEncryption) | Key identifier uploaded in AWS console. Static or dynamic. |
| `InputEncryption.Key` | String | Required (in InputEncryption) | PEM definition of the public key (signed with EncryptionKeyId). Static or dynamic. |
| `DTMFConfiguration` | Object | Optional | Override default DTMF behavior for voice calls |
| `DTMFConfiguration.InputTerminationSequence` | String | Optional | Up to 5 digits as the terminating sequence |
| `DTMFConfiguration.DisableCancelKey` | String (enum) | Optional | `True` or `False`. If True, `*` key doesn't cancel DTMF gathering. |
| `DTMFConfiguration.InterdigitTimeLimitSeconds` | Integer | Optional | 1-20 seconds. Timeout between each DTMF digit after first entry. Static or dynamic. |

```json
{
  "PromptId": "arn:aws:connect:...:prompt/...",
  "InputTimeLimitSeconds": 10,
  "StoreInput": "True",
  "InputValidation": {
    "CustomValidation": {
      "MaximumLength": 16
    }
  },
  "InputEncryption": {
    "EncryptionKeyId": "key-id",
    "Key": "PEM-encoded-public-key"
  },
  "DTMFConfiguration": {
    "InputTerminationSequence": "#",
    "DisableCancelKey": "False",
    "InterdigitTimeLimitSeconds": 5
  }
}
```

**Transitions / Conditions:**

- If `StoreInput` = `True`: No run result, conditions NOT supported.
- If `StoreInput` = `False` or not defined: Result is the participant input. Conditions supported with `Equals` operator only. Values must be static, single character: `0`-`9`, `*`, or `#`.

**Errors:**

| Error | Required When | Description |
|-------|--------------|-------------|
| `NoMatchingCondition` | StoreInput is False | No condition evaluated to true |
| `NoMatchingError` | Always | If no other Error matches |
| `InvalidPhoneNumber` | StoreInput is True + PhoneNumberValidation specified | Input was not a valid phone number |
| `InputTimeLimitExceeded` | Always | No response before configured timeout |

**Restrictions:** Voice channel only. Available in contact flows, transfer flows, and customer queue flows. Not in whisper flows or hold flows.

**UI Block:** [Get customer input](https://docs.aws.amazon.com/connect/latest/adminguide/get-customer-input.html)

---

### 3.4 MessageParticipant

**Action Type:** `MessageParticipant`

**Description:** Sends a message to the participant. This is an audio prompt or text-to-speech for voice contacts, or a text message for other channels.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PromptId` | String (ID or ARN) | Optional | Prompt to play. May not be specified if Text or SSML specified. Static or single JSONPath. |
| `Text` | String | Optional | Text to send. May not be specified if PromptId or SSML specified. Static or dynamic. |
| `SSML` | String | Optional | SSML to send. May not be specified if Text or PromptId specified. Static or dynamic. |
| `Media` | Object | Optional | External media source |
| `Media.Uri` | String | Required (in Media) | Location of the message |
| `Media.SourceType` | String | Required (in Media) | Only supported: `S3` |
| `Media.MediaType` | String | Required (in Media) | Only supported: `Audio` |

```json
{
  "PromptId": "arn:aws:connect:...:prompt/...",
  "Text": "Thank you for calling.",
  "SSML": "<speak>Thank you for calling.</speak>",
  "Media": {
    "Uri": "s3://bucket/greeting.wav",
    "SourceType": "S3",
    "MediaType": "Audio"
  }
}
```

**Transitions / Conditions:** None. No conditions supported.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If an error occurred and no other error matched |

**Restrictions:** Supported in contact flows, transfer flows, whisper flows, and customer queue flows. NOT in hold flows. `PromptId` and `SSML` are voice channel only. All other channels support only `Text`.

**UI Block:** [Play](https://docs.aws.amazon.com/connect/latest/adminguide/play.html)

---

### 3.5 MessageParticipantIteratively

**Action Type:** `MessageParticipantIteratively`

**Description:** Loops a sequence of prompts while a customer or agent is on hold or in queue. Can be configured with an interruption timeout in Queue flows that interrupts the message loop to run other flow logic.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `Messages` | Array | Required | List of messages to play in a loop |
| `Messages[].Text` | String | Optional | Text to send to participant |
| `Messages[].PromptId` | String (ID or ARN) | Optional | Prompt to play |
| `Messages[].SSML` | String | Optional | SSML to speak |
| `Messages[].Media` | Object | Optional | External media source |
| `Messages[].Media.Uri` | String | Required (in Media) | Location of the message |
| `Messages[].Media.SourceType` | String | Required (in Media) | Only supported: `S3` |
| `Messages[].Media.MediaType` | String | Required (in Media) | Only supported: `Audio` |
| `InterruptFrequencySeconds` | Number | Optional | Time to elapse before action completes with "MessagesInterrupted" |

```json
{
  "Messages": [
    { "Text": "Please continue to hold." },
    { "PromptId": "arn:aws:connect:...:prompt/hold-music" },
    { "SSML": "<speak>Your call is important to us.</speak>" },
    {
      "Media": {
        "Uri": "s3://bucket/hold-music.wav",
        "SourceType": "S3",
        "MediaType": "Audio"
      }
    }
  ],
  "InterruptFrequencySeconds": 30
}
```

**Transitions / Conditions:**

| Result | Description |
|--------|-------------|
| `MessagesInterrupted` | Timeout elapsed, loop interrupted |

- Only `Equals` operator supported. Only `MessagesInterrupted` is a valid operand.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |

**Restrictions:** Supported in Customer Queue, Customer Hold, and Agent Hold flows. `PromptId` is voice channel only; other channels support only `Text`. On chat channel, immediately takes error branch; if no error branch, flow stops and contact routes to next available agent.

**UI Block:** [Loop prompt](https://docs.aws.amazon.com/connect/latest/adminguide/loop-prompts.html)

---

### 3.6 ShowView

**Action Type:** `ShowView`

**Description:** Initiates a UI-based workflow that can be surfaced to users of front-end applications. Used to create step-by-step guides for agents in the Connect agent workspace.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ViewResource.Id` | String | Required | ID of the View Resource to show in the UI |
| `ViewResource.Version` | String | Required | Version of the View Resource |
| `InvocationTimeLimitSeconds` | Number | Optional | Timeout for user response (default example: 400) |
| `ViewData` | Object (Map) | Optional | Data passed to the View Resource. Keys/values static or dynamic. |
| `SensitiveDataConfiguration.HideResponseOn` | Array of Strings | Optional | Where to hide response. Supported: `TRANSCRIPT` |

```json
{
  "ViewResource": {
    "Id": "view-resource-id",
    "Version": "1"
  },
  "InvocationTimeLimitSeconds": 400,
  "ViewData": {
    "Description": "Please verify the customer's identity."
  },
  "SensitiveDataConfiguration": {
    "HideResponseOn": ["TRANSCRIPT"]
  }
}
```

**Transitions / Conditions:**

- The result is what the user selects when interacting with the View.
- Available conditions are dependent on the View resource specified.

**Errors:**

| Error | Description |
|-------|-------------|
| `NoMatchingError` | If no other Error matches |
| `NoMatchingCondition` | If no other Condition matches |
| `TimeLimitExceeded` | No response before configured InvocationTimeLimitSeconds |

**Restrictions:** Chat channel only. Available in inbound flows and customer queue flows. Limit combined inputs and contact attributes to 16KB or less for reliable rendering.

**Note:** This action routes step-by-step guides as chat contacts to agents in the agent workspace. This chat contact type is different from the customer-based contact the agent is handling.

**UI Block:** [Show View](https://docs.aws.amazon.com/connect/latest/adminguide/show-view-block.html)

---

## Quick Reference: Action Availability Matrix

| Action | Inbound Flow | Transfer Flow | Customer Queue | Whisper | Hold | All Channels |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Flow Control** | | | | | | |
| CheckHoursOfOperation | Y | Y | Y | - | - | Y |
| CheckMetricData | Y | Y | Y | - | - | Y |
| CheckOutboundCallStatus | Outbound only | - | - | - | - | Voice |
| CheckVoiceId | Y | Y | Y | Y | Y | Voice |
| Compare | Y | Y | Y | Y | Y | Y |
| DistributeByPercentage | Y | Y | Y | - | - | Y |
| EndFlowExecution | - | - | Y | Y | - | Y |
| GetMetricData | Y | Y | Y | Y | Y | Y |
| Loop | Y | Y | Y | Y | Y | Y |
| StartVoiceIdStream | Y | Y | Y | Y | - | Voice |
| TransferToFlow | Y | Y | - | - | - | Y |
| UpdateFlowAttributes | Y | Y | Y | Y | Y | Y |
| UpdateFlowLoggingBehavior | Y | Y | Y | Y | Y | Y |
| UpdateRoutingCriteria | Y | - | Y | - | - | Y |
| Wait | Y | Y | Y | Y | Y | Chat |
| **Interactions** | | | | | | |
| AssociateContactToCustomerProfile | Y | Y | Y | Y | Y | Y |
| CreateCallbackContact | Y | Y | Y | - | - | Y |
| CreateCustomerProfile | Y | Y | Y | Y | Y | Y |
| InvokeLambdaFunction | Y | Y | Y | Y | Y | Y |
| GetCustomerProfile | Y | Y | Y | Y | Y | Y |
| GetCustomerProfileObject | Y | Y | Y | Y | Y | Y |
| GetCalculatedAttributesForCustomerProfile | Y | Y | Y | Y | Y | Y |
| UpdateCustomerProfile | Y | Y | Y | Y | Y | Y |
| **Participant** | | | | | | |
| ConnectParticipantWithLexBot | Y | Y | Y | - | - | Y |
| DisconnectParticipant | Y | Y | Y | - | - | Y |
| GetParticipantInput | Y | Y | Y | - | - | Voice |
| MessageParticipant | Y | Y | Y | Y | - | Y |
| MessageParticipantIteratively | - | - | Y | - | Y | Voice |
| ShowView | Y | - | Y | - | - | Chat |

---

## Common Error Types Reference

| Error Type | Description |
|-----------|-------------|
| `NoMatchingError` | Catch-all error when no other error type matches |
| `NoMatchingCondition` | No specified condition evaluated to true |
| `InputTimeLimitExceeded` | No response received before timeout |
| `TimeLimitExceeded` | ShowView-specific timeout |
| `InvalidPhoneNumber` | Stored input failed phone number validation |
| `MultipleFoundError` | Multiple customer profiles found |
| `NoneFoundError` | No customer profiles found |
| `ParticipantNotFound` | Participant not available (Wait action) |

---

## Common Condition Operators

| Operator | Used By |
|----------|---------|
| `Equals` | CheckHoursOfOperation, CheckOutboundCallStatus, CheckVoiceId, Loop, Wait, ConnectParticipantWithLexBot, GetParticipantInput, MessageParticipantIteratively |
| `NumericLessThan` | DistributeByPercentage |
| `NumberGreaterThan` | CheckMetricData (for NumberOfAgents* metrics) |
| `Number*` (various) | CheckMetricData (for other metrics) |

---

*Source: [AWS Connect Flow Language API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/) -- fetched 2026-05-28*
