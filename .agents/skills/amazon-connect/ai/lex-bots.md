# Amazon Lex Integration with Amazon Connect

## Overview

Amazon Lex is natively integrated with Amazon Connect to provide conversational IVR (Interactive Voice Response) and chatbot capabilities. Lex handles natural language understanding (NLU) for intent detection and slot filling, automatic speech recognition (ASR), and neural text-to-speech (TTS).

**Important:** Amazon Lex V1 (Classic) end of support is September 15, 2025. After that date, you cannot access the Lex V1 console or resources. Migrate to Amazon Lex V2.

---

## Core Capabilities

### Natural Language Understanding (NLU)

Lex NLU performs intent detection and entity extraction:

- **Intent detection** -- identifies what the customer wants to do from their utterance
- **Slot filling** -- extracts structured data (dates, numbers, names, etc.) from free-form speech or text
- **Confirmation prompts** -- verifies extracted data with the customer before proceeding
- **Fallback intents** -- handles unrecognized utterances gracefully

### Automatic Speech Recognition (ASR)

- **25+ languages and locales** supported for speech-to-text
- Optimized for telephony audio (8kHz)
- Supports DTMF input alongside voice
- Confidence scores on transcriptions
- Custom vocabularies for domain-specific terms (product names, acronyms)

### Neural Text-to-Speech (TTS)

- **30+ languages** supported for text-to-speech
- Neural voices for natural-sounding responses
- SSML support for fine-grained speech control (pauses, emphasis, pronunciation)
- Multiple voice options per language (male/female, different styles)
- Default voice for Connect is Joanna

---

## Lex V2 Bot Setup

### Creating a Lex V2 Bot

1. Open the Amazon Lex V2 console
2. Choose **Create bot** > **Create a blank bot**
3. Configure bot settings:
   - **Bot name** -- descriptive name for the bot
   - **IAM permissions** -- select existing role or create a new one with basic Lex permissions
   - **COPPA** -- whether the bot is subject to Child Online Privacy Protection Act
   - **Session timeout** -- how long to wait for caller input before ending the session
4. Choose **Next**
5. Configure language and voice:
   - **Language** -- select language and locale from supported list
   - **Voice interaction** -- select the voice for the bot (default: Joanna)
6. Choose **Done**

### Creating Intents

Each intent represents a customer goal:

1. On the Intents page, choose **Add intent** > **Add empty intent**
2. Enter the intent name (e.g., `AccountLookup`)
3. Add **sample utterances** -- phrases customers might say to trigger this intent
   - Include both voice utterances ("Check my account balance") and DTMF equivalents ("One")
   - Lex does not support numeric input directly in V1 Classic -- use word form ("one" not "1"); V2 handles both
4. Add **slots** for data collection:
   - Set Required/Optional
   - Choose slot type (e.g., `AMAZON.Number`)
   - Add elicitation prompt (e.g., "Using your touch-tone keypad, please enter your account number")
5. Add **closing responses** -- message after intent is fulfilled
6. Choose **Save intent**

### Slot Types

**Built-in slot types:**
- `AMAZON.Number` -- numeric values
- `AMAZON.Date` -- date values
- `AMAZON.Time` -- time values
- `AMAZON.PhoneNumber` -- phone numbers
- `AMAZON.EmailAddress` -- email addresses
- `AMAZON.City`, `AMAZON.Country`, `AMAZON.State` -- geographic entities
- `AMAZON.FirstName`, `AMAZON.LastName` -- person names
- `AMAZON.AlphaNumeric` -- alphanumeric strings
- Many more domain-specific types

**Custom slot types:**
- Define your own slot types with specific values
- Add synonyms for each value
- Example: a `ProductCategory` slot with values "laptop", "desktop", "tablet"

**Composite slot types (V2):**
- Combine multiple slot types into a single composite slot
- Useful for complex data structures like addresses (street + city + state + zip)

### Slot Elicitation

**Prompts:**
- Write prompts natural for spoken conversation, not written text
- Example: "What date would you like to schedule?" instead of "Enter date (YYYY-MM-DD)"
- Multiple prompt variations for natural conversation flow

**Validation:**
- Lambda CodeHook can validate slot values during elicitation
- Return validation failure message to re-prompt the customer
- Set maximum retry count before falling back

**Confirmation:**
- Enable confirmation prompts to verify extracted data before fulfillment
- "I have your appointment for Tuesday at 2 PM. Is that correct?"
- Confirmation status: `Confirmed`, `Denied`, `None`

---

## Bot Versioning and Aliases

### Versions

1. Navigate to **Bot versions** in the left menu
2. Choose **Create version**
3. Review bot configuration and confirm
4. Creates an immutable snapshot (Version 1, Version 2, etc.)
5. You can switch versions on an alias without tracking which version is published

