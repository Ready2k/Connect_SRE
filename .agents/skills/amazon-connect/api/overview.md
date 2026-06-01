# Amazon Connect API Architecture Overview

## Sub-Services

Amazon Connect is composed of **9 sub-services**, each with its own API endpoint, client package, and IAM action namespace:

| Sub-Service | SDK v3 Package | IAM Prefix | Endpoint Pattern |
|---|---|---|---|
| Connect Service | `@aws-sdk/client-connect` | `connect:` | `connect.{region}.amazonaws.com` |
| Contact Lens | `@aws-sdk/client-connect-contact-lens` | `connect:` | `contact-lens.{region}.amazonaws.com` |
| Customer Profiles | `@aws-sdk/client-customer-profiles` | `profile:` | `profile.{region}.amazonaws.com` |
| Cases | `@aws-sdk/client-connectcases` | `cases:` | `cases.connect.{region}.amazonaws.com` |
| Q Connect (Wisdom) | `@aws-sdk/client-qconnect` | `wisdom:` | `wisdom.{region}.amazonaws.com` |
| Participant | `@aws-sdk/client-connectparticipant` | `connectparticipant:` | `participant.connect.{region}.amazonaws.com` |
| Outbound Campaigns V1 | `@aws-sdk/client-connect-campaign` | `connect-campaigns:` | `connect-campaigns.{region}.amazonaws.com` |
| Outbound Campaigns V2 | `@aws-sdk/client-connect-campaign-v2` | `connect-campaigns:` | `connect-campaigns.{region}.amazonaws.com` |
| App Integrations | `@aws-sdk/client-appintegrations` | `app-integrations:` | `app-integrations.{region}.amazonaws.com` |

## Regional Availability

Amazon Connect is available in the following AWS regions:

- **Americas**: us-east-1, us-west-2, ca-central-1
- **Europe**: eu-west-2, eu-central-1
- **Asia Pacific**: ap-southeast-1, ap-southeast-2, ap-northeast-1, ap-northeast-2
- **Africa**: af-south-1 (limited — Outbound Campaigns V1 not available)
- **GovCloud**: us-gov-west-1

Endpoint format: `https://{service}.{region}.amazonaws.com`

## Authentication — SigV4

All Amazon Connect APIs use AWS Signature Version 4 for authentication. The SDK handles this automatically. The 6 common SigV4 parameters included in every request:

| Parameter | Description |
|---|---|
| `X-Amz-Algorithm` | Signing algorithm — always `AWS4-HMAC-SHA256` |
| `X-Amz-Credential` | Credential scope: `{AccessKeyId}/{date}/{region}/{service}/aws4_request` |
| `X-Amz-Date` | ISO 8601 UTC timestamp of the request |
| `X-Amz-Security-Token` | Session token (only when using temporary credentials from STS) |
| `X-Amz-Signature` | Computed HMAC-SHA256 signature over canonical request |
| `X-Amz-SignedHeaders` | Semicolon-separated list of headers included in the signature |

**The AWS SDK v3 handles all SigV4 signing automatically.** You never construct these parameters manually.

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';

