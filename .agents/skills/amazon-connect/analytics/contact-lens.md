# Contact Lens — Conversational Analytics

Contact Lens provides conversational analytics for voice, chat, and email channels in Amazon Connect. It operates in two modes for voice and chat (real-time and post-contact) and in post-contact mode for email (since email is inherently asynchronous).

---

## Setup and Enabling

Contact Lens is enabled per contact flow using the **Set recording and analytics behavior** block.

### Configuration Options

| Setting | Description |
|---|---|
| **Enable analytics** | Turn on Contact Lens for the contact flow. |
| **Real-time analytics** | Must be explicitly enabled; post-contact alone does not provide streaming data. |
| **Post-contact analytics** | Runs after the interaction ends; produces a comprehensive analytics artifact in S3. |
| **Redaction** | Optional; enable within the same block after enabling analytics. |
| **Language** | Set the language for transcription and analytics. |

### Channels

| Channel | Real-Time | Post-Contact | Notes |
|---|---|---|---|
| **Voice** | Yes | Yes | Real-time requires explicit opt-in in the flow block. |
| **Chat** | Yes | Yes | Each processed chat message is billed even if not all features apply. |
| **Email** | N/A | Yes | Email is asynchronous; analysis initiates as soon as the Set recording block is hit. No real-time vs post-contact distinction. |

---

## Real-Time Analytics (Voice & Chat)

Real-time Contact Lens analyzes conversations as they happen, enabling supervisors and automated systems to intervene during live interactions.

### Capabilities

- **Live issue detection** — Identify customer frustration, compliance violations, or escalation triggers during the call/chat.
- **Supervisor alerts** — Rules fire in real-time and can trigger alerts on the supervisor dashboard, send EventBridge events, or invoke Lambda functions.
- **Real-time categories** — Custom category rules evaluated continuously against the in-progress transcript.
- **Live transcript** — Streaming transcript visible on the Contact details page for in-progress contacts.
- **Sentiment trend** — Customer sentiment graph updates as the conversation progresses.

### APIs

| Method | Description |
|---|---|
| **ListRealtimeContactAnalysisSegmentsV2** | Stream real-time transcript and analytics segments for an in-progress contact. |
| **Kinesis** | Real-time analytics segments can be streamed to Kinesis for custom processing. |

---

## Post-Contact Analytics (Voice, Chat & Email)

Post-contact analysis runs after the interaction ends and produces a comprehensive analytics artifact stored in S3.

### Output Location

Analytics files are written to the S3 bucket configured in the instance storage settings under `Analysis - Voice/Chat/Email`. The file format is JSON and includes all analytics dimensions described below.

### S3 Path Structure

| Channel | Path Pattern |
|---|---|
| **Voice** | `connect-{instanceARN}/Analysis/Voice/` |
| **Chat** | `connect-{instanceARN}/Analysis/Chat/` |
| **Email** | `connect-{instanceARN}/Analysis/Email/` |

---

## Sentiment Analysis

Contact Lens assigns sentiment at multiple granularities:

| Level | Description |
|---|---|
| **Per-turn sentiment** | Each utterance/message is classified as `POSITIVE`, `NEGATIVE`, or `NEUTRAL`. |
| **Overall sentiment** | A numeric score from **-5** (most negative) to **+5** (most positive) computed per participant (agent and customer separately). |
| **Sentiment by period** | The conversation is divided into quarters, and a score is computed for each quarter per participant. |
| **Sentiment shift** | Indicates whether sentiment improved, worsened, or remained stable between the beginning and end of the conversation. Useful for identifying whether the agent successfully de-escalated. |

### How Scores Are Determined

Contact Lens considers two factors for each participant turn to assign a score that ranges from -5 to +5 for each period of the call:

1. **Frequency** — The number of times the sentiment is positive, negative, or neutral within the period.
2. **Sentiment streaks** — Consecutive turns with the same sentiment weight the score more heavily.

The overall sentiment score is the average of the scores assigned during each portion of the call.

### Sentiment Score Interpretation