### Aliases

1. Navigate to **Aliases** in the left menu
2. Choose **Create alias**
3. Enter an alias name (e.g., `Production`)
4. Associate with a specific bot version (e.g., Version 1)
5. Choose **Create**

**Important:**
- **Never use `TestBotAlias` (V2) or `$LATEST` (V1 Classic) in production** -- they support a limited number of concurrent calls
- Always create a named alias for production and associate it with a specific bot version
- Runtime quotas for test aliases are significantly lower than production aliases

---

## Adding the Bot to Connect

### Lex V2

1. Open the Connect console and select your instance
2. Navigate to **Flows** in the left menu
3. Under **Amazon Lex**, select the Region of your Lex bot
4. Select the bot name from the dropdown
5. Select the bot alias from the dropdown
6. Choose **+ Add Lex Bot**

**Resource-based policies:** When you associate a Lex bot with Connect, the resource-based policy on the bot is automatically updated to grant Connect permission to invoke the bot.

### Lex V1 Classic

1. Same steps but select the bot with "(Classic)" suffix
2. Enter the alias name in the Alias field manually

---

## Connect Flow Integration

### Get Customer Input Block

The primary integration point is the **Get customer input** flow block:

```
Get customer input
  --> Input type: Amazon Lex
  --> Lex bot: MyBot
  --> Alias: Production (or set manually via ARN)
  --> Intents:
      --> BookAppointment --> [next block]
      --> CancelAppointment --> [next block]
      --> FallbackIntent --> [fallback handling]
  --> Error --> [error handling]
```

**Configuration options:**

- **Lex bot name and alias** -- which bot and version to invoke
- **Manual ARN** -- for V2 bots, you can set the bot alias ARN manually or via a dynamic attribute
- **Session attributes** -- key-value pairs passed to Lex (and available in Lambda fulfillment)
- **DTMF input** -- enable digit input alongside voice
- **Timeout** -- how long to wait for customer input
- **Barge-in** -- allow customers to interrupt the prompt

**V2 language requirement:** Your Connect language attribute must match the language model used to build your Lex V2 bot. Use a Set voice block or Set contact attributes block to set the language.

**Multi-locale tip:** If your business uses multiple locales in a single bot, add a Set contact attributes block at the beginning of your flow using the `$.LanguageCode` system attribute.

### DTMF Input Configuration

- Customers can press digits on their keypad instead of speaking
- Map digit utterances to intents (e.g., utterance "One" or "1" maps to `AccountLookup` intent)
- **Terminator character** -- configure the character that signals end of DTMF input (default: `#`)
- **Input timeout** -- how long to wait between digit presses before processing
- DTMF and voice can be used simultaneously -- whichever input arrives first is processed
- Always offer a DTMF option alongside voice input for accessibility

### Session Attributes

Lex session attributes provide a bidirectional data channel between the Connect flow and the Lex bot:

**Flow --> Lex (setting attributes before the Get Customer Input block):**

```
Set contact attributes
  Namespace: Lex
  Key: customerTier
  Value: $.Attributes.customerTier
```

**Lex --> Flow (reading attributes after the Get Customer Input block):**

```
Check contact attributes
  Namespace: Lex
  Key: appointmentDate
  Condition: Is set --> [proceed]
```

**Accessing slot values in flows:**

```
Check contact attributes
  Namespace: Lex
  Key: slots.PhoneNumber
  Condition: Is set --> [proceed with phone number]
```

Or use a Lambda function for complex slot processing.

**Common session attribute patterns:**

| Attribute | Direction | Purpose |
|-----------|-----------|---------|
| `customerTier` | Flow --> Lex | Customize bot behavior based on customer segment |
| `language` | Flow --> Lex | Set bot language preference |
| `appointmentDate` | Lex --> Flow | Extracted slot value for downstream processing |
| `intentName` | Lex --> Flow | The matched intent name |
| `confirmationStatus` | Lex --> Flow | Whether the customer confirmed (Confirmed/Denied/None) |
| `Tool` | Lex --> Flow | Return to Control tool name (for agentic self-service) |

### Confidence Scores and NLU Branching

- Lex returns an NLU confidence score (0.0-1.0) for each matched intent
- Configure confidence thresholds to avoid false-positive intent matches
- Route low-confidence results to the FallbackIntent or a disambiguation prompt
- Use `$.Lex.IntentConfidence` in flow branching to make routing decisions based on confidence level

---

## Multi-Turn Conversations

### Session State Management

Lex manages session state across multiple turns of conversation:

