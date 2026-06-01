# AWS SDK v3 JavaScript/TypeScript Patterns for Amazon Connect

All code patterns use **AWS SDK v3 for JavaScript/TypeScript** exclusively. SDK v2 (`aws-sdk`) is deprecated.

## Client Instantiation

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });
```

### All 8 Client Packages

```typescript
// Core Connect Service
import { ConnectClient } from '@aws-sdk/client-connect';

// Contact Lens (real-time analytics)
import { ConnectContactLensClient } from '@aws-sdk/client-connect-contact-lens';

// Customer Profiles
import { CustomerProfilesClient } from '@aws-sdk/client-customer-profiles';

// Cases
import { ConnectCasesClient } from '@aws-sdk/client-connectcases';

// Q Connect (Wisdom)
import { QConnectClient } from '@aws-sdk/client-qconnect';

// Participant (chat/task interaction)
import { ConnectParticipantClient } from '@aws-sdk/client-connectparticipant';

// Outbound Campaigns V1
import { ConnectCampaignClient } from '@aws-sdk/client-connect-campaign';

// Outbound Campaigns V2
import { ConnectCampaignV2Client } from '@aws-sdk/client-connect-campaign-v2';
```

## Command Pattern

Every API action follows the same pattern: create a command object, send it via the client.

```typescript
import { ConnectClient, DescribeInstanceCommand } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

const response = await client.send(
  new DescribeInstanceCommand({
    InstanceId: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
  })
);

console.log('Instance:', response.Instance?.InstanceAlias);
console.log('Status:', response.Instance?.InstanceStatus);
```

## Pagination

Use the built-in paginator functions with `for await...of`:

```typescript
import { ConnectClient, paginateListUsers } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });
const instanceId = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const users: any[] = [];
for await (const page of paginateListUsers({ client }, { InstanceId: instanceId })) {
  users.push(...(page.UserSummaryList ?? []));
}

console.log(`Total users: ${users.length}`);
```

### Manual Pagination

When you need more control (e.g., early exit):

```typescript
import { ConnectClient, ListQueuesCommand } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

let nextToken: string | undefined;
const queues: any[] = [];