| Score Range | Meaning |
|---|---|
| +3 to +5 | Strongly positive |
| +1 to +2 | Mildly positive |
| 0 | Neutral |
| -1 to -2 | Mildly negative |
| -3 to -5 | Strongly negative |

### Investigation Patterns

- **Positive-to-negative shift** — Customer started happy but left unhappy. Prioritize for quality assurance sampling.
- **Negative-to-positive shift** — Agent successfully de-escalated. Analyze to replicate successful techniques.
- **Sentiment trendline** — Visual chart showing variation in customer sentiment as the contact progresses.

---

## Transcription

Contact Lens produces high-accuracy transcripts for voice interactions using Amazon Transcribe under the hood.

### Features

- **Speaker identification** — Each segment is labeled as `AGENT` or `CUSTOMER`. For multi-party calls (conferences), additional participants are identified via `ParticipantId` and `ParticipantRole`.
- **Timestamps** — Every segment includes `BeginOffsetMillis` and `EndOffsetMillis` relative to the start of the recording.
- **Confidence scores** — Word-level confidence scores for transcript accuracy.
- **Loudness scores** — Per-second loudness scores for each turn (array of numeric values, one per second of the turn).
- **Talk speed** — Average words per minute computed per participant (`AverageWordsPerMinute`).
- **Custom vocabularies** — Support for domain-specific terms to improve transcription accuracy.
- **Redacted transcripts** — A separate redacted version with PII replaced by placeholders (see PII Redaction below).

### Transcript JSON Structure (per turn)

```json
{
  "BeginOffsetMillis": 7370,
  "EndOffsetMillis": 11190,
  "Content": "I need to cancel my plan subscription.",
  "Id": "turn-unique-id",
  "ParticipantId": "CUSTOMER",
  "Sentiment": "NEGATIVE",
  "LoudnessScore": [77.18, 79.59, 85.23, 81.08, 73.99],
  "IssuesDetected": [...],
  "Redaction": {
    "RedactedTimestamps": [
      { "BeginOffsetMillis": 3290, "EndOffsetMillis": 3620 }
    ]
  }
}
```

---

## Categories

Categories allow you to automatically classify contacts based on rules you define.

### Rule Types

| Rule Type | Description |
|---|---|
| **Keywords/phrases (Exact Match)** | Match exact words or phrases spoken by agent or customer. |
| **Keywords/phrases (Pattern Match)** | Match patterns that may be less than 100% exact. Supports distance constraints (e.g., "credit" NOT within 1 word of "card"). |
| **Keywords/phrases (Semantic Match)** | Match based on semantic meaning. **Post-contact only** — not available for real-time. |
| **Sentiment** | Match based on sentiment of a turn or overall score. |
| **Interruptions** | Match when interruption count exceeds a threshold. |
| **Non-talk time** | Match when silence duration exceeds a threshold. |
| **Composite** | Combine multiple conditions with AND/OR/NOT logic. |

### Evaluation Modes

- **Post-contact** — Rules evaluated after the full transcript is available. Most accurate. Supports all match types including semantic match.
- **Real-time** — Rules evaluated incrementally during the conversation. Enables live alerting. Only supports exact match and pattern match.

### Logic Model

- Within a single card of words/phrases: each line is evaluated with **OR** logic.
- Between multiple cards: cards are connected with **AND** logic.
- Example: (Card 1 line 1 OR Card 1 line 2) AND (Card 2 line 1 OR Card 2 line 2).

### Additional Conditions

Rules can be further scoped with:
- **Queue filter** — Apply rule only to specific queues.
- **Contact attributes** — Apply when contact attributes have certain values.
- **Sentiment score threshold** — Apply when sentiment scores meet certain criteria.

### Use Cases

- Compliance monitoring (agent read disclosure script)
- Escalation detection (customer mentions "supervisor" or "cancel")
- Quality assurance categorization (greeting compliance, hold procedure)
- Script adherence (verify agent spoke required phrases)

---

## Contact Lens Rules — Actions

When a rule matches, Contact Lens can perform the following actions:

