# Amazon Connect Participant API Reference

The Participant API enables real-time interaction with active chat, task, and email contacts. Unlike other Connect APIs, it uses **ConnectionToken-based authentication** (not IAM SigV4). It includes **11 actions** and approximately **17 data types**.

**SDK Package**: `@aws-sdk/client-connectparticipant`

```typescript
import { ConnectParticipantClient } from '@aws-sdk/client-connectparticipant';
const client = new ConnectParticipantClient({ region: 'us-east-1' });
```

## Authentication — ConnectionToken

The Participant API does **not** use IAM credentials for most operations. Instead:

1. Use the Connect Service API `CreateParticipantConnection` (IAM-authenticated) to get a `ConnectionToken`.
2. Pass the `ConnectionToken` as a header (`X-Amz-Bearer`) in all subsequent Participant API calls.
3. The token is scoped to a single contact and expires when the contact ends.

```typescript
import { ConnectClient, CreateParticipantConnectionCommand } from '@aws-sdk/client-connect';
import { ConnectParticipantClient, SendMessageCommand } from '@aws-sdk/client-connectparticipant';

// Step 1: Get ConnectionToken via Connect Service API (IAM auth)
const connectClient = new ConnectClient({ region: 'us-east-1' });
const connection = await connectClient.send(new CreateParticipantConnectionCommand({
  ParticipantToken: participantToken, // from StartChatContact
  Type: ['CONNECTION_CREDENTIALS'],
}));

const connectionToken = connection.ConnectionCredentials!.ConnectionToken!;

// Step 2: Use ConnectionToken for Participant API calls (no IAM needed)
const participantClient = new ConnectParticipantClient({ region: 'us-east-1' });
```

## Actions

### CreateParticipantConnection

Establishes a connection for a participant. Returns WebSocket URL for real-time events and ConnectionToken for API calls.

```typescript
import { ConnectParticipantClient, CreateParticipantConnectionCommand } from '@aws-sdk/client-connectparticipant';

const response = await client.send(new CreateParticipantConnectionCommand({
  ParticipantToken: 'participant-token-from-start-chat', // from StartChatContact
  Type: ['WEBSOCKET', 'CONNECTION_CREDENTIALS'],
  ConnectParticipant: true,
}));

const wsUrl = response.Websocket?.Url; // WebSocket URL for real-time events
const token = response.ConnectionCredentials?.ConnectionToken; // for subsequent API calls
const expiry = response.ConnectionCredentials?.Expiry; // token expiration
```

### SendMessage

Send a text message in the chat.

```typescript
import { SendMessageCommand } from '@aws-sdk/client-connectparticipant';

const response = await client.send(new SendMessageCommand({
  ConnectionToken: connectionToken,
  ContentType: 'text/plain', // or 'text/markdown', 'application/json'
  Content: 'Hello, how can I help you today?',
}));

console.log('Message ID:', response.Id);
console.log('Absolute Time:', response.AbsoluteTime);
```

### SendEvent

Send a chat event (typing indicator, read receipt, etc.).

```typescript
import { SendEventCommand } from '@aws-sdk/client-connectparticipant';

// Send typing indicator
await client.send(new SendEventCommand({
  ConnectionToken: connectionToken,
  ContentType: 'application/vnd.amazonaws.connect.event.typing',
  Content: undefined,
}));

// Send read receipt
await client.send(new SendEventCommand({
  ConnectionToken: connectionToken,
  ContentType: 'application/vnd.amazonaws.connect.event.message.read',
  Content: JSON.stringify({ messageId: 'msg-xxx' }),
}));
```

Event content types:
- `application/vnd.amazonaws.connect.event.typing` — typing indicator
- `application/vnd.amazonaws.connect.event.message.read` — read receipt
- `application/vnd.amazonaws.connect.event.message.delivered` — delivery receipt
- `application/vnd.amazonaws.connect.event.participant.joined` — participant joined
- `application/vnd.amazonaws.connect.event.participant.left` — participant left
- `application/vnd.amazonaws.connect.event.transfer.succeeded` — transfer successful
- `application/vnd.amazonaws.connect.event.transfer.failed` — transfer failed
- `application/vnd.amazonaws.connect.event.chat.ended` — chat ended

### GetTranscript

Retrieve the chat transcript for the current contact.

```typescript
import { GetTranscriptCommand } from '@aws-sdk/client-connectparticipant';

const transcript = await client.send(new GetTranscriptCommand({
  ConnectionToken: connectionToken,
  MaxResults: 100,
  SortOrder: 'ASCENDING', // or 'DESCENDING'
  StartPosition: {
    AbsoluteTime: '2026-01-01T00:00:00.000Z', // optional: start from a specific time
  },
}));

for (const item of transcript.Transcript ?? []) {
  console.log(`[${item.ParticipantRole}] ${item.DisplayName}: ${item.Content}`);
  console.log(`  Type: ${item.Type}, Time: ${item.AbsoluteTime}`);
}
```

### GetAttachment

Get a download URL for a file attachment.

```typescript
import { GetAttachmentCommand } from '@aws-sdk/client-connectparticipant';

const attachment = await client.send(new GetAttachmentCommand({
  ConnectionToken: connectionToken,
  AttachmentId: 'attachment-xxx',
}));

console.log('Download URL:', attachment.Url);
console.log('URL Expiry:', attachment.UrlExpiry);
```