// SDK handles SigV4 signing, credential refresh, and region endpoint resolution
const client = new ConnectClient({ region: 'us-east-1' });
```

## Common Errors

All Amazon Connect sub-services share these 14 common error responses:

| Error | HTTP Status | Description |
|---|---|---|
| `AccessDeniedException` | 403 | IAM policy denies the action or resource |
| `ExpiredTokenException` | 403 | Temporary security credentials have expired |
| `IncompleteSignature` | 403 | SigV4 signature is malformed or missing components |
| `InternalFailure` | 500 | Unexpected server-side error — safe to retry |
| `MalformedHttpRequestException` | 400 | Request body is not valid JSON or has structural errors |
| `NotAuthorized` | 401 | Caller identity could not be authenticated |
| `OptInRequired` | 403 | Account has not opted in to use the service |
| `RequestAbortedException` | 400 | Client closed the connection before the request completed |
| `RequestEntityTooLargeException` | 413 | Request body exceeds maximum size (typically 1MB) |
| `RequestTimeoutException` | 408 | Request took longer than the server-side timeout |
| `ServiceUnavailable` | 503 | Service is temporarily unavailable — retry with backoff |
| `ThrottlingException` | 400 | Request rate exceeded the per-account per-region limit |
| `UnknownOperationException` | 404 | The API action name does not exist |
| `UnrecognizedClientException` | 403 | AWS access key ID or security token is invalid |
| `ValidationError` | 400 | One or more request parameters failed validation |
| `ServiceQuotaExceededException` | 402 | Account has reached a service quota (e.g., max instances, max flows) |
| `ResourceConflictException` | 409 | Resource state conflicts with the request (e.g., concurrent update) |
| `IdempotencyException` | 409 | Request with same ClientToken but different parameters was already processed |

## Idempotency (ClientToken)

Some mutating APIs accept a `ClientToken` parameter for idempotency:
- If you retry a request with the same `ClientToken` and identical parameters, the API returns the original response without creating a duplicate resource
- If you reuse a `ClientToken` with different parameters, the API returns `IdempotencyException`
- Token validity: typically 24 hours
- Used in: `StartOutboundVoiceContact`, `StartChatContact`, `CreateContactFlow`, `PutDialRequestBatch`, and others
- Best practice: generate a UUID per logical operation, reuse on retries only

## Attachment File Types

Supported file types for attachments (chat, email, cases):
- Documents: PDF, DOC, DOCX, TXT, CSV, XLS, XLSX, PPT, PPTX
- Images: JPG, JPEG, PNG, GIF, BMP, HEIC
- Audio: WAV, MP3, MP4
- Other: ZIP
- Max file size: 100 MB (configurable per instance, default varies by feature)
- Presigned S3 URLs expire after the configured timeout — do not cache or share

## Best Practices

### Throttling

- Amazon Connect APIs return **HTTP 429** (or `ThrottlingException` with HTTP 400) when rate limits are exceeded.
- Rate limits are **per-account, per-region** — not per-user or per-client.
- Default rate limit for most APIs: **2 TPS** (transactions per second).
- Some APIs have higher limits: `GetMetricDataV2` (10 TPS), `SearchContacts` (10 TPS), `GetCurrentMetricData` (5 TPS).
- Metric APIs are the most commonly throttled due to dashboard polling.

### Retry Strategy

Use `EqualJitterBackoffStrategy` for retries — this adds randomized jitter to prevent thundering herd:

```typescript
import { ConnectClient } from '@aws-sdk/client-connect';

const client = new ConnectClient({
  region: 'us-east-1',
  maxAttempts: 3,
  retryStrategy: new (await import('@aws-sdk/util-retry')).ConfiguredRetryStrategy(
    3, // max attempts
    (attempt) => {
      const baseDelay = Math.min(1000 * Math.pow(2, attempt), 5000);
      const jitter = Math.random() * baseDelay;
      return baseDelay / 2 + jitter / 2; // equal jitter
    }
  ),
});
```

Key retry rules:
- Retry on `ThrottlingException`, `ServiceUnavailable`, `InternalFailure`, `RequestTimeoutException`.
- **Never retry** on `AccessDeniedException`, `ValidationError`, `UnknownOperationException`.
- Use 3 retries max with 1-5 second backoff range.

### Pagination

- Most List/Search APIs accept `maxResults` (default varies, max up to **1000** for some APIs).
- `nextToken` is returned when more results exist. Tokens expire after **24 hours**.
- **Prefer Search APIs over List+Describe patterns** — Search returns full objects in one call, List returns only ARNs/IDs requiring individual Describe calls.

```typescript
import { paginateSearchUsers } from '@aws-sdk/client-connect';

