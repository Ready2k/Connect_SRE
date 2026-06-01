# Live Media Streaming in Amazon Connect

## Overview

Live media streaming enables real-time streaming of customer audio from Amazon Connect to Amazon Kinesis Video Streams (KVS). This allows external applications to process audio in real time for use cases such as transcription, sentiment analysis, compliance monitoring, and custom AI/ML processing.

Media streaming captures audio and sends it as fragments to a Kinesis Video Stream. Your application consumes these fragments in real time. Depending on configuration, audio can be captured for the entire interaction or only in one direction:
- **From the customer**: What the customer says, including when they are on hold.
- **To the customer**: What the customer hears, including agent speech and system prompts.

Customer audio streams also include interactions with an Amazon Lex bot if one is used in the flow.

## Use Cases

- **Real-time transcription**: Stream audio to a custom STT engine or Amazon Transcribe for live transcripts.
- **Sentiment analysis**: Analyze customer tone and emotion during the call.
- **Compliance monitoring**: Detect prohibited language, verify required disclosures, or monitor for script adherence.
- **Custom AI/ML processing**: Feed audio to custom models for intent detection, speaker identification, or anomaly detection.
- **Agent assist**: Process audio to provide real-time suggestions, knowledge articles, or next-best-action recommendations to the agent.
- **Call recording with custom storage**: Stream audio to your own storage solution alongside or instead of the built-in Connect recording.

## Flow Blocks

### Start Media Streaming

Located in the **Media and Streaming** category in the flow designer.

**What it does**: Begins streaming audio to a Kinesis Video Stream. A new KVS stream is created (or reused) for each contact.

**Configuration**:
- **Media stream type**: Customer audio.
- **Participants to stream**: Choose what to stream:
  - **From the customer**: Customer's spoken audio (what they say).
  - **To the customer**: Audio the customer hears (agent speech, system prompts).
  - Both options can be selected simultaneously.

**Branches**:
- **Success**: Streaming started successfully. The KVS stream ARN is now available in contact attributes.
- **Error**: Failed to start streaming (e.g., KVS configuration issue, permissions).

**After this block executes**, the following contact attributes are populated:
- `$.MediaStreams.Customer.Audio.StreamARN` -- The ARN of the Kinesis Video Stream.
- `$.MediaStreams.Customer.Audio.StartTimestamp` -- Epoch timestamp (milliseconds) when streaming began.
- `$.MediaStreams.Customer.Audio.StartFragmentNumber` -- The fragment number to start consuming from.

### Stop Media Streaming

**What it does**: Stops the live audio stream to Kinesis Video Streams.

**When to use**:
- After your processing is complete (e.g., authentication step is done).
- Before transferring to a queue if you do not need streaming during the queue wait.
- To free up KVS resources.

**Configuration**:
- Same participant options as Start: From the customer, To the customer.

**Branches**:
- **Success**: Streaming stopped.
- **Error**: Failed to stop streaming.

If you do not explicitly stop streaming, it continues until the contact ends. Streaming automatically stops when the contact disconnects.

**After stop**, the following attribute is populated:
- `$.MediaStreams.Customer.Audio.StopTimestamp` -- When the stream stopped.

Customer audio is captured until a Stop media streaming block is invoked, even if the contact is passed to another flow.

## Architecture

```
Customer Audio
     |
     v
Amazon Connect
     |
     v
Kinesis Video Streams (KVS)
     |
     v
Consumer Application
(Lambda, ECS, EC2, etc.)
     |
     v
Downstream Processing
(Transcribe, custom ML, storage)
```

### Audio Format

- **Codec**: PCM (Linear16)
- **Sample rate**: 8 kHz
- **Bit depth**: 16-bit
- **Channels**: Mono (single channel)
- **Container**: MKV (Matroska) fragments in KVS

## Configuration

### Enable Media Streaming on the Instance

Before using the flow blocks, enable media streaming at the instance level:

1. Go to Amazon Connect console > Your instance > Data storage.
2. Under **Live media streaming**, choose Edit.
3. Enable live media streaming.
4. Configure:
   - **Prefix for the Kinesis Video Stream**: A prefix for the KVS stream names (e.g., `connect-media-`). Connect appends the contact ID. This prefix makes it easier to identify streams with the data.
   - **Data retention period**: How long KVS retains the stream data. Options:
     - **No data retention**: Data is not retained and is available for consumption for only 5 minutes (Kinesis default minimum).
     - Custom period: Up to 87,600 hours (10 years).
     - Kinesis Video Streams quotas apply.
5. Choose Save under Live media streaming, then Save at the bottom of the page.

### Encryption

- KVS streams are encrypted at rest using AWS KMS.
- Data is encrypted before it's written to the KVS stream storage layer and decrypted after retrieval. Data is always encrypted at rest within KVS.
- By default, Connect uses the AWS managed key for Kinesis Video Streams (`aws/kinesisvideo`).
- You can specify a customer-managed KMS key for additional control.
- The KMS key must be in the **same Region** as the instance.
- The KMS key should be either a customer managed key OR the AWS managed key for KVS (`aws/kinesisvideo`). It should NOT be AWS managed keys for other services (e.g., `aws/connect`, `aws/lambda`, `aws/kinesis`).
- The grant provisioned for the key by Connect should not be revoked. The `GranteePrincipal` format is: `arn:aws:iam::{account-id}:role/aws-service-role/connect.amazonaws.com/AWSServiceRoleForAmazonConnect_{hash}`.

### IAM Permissions

The Connect service-linked role needs permissions to:
- `kinesisvideo:CreateStream`
- `kinesisvideo:DescribeStream`
- `kinesisvideo:PutMedia`
- `kinesisvideo:GetDataEndpoint`
- `kinesisvideo:TagStream`

These are automatically granted when you enable media streaming through the console. If configuring via API/CloudFormation, ensure the service role has these permissions.

## Contact Attributes for Media Streaming

Use these in your flow so the contact record includes the streaming data. You can also pass them to Lambda functions.

| Attribute | JSONPath | Description |
|-----------|----------|-------------|
| Customer Audio Stream ARN | `$.MediaStreams.Customer.Audio.StreamARN` | ARN of the KVS stream for customer audio. |
| Customer Audio Start Timestamp | `$.MediaStreams.Customer.Audio.StartTimestamp` | When customer audio stream started. |
| Customer Audio Stop Timestamp | `$.MediaStreams.Customer.Audio.StopTimestamp` | When customer audio stream stopped. |
| Customer Audio Start Fragment Number | `$.MediaStreams.Customer.Audio.StartFragmentNumber` | Fragment number where streaming began. |

## Consuming the Stream

### From Lambda

A common pattern is to use a Lambda function triggered by the flow that starts consuming:

```javascript
const {
  KinesisVideoClient,
  GetDataEndpointCommand
} = require("@aws-sdk/client-kinesis-video");

const {
  KinesisVideoMediaClient,
  GetMediaCommand
} = require("@aws-sdk/client-kinesis-video-media");

exports.handler = async (event) => {
  const streamARN = event.Details.ContactData.MediaStreams.Customer.Audio.StreamARN;
  const startFragment = event.Details.ContactData.MediaStreams.Customer.Audio.StartFragmentNumber;

  // Get the data endpoint for the stream
  const kvsClient = new KinesisVideoClient({ region: process.env.AWS_REGION });
  const endpointResponse = await kvsClient.send(new GetDataEndpointCommand({
    StreamARN: streamARN,
    APIName: "GET_MEDIA"
  }));

  // Get media from the stream
  const mediaClient = new KinesisVideoMediaClient({
    region: process.env.AWS_REGION,
    endpoint: endpointResponse.DataEndpoint
  });

  const mediaResponse = await mediaClient.send(new GetMediaCommand({
    StreamARN: streamARN,
    StartSelector: {
      StartSelectorType: "FRAGMENT_NUMBER",
      AfterFragmentNumber: startFragment
    }
  }));

  // Process the audio stream (mediaResponse.Payload is a readable stream)
  // Note: Lambda has a 15-minute max execution time; for long calls,
  // use ECS or EC2 for continuous consumption.

  return { status: "streaming_started" };
};
```