### StartAttachmentUpload

Start uploading a file attachment to the chat.

```typescript
import { StartAttachmentUploadCommand, CompleteAttachmentUploadCommand } from '@aws-sdk/client-connectparticipant';

// Step 1: Start upload
const startRes = await client.send(new StartAttachmentUploadCommand({
  ConnectionToken: connectionToken,
  ContentType: 'application/pdf',
  AttachmentName: 'invoice.pdf',
  AttachmentSizeInBytes: fileBuffer.byteLength,
}));

// Step 2: Upload to presigned URL
await fetch(startRes.UploadMetadata!.Url!, {
  method: 'PUT',
  headers: startRes.UploadMetadata!.HeadersToInclude as Record<string, string>,
  body: fileBuffer,
});

// Step 3: Complete upload
await client.send(new CompleteAttachmentUploadCommand({
  ConnectionToken: connectionToken,
  AttachmentIds: [startRes.AttachmentId!],
}));
```

### CompleteAttachmentUpload

Confirm that a file has been uploaded to the presigned URL. See `StartAttachmentUpload` above.

### DisconnectParticipant

Disconnect the participant from the chat.

```typescript
import { DisconnectParticipantCommand } from '@aws-sdk/client-connectparticipant';

await client.send(new DisconnectParticipantCommand({
  ConnectionToken: connectionToken,
}));
```

### DescribeView

Get details of an agent workspace view associated with the contact.

```typescript
import { DescribeViewCommand } from '@aws-sdk/client-connectparticipant';

const view = await client.send(new DescribeViewCommand({
  ConnectionToken: connectionToken,
  ViewToken: 'view-token-xxx',
}));

console.log('View:', view.View?.Name);
console.log('Content:', view.View?.Content);
```

### GetAuthenticationUrl

Get an authentication URL for customer identity verification during chat.

```typescript
import { GetAuthenticationUrlCommand } from '@aws-sdk/client-connectparticipant';

const authUrl = await client.send(new GetAuthenticationUrlCommand({
  ConnectionToken: connectionToken,
  RedirectUri: 'https://myapp.com/auth-callback',
  SessionId: 'session-xxx',
}));

console.log('Auth URL:', authUrl.AuthenticationUrl);
```

### CancelParticipantAuthentication

Cancel an in-progress authentication request.

```typescript
import { CancelParticipantAuthenticationCommand } from '@aws-sdk/client-connectparticipant';

await client.send(new CancelParticipantAuthenticationCommand({
  ConnectionToken: connectionToken,
  SessionId: 'session-xxx',
}));
```

## Key Data Types

### Item (Transcript Item)

```typescript
interface Item {
  AbsoluteTime: string; // ISO 8601
  Content?: string;
  ContentType: string;
  Id: string;
  Type: 'TYPING' | 'PARTICIPANT_JOINED' | 'PARTICIPANT_LEFT' | 'CHAT_ENDED' | 'TRANSFER_SUCCEEDED' | 'TRANSFER_FAILED' | 'MESSAGE' | 'EVENT' | 'ATTACHMENT' | 'CONNECTION_ACK' | 'MESSAGE_DELIVERED' | 'MESSAGE_READ';
  ParticipantId: string;
  DisplayName: string;
  ParticipantRole: 'AGENT' | 'CUSTOMER' | 'SYSTEM' | 'CUSTOM_BOT' | 'SUPERVISOR';
  Attachments?: AttachmentItem[];
  MessageMetadata?: MessageMetadata;
  RelatedContactId?: string;
  ContactId?: string;
}
```

### ConnectionCredentials

```typescript
interface ConnectionCredentials {
  ConnectionToken: string;
  Expiry: string; // ISO 8601 expiration time
}
```

### Websocket

```typescript
interface Websocket {
  Url: string; // wss:// URL for real-time events
  ConnectionExpiry: string;
}
```

### AttachmentItem

```typescript
interface AttachmentItem {
  ContentType: string;
  AttachmentId: string;
  AttachmentName: string;
  Status: 'APPROVED' | 'REJECTED' | 'IN_PROGRESS';
}
```

### UploadMetadata

```typescript
interface UploadMetadata {
  Url: string; // presigned S3 URL
  UrlExpiry: string;
  HeadersToInclude: Record<string, string>;
}
```

### View

```typescript
interface View {
  Id: string;
  Arn: string;
  Name: string;
  Version: number;
  Content?: ViewContent;
}
```

## WebSocket Events

After establishing a WebSocket connection via `CreateParticipantConnection`, you receive real-time events:

```typescript
const ws = new WebSocket(wsUrl);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.ContentType) {
    case 'application/vnd.amazonaws.connect.event.typing':
      console.log(`${data.DisplayName} is typing...`);
      break;
    case 'text/plain':
    case 'text/markdown':
      console.log(`[${data.ParticipantRole}] ${data.Content}`);
      break;
    case 'application/vnd.amazonaws.connect.event.chat.ended':
      console.log('Chat ended');
      ws.close();
      break;
  }
};

// Send heartbeat to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({
    topic: 'aws/heartbeat',
    content: { type: 'HeartbeatRequest' },
  }));
}, 30000);
```
