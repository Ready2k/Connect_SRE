# Amazon Connect Outbound Campaigns API Reference

The Outbound Campaigns API manages outbound contact campaigns for voice, email, SMS, and WhatsApp. There are two versions: **V1** (voice-only, legacy) and **V2** (multi-channel, current). Combined they include approximately **46+ actions** and **85 data types**.

**SDK Packages**:

```typescript
// V1 (legacy — voice only)
import { ConnectCampaignClient } from '@aws-sdk/client-connect-campaign';

// V2 (current — multi-channel)
import { ConnectCampaignV2Client } from '@aws-sdk/client-connect-campaign-v2';
```

> **Note**: V1 is not available in `af-south-1`. Use V2 for all new implementations.

## V1 API (~21 Actions)

V1 supports outbound voice campaigns only.

### Campaign Lifecycle

- `CreateCampaign` — create a voice campaign
- `DescribeCampaign` — get campaign details
- `UpdateCampaignName` — rename campaign
- `UpdateCampaignDialerConfig` — update dialer settings
- `UpdateCampaignOutboundCallConfig` — update caller ID and flow
- `DeleteCampaign` — delete a campaign
- `ListCampaigns` — list campaigns with filters
- `TagResource` / `UntagResource` / `ListTagsForResource` — manage tags

### Campaign State

- `GetCampaignState` — get current state of a single campaign
- `GetCampaignStateBatch` — get state of multiple campaigns (up to 25)
- `PauseCampaign` — pause a running campaign
- `ResumeCampaign` — resume a paused campaign
- `StartCampaign` — start a campaign
- `StopCampaign` — stop a running campaign

### Dial Requests

- `PutDialRequestBatch` — submit a batch of phone numbers to dial (up to 25 per batch)

### Instance Onboarding

- `StartInstanceOnboardingJob` — onboard a Connect instance for campaigns
- `GetConnectInstanceConfig` — get instance campaign config
- `GetInstanceOnboardingJobStatus` — check onboarding status
- `DeleteConnectInstanceConfig` — remove campaign config
- `DeleteInstanceOnboardingJob` — delete onboarding job

```typescript
import {
  ConnectCampaignClient,
  CreateCampaignCommand,
  PutDialRequestBatchCommand,
  StartCampaignCommand,
} from '@aws-sdk/client-connect-campaign';

const client = new ConnectCampaignClient({ region: 'us-east-1' });

// Create a campaign
const campaign = await client.send(new CreateCampaignCommand({
  name: 'appointment-reminders',
  connectInstanceId: 'instance-xxx',
  dialerConfig: {
    predictiveDailerConfig: {
      bandwidthAllocation: 1.0,
    },
  },
  outboundCallConfig: {
    connectContactFlowId: 'flow-xxx',
    connectSourcePhoneNumber: '+15551234567',
    connectQueueId: 'queue-xxx',
  },
}));

// Start the campaign
await client.send(new StartCampaignCommand({ id: campaign.id! }));

// Submit dial requests
await client.send(new PutDialRequestBatchCommand({
  id: campaign.id!,
  dialRequests: [
    {
      clientToken: 'unique-token-1',
      phoneNumber: '+15559876543',
      expirationTime: new Date(Date.now() + 3600000).toISOString(),
      attributes: { appointment_date: '2026-06-01', customer_name: 'Jane Smith' },
    },
    {
      clientToken: 'unique-token-2',
      phoneNumber: '+15551112222',
      expirationTime: new Date(Date.now() + 3600000).toISOString(),
      attributes: { appointment_date: '2026-06-02', customer_name: 'John Doe' },
    },
  ],
}));
```

### V1 Dialer Types

| Dialer | Use Case | Config |
|---|---|---|
| `predictiveDailerConfig` | High-volume outbound with ML-predicted connect rates | `bandwidthAllocation` (0.0-1.0) |
| `progressiveDailerConfig` | Dial one at a time per available agent | `bandwidthAllocation` (0.0-1.0) |
| `agentlessDialerConfig` | Automated calls without agents (IVR/voicemail) | `dialingCapacity` (optional) |