const users = [];
for await (const page of paginateSearchUsers({ client }, { InstanceId })) {
  users.push(...(page.Users ?? []));
}
```

### Eventual Consistency

Amazon Connect uses eventually consistent reads. After a Create/Update operation:
- Subsequent Get/Describe calls may return `ResourceNotFoundException` for a brief window.
- Strategy: retry with backoff for up to 5 seconds after resource creation.
- Tags applied via `TagResource` may take a few seconds to appear in `ListTagsForResource`.

```typescript
async function waitForResource<T>(
  fn: () => Promise<T>,
  maxAttempts = 5,
  delayMs = 1000
): Promise<T> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.name === 'ResourceNotFoundException' && i < maxAttempts - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
        continue;
      }
      throw err;
    }
  }
  throw new Error('Resource not found after max retries');
}
```

## Attachment Upload — 3-Step Process

File attachments (for chat, cases, email) use a 3-step process:

```typescript
import { ConnectClient, StartAttachedFileUploadCommand, CompleteAttachedFileUploadCommand } from '@aws-sdk/client-connect';

// Step 1: Start upload — returns presigned S3 URL
const startRes = await client.send(new StartAttachedFileUploadCommand({
  InstanceId: 'i-xxxx',
  AssociatedResourceArn: contactArn,
  FileName: 'document.pdf',
  FileSizeInBytes: fileBuffer.byteLength,
  FileUseCaseType: 'ATTACHMENT',
}));

const { FileArn, UploadUrlMetadata } = startRes;

// Step 2: PUT file to presigned S3 URL (up to 100MB)
await fetch(UploadUrlMetadata!.Url!, {
  method: 'PUT',
  headers: UploadUrlMetadata!.HeadersToInclude as Record<string, string>,
  body: fileBuffer,
});

// Step 3: Complete upload
await client.send(new CompleteAttachedFileUploadCommand({
  InstanceId: 'i-xxxx',
  AssociatedResourceArn: contactArn,
  FileArn: FileArn!,
}));
```

Maximum file size: **100MB**.

## Resource Integrations

### CloudFormation

Amazon Connect supports **21 CloudFormation resource types**:

- `AWS::Connect::Instance`, `AWS::Connect::InstanceStorageConfig`
- `AWS::Connect::ContactFlow`, `AWS::Connect::ContactFlowModule`
- `AWS::Connect::Queue`, `AWS::Connect::RoutingProfile`
- `AWS::Connect::User`, `AWS::Connect::UserHierarchyGroup`, `AWS::Connect::UserHierarchyStructure`
- `AWS::Connect::HoursOfOperation`, `AWS::Connect::PhoneNumber`
- `AWS::Connect::QuickConnect`, `AWS::Connect::SecurityProfile`
- `AWS::Connect::Rule`, `AWS::Connect::EvaluationForm`
- `AWS::Connect::View`, `AWS::Connect::ViewVersion`
- `AWS::Connect::Prompt`, `AWS::Connect::PredefinedAttribute`
- `AWS::Connect::AgentStatus`, `AWS::Connect::TrafficDistributionGroup`

### CloudTrail

All Amazon Connect API calls are logged to AWS CloudTrail. Every action across all 9 sub-services generates a CloudTrail event with:
- `eventSource`: e.g., `connect.amazonaws.com`
- `eventName`: the API action name
- `requestParameters` and `responseElements`: sanitized request/response

### EventBridge

Amazon Connect publishes events to Amazon EventBridge for:
- Contact events (initiated, connected, disconnected, missed, transferred)
- Agent events (login, logout, status change)
- Contact flow events
- Rule action executions
- Evaluation events

## SDK v3 Client Packages

All 8 client packages for JavaScript/TypeScript:

```bash
pnpm add @aws-sdk/client-connect
pnpm add @aws-sdk/client-connect-contact-lens
pnpm add @aws-sdk/client-customer-profiles
pnpm add @aws-sdk/client-connectcases
pnpm add @aws-sdk/client-qconnect
pnpm add @aws-sdk/client-connectparticipant
pnpm add @aws-sdk/client-connect-campaign
pnpm add @aws-sdk/client-connect-campaign-v2
```
