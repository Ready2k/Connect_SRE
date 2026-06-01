# Web, In-App, and Video Calling

Amazon Connect supports in-app calling, web-based calling, and video calling. Customers initiate contact from within your application or website without switching to a phone -- and you can pass contextual data to Connect so agents already know who the customer is.

## Overview

This channel eliminates the friction of traditional phone support. Instead of a customer calling a 1-800 number and navigating an IVR, they tap a button inside your app or website and are connected directly to an agent with full context.

**Key benefits:**
- Customer never leaves your app or website
- Contextual information (logged-in user, current page, cart contents, session data) is passed to Connect automatically
- No re-identification needed -- the agent knows who the customer is before they speak
- WebRTC-based -- works in modern browsers and mobile apps without plugins
- Supports voice, video, and screen sharing in a single session

---

## In-App Calling

Embed calling directly into your iOS, Android, or web application.

**How it works:**
1. Customer taps "Call Support" in your app
2. Your app calls the `StartWebRTCContact` API with contextual attributes
3. Connect creates a contact and routes it through a contact flow
4. The agent receives the call with all context (customer name, account, current screen, etc.)
5. Voice (and optionally video) is established via WebRTC

**Contextual data flow:**
- Your app passes attributes at call initiation (user ID, order number, page URL, error codes)
- Contact flow receives these as contact attributes
- Agent sees them in the CCP before accepting the call
- No IVR prompts needed -- "What's your account number?" becomes unnecessary

**Mobile SDKs:**
- iOS: Amazon Connect Participant SDK for iOS
- Android: Amazon Connect Participant SDK for Android
- Both SDKs handle WebRTC negotiation, ICE candidates, audio/video streams
- Web SDK also works in mobile browsers for cross-platform support

---

## Web Calling -- Communications Widget

For websites, Connect provides the same hosted communications widget used for chat, extended with voice and video capabilities.

**Setup:**
- Enable voice/video in the communications widget configuration
- Same short JavaScript snippet as chat -- add calling with minimal code changes
- Widget handles the WebRTC connection, UI controls, mute/unmute, video toggle

**Widget capabilities:**
- Voice calling from the browser
- Video calling (customer and agent)
- Seamless escalation from chat to voice/video within the same widget
- Customer does not need to install anything -- works in Chrome, Firefox, Edge, Safari

**Widget limit:** 20 communications widgets per instance

**Embedding:**

```html
<script type="text/javascript">
  (function(w, d, x, id){
    s=d.createElement('script');
    s.src='https://d3xxxxxxxxxxxx.cloudfront.net/amazon-connect-chat-interface-client.js';
    s.async=1;
    s.id=id;
    d.getElementsByTagName('head')[0].appendChild(s);
    w[x] = w[x] || function() { (w[x].ac = w[x].ac || []).push(arguments) };
  })(window, document, 'amazon_connect', 'amazon-connect-widget');

  amazon_connect('snippetId', 'YOUR_SNIPPET_ID');
  amazon_connect('supportedMessagingContentTypes', [
    'text/plain',
    'text/markdown',
    'application/vnd.amazonaws.connect.message.interactive',
  ]);
</script>
```

---

## StartWebRTCContact API

The primary API for initiating in-app and web-based calls. Places an inbound in-app, web, or video call to a contact, then initiates the flow specified by `ContactFlowId`.

### Request

```
PUT /contact/webrtc HTTP/1.1
Content-type: application/json
```

```javascript
import { ConnectClient, StartWebRTCContactCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

const response = await client.send(new StartWebRTCContactCommand({
  // Required
  InstanceId: instanceId,
  ContactFlowId: contactFlowId,
  ParticipantDetails: {
    DisplayName: "Jane Customer",
  },
  // Optional: contextual data from your app
  Attributes: {
    customerId: "CUST-12345",
    currentPage: "/orders/789",
    accountTier: "Premium",
    deviceType: "iOS",
    appVersion: "3.2.1",
    sessionId: "sess-abc-def",
  },
  // Optional: enable video and screen sharing
  AllowedCapabilities: {
    Customer: {
      Video: "SEND",        // Customer can send video
      ScreenShare: "SEND",  // Customer can share screen
    },
    Agent: {
      Video: "SEND",        // Agent can send video
      ScreenShare: "SEND",  // Agent can share screen
    },
  },
  // Optional: related contact for context continuity
  RelatedContactId: relatedContactId,
  // Optional: references (links, metadata)
  References: {
    "OrderLink": {
      Type: "URL",
      Value: "https://app.example.com/orders/789",
    },
  },
  // Optional: description shown to agent
  Description: "Customer calling from billing page about order #789",
  // Optional: idempotency token (valid for 7 days)
  ClientToken: "unique-token-123",
}));
```