| Action | Description |
|---|---|
| **Assign contact category** | Tag the contact with a named category (e.g., "Compliant", "Escalation"). |
| **Generate EventBridge event** | Publish an event to Amazon EventBridge for downstream processing. |
| **Create task** | Automatically create a Connect task for follow-up. |
| **Send email notification** | Send an email alert to supervisors. |
| **Supervisor alert** | Display alert on the real-time agent performance dashboard. |

### Rule Management

- Rules are created via **Analytics and optimization > Rules > Create a rule > Conversational analytics** in the Connect console.
- Rules can also be managed programmatically via the Connect Rules APIs.
- Requires **CallCenterManager** security profile or explicit **Rules** permissions.

---

## PII Redaction

Contact Lens can detect and redact personally identifiable information from transcripts, audio recordings, and email content.

### Supported PII Entity Types

- Credit/debit card numbers (`CREDIT_DEBIT_NUMBER`)
- Social Security numbers
- Names (`NAME`)
- Addresses
- Email addresses
- Phone numbers
- Bank account numbers
- Date of birth
- Usernames (`USERNAME`)
- PINs
- Other sensitive data as classified by the NLU model

### Redaction Targets

| Target | Description |
|---|---|
| **Transcript** | PII replaced with `[PII]` placeholder (when `RedactionMaskMode` = `PII`) or entity type placeholder like `[NAME]` (when `RedactionMaskMode` = `ENTITY_TYPE`). |
| **Audio** | PII segments replaced with silence in the audio recording (.wav file). Silent portions are NOT flagged as non-talk time. |
| **Email** | PII redacted from email body and subject in analytics output. |

### Output Files When Redaction Is Enabled

| File | Description |
|---|---|
| **Redacted file** | Generated by default. Output schema with sensitive data redacted. |
| **Original (raw) analyzed file** | Generated only when "Get redacted and original transcripts with redacted audio" is selected. Contains the complete unredacted conversation. |
| **Redacted audio file (.wav)** | For voice contacts. Sensitive data replaced with silence. |

### Configuration

- PII redaction is configured per contact flow in the **Set recording and analytics behavior** block.
- You choose which entity types to redact and whether to redact from transcript only, audio only, or both.
- The original (unredacted) files can optionally be retained in a separate S3 location with restricted access.
- For voice contacts, redaction is applied after the call disconnects.
- For email contacts, redaction is applied after the email contact ends.

### Important Limitations

- Redaction uses machine learning and may not catch all instances of PII. Review redacted output.
- Does not meet de-identification requirements under HIPAA. Continue treating redacted data as protected health information.
- Redaction is supported for post-call analytics and chat analytics in supported languages. Not supported for real-time call analytics.

---

## Theme Detection

Theme detection uses unsupervised machine learning to identify recurring topics across your contact center interactions.

- Automatically groups contacts by emerging themes without requiring predefined categories.
- Helps identify new or trending issues that you haven't built categories for yet.
- Available in the Contact Lens dashboard in the Amazon Connect console.
- Themes are surfaced with representative phrases and contact counts.
- Operates across a time window to detect patterns at scale.

---

## Talk Time Metrics

Contact Lens measures detailed talk time breakdowns for voice interactions:

| Metric | Description |
|---|---|
| **Total conversation duration** | End-to-end duration of the voice interaction (`TotalConversationDurationMillis`). |
| **Agent talk time** | Total time the agent was speaking (`TalkTime.DetailsByParticipant.AGENT.TotalTimeMillis`). |
| **Customer talk time** | Total time the customer was speaking (`TalkTime.DetailsByParticipant.CUSTOMER.TotalTimeMillis`). |
| **Total talk time** | Combined agent + customer talk time (`TalkTime.TotalTimeMillis`). |
| **Non-talk time** | Total silence duration — neither party speaking (`NonTalkTime.TotalTimeMillis`). Includes individual silence instances with timestamps. |
| **Agent talk time %** | Agent talk time as a percentage of total conversation. |
| **Customer talk time %** | Customer talk time as a percentage of total conversation. |
| **Non-talk time %** | Silence as a percentage of total conversation. |
| **Longest non-talk time** | The longest single stretch of silence. |
| **Interruptions (total)** | Total count of interruptions (`Interruptions.TotalCount`). |
| **Interruptions (total time)** | Total time spent in interruptions (`Interruptions.TotalTimeMillis`). |
| **Interruptions by interrupter** | Broken down by AGENT and CUSTOMER, with begin/end offsets and duration for each instance. |
| **Talk speed (agent)** | Average words per minute for the agent (`TalkSpeed.DetailsByParticipant.AGENT.AverageWordsPerMinute`). |
| **Talk speed (customer)** | Average words per minute for the customer. |