- **Dialog delegation** -- Lex automatically manages the dialog flow, prompting for missing slots and confirming values
- **ElicitSlot** -- bot asks for a specific slot value
- **ElicitIntent** -- bot asks the customer what they want to do
- **ConfirmIntent** -- bot confirms the customer's intent before fulfillment
- **Close** -- bot completes the interaction
- **Delegate** -- Lex determines the next action automatically

**Session state persists across turns:**
- Slot values filled in earlier turns are retained
- Session attributes carry forward
- Context from previous intents can influence subsequent intent matching

### Intent Chaining and Follow-Up Intents

- After fulfilling one intent, the bot can transition to another intent
- Use Lambda fulfillment to set the next intent via `dialogAction`
- Example: after `CheckBalance`, automatically transition to `MakePayment` if the balance is overdue
- Follow-up intents allow natural conversation flow without restarting the bot

---

## Lambda Fulfillment

### CodeHook Integration

Lex can invoke Lambda functions for slot validation and fulfillment:

```javascript
exports.handler = async (event) => {
  const intentName = event.sessionState.intent.name;
  const slots = event.sessionState.intent.slots;

  if (intentName === "CheckOrderStatus") {
    const orderNumber = slots.OrderNumber?.value?.interpretedValue;
    
    // Look up order in backend system
    const orderStatus = await lookupOrder(orderNumber);

    return {
      sessionState: {
        dialogAction: { type: "Close" },
        intent: {
          name: intentName,
          state: "Fulfilled",
          slots: slots,
        },
        sessionAttributes: {
          orderStatus: orderStatus,
          orderNumber: orderNumber,
        },
      },
      messages: [
        {
          contentType: "PlainText",
          content: `Your order ${orderNumber} is currently ${orderStatus}.`,
        },
      ],
    };
  }
};
```

### Dialog Delegation

- **Delegate** -- let Lex manage the dialog automatically based on bot configuration
- **ElicitSlot** -- explicitly ask for a specific slot
- **ElicitIntent** -- ask the customer for a new intent
- **ConfirmIntent** -- confirm before fulfilling
- **Close** -- end the dialog with a fulfillment message

### Slot Validation via Lambda

```javascript
// Validate a slot value and re-prompt if invalid
if (intentName === "BookAppointment" && event.invocationSource === "DialogCodeHook") {
  const date = slots.AppointmentDate?.value?.interpretedValue;
  
  if (date && isPastDate(date)) {
    return {
      sessionState: {
        dialogAction: {
          type: "ElicitSlot",
          slotToElicit: "AppointmentDate",
        },
        intent: {
          name: intentName,
          state: "InProgress",
          slots: {
            ...slots,
            AppointmentDate: null, // Clear invalid value
          },
        },
      },
      messages: [
        {
          contentType: "PlainText",
          content: "The date you provided is in the past. Please provide a future date.",
        },
      ],
    };
  }
}
```

---

## Generative AI Features

Lex includes several generative AI enhancements powered by Amazon Bedrock:

### LLM-Assisted Slot Resolution

The LLM helps resolve ambiguous slot values that traditional NLU would miss:

- Understands context to fill slots more accurately
- Handles synonyms and paraphrasing (e.g., "tomorrow" --> actual date)
- Resolves entity references across turns (e.g., "the first one" referring to a previously listed option)

### Conversational FAQs

Connect a knowledge base to the Lex bot for FAQ handling:

- Lex queries the knowledge base when no intent matches
- Generates natural language answers from KB content
- Falls back gracefully if no relevant content is found
- No need to define intents for every possible FAQ -- the KB handles the long tail

### Sample Utterance Generation

AI-assisted bot building:

- Provide a few example utterances for an intent
- The LLM generates additional diverse utterances automatically
- Expands coverage without manual effort
- Reduces the chance of missed intent matches in production

### Bot Creation from Natural Language Description

Create a bot by describing what it should do in plain English:

- Describe the use case: "I need a bot that handles appointment scheduling, cancellations, and rescheduling for a dental office"
- Lex generates intents, slots, sample utterances, and confirmation prompts
- Review, refine, and deploy
- Significantly accelerates bot development for standard use cases

---

## Bot Architecture for Connect

### Recommended Structure

```
Lex Bot (e.g., "CustomerServiceBot")
  |
  +-- Intent: Greeting
  |     Utterances: "hello", "hi", "good morning"
  |     Fulfillment: Return to flow
  |
  +-- Intent: CheckOrderStatus
  |     Slots: OrderNumber (AMAZON.Number)
  |     Utterances: "where is my order", "check order {OrderNumber}"
  |     Fulfillment: Lambda function
  |
  +-- Intent: TransferToAgent
  |     Utterances: "speak to someone", "transfer me", "agent"
  |     Fulfillment: Return to flow (route to queue)
  |
  +-- Intent: FallbackIntent (built-in)
        Fulfillment: Conversational FAQ or escalation
```

