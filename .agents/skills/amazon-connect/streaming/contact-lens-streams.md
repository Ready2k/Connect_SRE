# Contact Lens Real-Time Streaming

Contact Lens real-time analytics can be streamed via Amazon Kinesis Data Streams, providing live transcription, sentiment analysis, category matches, issue detection, and post-contact summaries during and after active contacts. This overcomes the scaling limitations of the REST API (`ListRealtimeContactAnalysisSegments`) and enables building low-latency agent assist applications.

---

## Enabling Contact Lens Streaming

Contact Lens streaming is enabled per-contact via a flow block:

1. Add the **"Set recording, analytics and processing behavior"** block to your contact flow.
2. Enable **Contact Lens real-time analytics** within the block.
3. Configure the output Kinesis Data Stream in the Connect instance settings under **Data storage**.
4. Set language, redaction, and analytics mode options in the flow block.

The stream receives events for all contacts that pass through flows with Contact Lens enabled.

---

## Event Types

| Event Type | When Emitted | Purpose |
|---|---|---|
| `STARTED` | Beginning of Contact Lens analysis | Signals that real-time analysis has begun for a contact. |
| `SEGMENTS` | During the contact (continuously) | Contains analyzed data: transcripts, sentiment, categories, issues. |
| `COMPLETED` | Contact ends successfully | Signals that analysis finished normally. |
| `FAILED` | Analysis encounters an error | Signals that analysis could not complete. |

### Event Lifecycle

```
Contact begins -> STARTED -> SEGMENTS (repeated) -> COMPLETED or FAILED
```

- `STARTED` is emitted once per contact when Contact Lens begins processing.
- `SEGMENTS` events are emitted continuously throughout the contact as new data is analyzed.
- `COMPLETED` or `FAILED` is emitted once when the contact ends.

---

## Output File Structure

Contact Lens produces output files in S3 (post-call) with the following top-level structure:

```json
{
  "Version": "1.1.0",
  "AccountId": "123456789012",
  "Channel": "VOICE",
  "ContentMetadata": {
    "Output": "Raw"
  },
  "JobStatus": "COMPLETED",
  "JobDetails": {
    "SkippedAnalysis": [ ... ]
  },
  "LanguageCode": "en-US",
  "Participants": [ ... ],
  "Categories": { ... },
  "ConversationCharacteristics": { ... },
  "CustomModels": [ ... ],
  "Transcript": [ ... ]
}
```

### ContentMetadata

| Field | Value | Description |
|---|---|---|
| `Output` | `Raw` | Original (unredacted) file. |
| `Output` | `Redacted` | Redacted file with PII removed. |
| `RedactionTypes` | `["PII"]` | Types of redaction applied. |
| `RedactionTypesMetadata.PII.RedactionEntitiesRequested` | String[] | Entities selected for redaction (e.g., `CREDIT_DEBIT_NUMBER`, `NAME`, `USERNAME`). |
| `RedactionTypesMetadata.PII.RedactionMaskMode` | String | `PII` (replaces with `[PII]`) or `EntityType` (replaces with entity label like `[NAME]`). |

### SkippedAnalysis (JobDetails)

When categories are skipped due to quotas or safety guidelines:

```json
{
  "Feature": "CATEGORIZATION",
  "ReasonCode": "QUOTA_EXCEEDED",
  "SkippedEntities": [
    {
      "CategoryName": "PotentialFraud",
      "RuleId": "a1130485-9529-4249-a1d4-5738b4883748"
    }
  ]
}
```

ReasonCode values: `QUOTA_EXCEEDED`, `FAILED_SAFETY_GUIDELINES`.

---

## SEGMENTS Event Data

The `SEGMENTS` event is the primary carrier of analytics data. Each SEGMENTS event contains one or more of the following:

### Transcript Segments

Real-time transcription of the conversation, delivered as individual utterances.

```json
{
  "BeginOffsetMillis": 160,
  "EndOffsetMillis": 4640,
  "Content": "Just hello. My name is Peter and help.",
  "Id": "segment-uuid",
  "ParticipantId": "CUSTOMER",
  "ParticipantRole": "CUSTOMER",
  "Sentiment": "NEUTRAL",
  "LoudnessScore": [66.56, 40.06, 85.27, 82.22, 77.66],
  "Redaction": {
    "RedactedTimestamps": [
      {
        "BeginOffsetMillis": 3290,
        "EndOffsetMillis": 3620
      }
    ]
  }
}
```

**Transcript segment fields:**

