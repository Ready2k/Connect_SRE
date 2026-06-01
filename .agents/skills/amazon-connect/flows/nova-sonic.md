# Amazon Nova Sonic Speech-to-Speech in Amazon Connect

## Overview

Amazon Nova Sonic is a speech-to-speech foundation model that enables natural conversational voice AI in Amazon Connect contact flows. Unlike the traditional IVR pipeline (TTS prompt -> ASR -> NLU -> response TTS), Nova Sonic processes speech input directly and generates speech output, creating a more natural, low-latency conversational experience.

Nova Sonic is configured as a speech model on a Conversational AI bot locale in Amazon Connect. Connect continues to manage orchestration, intents, and flows.

## How It Works

### Traditional IVR Pipeline

```
Customer speaks
  -> Automatic Speech Recognition (ASR)
  -> Text sent to NLU engine (Lex)
  -> Intent + slots resolved
  -> Response text generated
  -> Text-to-Speech (TTS)
  -> Customer hears response
```

Each step adds latency. The experience is turn-based: the customer speaks, waits, hears a response.

### Nova Sonic Pipeline

```
Customer speaks
  -> Nova Sonic processes speech directly
  -> Generates speech response
  -> Customer hears response
```

Nova Sonic handles speech understanding and generation in a single model, reducing latency and enabling more natural conversational patterns like interruptions, back-channeling, and overlapping speech.

## Prerequisites

- A Conversational AI bot exists in Amazon Connect.
- The locale you want to use with Nova Sonic is already created.
- You have permissions to edit the bot configuration and build the language.

## Part 1: Configure Speech-to-Speech for a Bot Locale

### Step 1: Open the Speech Model Configuration

1. Sign in to the Amazon Connect admin website.
2. Choose **Bots**, then select the **Configuration** tab.
3. Select the locale you want to configure.
4. In the Speech model section, choose **Edit**.

### Step 2: Select Speech-to-Speech

In the Speech model modal, open the Model type dropdown and choose **Speech-to-Speech**.

### Step 3: Choose Amazon Nova Sonic

After selecting Speech-to-Speech, open Voice provider and select **Amazon Nova Sonic**. Then choose **Confirm**.

### Step 4: Review Speech Model Status

The Speech model card now shows "Speech-to-Speech: Amazon Nova Sonic" and displays a warning to select a Nova Sonic-compatible voice in your Set voice block.

### Step 5: Build and Activate the Locale

If the locale shows **Unbuilt changes**, choose **Build language**. The new STT settings become active after a successful build.

## Part 2: Configure a Nova Sonic Compatible Voice in a Flow

After enabling Nova Sonic at the bot level, you must configure a matching Nova Sonic-compatible expressive voice in your flow using the Set voice block.

### Supported Nova Sonic Voices (Launch Set)

| Voice | Locale | Gender |
|-------|--------|--------|
| Matthew | en-US | Masculine |
| Amy | en-GB | Feminine |
| Olivia | en-AU | Feminine |
| Lupe | es-US | Feminine |

### Step 1: Add or Open a Set Voice Block

1. Open the target flow in the Flow designer.
2. Search for Set voice in the block library.
3. Drag a Set voice block onto the canvas or open an existing one.

### Step 2: Select Override and Generative Speaking Style

In Other settings, choose **Override speaking style** and select **Generative** to enable Nova Sonic expressive output.

### Step 3: Select a Nova Sonic Compatible Voice

1. Set Voice provider to **Amazon**.
2. Under Language, select the locale that corresponds to the voice you want.
3. Under Voice, select one of the Nova Sonic-compatible voices.

### Step 4: Review Selected Voice

The Set voice block now shows the selected voice and style, such as "Voice: Matthew (Generative)".

### Step 5: Save and Publish the Flow

Choose **Save**, then **Publish** to activate the configuration.

## Configuration in Contact Flows

### The Connect Assistant Block

The **Connect assistant** block (in the Interact category) configures Nova Sonic for a contact.

**Block Settings**:

- **Assistant**: Select or create an Amazon Connect AI assistant configuration.
- **Session attributes**: Pass context to the assistant (customer name, account info, prior interaction data).
- **Guardrails**: Configure Amazon Bedrock Guardrails to apply content filtering, topic restrictions, and safety controls.
- **Timeout**: Maximum duration for the assistant interaction before the flow continues.

**Branches**:
- **Complete**: The assistant interaction completed (customer said goodbye, assistant resolved the issue, or timeout reached).
- **Error**: The assistant failed to initialize or encountered a runtime error.

### Setting Up an Assistant

1. Navigate to Amazon Connect console > Conversational AI > AI Assistants.
2. Create a new assistant:
   - **Name**: Descriptive name (e.g., "Billing Support Assistant").
   - **Model**: Amazon Nova Sonic.
   - **System prompt**: Instructions that define the assistant's persona, scope, and behavior.
   - **Knowledge bases**: Attach Amazon Bedrock Knowledge Bases for grounded responses.
   - **Tools**: Define actions the assistant can take (e.g., look up account, create case, transfer to agent).
   - **Guardrails**: Apply content filters and topic restrictions.

### System Prompt Guidelines

The system prompt shapes the assistant's behavior:

```
You are a helpful customer service assistant for [Company].

Your responsibilities:
- Answer billing questions using the knowledge base
- Look up account information when the customer provides their account number
- Transfer to a human agent for complex issues or complaints
- Collect callback information if no agents are available

Tone: Professional, empathetic, concise. Do not use jargon.

Boundaries:
- Never provide legal or medical advice
- Never share internal policies or procedures
- If unsure, offer to transfer to a human agent
```

### Tools Configuration

Tools allow the assistant to take actions during the conversation:

- **Lambda function tools**: The assistant can invoke Lambda functions to look up data, update records, or perform actions.
- **Transfer tool**: Transfer the contact to a specific queue or agent.
- **Knowledge base tool**: Query attached knowledge bases for relevant information.

Each tool has:
- A name and description (used by the model to decide when to use it)
- Input schema (what parameters the tool accepts)
- The underlying resource (Lambda ARN, queue ARN, knowledge base ID)

## Flow Design Patterns

### Pattern 1: Nova Sonic as Primary IVR

Replace the traditional IVR menu entirely with a conversational assistant.

```
Inbound call
  -> Set voice (Nova Sonic compatible voice, Generative style)
  -> Set contact attributes (customer context)
  -> Connect assistant
      -> [Complete]: Transfer to queue / Disconnect
      -> [Error]: Fallback to traditional IVR
```

### Pattern 2: Nova Sonic for Specific Interactions

Use Nova Sonic for complex interactions while keeping traditional IVR for simple ones.

```
Inbound call
  -> Play prompt ("Press 1 for billing, 2 for support, or stay on the line to speak with our AI assistant")
  -> Get customer input (DTMF)
      -> 1: Traditional billing flow
      -> 2: Traditional support flow
      -> Timeout/No match: Connect assistant (Nova Sonic)
```

### Pattern 3: Nova Sonic with Pre-Lookup

Perform a data lookup before engaging Nova Sonic to give it context.

```
Inbound call
  -> Invoke Lambda (customer lookup by ANI)
  -> Set contact attributes (customerName, accountId, tier)
  -> Set voice (Nova Sonic compatible voice, Generative style)
  -> Connect assistant (session attributes include customer context)
      -> Assistant greets by name, has account context
```

### Pattern 4: Post-Assistant Flow

After the assistant interaction, continue the flow for routing or post-processing.

```
Connect assistant
  -> [Complete]
      -> Check contact attributes (did assistant resolve?)
          -> Yes: Disconnect (or survey)
          -> No: Transfer to queue
  -> [Error]
      -> Play prompt ("Let me connect you with an agent")
      -> Transfer to queue
```

## Integration with Contact Attributes

Nova Sonic can read and write contact attributes:

- **Reading**: Session attributes passed to the Connect assistant block are available to the model.
- **Writing**: When the assistant uses tools (Lambda functions), the results can be saved as contact attributes.
- **Post-interaction**: After the Connect assistant block completes, any attributes set during the interaction are available to subsequent flow blocks.

## Integration with Amazon Bedrock Guardrails

Apply guardrails to control the assistant's behavior:

- **Content filters**: Block harmful, offensive, or inappropriate content.
- **Denied topics**: Prevent the assistant from discussing specific topics (e.g., competitor products, legal advice).
- **Word filters**: Block specific words or phrases.
- **Sensitive information filters**: Detect and redact PII (SSN, credit card numbers).
- **Grounding checks**: Ensure responses are grounded in the provided knowledge base, reducing hallucination.

Configure guardrails in Amazon Bedrock and reference the guardrail ID in the Connect assistant configuration.

## Audio and Voice

- Nova Sonic generates its own speech output directly (not via Amazon Polly TTS).
- Voice is selected via the `Set voice` block with **Generative** speaking style.
- Only Nova Sonic-compatible voices are supported (Matthew, Amy, Olivia, Lupe at launch).
- The `Set voice` block must be placed **before** the `Get customer input` block that triggers the Lex bot with Nova Sonic.
- Nova Sonic supports natural conversational patterns:
  - **Barge-in**: The customer can interrupt the assistant mid-sentence.
  - **Back-channeling**: The assistant can acknowledge the customer while they speak.
  - **Natural pacing**: Responses are not rigidly turn-based.

## Monitoring and Analytics

- **CloudWatch Logs**: Flow logging captures Connect assistant block execution, including entry/exit and errors.
- **Contact Lens**: If enabled, Contact Lens processes the full conversation for post-call analytics, sentiment, and categorization.
- **Contact records**: The contact record includes the assistant interaction duration and outcome.
- **Amazon Bedrock logs**: If enabled, Bedrock model invocation logs capture the model's inputs and outputs for debugging and auditing.

## Limits

| Limit | Value |
|-------|-------|
| Maximum assistant interaction duration | Configurable in the block (up to flow execution time limit) |
| Maximum concurrent Nova Sonic sessions | Subject to Bedrock service quotas |
| Maximum tools per assistant | 10 |
| Maximum knowledge bases per assistant | 5 |
| Supported channels | Voice only |
| Supported voices (launch) | Matthew (en-US), Amy (en-GB), Olivia (en-AU), Lupe (es-US) |
| Supported languages | English (US, GB, AU), Spanish (US) at launch; check AWS docs for updates |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|---------|
| Error branch taken immediately | Assistant not configured | Verify the AI assistant exists and is properly configured in the Connect console |
| High latency in responses | Model cold start or complex queries | Monitor Bedrock invocation metrics; consider simplifying the system prompt |
| Assistant not using tools | Tool descriptions unclear | Improve tool names and descriptions so the model understands when to use them |
| Responses not grounded | No knowledge base attached | Attach a Bedrock Knowledge Base; enable grounding guardrails |
| PII in responses | No guardrails configured | Apply Bedrock Guardrails with sensitive information filters |
| Customer cannot interrupt | Barge-in not working | Verify the Connect assistant block configuration; check audio routing |
| Voice not working | Incompatible voice selected | Ensure a Nova Sonic-compatible voice is selected in Set voice block with Generative speaking style |
| Locale not building | Speech model not set | Set Model type to Speech-to-Speech, select Amazon Nova Sonic, then Build language |
| No speech output | Set voice block missing | Add a Set voice block before the Get customer input block with a Nova Sonic-compatible voice |
