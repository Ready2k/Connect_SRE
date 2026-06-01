# Voice Channel

Amazon Connect's voice channel provides cloud-based telephony with softphone and PSTN options, call recording, audio enhancement, and outbound calling capabilities.

## Softphone

The Connect softphone runs in the agent's browser via WebRTC. No physical hardware or PBX infrastructure required.

**Audio quality:**
- 16 kHz wideband audio (twice the sample rate of traditional 8 kHz telephony)
- Resistant to packet loss — maintains call quality even on imperfect network connections
- Agents only need a headset and a supported browser (Chrome, Firefox)

**Requirements:**
- Stable internet connection (minimum 100 Kbps per call)
- UDP port 3478 for TURN relay
- Agents set their phone type to "Softphone" in the Contact Control Panel (CCP)

**Softphone vs desk phone:**
- **Softphone** — WebRTC in browser, zero hardware, supports all CCP features natively (hold, transfer, conference). Audio quality is 16 kHz wideband. Requires stable internet.
- **Desk phone** — Agent receives calls on an external phone number (mobile or landline). Agent controls (hold, transfer) still happen in CCP but audio goes through PSTN. Useful when internet is unreliable or for remote agents without headsets. Configured per-agent in CCP settings by entering an external phone number.
- Agents can switch between softphone and desk phone at any time from the CCP settings — no admin intervention required.
- Desk phone calls incur additional PSTN telephony charges (outbound leg to the agent's phone number).

## PSTN Telephony

Connect supports traditional PSTN telephony for both inbound and outbound calls.

- Claim phone numbers (DID and toll-free) directly from the Connect console
- Port existing numbers to Connect
- Numbers available in 200+ countries and territories
- E.164 international format required for all phone numbers (e.g., `+14155551234`)

## Call Recording

Record calls for quality assurance, compliance, training, and dispute resolution. Recordings are stored in your designated S3 bucket.

**Recording modes:**
- **Agent only** — captures only the agent's audio channel
- **Customer only** — captures only the customer's audio channel
- **Agent and customer** — captures both channels (dual-channel recording)

**Dual-channel recording:**
- Each participant's audio is captured on a separate channel within the same file
- Channel 0 = agent audio, Channel 1 = customer audio
- Enables independent analysis of each speaker (critical for Contact Lens transcription accuracy)
- Required for accurate speaker separation in post-call analytics

**IVR / automated interaction recording:**
- The "Set recording and analytics behavior" block has a separate toggle for **Automated interaction call recording**
- When set to **On**, recording captures customer and IVR audio immediately — before any agent joins
- When set to **Off**, pauses any ongoing IVR recording
- Useful for compliance: capture what the customer said during self-service before agent pickup

**Storage:**
- Recordings are stored as WAV files in your configured S3 bucket
- S3 bucket must be in the same AWS region as your Connect instance
- Enable server-side encryption (SSE-S3 or SSE-KMS) for compliance
- Retention policies managed via S3 lifecycle rules
- Recording file path follows a predictable convention: `connect/<instance-id>/CallRecordings/<year>/<month>/<day>/<contactId>_<timestamp>.wav`

**Enabling recording:**
- Set the "Set recording and analytics behavior" block in the contact flow
- Recording starts when the agent picks up (not during IVR or queue) unless automated interaction recording is enabled
- Can be started, stopped, suspended, and resumed programmatically during a call
- For outbound calls, create an **outbound whisper flow** containing the "Set recording and analytics behavior" block and assign it to the queue used for outbound calls

**Screen recording:**
- Connect can capture agent screen activity alongside voice recording
- Configured in the same "Set recording and analytics behavior" block
- Screen recordings stored in the same S3 bucket as audio recordings
- Useful for quality management — supervisors see exactly what the agent did during the call

**Multi-party call recording:**
- When enhanced monitoring is enabled, calls can have up to 6 participants plus 2 supervisors
- Recording captures all participants on the call
- Contact Lens supports transcription for calls with up to 2 participants; disable Contact Lens for calls expected to have 3+ participants

**Recording APIs:**

| API | Purpose |
|-----|---------|
| `StartContactRecording` | Begin recording a live contact |
| `StopContactRecording` | Permanently stop recording — cannot be restarted after this call |
| `SuspendContactRecording` | Temporarily pause recording (e.g., while customer reads credit card number) |
| `ResumeContactRecording` | Resume a previously suspended recording |

**Example — suspend recording during sensitive data collection:**

```javascript
import { ConnectClient, SuspendContactRecordingCommand, ResumeContactRecordingCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

// Suspend before collecting PCI data
await client.send(new SuspendContactRecordingCommand({
  InstanceId: instanceId,
  ContactId: contactId,
  InitialContactId: initialContactId,
}));

// ... agent collects sensitive info ...

// Resume recording
await client.send(new ResumeContactRecordingCommand({
  InstanceId: instanceId,
  ContactId: contactId,
  InitialContactId: initialContactId,
}));
```

**Important behavioral notes:**
- `StopContactRecording` is final — once stopped, recording cannot be restarted for that contact
- `SuspendContactRecording` / `ResumeContactRecording` are the correct pair for temporary pauses
- If the contact disconnects while suspended, the partial recording is still saved to S3
- Recordings are available in the contact record after the call ends (not in real time)
- Security profile permissions must be assigned to managers so they can review recordings

## Audio Enhancement

Connect provides real-time audio processing to improve call quality. These features run server-side — no agent hardware changes required.

**Noise suppression:**
- Removes background noise from the agent's environment (keyboard clicks, office chatter, HVAC)
- Also applies to the customer's audio stream
- Enabled per-instance or per-contact-flow

**Voice isolation:**
- Advanced ML-based feature that isolates the primary speaker's voice
- Strips out competing voices and ambient sound more aggressively than basic noise suppression
- Particularly useful for work-from-home or open-office environments

**Agent control:**
- Agents can adjust audio enhancement settings during an active session from the CCP
- Toggle noise suppression on/off based on their current environment
- Changes take effect immediately without interrupting the call

## Outbound Calling

Place outbound calls from Connect for proactive outreach, callbacks, and follow-ups.

**Capabilities:**
- Call 200+ countries and destinations worldwide
- All numbers must be in E.164 format (e.g., `+442071234567` for UK)
- Outbound caller ID can be set per queue or per contact flow
- Supports both agent-initiated (manual dial from CCP) and API-initiated outbound calls

**Caller ID configuration:**
- Set the outbound caller ID number in the queue configuration under **Outbound caller ID number**
- Must be a number claimed in your Connect instance
- Can also be set dynamically in a contact flow using the "Set callback number" block
- Some countries require local presence — ensure compliance with local telecom regulations
- Caller ID cannot be spoofed — it must be a number you own in your Connect instance

**Outbound campaigns:**
- High-volume outbound dialing via Amazon Connect outbound campaigns
- Predictive, progressive, and agentless dialing modes
- Integrates with Amazon Pinpoint for customer segmentation
- **Predictive dialing** — system dials multiple numbers simultaneously, predicts agent availability, connects answered calls to agents
- **Progressive dialing** — dials one call per available agent, waits for answer before dialing next
- **Agentless dialing** — automated calls without agents (e.g., appointment reminders, notifications via Polly TTS)

**Emergency calling limitations:**
- Connect does **not** support 911/emergency calling
- Not a replacement for traditional phone service for emergency dialing
- Organizations must maintain alternative means for emergency calls

**StartOutboundVoiceContact API:**

```javascript
import { ConnectClient, StartOutboundVoiceContactCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

const response = await client.send(new StartOutboundVoiceContactCommand({
  InstanceId: instanceId,
  ContactFlowId: contactFlowId,
  DestinationPhoneNumber: "+14155551234",  // E.164 format required
  SourcePhoneNumber: "+18005551234",       // Must be claimed in your instance
  Attributes: {
    campaignId: "campaign-123",
    customerId: "cust-456",
  },
  // Optional: queue to associate the contact with
  QueueId: queueId,
}));

// response.ContactId — unique ID for this outbound contact
```

**StopContact API:**

```javascript
import { ConnectClient, StopContactCommand } from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

await client.send(new StopContactCommand({
  InstanceId: instanceId,
  ContactId: contactId,
}));
```

## DTMF Handling

Capture and process DTMF (touch-tone) input from callers during IVR interactions.

**Get customer input block:**
- Presents a prompt (TTS or audio file) and waits for DTMF or speech input
- Can route to an Amazon Lex bot for natural language understanding
- Configurable timeout for how long to wait for input (default 5 seconds)
- Supports terminator digit (e.g., `#`) to signal end of input

**Store customer input block:**
- Captures a sequence of DTMF digits (e.g., account number, PIN, credit card)
- Stores the input in a contact attribute for later use in the flow
- Configurable minimum and maximum digit count
- Supports encryption of sensitive input using a KMS key — digits are encrypted at entry and only decrypted by your backend Lambda
- Terminator digit configurable (default `#`)

**DTMF in Lex integration:**
- When using a Lex bot in a flow, DTMF digits are sent as text input to the bot
- Lex can interpret DTMF input as slot values (e.g., "press 1 for billing" maps digit `1` to the billing intent)

**DTMF during transfers:**
- Agents can send DTMF tones during external transfers (e.g., navigating a third-party IVR)
- Available in CCP when connected to an external number

## Call Quality Monitoring

Monitor the real-time quality of voice calls.

**Metrics available:**
- **MOS (Mean Opinion Score)** — estimated voice quality score (1.0–5.0, where 4.0+ is good)
- **Jitter** — variation in packet arrival time (measured in milliseconds)
- **Packet loss** — percentage of audio packets lost in transit
- **Round-trip time** — latency for audio packets between agent and Connect

**Softphone metrics:**
- Available via the Streams API for custom CCP implementations
- Metrics are collected from the WebRTC connection
- Can be logged to CloudWatch or a custom monitoring system
- Help diagnose agent connectivity issues (bad WiFi, VPN problems, etc.)

## Multi-Party Conferencing

Connect supports multi-party calls (conference calls) with up to 6 participants plus supervisor monitoring.

**Default (without enhanced monitoring):**
- 3 participants on a call (e.g., customer + agent + one additional party)
- 5 supervisors can monitor the call simultaneously

**With enhanced monitoring enabled:**
- Up to 6 participants on a call (customer + agent + 4 additional parties)
- 2 supervisors can monitor (silent monitor or barge-in)
- Participants can be other agents (via quick connects) or external phone numbers

**Adding participants:**
- Agents use quick connects in the CCP to add participants
- External parties added by dialing an external number
- Each added participant gets their own contact record

**Enabling:**
- Enable "Enhanced contact monitoring capabilities" in the Connect console under **Telephony**
- Only available in CCPv2 (URL: `https://<instance>.my.connect.aws/ccp-v2/`)

## Early Media Support

Early media allows the caller to hear audio before the call is fully connected (e.g., ringback tone, carrier announcements).

- Connect supports early media for outbound calls
- Agents hear carrier-side audio (busy signals, voicemail greetings, network announcements) before the far end answers
- Useful for agents to know whether the call was answered by a human or voicemail
- Enabled by default — no additional configuration required

## Whisper Flows

Whisper flows play a short message to either the agent or the customer (or both) at the moment they are connected, before they can hear each other.

**Agent whisper flow:**
- Plays a message only the agent can hear (customer cannot hear it)
- Use cases: announce the queue name, caller intent, VIP status, or any context the agent needs
- Example: "This is a billing call from a premium customer"
- Configured per-queue or per-contact-flow

**Customer whisper flow:**
- Plays a message only the customer can hear (agent cannot hear it)
- Use cases: "This call may be recorded for quality purposes" or "You are being connected to a billing specialist"
- Runs after the customer leaves the queue and before the agent whisper

**Configuration:**
- Set in queue settings under **Agent whisper flow** and **Customer whisper flow**
- Can also be set dynamically in the contact flow using "Set whisper flow" block
- Keep whisper messages short (2-5 seconds) — long whispers delay the conversation

## Hold Behavior and Music

**Placing on hold:**
- Agents can place a customer on hold from the CCP
- Customer hears hold music or a custom hold prompt
- Agent's microphone is muted while customer is on hold

**Hold flow:**
- Configure the customer's hold experience using the "Set hold flow" block in the contact flow
- Hold flows can play music, loop prompts, or provide estimated wait times
- Default hold music is provided by Connect; custom audio files (WAV/MP3) can be uploaded

**Customer queue flow:**
- Defines what the customer hears while waiting in queue (before agent pickup)
- Can play music, announce position in queue, offer callback option
- Configured per-queue or per-contact-flow

## Transfer Types

**Warm transfer (consultation):**
- Agent puts customer on hold, calls the transfer target, briefs them, then connects all parties
- Agent can drop off after introducing the customer
- Customer context (attributes, notes) carries over to the new agent

**Cold transfer (blind):**
- Agent transfers the customer directly to another queue, agent, or phone number without speaking to the target first
- Faster but no context handoff via voice — rely on contact attributes
- Customer may re-enter a queue and wait

**External transfer:**
- Transfer to an external phone number (outside Connect)
- Agent dials the external number, customer is connected to the external party
- Connect can still record the agent's side if recording is active
- Agent can remain on the call (conference) or drop off

**Quick connects:**
- Pre-configured transfer destinations (agents, queues, or phone numbers)
- Assigned to queues — agents see available quick connects in the CCP
- Three types: Agent, Queue, External phone number

## Contact Flow Integration

Voice-specific contact flow blocks:

| Block | Purpose |
|-------|---------|
| Set recording and analytics behavior | Enable/configure recording (voice, IVR, screen) |
| Set voice | Choose Amazon Polly voice for prompts (language, neural/standard) |
| Get customer input | DTMF or Lex bot input during IVR |
| Store customer input | Capture DTMF digits (e.g., account number) with optional encryption |
| Play prompt | Text-to-speech or audio file playback |
| Set hold flow | Define experience while customer is on hold |
| Set whisper flow | Define agent/customer whisper at connection time |
| Set callback number | Configure caller ID for outbound or callback |
| Start media streaming | Stream real-time audio via Kinesis Video Streams |
| Transfer to queue | Move contact to a different queue |
| Transfer to phone number | Transfer to an external phone number |

## Real-Time Audio Streaming

Stream live call audio to external services via Kinesis Video Streams (KVS).

- Use the "Start media streaming" block in the contact flow
- Audio delivered as PCM frames to a KVS stream
- Common use cases: real-time transcription, sentiment analysis, agent assist
- Each contact gets its own KVS stream with a predictable naming convention
- Stop streaming with the "Stop media streaming" block or when the contact ends

## Voice APIs Summary

| API | Purpose |
|-----|---------|
| `StartOutboundVoiceContact` | Initiate an outbound call programmatically |
| `StopContact` | End an active contact (voice, chat, or task) |
| `StartContactRecording` | Begin recording a live contact |
| `StopContactRecording` | Permanently stop recording |
| `SuspendContactRecording` | Temporarily pause recording |
| `ResumeContactRecording` | Resume a suspended recording |
| `MonitorContact` | Start silent monitoring of a live contact |
| `TransferContact` | Transfer a contact to another queue or agent |
| `CreateQuickConnect` | Create a quick connect entry for transfers |
| `StartContactStreaming` | Start real-time chat event streaming |

## Key Considerations

- **Encryption:** All voice traffic is encrypted in transit (TLS) and recordings can be encrypted at rest (S3 SSE)
- **Compliance:** Supports PCI DSS, HIPAA, SOC, and other compliance frameworks
- **Capacity:** No hard limit on concurrent calls — scales automatically
- **Latency:** Connect uses AWS global infrastructure; choose the region closest to your agents and customers
- **Emergency calling:** Connect does not support 911/emergency calling — not a replacement for traditional phone service in that regard
- **Bot analytics:** Enable "Bot Analytics and Transcripts" in the Connect console to get human-readable logs of DTMF menu and Lex bot interactions in the flow
- **Security profiles:** Assign recording review permissions to managers via security profiles so they can access past recordings