| Field | Type | Description |
|---|---|---|
| `Id` | String | Unique identifier for this transcript segment. |
| `ParticipantId` | String | `AGENT` or `CUSTOMER`. |
| `ParticipantRole` | String | `AGENT` or `CUSTOMER`. |
| `Content` | String | Transcribed text. In redacted files, PII is replaced with `[PII]` or entity type labels. |
| `BeginOffsetMillis` | Integer | Start time offset relative to call start (voice). |
| `EndOffsetMillis` | Integer | End time offset relative to call start (voice). |
| `Sentiment` | String | `POSITIVE`, `NEGATIVE`, `NEUTRAL`, or `MIXED`. |
| `LoudnessScore` | Float[] | Array of loudness scores for the utterance, one per second of audio. |

### Redaction

Present in transcript segments only when PII is detected. Each turn includes a `Redaction` section only if it contains PII.

```json
{
  "Redaction": {
    "RedactedTimestamps": [
      {
        "BeginOffsetMillis": 3290,
        "EndOffsetMillis": 3620
      }
    ]
  }
}
```

- If two or more PII redactions exist in a turn, offsets are ordered: first offset applies to first PII, second to second PII, etc.
- In .wav files, the redacted audio portion is replaced with silence.
- The original file does not indicate which specific entity type was redacted (all marked as PII).

### Issue Detection

Automatically identified customer issues within transcript segments:

```json
{
  "IssuesDetected": [
    {
      "CharacterOffsets": {
        "BeginOffsetChar": 0,
        "EndOffsetChar": 55
      },
      "Text": "I need to cancel. I want to cancel my plan subscription"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `CharacterOffsets.BeginOffsetChar` | Integer | Start character offset within the Content string. |
| `CharacterOffsets.EndOffsetChar` | Integer | End character offset within the Content string. |
| `Text` | String | The detected issue text. |

### Outcomes Detection

Automatically identified outcomes (actions completed by the agent):

```json
{
  "OutcomesDetected": [
    {
      "CharacterOffsets": {
        "BeginOffsetChar": 9,
        "EndOffsetChar": 77
      },
      "Text": "I made all the changes to the account and now these discounts applied"
    }
  ]
}
```

### Action Items Detection

Automatically identified action items (commitments made by the agent):

```json
{
  "ActionItemsDetected": [
    {
      "CharacterOffsets": {
        "BeginOffsetChar": 12,
        "EndOffsetChar": 102
      },
      "Text": "I will send you all the details later today and call you back next week to check up on you"
    }
  ]
}
```

### Category Matches

When a Contact Lens rule category is triggered during the contact:

```json
{
  "Categories": {
    "MatchedCategories": ["Cancellation"],
    "MatchedDetails": {
      "Cancellation": {
        "PointsOfInterest": [
          {
            "BeginOffsetMillis": 7370,
            "EndOffsetMillis": 11190
          }
        ]
      }
    }
  }
}
```

Categories are defined in the Connect console under Contact Lens rules. They use keyword matching, sentiment thresholds, and other criteria.

### Post-Contact Summary

Generative AI-powered summary of the conversation:

```json
{
  "ConversationCharacteristics": {
    "ContactSummary": {
      "PostContactSummary": {
        "Content": "The customer and agent's conversation did not have any clear issues, outcomes or next steps. Agent verified customer information and finished the call."
      }
    }
  }
}
```

---

## Conversation Characteristics

The `ConversationCharacteristics` object contains aggregate analytics for the entire contact:

### Sentiment

```json
{
  "Sentiment": {
    "OverallSentiment": {
      "AGENT": 0,
      "CUSTOMER": 3.1
    },
    "SentimentByPeriod": {
      "QUARTER": {
        "AGENT": [
          {
            "BeginOffsetMillis": 0,
            "EndOffsetMillis": 7427,
            "Score": 0
          }
        ],
        "CUSTOMER": [
          {
            "BeginOffsetMillis": 0,
            "EndOffsetMillis": 8027,
            "Score": -2.5
          }
        ]
      }
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `OverallSentiment.AGENT` | Float | Overall agent sentiment score (-5 to +5). |
| `OverallSentiment.CUSTOMER` | Float | Overall customer sentiment score (-5 to +5). |
| `SentimentByPeriod.QUARTER` | Array | Sentiment broken into quarters, each with begin/end offsets and score. |

### Interruptions

```json
{
  "Interruptions": {
    "InterruptionsByInterrupter": {
      "CUSTOMER": [{ "BeginOffsetMillis": 10710, "DurationMillis": 3790, "EndOffsetMillis": 14500 }],
      "AGENT": [{ "BeginOffsetMillis": 10710, "DurationMillis": 3790, "EndOffsetMillis": 14500 }]
    },
    "TotalCount": 2,
    "TotalTimeMillis": 7580
  }
}
```

### Non-Talk Time

```json
{
  "NonTalkTime": {
    "TotalTimeMillis": 0,
    "Instances": []
  }
}
```

### Talk Speed

```json
{
  "TalkSpeed": {
    "DetailsByParticipant": {
      "AGENT": { "AverageWordsPerMinute": 239 },
      "CUSTOMER": { "AverageWordsPerMinute": 163 }
    }
  }
}
```

### Talk Time

```json
{
  "TalkTime": {
    "TotalTimeMillis": 28698,
    "DetailsByParticipant": {
      "AGENT": { "TotalTimeMillis": 15079 },
      "CUSTOMER": { "TotalTimeMillis": 13619 }
    }
  }
}
```

### Total Conversation Duration

```json
{
  "TotalConversationDurationMillis": 32110
}
```

---

## Custom Models

Custom vocabulary models applied to the transcription:

```json
{
  "CustomModels": [
    {
      "Type": "TRANSCRIPTION_VOCABULARY",
      "Name": "ProductNames",
      "Id": "4e14b0db-f00a-451a-8847-f6dbf76ae415"
    }
  ]
}
```

---

## Participants

```json
{
  "Participants": [
    { "ParticipantId": "CUSTOMER", "ParticipantRole": "CUSTOMER" },
    { "ParticipantId": "AGENT", "ParticipantRole": "AGENT" }
  ]
}
```

---

## Voice vs Chat Data Models

Contact Lens uses **separate data models** for voice and chat channels:

**Voice-specific fields:**
- `BeginOffsetMillis` / `EndOffsetMillis` -- time offsets relative to call start
- `LoudnessScore` -- per-second loudness scores for each utterance
- `Redaction.RedactedTimestamps` -- audio offsets for PII redaction
- Non-talk time detection
- Talk speed (words per minute)
- Interruption detection

**Chat-specific fields:**
- `AbsoluteTime` -- wall-clock timestamp for each message
- Message type metadata (text, attachment, event)
- No audio-related fields (no loudness, no talk speed, no non-talk time)

When building consumers, check the `Channel` field in the contact metadata to determine which data model to expect.

---

## Consumer Architecture

### Real-Time Agent Assist Pattern

```javascript
import { KinesisClient, GetRecordsCommand } from "@aws-sdk/client-kinesis";

// 1. Consume from the Contact Lens Kinesis stream
// 2. Filter SEGMENTS events by ContactId
// 3. Extract transcript segments for display
// 4. Monitor category matches for alerts
// 5. Track IssuesDetected for real-time issue surfacing
// 6. Push to agent UI via WebSocket (API Gateway + Lambda)
```

### Scaling Advantages Over REST API

| Approach | Scalability | Latency | Use Case |
|---|---|---|---|
| `ListRealtimeContactAnalysisSegments` REST API | Limited by API throttling | Request-response | Low-volume, on-demand queries |
| Kinesis Data Stream | Scales with shard count | Sub-second push | High-volume, real-time agent assist |

The REST API has per-instance throttle limits that become a bottleneck at scale. Kinesis streaming scales horizontally by adding shards.

---

## Key Considerations

- **Stream configuration:** The Kinesis stream must be in the same region as the Connect instance.
- **Shard planning:** Each concurrent contact generates multiple SEGMENTS events per second. Plan shard capacity based on peak concurrent contacts.
- **Ordering:** Events for a single contact are ordered within a shard (ContactId is used as the partition key).
- **Latency:** Transcript segments typically arrive within 1-3 seconds of the spoken word.
- **Partial transcripts:** Utterance segments arrive faster but may change -- always use the final transcript segment for persistence.
- **Encryption:** Enable server-side encryption on the Kinesis stream; see [data-streaming.md](./data-streaming.md) for KMS key policy setup.
- **Cost:** Contact Lens real-time analysis is billed per minute of analyzed audio, in addition to Kinesis stream costs.
- **Language support:** Real-time transcription supports a subset of languages compared to post-call. Post-call supports 30+ languages; real-time supports fewer. Check the Connect documentation for current language availability.
- **Redaction:** PII redaction in real-time streaming applies the same entity types as post-call. Configure via the flow block's RedactionConfiguration.
- **Category quotas:** If category evaluation is skipped (quota exceeded or safety guidelines), the `SkippedAnalysis` section in the output file documents which categories were skipped and why.