## V2 API (~25+ Actions)

V2 adds multi-channel support (voice, email, SMS, WhatsApp), communication limits, scheduling, and profile-based outbound.

### Campaign Lifecycle

- `CreateCampaign` — create a multi-channel campaign
- `GetCampaign` — get campaign details
- `UpdateCampaignName` — rename campaign
- `UpdateCampaignChannelSubtypeConfig` — update channel-specific settings
- `UpdateCampaignCommunicationTime` — update campaign schedule windows
- `UpdateCampaignCommunicationLimits` — set frequency caps
- `UpdateCampaignFlowAssociation` — update flow associations
- `UpdateCampaignSchedule` — update campaign schedule
- `UpdateCampaignSource` — update campaign source configuration
- `DeleteCampaign` — delete campaign
- `ListCampaigns` — list all campaigns

### Campaign State

- `GetCampaignState` — get current state
- `GetCampaignStateBatch` — get state for multiple campaigns
- `PauseCampaign` — pause
- `ResumeCampaign` — resume
- `StartCampaign` — start
- `StopCampaign` — stop

### Outbound Requests

- `PutOutboundRequestBatch` — submit outbound requests (voice/email/SMS/WhatsApp)
- `PutProfileOutboundRequestBatch` — submit requests using Customer Profile IDs instead of raw contact info

### Instance Onboarding

- `StartInstanceOnboardingJob` — onboard instance for V2 campaigns
- `GetConnectInstanceConfig` — get instance config
- `GetInstanceOnboardingJobStatus` — check onboarding status
- `DeleteConnectInstanceConfig` — remove config
- `DeleteInstanceOnboardingJob` — delete onboarding job

```typescript
import {
  ConnectCampaignV2Client,
  CreateCampaignCommand,
  PutOutboundRequestBatchCommand,
  PutProfileOutboundRequestBatchCommand,
} from '@aws-sdk/client-connect-campaign-v2';

const client = new ConnectCampaignV2Client({ region: 'us-east-1' });

// Create a multi-channel campaign
const campaign = await client.send(new CreateCampaignCommand({
  name: 'multi-channel-outreach',
  connectInstanceId: 'instance-xxx',
  channelSubtypeConfig: {
    telephony: {
      capacity: 1.0,
      outboundMode: {
        progressive: { bandwidthAllocation: 1.0 },
      },
      defaultOutboundConfig: {
        connectContactFlowId: 'flow-xxx',
        connectSourcePhoneNumber: '+15551234567',
        connectQueueId: 'queue-xxx',
      },
    },
    email: {
      capacity: 1.0,
      outboundMode: {
        agentless: {},
      },
      defaultOutboundConfig: {
        connectSourceEmailAddress: 'support@example.com',
        wisdomTemplateArn: 'arn:aws:wisdom:us-east-1:123:message-template/xxx',
      },
    },
    sms: {
      capacity: 1.0,
      outboundMode: {
        agentless: {},
      },
      defaultOutboundConfig: {
        connectSourcePhoneNumberArn: 'arn:aws:connect:us-east-1:123:phone-number/xxx',
        wisdomTemplateArn: 'arn:aws:wisdom:us-east-1:123:message-template/yyy',
      },
    },
  },
  communicationLimitsOverride: {
    allChannelSubtypes: {
      communicationLimitsList: [
        { maxCountPerRecipient: 3, frequency: 1, unit: 'DAY' },
        { maxCountPerRecipient: 10, frequency: 1, unit: 'WEEK' },
      ],
    },
  },
  schedule: {
    startTime: new Date('2026-06-01T09:00:00Z').toISOString(),
    endTime: new Date('2026-06-30T17:00:00Z').toISOString(),
    refreshFrequency: 'P1D', // ISO 8601 duration
  },
}));

// Submit outbound requests by channel
await client.send(new PutOutboundRequestBatchCommand({
  id: campaign.id!,
  outboundRequests: [
    {
      clientToken: 'req-1',
      channelSubtype: 'TELEPHONY',
      expirationTime: new Date(Date.now() + 86400000).toISOString(),
      customer: {
        phoneNumber: '+15559876543',
      },
      attributes: { customer_name: 'Jane Smith' },
    },
    {
      clientToken: 'req-2',
      channelSubtype: 'EMAIL',
      expirationTime: new Date(Date.now() + 86400000).toISOString(),
      customer: {
        emailAddress: 'jane@example.com',
      },
      attributes: { customer_name: 'Jane Smith' },
    },
  ],
}));

// Or use profile-based outbound (pulls contact info from Customer Profiles)
await client.send(new PutProfileOutboundRequestBatchCommand({
  id: campaign.id!,
  profileOutboundRequests: [
    {
      clientToken: 'profile-req-1',
      profileId: 'profile-xxx',
      expirationTime: new Date(Date.now() + 86400000).toISOString(),
    },
  ],
}));
```