### Interactive Messages for Chat

- Lex can power interactive messages for Connect chat
- Rich messages with prompts and pre-configured display options for customer selection
- Configured through Lex using a Lambda function
- Provides visual UI elements (buttons, lists, carousels) in the chat interface

---

## Building and Testing

### Build

1. After configuring intents and slots, choose **Build** at the bottom of the page
2. Build may take a minute or two
3. Must rebuild after any changes to intents, slots, or utterances

### Test

1. Choose **Test** after build completes
2. In the **Test Draft version** pane, type utterances to test intent matching
3. Test both voice utterances ("Check my account balance") and DTMF equivalents ("1")
4. Clear the test box between intent tests
5. Always test in the actual Connect telephony environment -- ASR behaves differently with 8kHz telephony audio vs. 16kHz

---

## Creating a Flow with Lex

### Complete Flow Example

1. Add a **Get customer input** block connected to the Entry point
2. Configure with text-to-speech prompt matching your intents: "To check your account balance, press or say 1. To speak to an agent, press or say 2."
3. Select the **Amazon Lex** tab, choose your bot and alias
4. Add intents: `AccountLookup`, `SpeakToAgent`

**For the AccountLookup branch:**
5. Add a **Play prompt** block with the result message
6. Connect to a **Disconnect** block

**For the SpeakToAgent branch:**
7. Add a **Set working queue** block to set the target queue
8. Add a **Transfer to queue** block
9. Connect Success to the transfer

10. Choose **Save**, then **Publish**

### Assign the Flow to a Phone Number

1. In Connect console, choose **Routing** > **Phone numbers**
2. Select the phone number
3. In the **Flow/IVR** dropdown, choose your new flow
4. Choose **Save**

---

## Multi-Language Support

### Voice Languages (ASR) -- 25+ Locales

| Language | Locale Code |
|----------|-------------|
| English (US) | `en_US` |
| English (UK) | `en_GB` |
| English (AU) | `en_AU` |
| Spanish (US) | `es_US` |
| Spanish (ES) | `es_ES` |
| French (FR) | `fr_FR` |
| French (CA) | `fr_CA` |
| German | `de_DE` |
| Italian | `it_IT` |
| Portuguese (BR) | `pt_BR` |
| Japanese | `ja_JP` |
| Korean | `ko_KR` |
| Chinese (Mandarin) | `zh_CN` |
| Hindi | `hi_IN` |
| Arabic | `ar_SA` |

### TTS Languages -- 30+

Neural TTS supports all ASR languages plus additional locales. Each language typically offers multiple voice options.

### V2 Language Matching

For Lex V2 bots, the Connect language attribute must match the Lex bot's language model:
- Use a **Set voice** block to set the Connect language
- Or use a **Set contact attributes** block with the language code
- For multi-locale bots, use `$.LanguageCode` system attribute at the start of the flow

---

## Contact Lens Integration with Lex

- Contact Lens can analyze conversations that include Lex bot interactions
- Real-time and post-contact analytics apply to the full conversation (bot + agent segments)
- Sentiment analysis captures customer sentiment during bot interactions
- Categorization rules can reference content from the Lex portion of the conversation

---

## Quotas

| Item | Specification |
|------|---------------|
| Chat Amazon Lex bot integration timeout | 10 seconds |
| Concurrent calls (TestBotAlias / $LATEST) | Limited (use production alias) |

---

## Best Practices

1. **Use bot aliases** -- never point production flows at `$LATEST` or `TestBotAlias`; use a named alias with version pinning
2. **FallbackIntent is critical** -- always configure a meaningful fallback that either retries, escalates, or queries a FAQ knowledge base
3. **Session attributes for context** -- pass customer context (tier, language, account info) from the flow to the bot to enable personalized responses
4. **DTMF fallback** -- for IVR, always offer a DTMF option alongside voice input for accessibility
5. **Test with telephony audio** -- Lex ASR behaves differently with 8kHz telephony audio vs. 16kHz; always test in the actual Connect environment
6. **Slot elicitation prompts** -- write prompts that are natural for spoken conversation, not written text
7. **Confidence thresholds** -- configure NLU confidence thresholds to avoid false-positive intent matches; route low-confidence results to fallback
8. **Disambiguation** -- when multiple intents match with similar confidence, present the customer with options rather than guessing
9. **Error handling** -- always wire the Error branch of the Get customer input block to a graceful fallback (transfer to agent, retry, or informative message)
10. **Lambda validation** -- use CodeHook for real-time slot validation to catch errors early in the conversation
11. **Resource-based policies** -- Connect automatically manages Lex permissions when you associate the bot; no manual IAM policy updates needed
12. **Rebuild after changes** -- always rebuild the bot after modifying intents, slots, or utterances before testing