These metrics are valuable for coaching: excessive agent talk time may indicate the agent is not listening, while excessive non-talk time may indicate holds without proper communication.

---

## Response Time Metrics

| Metric | Description |
|---|---|
| **Agent greeting time** | Time from conversation start to the agent's first utterance. |
| **Agent response time (avg)** | Average time the agent takes to respond after the customer finishes speaking. |
| **Customer response time (avg)** | Average time the customer takes to respond after the agent finishes speaking. |

These are particularly useful for chat where response delays are more visible to the customer.

---

## Key Highlights

Contact Lens automatically identifies key highlights from the conversation using generative AI:

| Highlight | JSON Field | Description |
|---|---|---|
| **Issue** | `IssuesDetected` | The primary reason for the contact as detected from the conversation. Includes character offsets and text. |
| **Outcome** | `OutcomesDetected` | Whether the issue was resolved and how. Includes character offsets and text. |
| **Action item** | `ActionItemsDetected` | Any follow-up actions mentioned during the conversation. Includes character offsets and text. |
| **Post-contact summary** | `ContactSummary.PostContactSummary.Content` | AI-generated summary of the entire conversation. |

These appear on the Contact details page and in the output JSON.

---

## Email Analytics

For the email channel, Contact Lens provides:

| Capability | Description |
|---|---|
| **Categorization** | Auto-categorize emails using the same rules engine as voice/chat. |
| **PII redaction** | Detect and redact PII from email body and subject line. |
| **Summaries** | AI-generated summaries of email threads. |
| **Sentiment** | Not available for email (email is asynchronous). |

There is no real-time vs. post-contact distinction for email since email is an asynchronous channel. Analytics are produced after each email message is processed.

---

## Custom Vocabulary

Improve transcription accuracy for domain-specific terms (product names, medical terms, jargon).

### Setup

1. Navigate to **Analytics and optimization > Custom vocabularies** in the Connect console.
2. Choose **Add custom vocabulary**, enter a name, and select a language.
3. Download the sample file (English only) or create a tab-separated file with the header: `Phrase`, `IPA`, `SoundsLike`, `DisplayAs`.
4. Upload the file. Multi-word phrases use hyphens (not spaces) in the Phrase column.
5. Set the vocabulary as **default** for it to be applied to analyses.

### File Format

| Column | Required | Description |
|---|---|---|
| **Phrase** | Yes | The word or hyphen-separated phrase to recognize. |
| **IPA** | No | International Phonetic Alphabet pronunciation. |
| **SoundsLike** | No | Phonetic hint using similar-sounding words. |
| **DisplayAs** | No | How the word should appear in the transcript. |

### Key Details

- File must be in **LF** format (not CRLF).
- One active (default) vocabulary per language per instance.
- Up to **20** vocabulary files can be uploaded and activated simultaneously.
- Processing states: **Processing** (validating) -> **Ready** (valid but not applied) -> **Ready (default)** (actively applied).
- Deletion takes approximately **90 minutes**.
- Transcription is a one-time event; new vocabularies are NOT applied retroactively.
- Custom vocabularies apply to **speech analytics only** (not chat, since chat transcripts already exist).
- Applied to both real-time and post-call analyses when set as default.

### APIs

- `CreateVocabulary` — Create a new custom vocabulary.
- `AssociateDefaultVocabulary` — Set a vocabulary as the default for a language.

---

## Language Support

The following table shows Contact Lens feature support by language. Languages marked with * are not available in Africa (Cape Town) or AWS GovCloud (US-West).

### Full Feature Support (Post-Call + Real-Time + Sentiment + Redaction + Summaries)