### V2 Channel Subtypes

| Channel | Subtype Value | Required Config |
|---|---|---|
| Voice | `TELEPHONY` | `connectContactFlowId`, `connectSourcePhoneNumber`, `connectQueueId` |
| Email | `EMAIL` | `connectSourceEmailAddress`, `wisdomTemplateArn` |
| SMS | `SMS` | `connectSourcePhoneNumberArn`, `wisdomTemplateArn` |
| WhatsApp | `WHATSAPP` | `connectSourcePhoneNumberArn`, `wisdomTemplateArn` |

### V2 Communication Limits

V2 adds frequency caps to prevent over-contacting customers:

```typescript
interface CommunicationLimit {
  maxCountPerRecipient: number; // max attempts per recipient
  frequency: number; // time window value
  unit: 'DAY' | 'WEEK'; // time window unit
}
```

### V2 Scheduling

V2 campaigns support scheduled windows:

```typescript
interface Schedule {
  startTime: string; // ISO 8601
  endTime: string; // ISO 8601
  refreshFrequency?: string; // ISO 8601 duration (e.g., 'P1D' for daily)
}
```

## Campaign States

Both V1 and V2 share these campaign states:

| State | Description |
|---|---|
| `Initialized` | Campaign created but not started |
| `Running` | Campaign is actively dialing/sending |
| `Paused` | Campaign is paused (can be resumed) |
| `Stopped` | Campaign has been stopped |
| `Failed` | Campaign failed due to an error |
| `Completed` | All outbound requests have been processed |

## Key Data Types (Combined ~85)

### V1 Types

- **Campaign** — id, name, connectInstanceId, dialerConfig, outboundCallConfig
- **DialRequest** — clientToken, phoneNumber, expirationTime, attributes
- **DialerConfig** — predictive/progressive/agentless config union
- **OutboundCallConfig** — connectContactFlowId, connectSourcePhoneNumber, answerMachineDetectionConfig
- **CampaignSummary** — id, name, connectInstanceId, state

### V2 Types

- **Campaign** — id, name, connectInstanceId, channelSubtypeConfig, communicationLimitsOverride, schedule, source
- **OutboundRequest** — clientToken, channelSubtype, customer, expirationTime, attributes
- **ProfileOutboundRequest** — clientToken, profileId, expirationTime
- **ChannelSubtypeConfig** — telephony, email, sms, whatsapp channel configs
- **CommunicationLimitsConfig** — allChannelSubtypes limits list
- **SuccessfulRequest** / **FailedRequest** — batch response items

## Regional Availability

| Region | V1 | V2 |
|---|---|---|
| us-east-1 | Yes | Yes |
| us-west-2 | Yes | Yes |
| eu-west-2 | Yes | Yes |
| ap-southeast-2 | Yes | Yes |
| af-south-1 | **No** | Yes |
| All other Connect regions | Yes | Yes |
