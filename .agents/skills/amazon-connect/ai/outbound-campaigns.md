# Amazon Connect Outbound Campaigns

## Overview

Amazon Connect Outbound Campaigns enables high-volume outbound customer contact at scale -- capable of millions of contacts per day. It supports predictive, progressive, and agentless dialing modes across voice, email, SMS, and WhatsApp channels.

Two API versions exist:

- **Campaigns V1** -- original API, voice-only
- **Campaigns V2** -- current API, multi-channel support, enhanced scheduling and priority features

Use Campaigns V2 for all new implementations.

---

## Predictive Dialer

### ML-Powered Answering Machine Detection (AMD)

The predictive dialer uses machine learning to detect whether a human or answering machine answered the call, enabling agents to skip voicemails and connect only with live customers.

### AnsweringMachineDetectionStatus Values

12 possible detection statuses:

| Status | Description |
|--------|-------------|
| `HUMAN_ANSWERED` | A human picked up the call |
| `VOICEMAIL_BEEP` | Answering machine detected, beep tone heard (can leave message) |
| `VOICEMAIL_NO_BEEP` | Answering machine detected, no beep (greeting still playing or no beep machine) |
| `AMD_UNANSWERED` | Call was not answered within the detection window |
| `AMD_UNRESOLVED` | Detection could not determine human vs. machine |
| `AMD_NOT_APPLICABLE` | AMD was not enabled for this call |
| `SIT_TONE_DETECTED` | Special Information Tone detected (number disconnected, changed, etc.) |
| `SIT_TONE_BUSY` | SIT tone indicating the line is busy |
| `SIT_TONE_INVALID_NUMBER` | SIT tone indicating the number is invalid |
| `SIT_TONE_VACANT` | SIT tone indicating the number is vacant/disconnected |
| `FAX_MACHINE_DETECTED` | Fax machine tones detected |
| `AMD_ERROR` | An error occurred during detection |

### Dialing Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Predictive** | ML model predicts agent availability and dials ahead; optimizes for minimal agent idle time | High-volume sales, collections |
| **Progressive** | Dials one call per available agent; no risk of abandoned calls | Compliance-sensitive campaigns |
| **Agentless** | No agent involvement; plays a message or triggers a flow | Appointment reminders, notifications |

---

## Contact Priority Ordering

Campaigns V2 supports prioritizing which contacts to dial first based on customer profile attributes:

- Up to **10 profile attributes** can be used for priority ordering
- Attributes are evaluated in order (first attribute is highest priority)
- Supports ascending and descending sort per attribute
- Examples: prioritize by account value, days past due, last contact date, VIP status

```javascript
const { ConnectCampaignsV2Client, CreateCampaignCommand } = require("@aws-sdk/client-connectcampaignsv2");

const client = new ConnectCampaignsV2Client({ region: "us-east-1" });

await client.send(new CreateCampaignCommand({
  name: "CollectionsCampaign",
  connectInstanceId: "instance-id",
  channelSubtypeConfig: {
    telephony: {
      capacity: 1.0,
      outboundMode: {
        predictive: {}
      },
      defaultOutboundConfig: {
        connectContactFlowId: "flow-arn",
        connectSourcePhoneNumber: "+15551234567",
        answerMachineDetectionConfig: {
          enableAnswerMachineDetection: true,
          awaitAnswerMachinePrompt: false
        }
      }
    }
  },
  connectCampaignFlowArn: "campaign-flow-arn",
  schedule: {
    startTime: "2024-01-15T09:00:00Z",
    endTime: "2024-01-15T17:00:00Z",
    refreshFrequency: "PT1H"
  },
  source: {
    customerProfilesSegmentArn: "segment-arn"
  },
  communicationTimeConfig: {
    telephony: {
      openHours: {
        dailyHours: {
          MONDAY: [{ startTime: "09:00", endTime: "17:00" }],
          TUESDAY: [{ startTime: "09:00", endTime: "17:00" }],
          WEDNESDAY: [{ startTime: "09:00", endTime: "17:00" }],
          THURSDAY: [{ startTime: "09:00", endTime: "17:00" }],
          FRIDAY: [{ startTime: "09:00", endTime: "17:00" }]
        }
      },
      restrictedPeriods: {
        restrictedPeriodList: [
          { name: "NewYears", startDate: "2024-01-01", endDate: "2024-01-01" }
        ]
      }
    }
  }
}));
```