### From ECS / EC2 (Long-Running Consumer)

For continuous audio processing during calls, use an ECS task or EC2 instance:

1. The flow invokes a Lambda that starts an ECS task, passing the stream ARN and fragment number.
2. The ECS task connects to KVS using the `GetMedia` API.
3. The task parses MKV fragments, extracts PCM audio, and processes it.
4. When the contact ends, the stream closes and the task exits.

### Parsing MKV Fragments

KVS delivers audio as MKV (Matroska) fragments. Use an MKV parser to extract the raw PCM audio:

- **AWS KVS Parser Library** (Java): `amazon-kinesis-video-streams-parser-library`
- **Custom parser**: Parse MKV EBML headers to extract audio tracks. Each fragment contains a cluster of audio frames.

## Flow Design Patterns

### Pattern 1: Stream During Entire Call

```
Start flow
  -> Start media streaming
  -> [rest of flow: prompts, Lex, Lambda, queue]
  -> (streaming stops automatically on disconnect)
```

### Pattern 2: Stream During Specific Segment

```
Start flow
  -> Play prompt ("Please state your issue")
  -> Start media streaming
  -> [Collect and process audio]
  -> Stop media streaming
  -> [Continue flow without streaming]
```

### Pattern 3: Stream with Lambda Processing

```
Start flow
  -> Start media streaming
  -> Invoke Lambda (pass stream ARN via contact attributes)
      Lambda kicks off ECS task for continuous processing
  -> Transfer to queue
  -> (ECS task continues processing until disconnect)
```

### Pattern 4: Stream Both Directions

```
Start flow
  -> Start media streaming (From the customer AND To the customer)
  -> [rest of flow]
  -> (captures both sides of the conversation)
```

### Block Placement

- Place `Start media streaming` **early** in the flow, before any queue or transfer, to ensure audio is captured from the beginning.
- Customer audio is captured continuously after Start, even across flow transfers, until Stop is invoked or the contact disconnects.
- Place `Stop media streaming` when you no longer need audio (e.g., after authentication) to free KVS resources.

## Limits

| Limit | Value |
|-------|-------|
| Streams per contact | 1 (customer audio) |
| Audio format | PCM 8 kHz 16-bit mono |
| Maximum retention | 87,600 hours (10 years) |
| Minimum retention | 0 hours (no retention; data available for 5 minutes only) |
| KVS streams per AWS account | Default 5,000 (soft limit) |
| KVS PutMedia connections per stream | 1 |
| KVS GetMedia connections per stream | 3 |

Kinesis Video Streams quotas apply: see [KVS quotas](https://docs.aws.amazon.com/kinesisvideostreams/latest/dg/limits.html).

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|---------|
| Stream ARN is empty | Media streaming not enabled on instance | Enable in Connect console > Data storage > Live media streaming |
| Error branch taken on Start | KMS key permissions | Ensure service role has `kms:GenerateDataKey` on the KMS key. Verify KMS key is in the same Region. Verify the key is customer-managed or `aws/kinesisvideo`, not an AWS managed key for another service. |
| No audio data in stream | Block placed after disconnect | Place `Start media streaming` early in the flow, before any queue/transfer |
| Consumer falls behind | Slow processing | Scale consumer (more ECS tasks, faster processing), or use Kinesis Data Streams as intermediary |
| Audio is garbled | Wrong parser or sample rate | Ensure you are parsing MKV correctly and using 8 kHz 16-bit PCM |
| KMS grant revoked | Service role grant was revoked | Re-enable media streaming in the console to re-provision the KMS grant |
| No data after 5 minutes | Retention set to 0 (no retention) | Increase retention period or ensure consumer processes data within 5 minutes |