### Request Parameters

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `InstanceId` | String | Yes | 1-100 chars | Connect instance ID |
| `ContactFlowId` | String | Yes | Max 500 chars | Contact flow ARN or ID |
| `ParticipantDetails` | Object | Yes | -- | Customer details (DisplayName) |
| `Attributes` | Map | No | Up to 32,768 UTF-8 bytes total; keys: alphanumeric, `-`, `_`; key max 32,767 chars; value max 32,767 chars | Custom key-value pairs accessible in flows |
| `AllowedCapabilities` | Object | No | -- | Video and screen sharing capabilities for Customer and Agent |
| `References` | Map | No | Key max 4,096 chars; types: URL, NUMBER, STRING, DATE, EMAIL | Links and metadata shown in CCP |
| `RelatedContactId` | String | No | 1-256 chars | Related contact for context |
| `Description` | String | No | 0-4,096 chars | Description shown to agent |
| `ClientToken` | String | No | Max 500 chars | Idempotency token (valid 7 days) |

### AllowedCapabilities Values

For both `Customer` and `Agent`:
- `Video`: `"SEND"` to enable video sending
- `ScreenShare`: `"SEND"` to enable screen sharing

### Response

```javascript
{
  ContactId: "string",           // Unique contact ID (1-256 chars)
  ParticipantId: "string",       // Customer participant ID (1-256 chars)
  ParticipantToken: "string",    // Token for CreateParticipantConnection (1-1000 chars)
  ConnectionData: {
    Meeting: {
      MeetingId: "string",
      MediaRegion: "string",
      MediaPlacement: {
        AudioHostUrl: "string",
        AudioFallbackUrl: "string",
        SignalingUrl: "string",
        TurnControlUrl: "string",
        EventIngestionUrl: "string",
      },
      MeetingFeatures: {
        Audio: {
          EchoReduction: "string",
        },
      },
    },
    Attendee: {
      AttendeeId: "string",
      JoinToken: "string",
    },
  },
}
```

**ConnectionData** contains:
- **Meeting** -- media placement URLs (audio host, fallback, signaling, TURN control, event ingestion), media region, echo reduction settings
- **Attendee** -- attendee ID and join token for the WebRTC session
- **ParticipantToken** -- used by the customer to call `CreateParticipantConnection` API; valid for the lifetime of the contact participant

### Error Codes

| Error | HTTP Code | Description |
|-------|-----------|-------------|
| `InternalServiceException` | 500 | Service processing failure |
| `InvalidParameterException` | 400 | Invalid parameter values |
| `InvalidRequestException` | 400 | Invalid request structure |
| `LimitExceededException` | 429 | Resource limit exceeded |
| `ResourceNotFoundException` | 404 | Instance or flow not found |

---

## Establishing the WebRTC Connection (Client-Side)

After receiving the response from `StartWebRTCContact`:

```javascript
// Use the ConnectionData to establish the WebRTC session
const peerConnection = new RTCPeerConnection({
  iceServers: connectionData.IceServers.map(server => ({
    urls: server.Urls,
    username: server.Username,
    credential: server.Password,
  })),
});

// Add local audio (and video if enabled)
const localStream = await navigator.mediaDevices.getUserMedia({
  audio: true,
  video: true, // set to false for voice-only
});
localStream.getTracks().forEach(track => {
  peerConnection.addTrack(track, localStream);
});

// Handle remote stream (agent's audio/video)
peerConnection.ontrack = (event) => {
  const remoteVideo = document.getElementById('remote-video');
  remoteVideo.srcObject = event.streams[0];
};

// ICE candidate exchange via Connect signaling channel
// ... (handled by the Connect Participant SDK in production)
```

**Note:** In production, use the Amazon Connect Participant SDK which handles ICE negotiation, SDP exchange, and session management automatically.

---

## Video Calling

Video extends the voice channel with face-to-face interaction.

**Capabilities:**
- Two-way video between customer and agent
- Customer and agent can independently toggle video on/off during the call
- Video is optional -- either party can participate with voice-only
- Video quality adapts to available bandwidth
- Controlled via `AllowedCapabilities` in the `StartWebRTCContact` API

**Use cases:**
- Technical support with visual troubleshooting ("show me what you see")
- Identity verification (document review via camera)
- Healthcare telehealth consultations
- Financial advisory meetings
- Insurance claims -- customer shows damage via video

**Agent experience:**
- Agent sees the customer's video feed in the CCP (if the customer enables video)
- Agent can toggle their own camera on/off
- Video does not affect voice quality -- they run on separate media tracks
- Agent can handle video calls alongside other contact types per routing profile

---

## Screen Sharing

Share screens during a call for collaborative troubleshooting and guided walkthroughs.

