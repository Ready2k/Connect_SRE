# Contact Search

Contact Search in Amazon Connect allows you to find, filter, and manage contacts from the past 24 months, including contacts that are currently in progress.

---

## Overview

The Contact Search page provides a powerful interface for locating specific contacts using a wide range of filters. Results link to the Contact details page where you can view full contact information, recordings, transcripts, analytics, and evaluations.

---

## Search Scope

- **Historical contacts** -- Search contacts up to **2 years** (24 months) back from the current date.
- **In-progress contacts** -- Search for contacts that are currently active (connected, queued, in ACW).
- **All channels** -- Voice, chat, task, and email contacts are all searchable.

---

## Search Filters

### Core Filters

| Filter | Description |
|---|---|
| **ContactId** | Search by exact contact ID. Returns the specific contact and its chain. |
| **Phone number** | Search by customer phone number (full or partial match). |
| **Agent** | Filter by the agent who handled the contact. |
| **Queue** | Filter by the queue the contact was routed through. |
| **Channel** | VOICE, CHAT, TASK, or EMAIL. |
| **Initiation method** | INBOUND, OUTBOUND, TRANSFER, CALLBACK, API, QUEUE_TRANSFER, EXTERNAL_OUTBOUND, MONITOR, DISCONNECT. |
| **Disconnect reason** | CUSTOMER_DISCONNECT, AGENT_DISCONNECT, THIRD_PARTY_DISCONNECT, TELECOM_PROBLEM, CONTACT_FLOW_DISCONNECT, EXPIRED, OTHER. |
| **Date range** | Start and end timestamps for the search window. |

### Contact Attributes

Search by custom contact attributes set during the contact flow:

- Specify the attribute key and value.
- Supports exact match.
- Multiple attribute filters can be combined (AND logic).
- Maximum 10 contact attribute filters per search.

Example: Search for contacts where `AccountType = Premium` and `Region = West`.

### Segment Attributes

Search by segment-level attributes:

| Attribute | Description |
|---|---|
| `connect:Subtype` | Channel subtype (e.g., `connect:SMS`, `connect:WebRTC`, `connect:Email`). |
| `connect:Direction` | INBOUND or OUTBOUND. |

### Contact Lens Categories

Filter contacts by Contact Lens category matches:

- Select one or more categories.
- Returns contacts that matched the selected categories during analysis.
- Useful for finding compliance violations, escalations, or specific interaction patterns.
- Requires Contact Lens to be enabled.

### Additional Filters

| Filter | Description |
|---|---|
| **Routing profile** | Filter by agent's routing profile. |
| **Agent hierarchy** | Filter by agent hierarchy group (any level 1-5). |
| **Contact flow** | Filter by the contact flow used. |
| **Has recording** | Filter for contacts with or without recordings. |
| **Has evaluation** | Filter for contacts with or without evaluations. |
| **Evaluation score range** | Filter by evaluation score (min/max). |
| **Sentiment** | Filter by overall customer or agent sentiment range. |
| **Tags** | Filter by resource tags applied to contacts. |

### In-Progress Contact Filters

- Filter by contact state: CONNECTED, QUEUED, etc.
- Narrow to specific stages of active interactions.

---

## Transcript Search

When Contact Lens is enabled, you can search within conversation transcripts:

- Search for specific words or phrases.
- Filter by participant role (AGENT, CUSTOMER, or both).
- Match type:
  - **MATCH_ALL** -- All terms must appear in the transcript.
  - **MATCH_ANY** -- Any term matches.
- Results highlight the matching segments in the transcript.

---

## Search Results

### Result Fields

| Field | Description |
|---|---|
| **Contact ID** | Unique identifier (clickable to open Contact details). |
| **Agent** | Agent name who handled the contact. |
| **Queue** | Queue name. |
| **Channel** | VOICE, CHAT, TASK, or EMAIL. |
| **Initiation method** | How the contact was initiated. |
| **Disconnect reason** | Why the contact ended. |
| **Initiation time** | When the contact started. |
| **Duration** | Total contact duration. |
| **Sentiment** | Overall customer sentiment (if Contact Lens enabled). |
| **Categories** | Contact Lens categories matched. |

### Pagination

- Results are paginated.
- Default page size depends on the console view.
- Use `NextToken` in API calls for pagination.

### Download / Export

- Download current search results as CSV from the console.
- For bulk export, use the analytics data lake or Kinesis streaming.

---

## Contact Details Page

Clicking a contact in search results opens the Contact details page.

### For Completed Contacts

| Section | Content |
|---|---|
| **Contact information** | Contact ID, channel, initiation method, timestamps (initiation, connected, disconnect), disconnect reason, queue, agent, duration breakdown (queue time, interaction time, hold time, ACW time). |
| **Contact attributes** | All custom attributes set during the contact. |
| **Recording** | Audio recording player (voice) or chat transcript. Screen recording player (if enabled). |
| **Transcript** | Full transcript with speaker labels, timestamps, and sentiment per turn. Highlights for matched categories. |
| **Analytics** | Contact Lens results -- sentiment scores (overall, per-turn, end-of-call), categories matched, talk time breakdown, non-talk time, interruptions, key highlights (issue, outcome, action item). |
| **Evaluations** | Completed and draft evaluations for this contact. Start new evaluations from here. |
| **Contact chain** | Visual chain showing transfers and linked contacts (initial, previous, next, related contact IDs). |
| **References** | Any attached references (URLs, attachments, files). |
| **AI Agent info** | AI agent use case, version, escalation status (if applicable). |