do {
  const response = await client.send(new ListQueuesCommand({
    InstanceId: 'instance-xxx',
    MaxResults: 100,
    NextToken: nextToken,
  }));

  queues.push(...(response.QueueSummaryList ?? []));
  nextToken = response.NextToken;

  // Early exit if we have enough
  if (queues.length >= 500) break;
} while (nextToken);
```

## Error Handling

```typescript
import {
  ConnectClient,
  GetContactAttributesCommand,
  ResourceNotFoundException,
  ThrottlingException,
  InternalServiceException,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

try {
  const response = await client.send(new GetContactAttributesCommand({
    InstanceId: 'instance-xxx',
    InitialContactId: 'contact-xxx',
  }));
  console.log('Attributes:', response.Attributes);
} catch (error: any) {
  switch (error.name) {
    case 'ResourceNotFoundException':
      console.error('Contact not found:', error.message);
      break;
    case 'ThrottlingException':
      console.error('Rate limited — retry with backoff');
      break;
    case 'AccessDeniedException':
      console.error('IAM permission denied:', error.message);
      break;
    case 'InternalServiceException':
      console.error('Service error — safe to retry:', error.message);
      break;
    case 'InvalidParameterException':
      console.error('Bad parameter:', error.message);
      break;
    case 'InvalidRequestException':
      console.error('Invalid request:', error.message);
      break;
    default:
      console.error('Unexpected error:', error.name, error.message);
      throw error;
  }
}
```

### Type-Safe Error Handling

```typescript
import { ResourceNotFoundException } from '@aws-sdk/client-connect';

try {
  // ... API call
} catch (error) {
  if (error instanceof ResourceNotFoundException) {
    // TypeScript knows the error type here
    console.error('HTTP status:', error.$metadata.httpStatusCode);
    console.error('Request ID:', error.$metadata.requestId);
  }
}
```

## Retry Configuration

### Using ConfiguredRetryStrategy

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';
import { ConfiguredRetryStrategy } from '@aws-sdk/util-retry';

const client = new ConnectClient({
  region: 'us-east-1',
  retryStrategy: new ConfiguredRetryStrategy(
    4, // max attempts (1 initial + 3 retries)
    (attempt: number) => {
      // Equal jitter backoff: base/2 + random(0, base/2)
      const baseDelay = Math.min(1000 * Math.pow(2, attempt), 5000);
      return Math.floor(baseDelay / 2 + Math.random() * (baseDelay / 2));
    }
  ),
});
```

### Using maxAttempts (Simple)

```typescript
const client = new ConnectClient({
  region: 'us-east-1',
  maxAttempts: 3,
});
```

## Middleware

Add custom logic to the request/response pipeline:

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

// Add logging middleware
client.middlewareStack.add(
  (next, context) => async (args) => {
    const start = Date.now();
    console.log(`[${context.commandName}] Starting request`);

    const result = await next(args);

    const duration = Date.now() - start;
    console.log(`[${context.commandName}] Completed in ${duration}ms`);
    console.log(`  Request ID: ${result.output.$metadata.requestId}`);
    console.log(`  HTTP Status: ${result.output.$metadata.httpStatusCode}`);
    console.log(`  Retries: ${result.output.$metadata.attempts ?? 1}`);

    return result;
  },
  {
    step: 'initialize',
    name: 'requestLogger',
    tags: ['LOGGING'],
  }
);
```

### Request ID Extraction Middleware

```typescript
client.middlewareStack.add(
  (next) => async (args) => {
    const result = await next(args);
    // Store request ID for debugging
    const requestId = result.output.$metadata.requestId;
    if (requestId) {
      // Attach to your logging/tracing system
      myTracer.setTag('aws.requestId', requestId);
    }
    return result;
  },
  { step: 'deserialize', name: 'requestIdExtractor' }
);
```

## Credential Providers

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';

// From SSO (recommended for local development)
import { fromSSO } from '@aws-sdk/credential-providers';
const ssoClient = new ConnectClient({
  region: 'us-east-1',
  credentials: fromSSO({ profile: 'my-sso-profile' }),
});

// From .aws/credentials profile
import { fromIni } from '@aws-sdk/credential-providers';
const iniClient = new ConnectClient({
  region: 'us-east-1',
  credentials: fromIni({ profile: 'my-connect-profile' }),
});

// From environment variables (Lambda, ECS, CI)
import { fromEnv } from '@aws-sdk/credential-providers';
const envClient = new ConnectClient({
  region: 'us-east-1',
  credentials: fromEnv(),
});

// From STS AssumeRole (cross-account)
import { fromTemporaryCredentials } from '@aws-sdk/credential-providers';
const crossAccountClient = new ConnectClient({
  region: 'us-east-1',
  credentials: fromTemporaryCredentials({
    params: {
      RoleArn: 'arn:aws:iam::999999999999:role/ConnectAccessRole',
      RoleSessionName: 'connect-api-session',
      DurationSeconds: 3600,
    },
  }),
});

// Default provider chain (auto-detects: env → SSO → INI → ECS → IMDS)
// This is what happens when you don't specify credentials at all
const defaultClient = new ConnectClient({ region: 'us-east-1' });
```

## TypeScript Types

Every command has `Input` and `Output` types:

```typescript
import {
  ConnectClient,
  SearchContactsCommand,
  type SearchContactsCommandInput,
  type SearchContactsCommandOutput,
  type SearchCriteria,
  type Contact,
} from '@aws-sdk/client-connect';

// Input type
const input: SearchContactsCommandInput = {
  InstanceId: 'instance-xxx',
  TimeRange: {
    Type: 'INITIATION_TIMESTAMP',
    StartTime: new Date('2026-05-01'),
    EndTime: new Date('2026-05-25'),
  },
  SearchCriteria: {
    Channels: ['VOICE'],
    InitiationMethods: ['INBOUND'],
  },
  MaxResults: 100,
};

// Output type
const output: SearchContactsCommandOutput = await client.send(
  new SearchContactsCommand(input)
);

// Individual contact type
const contacts: Contact[] = output.Contacts ?? [];
```

## Common Patterns

### SearchContacts with Filters

```typescript
import {
  ConnectClient,
  SearchContactsCommand,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

const response = await client.send(new SearchContactsCommand({
  InstanceId: 'instance-xxx',
  TimeRange: {
    Type: 'INITIATION_TIMESTAMP',
    StartTime: new Date('2026-05-20'),
    EndTime: new Date('2026-05-25'),
  },
  SearchCriteria: {
    Channels: ['VOICE', 'CHAT'],
    InitiationMethods: ['INBOUND'],
    QueueIds: ['queue-xxx'],
    AgentIds: ['agent-xxx'],
    ContactAnalysis: {
      Transcript: {
        Criteria: [
          {
            MatchType: 'SEMANTIC',
            ParticipantRole: 'CUSTOMER',
            SearchText: ['billing dispute', 'refund request'],
          },
        ],
      },
    },
  },
  Sort: {
    FieldName: 'INITIATION_TIMESTAMP',
    Order: 'DESCENDING',
  },
  MaxResults: 50,
}));

for (const contact of response.Contacts ?? []) {
  console.log(`${contact.Id} — ${contact.Channel} — ${contact.InitiationMethod}`);
  console.log(`  Agent: ${contact.AgentInfo?.Id}`);
  console.log(`  Queue: ${contact.QueueInfo?.Id}`);
  console.log(`  Duration: ${contact.DisconnectTimestamp && contact.InitiationTimestamp
    ? Math.round((contact.DisconnectTimestamp.getTime() - contact.InitiationTimestamp.getTime()) / 1000)
    : 'N/A'}s`);
}
```

### GetMetricDataV2

```typescript
import {
  ConnectClient,
  GetMetricDataV2Command,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

const now = new Date();
const oneDayAgo = new Date(now.getTime() - 86400000);

const response = await client.send(new GetMetricDataV2Command({
  ResourceArn: 'arn:aws:connect:us-east-1:123456789012:instance/xxx',
  StartTime: oneDayAgo,
  EndTime: now,
  Interval: {
    TimeZone: 'UTC',
    IntervalPeriod: 'HOUR',
  },
  Filters: [
    {
      FilterKey: 'QUEUE',
      FilterValues: ['queue-xxx'],
    },
    {
      FilterKey: 'CHANNEL',
      FilterValues: ['VOICE'],
    },
  ],
  Groupings: ['QUEUE', 'CHANNEL'],
  Metrics: [
    { Name: 'CONTACTS_HANDLED' },
    { Name: 'CONTACTS_ABANDONED' },
    { Name: 'AVG_HANDLE_TIME' },
    { Name: 'AVG_QUEUE_ANSWER_TIME' },
    { Name: 'SERVICE_LEVEL',
      Threshold: [{ Comparison: 'LT', ThresholdValue: 30 }]
    },
    { Name: 'CONTACTS_QUEUED' },
    { Name: 'AVG_AFTER_CONTACT_WORK_TIME' },
    { Name: 'AVG_CONTACT_DURATION' },
  ],
}));

for (const result of response.MetricResults ?? []) {
  const queue = result.Dimensions?.QUEUE?.Id;
  console.log(`\nQueue: ${queue}`);

  for (const metric of result.Collections ?? []) {
    console.log(`  ${metric.Metric?.Name}: ${metric.Value}`);
  }
}
```

### StartContactRecording

```typescript
import {
  ConnectClient,
  StartContactRecordingCommand,
  StopContactRecordingCommand,
  SuspendContactRecordingCommand,
  ResumeContactRecordingCommand,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

// Start recording
await client.send(new StartContactRecordingCommand({
  InstanceId: 'instance-xxx',
  ContactId: 'contact-xxx',
  InitialContactId: 'contact-xxx',
  VoiceRecordingConfiguration: {
    VoiceRecordingTrack: 'ALL', // 'FROM_AGENT' | 'TO_AGENT' | 'ALL'
  },
}));

// Suspend recording (e.g., during PCI data collection)
await client.send(new SuspendContactRecordingCommand({
  InstanceId: 'instance-xxx',
  ContactId: 'contact-xxx',
  InitialContactId: 'contact-xxx',
}));

// Resume recording
await client.send(new ResumeContactRecordingCommand({
  InstanceId: 'instance-xxx',
  ContactId: 'contact-xxx',
  InitialContactId: 'contact-xxx',
}));

// Stop recording
await client.send(new StopContactRecordingCommand({
  InstanceId: 'instance-xxx',
  ContactId: 'contact-xxx',
  InitialContactId: 'contact-xxx',
}));
```

### UpdateContactAttributes

```typescript
import {
  ConnectClient,
  UpdateContactAttributesCommand,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

await client.send(new UpdateContactAttributesCommand({
  InstanceId: 'instance-xxx',
  InitialContactId: 'contact-xxx',
  Attributes: {
    customerTier: 'premium',
    caseId: 'CASE-12345',
    intentDetected: 'billing_dispute',
    sentimentScore: '-2.5',
  },
}));
```

### GetCurrentMetricData (Real-Time)

```typescript
import {
  ConnectClient,
  GetCurrentMetricDataCommand,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

const response = await client.send(new GetCurrentMetricDataCommand({
  InstanceId: 'instance-xxx',
  Filters: {
    Queues: ['queue-xxx', 'queue-yyy'],
    Channels: ['VOICE'],
  },
  Groupings: ['QUEUE'],
  CurrentMetrics: [
    { Name: 'AGENTS_ONLINE', Unit: 'COUNT' },
    { Name: 'AGENTS_AVAILABLE', Unit: 'COUNT' },
    { Name: 'AGENTS_ON_CALL', Unit: 'COUNT' },
    { Name: 'AGENTS_AFTER_CONTACT_WORK', Unit: 'COUNT' },
    { Name: 'CONTACTS_IN_QUEUE', Unit: 'COUNT' },
    { Name: 'OLDEST_CONTACT_AGE', Unit: 'SECONDS' },
    { Name: 'CONTACTS_SCHEDULED', Unit: 'COUNT' },
  ],
}));

for (const result of response.MetricResults ?? []) {
  const queueId = result.Dimensions?.Queue?.Id;
  console.log(`\nQueue: ${queueId}`);

  for (const metric of result.Collections ?? []) {
    console.log(`  ${metric.Metric?.Name}: ${metric.Value} ${metric.Metric?.Unit}`);
  }
}
```

### Batch Operations Pattern

```typescript
import {
  ConnectClient,
  SearchUsersCommand,
  UpdateUserPhoneConfigCommand,
} from '@aws-sdk/client-connect';

const client = new ConnectClient({ region: 'us-east-1' });

// Search all soft phone users
const users = [];
for await (const page of paginateSearchUsers({ client }, {
  InstanceId: 'instance-xxx',
  SearchCriteria: {
    StringCondition: {
      FieldName: 'PhoneConfig.PhoneType',
      Value: 'SOFT_PHONE',
      ComparisonType: 'EXACT',
    },
  },
})) {
  users.push(...(page.Users ?? []));
}

// Batch update with throttle protection
const BATCH_SIZE = 2; // respect 2 TPS limit
for (let i = 0; i < users.length; i += BATCH_SIZE) {
  const batch = users.slice(i, i + BATCH_SIZE);

  await Promise.all(batch.map((user) =>
    client.send(new UpdateUserPhoneConfigCommand({
      InstanceId: 'instance-xxx',
      UserId: user.Id!,
      PhoneConfig: {
        PhoneType: 'SOFT_PHONE',
        AutoAccept: true,
        AfterContactWorkTimeLimit: 30,
      },
    }))
  ));

  // Wait 1 second between batches to stay under 2 TPS
  if (i + BATCH_SIZE < users.length) {
    await new Promise((r) => setTimeout(r, 1000));
  }
}
```

### Lambda Handler Pattern

```typescript
import { ConnectClient, GetContactAttributesCommand } from '@aws-sdk/client-connect';

// Create client outside handler for connection reuse
const client = new ConnectClient({ region: process.env.AWS_REGION });

interface ConnectContactFlowEvent {
  Details: {
    ContactData: {
      Attributes: Record<string, string>;
      Channel: string;
      ContactId: string;
      InitialContactId: string;
      InstanceARN: string;
      CustomerEndpoint: { Address: string; Type: string };
      SystemEndpoint: { Address: string; Type: string };
    };
    Parameters: Record<string, string>;
  };
  Name: string;
}

export const handler = async (event: ConnectContactFlowEvent) => {
  const { ContactId, InstanceARN } = event.Details.ContactData;
  const instanceId = InstanceARN.split('/').pop()!;

  try {
    const attributes = await client.send(new GetContactAttributesCommand({
      InstanceId: instanceId,
      InitialContactId: ContactId,
    }));

    // Return key-value pairs back to the contact flow
    return {
      customerTier: attributes.Attributes?.customerTier ?? 'standard',
      greeting: `Welcome back, valued customer!`,
      lookupStatus: 'SUCCESS',
    };
  } catch (error: any) {
    console.error('Lookup failed:', error.name, error.message);
    return {
      customerTier: 'unknown',
      greeting: 'Welcome! How can we help you?',
      lookupStatus: 'FAILED',
    };
  }
};
```

## Environment Variables

Common environment variables the SDK reads automatically:

| Variable | Description |
|---|---|
| `AWS_REGION` | Default region for all clients |
| `AWS_ACCESS_KEY_ID` | Static access key (avoid in production) |
| `AWS_SECRET_ACCESS_KEY` | Static secret key (avoid in production) |
| `AWS_SESSION_TOKEN` | Session token for temporary credentials |
| `AWS_PROFILE` | Named profile from `~/.aws/config` |
| `AWS_SDK_LOAD_CONFIG` | Set to `1` to load from `~/.aws/config` |
| `AWS_MAX_ATTEMPTS` | Default max retry attempts |

In Lambda/ECS, the SDK automatically uses the execution role credentials — no explicit credential configuration needed.