| Language | Code | Post-Call | Real-Time | Sentiment | Redaction | Summaries | Pattern Rules |
|---|---|---|---|---|---|---|---|
| English (US) | en-US | Yes | Yes | Yes | Yes | Yes | Yes |
| English (UK) | en-GB | Yes | Yes | Yes | Yes | Yes | Yes |
| English (Australia) | en-AU | Yes | Yes | Yes | Yes | Yes | Yes |
| English (India) | en-IN | Yes | Yes | Yes | Yes | Yes | Yes |
| English (Ireland) | en-IE | Yes | Yes | Yes | Yes | Yes | Yes |
| English (New Zealand) | en-NZ | Yes | Yes | Yes | Yes | Yes | Yes |
| English (Scotland) | en-AB | Yes | Yes | Yes | Yes | Yes | Yes |
| English (South Africa) | en-ZA | Yes | Yes | Yes | Yes | Yes | Yes |
| English (Wales) | en-WL | Yes | Yes | Yes | Yes | Yes | Yes |
| French (Canada) | fr-CA | Yes | Yes | Yes | Yes | Yes | Yes |
| French (France) | fr-FR | Yes | Yes | Yes | Yes | Yes | Yes |
| German (Germany) | de-DE | Yes | Yes | Yes | Yes | Yes | Yes |
| Italian (Italy) | it-IT | Yes | Yes | Yes | Yes | Yes | Yes |
| Portuguese (Brazil) | pt-BR | Yes | Yes | Yes | Yes | Yes | Yes |
| Portuguese (Portugal) | pt-PT | Yes | Yes | Yes | Yes | Yes | Yes |
| Spanish (Spain) | es-ES | Yes | Yes | Yes | Yes | Yes | Yes |
| Spanish (US) | es-US | Yes | Yes | Yes | Yes | Yes | Yes |

### Post-Call + Real-Time + Sentiment (No Redaction)

| Language | Code | Post-Call | Real-Time | Sentiment | Summaries |
|---|---|---|---|---|---|
| Chinese Simplified | zh-CN | Yes | Yes | Yes | Yes |
| German (Switzerland) | de-CH | Yes | Yes | Yes | Yes |
| Hindi (India) | hi-IN | Yes | Yes | Yes | No |
| Japanese (Japan) | ja-JP | Yes | Yes | Yes | Yes |
| Korean (South Korea) | ko-KR | Yes | Yes | Yes | Yes |

### Post-Call + Real-Time (No Sentiment/Redaction)

| Language | Code |
|---|---|
| Arabic (Gulf)* | ar-AE |
| Arabic (Modern Standard)* | ar-SA |
| Catalan (Spain)* | ca-ES |
| Croatian (Croatia)* | hr-HR |
| Czech (Czech Republic)* | cs-CZ |
| Danish (Denmark)* | da-DK |
| Dutch (Netherlands)* | nl-NL |
| Farsi (Iran)* | fa-IR |
| Finnish (Finland)* | fi-FI |
| Galician (Spain)* | gl-ES |
| Greek (Greece)* | el-GR |
| Hebrew (Israel)* | he-IL |
| Indonesian (Indonesia)* | id-ID |
| Latvian (Latvia)* | lv-LV |
| Malay (Malaysia)* | ms-MY |
| Norwegian (Norway)* | no-NO |
| Polish (Poland)* | pl-PL |
| Romanian (Romania)* | ro-RO |
| Russian (Russia)* | ru-RU |
| Serbian (Serbia)* | sr-RS |
| Slovak (Slovakia)* | sk-SK |
| Swedish (Sweden)* | sv-SE |
| Tagalog (Philippines)* | tl-PH |
| Thai (Thailand)* | th-TH |
| Ukrainian (Ukraine)* | uk-UA |
| Vietnamese (Vietnam)* | vi-VN |

### Post-Call Only (No Real-Time)