### For In-Progress Contacts

| Section | Content |
|---|---|
| **Real-time transcript** | Live streaming transcript (if Contact Lens real-time is enabled). |
| **Contact information** | Current state, time in state, queue, agent (if connected). |
| **Contact attributes** | Attributes set so far in the contact flow. |

---

## Contact Management Actions

### Actions on In-Progress Contacts

From the Contact details page for an in-progress contact, authorized users can:

| Action | Permission Required | Description |
|---|---|---|
| **Transfer** | `Contact search - Transfer contact` | Transfer the contact to a different queue or agent. |
| **Reschedule** | `Contact search - Reschedule contact` | Reschedule a callback contact to a different time. |
| **End** | `Contact search - End contact` | Force-end the contact. The contact disconnects immediately. |

### Monitoring

Supervisors can monitor in-progress voice contacts:

- **Silent monitoring**: Listen to the call without the agent or customer knowing.
- **Barge**: Join the call and speak to both agent and customer.
- Requires appropriate security profile permissions.

---

## API: SearchContacts

The `SearchContacts` API provides programmatic access to contact search.

```
POST /contact/search
```

### Request Structure

```json
{
  "InstanceId": "instance-id",
  "TimeRange": {
    "Type": "INITIATION_TIMESTAMP",
    "StartTime": "2026-05-01T00:00:00Z",
    "EndTime": "2026-05-25T23:59:59Z"
  },
  "SearchCriteria": {
    "AgentIds": ["agent-id-1"],
    "Channels": ["VOICE"],
    "QueueIds": ["queue-id-1"],
    "InitiationMethods": ["INBOUND"],
    "DisconnectReasons": ["CUSTOMER_DISCONNECT"],
    "ContactAnalysis": {
      "Transcript": {
        "Criteria": [
          {
            "MatchType": "MATCH_ALL",
            "ParticipantRole": "CUSTOMER",
            "SearchText": ["cancel", "refund"]
          }
        ]
      },
      "Category": {
        "MatchType": "MATCH_ALL",
        "Values": ["Escalation", "Complaint"]
      }
    },
    "SearchableContactAttributes": {
      "Criteria": [
        {
          "Key": "AccountType",
          "Values": ["Premium"]
        }
      ],
      "MatchType": "MATCH_ALL"
    },
    "SearchableSegmentAttributes": {
      "Criteria": [
        {
          "Key": "connect:Subtype",
          "Values": ["connect:SMS"]
        }
      ],
      "MatchType": "MATCH_ALL"
    }
  },
  "MaxResults": 100,
  "Sort": {
    "FieldName": "INITIATION_TIMESTAMP",
    "Order": "DESCENDING"
  }
}
```

### Searchable Fields via API

| Field | API Filter | Description |
|---|---|---|
| Contact ID | `SearchCriteria.ContactId` | Exact contact ID. |
| Agent | `SearchCriteria.AgentIds` | List of agent IDs. |
| Queue | `SearchCriteria.QueueIds` | List of queue IDs. |
| Channel | `SearchCriteria.Channels` | List of channels (VOICE, CHAT, TASK, EMAIL). |
| Initiation method | `SearchCriteria.InitiationMethods` | List of initiation methods. |
| Disconnect reason | `SearchCriteria.DisconnectReasons` | List of disconnect reasons. |
| Contact attributes | `SearchCriteria.SearchableContactAttributes` | Key-value attribute filters with MatchType. |
| Segment attributes | `SearchCriteria.SearchableSegmentAttributes` | Segment attribute filters with MatchType. |
| Transcript text | `SearchCriteria.ContactAnalysis.Transcript` | Full-text search in transcripts with participant role and match type. |
| Category | `SearchCriteria.ContactAnalysis.Category` | Contact Lens category match with MatchType and Values. |

### Sort Options

| Sort Field | Description |
|---|---|
| `INITIATION_TIMESTAMP` | Sort by when the contact started. |
| `DISCONNECT_TIMESTAMP` | Sort by when the contact ended. |
| `SCHEDULED_TIMESTAMP` | Sort by scheduled callback time. |
| `CONNECTED_TO_AGENT_TIMESTAMP` | Sort by when agent connected. |
| `CHANNEL` | Sort by channel. |

### Response

Returns a list of contact summaries with pagination token (`NextToken`). Each summary includes:
- ContactId, InitialContactId
- Channel, InitiationMethod, DisconnectReason
- Timestamps (initiation, connected, disconnect, scheduled)
- Agent info (ID, connect timestamp)
- Queue info (ID, enqueue timestamp)
- Contact Lens analysis summary (if available)

---

## Permissions

| Permission | Required For |
|---|---|
| `Contact search - View` | Access the Contact search page. |
| `Contact search - View contact details` | View individual contact details. |
| `Contact search - Transfer contact` | Transfer an in-progress contact. |
| `Contact search - Reschedule contact` | Reschedule an in-progress callback. |
| `Contact search - End contact` | End an in-progress contact. |
| `Recorded conversations - Listen` | Listen to call recordings. |
| `Recorded conversations - Download` | Download call recording files. |
| `Screen recordings - View` | View screen recordings. |
| `Contact Lens - View` | View Contact Lens analytics on the contact details page. |

---

## Limitations

| Limit | Value |
|---|---|
| Search history depth | 24 months |
| Maximum results per API call | 100 |
| Maximum contact attribute filters | 10 per search |
| Transcript search | Requires Contact Lens to be enabled |
| In-progress contact actions | Require specific security profile permissions |
| Pagination | Use NextToken for results beyond MaxResults |
