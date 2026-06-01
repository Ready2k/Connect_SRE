# Amazon Connect Contact Lens API Reference

The Contact Lens API provides real-time and post-contact analytics for Amazon Connect. It has a minimal API surface — **2 actions** and **8 data types** — because the primary integration pattern is Kinesis streaming, not API polling.

**SDK Package**: `@aws-sdk/client-connect-contact-lens`

```typescript
import { ConnectContactLensClient } from '@aws-sdk/client-connect-contact-lens';
const client = new ConnectContactLensClient({ region: 'us-east-1' });
```

## Actions

### ListRealtimeContactAnalysisSegments (V1 — Legacy)

Returns real-time analysis segments for an active contact. **Legacy** — use V2 instead.

```typescript
import {
  ConnectContactLensClient,
  ListRealtimeContactAnalysisSegmentsCommand,
} from '@aws-sdk/client-connect-contact-lens';

const client = new ConnectContactLensClient({ region: 'us-east-1' });

const response = await client.send(
  new ListRealtimeContactAnalysisSegmentsCommand({
    InstanceId: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    ContactId: '11111111-2222-3333-4444-555555555555',
    MaxResults: 100,
    NextToken: undefined, // for pagination
  })
);

for (const segment of response.Segments ?? []) {
  if (segment.Transcript) {
    console.log(
      `[${segment.Transcript.ParticipantRole}] ${segment.Transcript.Content}`
    );
  }
  if (segment.Categories) {
    console.log('Matched categories:', segment.Categories.MatchedCategories);
  }
}
```

### ListRealtimeContactAnalysisSegmentsV2

Enhanced version with richer analysis segments. Available via the **Connect Service** client (not the Contact Lens client).

```typescript
import {
  ConnectClient,
  ListRealtimeContactAnalysisSegmentsV2Command,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

const response = await client.send(
  new ListRealtimeContactAnalysisSegmentsV2Command({
    InstanceId: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    ContactId: '11111111-2222-3333-4444-555555555555',
    OutputType: 'Raw', // 'Raw' or 'Redacted'
    SegmentTypes: ['Transcript', 'Categories', 'PostContactSummary'],
    MaxResults: 100,
  })
);
```

## Data Types

### RealtimeContactAnalysisSegment

The top-level segment object returned by V1. Each segment is one of:

```typescript
interface RealtimeContactAnalysisSegment {
  Transcript?: Transcript;
  Categories?: Categories;
}
```

### Transcript

A single utterance in the conversation:

```typescript
interface Transcript {
  Id: string;
  ParticipantId: string;
  ParticipantRole: 'AGENT' | 'CUSTOMER';
  Content: string;
  BeginOffsetMillis: number;
  EndOffsetMillis: number;
  Sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
  IssuesDetected?: IssueDetected[];
}
```

### Categories

Categories matched during analysis:

```typescript
interface Categories {
  MatchedCategories: string[];
  MatchedDetails: Record<string, CategoryDetails>;
}
```

### CategoryDetails

Details for a matched category:

```typescript
interface CategoryDetails {
  PointsOfInterest: PointOfInterest[];
}
```

### PointOfInterest

A time range within the contact where a category was matched:

```typescript
interface PointOfInterest {
  BeginOffsetMillis: number;
  EndOffsetMillis: number;
}
```

### IssueDetected

An issue detected within a transcript segment:

```typescript
interface IssueDetected {
  CharacterOffsets: CharacterOffsets;
}
```

### CharacterOffsets

Character position range within transcript content:

```typescript
interface CharacterOffsets {
  BeginOffsetChar: number;
  EndOffsetChar: number;
}
```

### PostContactSummary

AI-generated summary of the contact (V2 only):

```typescript
interface PostContactSummary {
  Content: string;
  Status: 'COMPLETED' | 'FAILED';
  FailureCode?: 'QUOTA_EXCEEDED' | 'INSUFFICIENT_CONVERSATION_CONTENT' | 'FAILED_SAFETY_GUIDELINES' | 'INVALID_ANALYSIS_CONFIGURATION' | 'INTERNAL_ERROR';
}
```

## Recommended Architecture: Kinesis Streaming

For production workloads, **do not poll these APIs**. Instead, use Kinesis streaming for real-time Contact Lens data:

1. **Enable Contact Lens** on the instance and configure Kinesis Data Stream as the output.
2. **Consume from Kinesis** using Lambda, KCL, or Kinesis Data Firehose.
3. **Real-time segments** are streamed as they are analyzed — no polling delay.

```typescript
// Contact Lens Kinesis record structure (simplified)
interface ContactLensKinesisRecord {
  Version: string;
  Channel: 'VOICE' | 'CHAT';
  AccountId: string;
  InstanceId: string;
  ContactId: string;
  EventType: 'SEGMENTS' | 'STARTED' | 'COMPLETED' | 'FAILED';
  Segments: Array<{
    Utterance?: {
      Id: string;
      TranscriptId: string;
      ParticipantId: string;
      ParticipantRole: 'AGENT' | 'CUSTOMER';
      PartialContent: string;
      Content: string;
      BeginOffsetMillis: number;
      EndOffsetMillis: number;
      Sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
      IssuesDetected: IssueDetected[];
      Loudness?: { Score: number };
    };
    Categories?: {
      MatchedCategories: string[];
      MatchedDetails: Record<string, CategoryDetails>;
    };
    PostContactSummary?: PostContactSummary;
  }>;
}
```

### Why Kinesis over API

| Concern | API Polling | Kinesis Streaming |
|---|---|---|
| Latency | Seconds (poll interval) | Sub-second |
| Throttling | 2 TPS per account | No API throttling |
| Scale | Limited by TPS | Shard-level parallelism |
| Cost | API call charges | Kinesis charges (lower at scale) |
| Completeness | May miss segments between polls | Guaranteed delivery |

Use the Contact Lens API only for:
- Ad-hoc debugging or inspection of a single contact
- One-off scripts that analyze a small number of contacts
- Testing and development