---

## Segment Refresh

- Campaign contact lists are sourced from **Customer Profiles segments**
- Segments refresh on an **hourly** cadence (previously 24-hour minimum)
- Newly qualifying contacts are added to the campaign automatically
- Contacts that no longer match the segment criteria are removed
- Manual refresh can be triggered via the API

---

## Multi-Contact Time Zone Detection

The system automatically detects contact time zones and enforces calling windows:

- Uses the contact's phone number area code and/or address to determine time zone
- Respects per-time-zone calling windows (e.g., only dial 9 AM - 9 PM in the contact's local time)
- Handles contacts spanning multiple time zones within a single campaign
- Compliant with TCPA and similar regulations that restrict calling hours

---

## Channel Subtypes (V2)

Campaigns V2 supports four channel subtypes:

### Voice

Traditional outbound phone calls with predictive/progressive/agentless dialing:

```javascript
channelSubtypeConfig: {
  telephony: {
    capacity: 1.0,
    outboundMode: { predictive: {} },
    defaultOutboundConfig: {
      connectContactFlowId: "flow-arn",
      connectSourcePhoneNumber: "+15551234567",
      answerMachineDetectionConfig: {
        enableAnswerMachineDetection: true
      }
    }
  }
}
```

### Email

Outbound email campaigns:

```javascript
channelSubtypeConfig: {
  email: {
    capacity: 5.0,  // Agents can handle multiple emails simultaneously
    outboundMode: { agentless: {} },
    defaultOutboundConfig: {
      connectSourceEmailAddress: "support@example.com",
      wisdomTemplateArn: "template-arn"  // Q Connect message template
    }
  }
}
```

### SMS

Text message campaigns:

```javascript
channelSubtypeConfig: {
  sms: {
    capacity: 5.0,
    outboundMode: { agentless: {} },
    defaultOutboundConfig: {
      connectSourcePhoneNumber: "+15551234567",
      wisdomTemplateArn: "template-arn"
    }
  }
}
```

### WhatsApp

WhatsApp Business messaging:

```javascript
channelSubtypeConfig: {
  whatsApp: {
    capacity: 5.0,
    outboundMode: { agentless: {} },
    defaultOutboundConfig: {
      connectSourcePhoneNumber: "+15551234567",
      wisdomTemplateArn: "template-arn"
    }
  }
}
```

---

## Batch Dial Requests

### PutDialRequestBatch (V1 -- Voice Only)

```javascript
const { ConnectCampaignsClient, PutDialRequestBatchCommand } = require("@aws-sdk/client-connectcampaigns");

const client = new ConnectCampaignsClient({ region: "us-east-1" });

await client.send(new PutDialRequestBatchCommand({
  id: "campaign-id",
  dialRequests: [
    {
      clientToken: "unique-token-1",
      phoneNumber: "+15551234567",
      expirationTime: "2024-01-15T23:59:59Z",
      attributes: {
        customerName: "Jane Smith",
        accountNumber: "12345"
      }
    },
    {
      clientToken: "unique-token-2",
      phoneNumber: "+15559876543",
      expirationTime: "2024-01-15T23:59:59Z",
      attributes: {
        customerName: "John Doe",
        accountNumber: "67890"
      }
    }
  ]
}));
```

### PutOutboundRequestBatch (V2 -- Multi-Channel)

```javascript
const { ConnectCampaignsV2Client, PutOutboundRequestBatchCommand } = require("@aws-sdk/client-connectcampaignsv2");

const client = new ConnectCampaignsV2Client({ region: "us-east-1" });

await client.send(new PutOutboundRequestBatchCommand({
  id: "campaign-id",
  outboundRequests: [
    {
      clientToken: "unique-token-1",
      channelSubtype: "TELEPHONY",  // or "EMAIL", "SMS", "WHATSAPP"
      expirationTime: "2024-01-15T23:59:59Z",
      channelSubtypeParameters: {
        telephony: {
          destinationPhoneNumber: "+15551234567",
          attributes: {
            customerName: "Jane Smith"
          },
          connectSourcePhoneNumber: "+15550001111"
        }
      }
    }
  ]
}));
```

---

## Communication Limits

Prevent over-contacting customers:

```javascript
communicationLimitsOverride: {
  allChannelSubtypes: {
    communicationLimitsList: [
      {
        maxCountPerRecipient: 3,
        frequency: 1,
        unit: "DAY"  // DAY or WEEK
      }
    ]
  }
}
```

- Limits apply per recipient across all channels or per channel subtype
- Configurable per day or per week
- System enforces limits automatically -- contacts exceeding the limit are skipped
- Override at the campaign level or set instance-wide defaults

---

## Scheduling

Campaign scheduling controls when the campaign is active:

```javascript
schedule: {
  startTime: "2024-01-15T09:00:00Z",
  endTime: "2024-03-15T17:00:00Z",
  refreshFrequency: "PT1H"  // ISO 8601 duration -- how often to refresh the contact segment
}
```

- **Start/end time** -- overall campaign window
- **Refresh frequency** -- how often to pull new contacts from the segment (minimum `PT1H`)
- **Open hours** -- per-day calling windows (see `communicationTimeConfig` above)
- **Restricted periods** -- blackout dates (holidays, maintenance windows)
- **Time zone aware** -- all scheduling respects the contact's local time zone

---

## Key API Operations

### Campaigns V2

| Operation | Description |
|-----------|-------------|
| `CreateCampaign` | Create a new outbound campaign |
| `UpdateCampaignChannelSubtypeConfig` | Update channel configuration |
| `UpdateCampaignSchedule` | Modify campaign schedule |
| `UpdateCampaignCommunicationTime` | Update calling windows |
| `UpdateCampaignCommunicationLimits` | Update contact frequency limits |
| `UpdateCampaignSource` | Change the contact segment source |
| `PutOutboundRequestBatch` | Submit contacts for outbound delivery |
| `StartCampaign` | Start a paused/created campaign |
| `PauseCampaign` | Pause a running campaign |
| `StopCampaign` | Stop a campaign permanently |
| `DeleteCampaign` | Delete a campaign |
| `GetCampaignState` | Check campaign status |
| `ListCampaigns` | List campaigns with filtering |

---

## Prerequisites

Before creating outbound campaigns, ensure the following are in place:

1. **KMS Key** -- create a symmetric KMS key for campaign data encryption. The key policy must grant `connect-campaigns.amazonaws.com` access to `kms:Encrypt`, `kms:Decrypt`, and `kms:GenerateDataKey`.

2. **Outbound Calling Enabled** -- in the Amazon Connect console, enable outbound calling on the instance under Telephony options.

3. **Customer Profiles Domain** -- a Customer Profiles domain must be configured and linked to the Connect instance. Campaign contact lists are sourced from Customer Profiles segments.

4. **Phone Number with Outbound Capability** -- claim or port a phone number with outbound calling capability. The number must be associated with the Connect instance and will serve as the caller ID.

5. **Service-Linked Role** -- the `AWSServiceRoleForConnectCampaignsV2` service-linked role is created automatically when you first use the service. Ensure your IAM policies do not block its creation.

---

## Multi-Step Journeys

A journey is a sequence of campaign steps that orchestrate outreach across multiple channels and time intervals.

### Journey Flow Blocks

| Block | Description |
|-------|-------------|
| **Wait** | Pause for a specified duration before the next step |
| **Branch** | Conditional logic based on previous step outcome (e.g., answered vs. not answered) |
| **Send** | Execute an outreach action on a specific channel (voice, SMS, email) |
| **End** | Terminate the journey for this contact |

### How It Works

- Each step in the journey can use a different channel and timing
- Branch blocks evaluate the result of the previous step to decide the next path
- Wait blocks introduce delays between steps (hours or days)
- Contacts exit the journey when they reach an End block or when communication limits are hit

### Example: Multi-Day Outreach Sequence

```
Day 1: Send email (payment reminder)
  └─ Wait 2 days
Day 3: Branch -- did customer open email?
  ├─ Yes → End (no further action)
  └─ No → Send SMS (brief reminder with link)
       └─ Wait 4 days
Day 7: Branch -- did customer respond to SMS?
  ├─ Yes → End
  └─ No → Send voice call (agent-assisted follow-up)
       └─ End
```

This approach increases contact rates while respecting customer preferences and avoiding over-contact.

---

## Event Triggers

Campaigns can be triggered automatically by EventBridge events rather than running on a fixed schedule.

### Event Sources

- **Customer Profiles segment membership changes** -- when a customer enters or exits a segment (e.g., account becomes past due)
- **External events** -- custom events published to EventBridge from your applications

### Configuration

```javascript
const { ConnectCampaignsV2Client, CreateCampaignCommand } = require("@aws-sdk/client-connectcampaignsv2");

const client = new ConnectCampaignsV2Client({ region: "us-east-1" });

await client.send(new CreateCampaignCommand({
  name: "SegmentTriggeredCampaign",
  connectInstanceId: "instance-id",
  channelSubtypeConfig: {
    telephony: {
      capacity: 1.0,
      outboundMode: { progressive: {} },
      defaultOutboundConfig: {
        connectContactFlowId: "flow-arn",
        connectSourcePhoneNumber: "+15551234567"
      }
    }
  },
  connectCampaignFlowArn: "campaign-flow-arn",
  source: {
    eventTrigger: {
      customerProfilesDomainArn: "domain-arn"
    }
  }
}));
```

### Use Cases

- Trigger a welcome call when a new customer profile is created
- Send a retention offer when a customer enters an at-risk segment
- Initiate a survey after a service interaction is completed

---

## Campaign Metrics

### Key Performance Indicators

| Metric | Description |
|--------|-------------|
| **Dial rate** | Number of dial attempts per unit time |
| **Completion rate** | Percentage of contacts in the list that were attempted |
| **Connect rate** | Percentage of dial attempts that resulted in a connection (human or machine) |
| **Right party contact rate** | Percentage of calls where the intended person was reached |
| **Abandon rate** | Percentage of connected calls where no agent was available (predictive mode) |

### AMD Results Aggregation

Track answering machine detection outcomes to measure campaign quality:

- `HUMAN_ANSWERED` rate indicates live contact effectiveness
- High `VOICEMAIL_BEEP` + `VOICEMAIL_NO_BEEP` rates suggest poor timing or stale numbers
- `SIT_TONE_*` rates indicate number quality issues in the contact list
- `AMD_UNRESOLVED` spikes may indicate audio quality or network issues

### Where Metrics Are Available

- **Contact records** -- each dial attempt produces a contact record with AMD status and disposition
- **Amazon Connect data lake** -- aggregated campaign metrics available for historical analysis and dashboards
- **Real-time metrics** -- agent occupancy and availability during active campaigns

---

## Security Profile Permissions

### Outbound Campaigns Permissions

Assign these permissions in the Connect security profile to control user access:

| Permission | Description |
|------------|-------------|
| **Outbound campaigns - Create** | Create new campaigns |
| **Outbound campaigns - Edit** | Modify campaign configuration, schedule, and limits |
| **Outbound campaigns - Delete** | Delete campaigns |
| **Outbound campaigns - Enable/Disable** | Start, pause, and stop campaigns |

### Communication Limits Permissions

| Permission | Description |
|------------|-------------|
| **Communication limits - View** | View instance-wide communication limit defaults |
| **Communication limits - Edit** | Modify instance-wide communication limit defaults |

### Required IAM Actions

For programmatic access, the IAM policy must include:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect-campaigns:CreateCampaign",
        "connect-campaigns:DeleteCampaign",
        "connect-campaigns:GetCampaign*",
        "connect-campaigns:ListCampaigns",
        "connect-campaigns:PauseCampaign",
        "connect-campaigns:PutOutboundRequestBatch",
        "connect-campaigns:ResumeCampaign",
        "connect-campaigns:StartCampaign",
        "connect-campaigns:StopCampaign",
        "connect-campaigns:UpdateCampaign*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Best Practices

### Dialing Configuration

- **Ring duration**: set to 15-25 seconds. Shorter durations miss slow-to-answer contacts; longer durations waste agent time.
- **Caller ID**: use local area code numbers when possible -- local numbers have measurably higher answer rates than toll-free or out-of-area numbers.

### PutDialRequestBatch / PutOutboundRequestBatch

- **Batch size**: maximum 25 requests per batch call
- **Throttling**: implement exponential backoff with jitter when receiving `ThrottlingException`
- **Idempotency**: use unique `clientToken` values to prevent duplicate dial attempts on retries
- **Expiration**: set reasonable `expirationTime` values to avoid stale contacts being dialed

### Dialer Mode Selection

| Mode | Best For | Key Consideration |
|------|----------|-------------------|
| **Predictive** | High-volume campaigns where throughput matters most | ML optimizes dial rate but may produce some abandoned calls; monitor abandon rate |
| **Progressive** | High-value or compliance-sensitive calls | 1:1 agent-to-call ratio eliminates abandoned calls; lower throughput |
| **Agentless** | Notifications, appointment confirmations, surveys | No agent needed; use with IVR flows for self-service interactions |

### Compliance

- **Time-of-day restrictions**: configure `communicationTimeConfig` to respect local calling hour laws (e.g., TCPA restricts calls before 8 AM and after 9 PM local time)
- **Do-Not-Call (DNC) lists**: filter contacts against DNC registries before adding to campaign segments
- **Consent management**: track and enforce opt-in/opt-out status in Customer Profiles attributes
- **Communication limits**: set daily and weekly caps per recipient to avoid over-contact

### Predictive Dialer Tuning

- Start with conservative settings and let the ML model learn agent handling patterns
- The model automatically adjusts dial-ahead rate based on observed agent availability and call duration
- Allow 1-2 hours of runtime for the model to stabilize before evaluating abandon rates
- Monitor the abandon rate target -- the system optimizes toward the configured threshold

---

## Lambda Integration in Campaigns

Lambda functions can be invoked at key points during the campaign dial lifecycle to add custom logic.

### Invocation Points

- **Pre-dial**: execute logic before each dial attempt
- **Post-dial**: execute logic after each dial attempt completes

### Common Use Cases

**Dynamic Caller ID Selection**

Select the caller ID number based on the contact's location or account attributes:

```javascript
exports.handler = async (event) => {
  const { contact } = event;
  const state = contact.attributes?.state;

  // Use a local number matching the contact's state
  const callerIdMap = {
    CA: "+14155550100",
    NY: "+12125550100",
    TX: "+12145550100"
  };

  return {
    connectSourcePhoneNumber: callerIdMap[state] || "+18005550100"
  };
};
```

**Contact Enrichment**

Look up additional data before the call connects to an agent:

```javascript
exports.handler = async (event) => {
  const { contactId, attributes } = event;
  const accountNumber = attributes?.accountNumber;

  // Fetch latest account status from your system
  const accountData = await fetchAccountDetails({ accountNumber });

  return {
    attributes: {
      ...attributes,
      currentBalance: accountData.balance,
      lastPaymentDate: accountData.lastPayment,
      preferredLanguage: accountData.language
    }
  };
};
```

**Custom Routing Logic**

Route the call to a specific queue or flow based on pre-dial evaluation:

```javascript
exports.handler = async (event) => {
  const { attributes } = event;
  const accountValue = parseFloat(attributes?.accountValue || "0");

  // High-value accounts get routed to senior agents
  if (accountValue > 50000) {
    return {
      connectContactFlowId: "high-value-flow-arn",
      connectQueueId: "senior-agents-queue-arn"
    };
  }

  return {};  // Use campaign defaults
};
```

### Configuration

Lambda functions are associated with the campaign's contact flow. Use the `InvokeLambdaFunction` block in the campaign flow to call your function at the appropriate point in the contact flow.