**Capabilities:**
- Agent shares their screen with the customer (guided walkthrough)
- Customer shares their screen with the agent (troubleshooting)
- Selective sharing -- share entire screen, specific window, or browser tab
- Screen share can be started and stopped during the call without disconnecting
- Controlled via `AllowedCapabilities.ScreenShare` in the API

**Use cases:**
- Agent walks customer through a form or application step-by-step
- Customer shows agent an error message or confusing UI element
- Agent demonstrates how to navigate a portal or complete a process
- Technical support for software configuration

**Privacy and security:**
- Screen sharing requires explicit consent from the sharing party
- The browser prompts to select what to share (screen, window, or tab)
- Sharing can be stopped at any time by either party
- Screen share data is encrypted in transit via DTLS-SRTP (same as WebRTC media)

---

## Architecture

```
Customer App/Website
    |
    |-- StartWebRTCContact API --> Amazon Connect
    |                                   |
    |-- WebRTC (STUN/TURN) -----------> Contact Flow
    |   (audio + video + screen)        |
    |                                   +--> Queue --> Agent CCP
    |                                   |
    |                                   +--> Contact Record (CTR)
    |
    +-- Context Attributes -----------> Agent sees customer info
        (userId, page, session)         before answering
```

**Connection flow:**
1. Client app calls `StartWebRTCContact` API
2. Connect returns `ConnectionData` with Meeting/Attendee info and `ParticipantToken`
3. Client uses `ParticipantToken` to call `CreateParticipantConnection` (Participant Service API)
4. WebRTC session is established using MediaPlacement URLs (signaling, TURN control, audio host)
5. Contact flows through the specified ContactFlowId
6. Agent receives the contact in CCP with all passed attributes

---

## Contact Flow Integration

Web/video contacts flow through standard Connect contact flows with additional capabilities.

| Block | Purpose |
|-------|---------|
| Check contact attributes | Branch on contextual data passed from the app (e.g., accountTier, deviceType) |
| Set contact attributes | Enrich with additional data from Lambda or flow logic |
| Transfer to queue | Route based on context (Premium customers to specialized queue) |
| Play prompt | Audio prompts play to the customer while waiting |
| Get customer input | DTMF or Lex interaction (voice-only, not video-specific) |

**Context-based routing example:**
- Customer calls from the billing page of your app
- `currentPage` attribute is `/billing`
- Contact flow checks this attribute and routes directly to the billing queue
- Agent receives the call with billing context -- no "How can I help you?" needed

---

## Routing Behavior

- Web/video contacts are routed through the same routing profiles as voice
- They consume a voice slot in the agent's concurrency configuration
- Priority and queue delay settings apply
- Agents can receive web calls mixed with PSTN calls based on queue membership
- Video capability does not affect routing -- it is an optional media upgrade during the call

---

## Network Requirements

| Requirement | Specification |
|-------------|---------------|
| Voice bandwidth | ~100 Kbps |
| Video bandwidth | 300 Kbps - 1.5 Mbps depending on quality |
| Protocol | WebRTC (UDP preferred) |
| NAT traversal | TURN servers handle NAT traversal |
| Required port | UDP 3478 for STUN/TURN |
| Encryption (media) | DTLS-SRTP |
| Encryption (signaling) | TLS |

---

## Browser Compatibility

WebRTC requires modern browsers:
- Chrome (latest)
- Firefox (latest)
- Edge (latest)
- Safari (latest)

Mobile browsers also supported via the web SDK. Native SDKs available for iOS and Android.

---

## Key Considerations

- **Browser support:** WebRTC requires Chrome, Firefox, Edge, or Safari (latest versions)
- **Bandwidth:** Voice requires ~100 Kbps; video requires 300 Kbps-1.5 Mbps depending on quality
- **Firewall/NAT:** TURN servers handle NAT traversal; ensure UDP 3478 is open
- **Mobile:** Native SDKs handle WebRTC complexity; web SDK works in mobile browsers
- **Recording:** WebRTC calls can be recorded same as PSTN calls (audio only -- video is not recorded)
- **Encryption:** All WebRTC media encrypted with DTLS-SRTP; signaling encrypted with TLS
- **Fallback:** If WebRTC fails (bad network), consider offering a callback on PSTN as fallback
- **No emergency calling:** WebRTC calls do not support 911/emergency services
- **Concurrent sessions:** Each WebRTC session consumes resources; monitor CloudWatch metrics for capacity
- **Contact Lens:** Real-time and post-contact analytics apply to WebRTC voice (transcription, sentiment, etc.)
- **Multi-party:** When enhanced monitoring is enabled, voice supports up to 6 participants; 2 supervisors can monitor
- **Idempotency:** `ClientToken` ensures retries are safe; valid for 7 days after creation
- **Widget limit:** Maximum 20 communications widgets per instance