| Language | Code |
|---|---|
| Afrikaans (South Africa)* | af-ZA |
| Bengali (Bangladesh)* | bn-IN |
| Bosnian (Bosnia)* | bs-BA |
| Bulgarian (Bulgaria)* | bg-BG |
| Estonian (Estonia)* | et-ET |
| Hungarian (Hungary)* | hu-HU |
| Kannada (India)* | kn-IN |
| Lithuanian (Lithuania)* | lt-LT |
| Macedonian (Macedonia)* | mk-MK |
| Malayalam (India)* | ml-IN |
| Marathi (India)* | mr-IN |
| Sinhala (Sri Lanka)* | si-LK |
| Slovenian (Slovenia)* | sl-SI |
| Somali (Somalia)* | so-SO |
| Sundanese (Indonesia)* | su-ID |
| Tamil (India)* | ta-IN |
| Telugu (India)* | te-IN |
| Turkish (Turkey)* | tr-TR |
| Zulu (South Africa)* | zu-ZA |

Note: Language list expands regularly. Check AWS docs for the current list.

---

## External Voice System Integration

Analyze audio from non-Connect voice systems (legacy PBX, third-party CCaaS).

| Detail | Description |
|---|---|
| **Upload method** | Upload audio files to S3. |
| **Supported formats** | WAV, MP3. |
| **Processing** | Use Contact Lens APIs to process uploaded audio. |
| **Results include** | Transcription, sentiment, categories, talk time metrics. |
| **Use case** | Migrate analytics from legacy systems while maintaining consistent analysis across platforms. |

---

## Output Artifacts — JSON Schema

The post-contact analytics JSON file includes the following top-level fields:

| Field | Description |
|---|---|
| `Version` | Schema version (e.g., "1.1.0"). |
| `AccountId` | AWS account ID. |
| `Channel` | VOICE, CHAT, or EMAIL. |
| `ContentMetadata.Output` | "Raw" for original file, "Redacted" for redacted file. |
| `JobStatus` | COMPLETED or FAILED. |
| `JobDetails.SkippedAnalysis` | Array of features that were skipped (e.g., categorization quota exceeded, safety guideline failures). |
| `LanguageCode` | Language code used for analysis. |
| `Participants` | Array of participants with `ParticipantId` and `ParticipantRole`. |
| `Categories` | `MatchedCategories` array and `MatchedDetails` with points of interest (begin/end offsets). |
| `ConversationCharacteristics` | Contains sentiment, interruptions, non-talk time, talk speed, talk time, and contact summary. |
| `CustomModels` | Custom vocabulary references (`Type`, `Name`, `Id`). |
| `Transcript` | Array of turns, each with content, timestamps, sentiment, loudness, and optional issues/outcomes/actions/redaction. |

### Redacted File Additions

| Field | Description |
|---|---|
| `ContentMetadata.RedactionTypes` | Array of redaction types (e.g., `["PII"]`). |
| `ContentMetadata.RedactionTypesMetadata.PII` | `RedactionEntitiesRequested` (entity types), `RedactionMaskMode` (`PII` or `ENTITY_TYPE`). |

---

## APIs and Data Access

| Method | Description |
|---|---|
| **ListRealtimeContactAnalysisSegmentsV2** | Stream real-time transcript and analytics segments for an in-progress contact. |
| **S3 analytics files** | Post-contact analytics written as JSON to the configured S3 bucket. |
| **Contact Lens rules** | Managed via the Amazon Connect console or Rules APIs. |
| **Data lake** | Contact Lens data available in the Connect analytics data lake for Athena queries. |
| **Kinesis** | Real-time analytics segments can be streamed to Kinesis for custom processing. |

---

## Pricing Considerations

| Dimension | Pricing Model |
|---|---|
| **Voice (post-call)** | Per minute of voice analyzed. |
| **Voice (real-time)** | Per minute of voice analyzed (priced separately from post-call). |
| **Chat** | Per message analyzed. Each processed message is billed the same way regardless of which features apply to that message. |
| **Email** | Per email message analyzed. |
| **PII redaction** | Additional charge on top of base analytics pricing. |
| **Theme detection** | Additional charge. |
| **Generative AI features** | Summaries, key highlights may incur additional charges. |

Real-time and post-contact are priced separately. See [Amazon Connect Pricing](https://aws.amazon.com/connect/pricing/) for current rates.
