# Amazon Connect Generative AI Features

## Overview

Amazon Connect integrates generative AI across multiple touchpoints in the contact center workflow -- from post-contact analysis to manager-level insights. These features are distinct from the agentic self-service and agent-assist capabilities covered in [connect-ai-agents.md](./connect-ai-agents.md) and focus on supervisory, quality, and operational use cases.

---

## Post-Contact Summaries

### How It Works

After a voice contact ends, Amazon Connect automatically generates a structured, concise summary of the conversation using generative AI. The summary is displayed on the Contact Control Panel (CCP) or custom agent desktop.

### Key Characteristics

- **Voice contacts only** -- summaries are generated from the Contact Lens conversation transcript
- **Displayed on CCP** -- appears in the contact details panel after the call ends, during After Contact Work (ACW)
- **Structured format** -- the summary follows a consistent structure:
  - **Issue** -- what the customer contacted about
  - **Outcome** -- how the issue was resolved (or not)
  - **Action items** -- any follow-up actions required
- **Concise** -- typically 3-5 sentences, designed to be scannable
- **Available via API** -- accessible through Contact Lens contact search results and the `GetContactSummary` API

### Use Cases

- **ACW reduction** -- agents spend less time writing post-call notes; the summary captures the essentials automatically
- **Supervisor review** -- managers can quickly review what happened on a call without listening to the recording
- **Handoff context** -- when a contact is transferred or a follow-up is needed, the summary provides immediate context
- **Compliance documentation** -- structured record of what was discussed and agreed upon

### Configuration

Post-contact summaries are enabled at the instance level and require Contact Lens to be active on the contact flow:

1. Enable Contact Lens on the contact flow (Set recording and analytics behavior block)
2. Enable post-contact summary in the Connect admin console under Analytics and optimization
3. Summaries are generated automatically for all Contact Lens-enabled voice contacts

---

## Conversational Analytics for Email

### How It Works

Contact Lens conversational analytics extends to email contacts, enabling automatic categorization, PII redaction, and contact summaries for email interactions.

### Configuration

Add the **Set recording, analytics and processing behavior** block to your flows before an email contact is assigned to your agent or sent to your end customer.

### Customization Options

- **PII redaction types** -- choose which PII types to redact
- **Redaction format** -- show specific PII type indicators (e.g., `[SSN]`) or generic markings (`[PII]`)
- **Storage** -- opt to store both original and redacted versions in separate storage
- **Contact summaries** -- enable or disable summary generation for emails

---

## Generative AI-Powered Email Assistance

### Overview

When an agent accepts an email contact enabled with Connect AI agents, they automatically receive three types of proactive responses in the Connect assistant panel:

1. **Email conversation overview**
2. **Knowledge base and guide recommendations**
3. **Generated email responses**

### Email Conversation Overview

The EmailOverview agent automatically analyzes the email conversation thread and provides a structured overview:

- Customer's key issues
- Previous agent actions (if a reply to another agent's reply on the same thread)
- Important contextual details
- Required next steps

The overview weights the current email message most heavily while maintaining context from previous messages in the thread.

### Knowledge Base and Guide Recommendations

The EmailResponse agent automatically suggests relevant content from your knowledge base:

- Knowledge articles matching the customer's issue
- Step-by-step guides associated with the knowledge article
- Agent can view original sources and preview knowledge base articles in the workspace
- Uses EmailResponse and EmailQueryReformulation prompts for generation

### Generated Email Responses

The EmailGenerativeAnswer agent automatically drafts a response based on the email context and knowledge base:

- Analyzes the email conversation context
- Incorporates relevant knowledge base content
- Generates a professional draft with appropriate greeting, closing, specific answers, and proper formatting
- Agent can:
  - Select an email template for branding and signature
  - Copy the generated response and paste into the editor
  - Use as-is or edit before sending
  - Choose **Regenerate** for a new draft
- Output is raw HTML by default (works with Connect's rich text editor)
- Customize output format by editing `QinConnectEmailGenerativeAnswerPrompt`

**Limitations:**
- Cannot use information from Customer Profiles, Cases, email templates, or quick responses in generated responses
- Generative email is for agent assistance with inbound email contacts only
- Outbound emails sent to the Connect assistant block will incur charges -- add a Check contact attributes block before Connect assistant to prevent this

### Configuration Steps

1. Complete initial setup for AI agents
2. Add a Check contact attributes block to verify it is an email contact
3. Add the Connect assistant block to your flows before the email is assigned to an agent
4. Customize outputs by adding knowledge bases and defining prompts to match your company's language, tone, and policies

### Best Practices for Email AI

- Train agents to review all AI-generated content before sending
- Use email templates for consistent formatting
- Maintain up-to-date knowledge base content for better response quality
- Use AI guardrails to ensure appropriate content generation
- Monitor AI agent performance through CloudWatch logs:
  - `TRANSCRIPT_RESULT_FEEDBACK` -- agent feedback on responses
  - `TRANSCRIPT_RECOMMENDATION` -- generated responses shown to agents

---

## Generative AI-Powered Evaluation Recommendations

### How It Works

When managers evaluate agent performance using evaluation forms, generative AI can automatically populate form fields with recommended scores and justifications based on the contact transcript and recording.

### Key Characteristics

- **Auto-populate evaluation forms** -- AI analyzes the transcript and suggests scores for each evaluation criterion
- **Justification text** -- each recommended score includes a text explanation referencing specific parts of the conversation
- **Manager review required** -- recommendations are suggestions, not final scores; the manager reviews and can override
- **Criteria-aware** -- the AI understands the evaluation form structure and maps conversation evidence to specific criteria
- **Automated evaluations** -- can be run automatically for voice and chat contacts analyzed by Contact Lens
- **Bot and AI agent evaluations** -- automated evaluations support both agent interactions and automated interactions (bots, AI agents)

### Supported Evaluation Criteria

The AI can provide recommendations for common evaluation dimensions:

| Criterion | What AI Evaluates |
|-----------|-------------------|
| Greeting/Opening | Did the agent greet the customer professionally? |
| Active listening | Did the agent acknowledge and paraphrase customer concerns? |
| Problem resolution | Was the customer's issue resolved during the contact? |
| Hold/transfer handling | Were holds and transfers handled according to procedure? |
| Compliance | Did the agent follow required scripts and disclosures? |
| Closing | Did the agent summarize, confirm next steps, and close professionally? |
| Empathy | Did the agent demonstrate empathy and emotional awareness? |
| Knowledge | Did the agent demonstrate product/process knowledge? |

### Multi-Language Support

Automated evaluations support multiple languages:
- Portuguese, French, Italian, German, and Spanish
- Managers define custom evaluation criteria in natural language
- AI generates evaluations with justifications in the preferred language
- **Cross-language evaluation** -- can complete assessments in English even when the conversation is in another language
- Enables standardized evaluation frameworks across multilingual contact centers

### Workflow

1. Manager opens a completed contact for evaluation
2. Selects an evaluation form
3. Clicks "Get AI Recommendations" (or recommendations auto-populate if configured)
4. AI fills in recommended scores and justification text for each applicable criterion
5. Manager reviews, adjusts scores as needed, adds manual notes
6. Manager submits the final evaluation

### Evaluation Form Configuration

- Manual evaluations supported for all contact types (voice, chat, email, task)
- Automated evaluations for voice and chat contacts analyzed by Contact Lens
- Forms support up to 100 sections and 100 questions
- Up to 50 versions per form, 400 forms per instance
- Maximum 3,000 evaluations per agent per month
- Section nesting up to 2 levels (sections can have sub-sections)

### Benefits

- **Consistency** -- reduces evaluator bias by providing an objective AI baseline
- **Speed** -- evaluations that took 15-20 minutes can be completed in 5 minutes
- **Coverage** -- enables evaluating a larger percentage of contacts since each evaluation takes less time
- **Calibration** -- AI recommendations serve as a calibration tool across evaluation teams

---

## AI-Powered Contact Categorization

### How It Works

Contact Lens automatically categorizes contacts based on rules that analyze conversation content, sentiment, and other attributes.

### Rule Types

- **Post-call rules** -- analyze completed voice contacts (up to 500 rules)
- **Post-chat rules** -- analyze completed chat contacts (up to 500 rules)
- **Real-time rules** -- analyze contacts during the conversation (up to 500 rules)
- **Email rules** -- analyze email contacts (up to 15 rules with natural language condition)

### Condition Types for Categorization

| Condition Type | Post-call | Post-chat | Real-time |
|---------------|-----------|-----------|-----------|
| Words/phrases -- exact match (up to 100 entries) | Yes | Yes | Yes |
| Words/phrases -- semantic match (up to 4 entries) | Yes | Yes | No |
| Words/phrases -- pattern match (up to 100 entries) | Yes | Yes | Yes |
| Natural language -- semantic match (1 entry) | Yes | Yes | No |
| Queue condition (up to 100 selections) | Yes | Yes | Yes |
| Agent condition (up to 100 selections) | Yes | Yes | Yes |
| Custom attributes (up to 5) | Yes | Yes | Yes |
| Sentiment -- time period (up to 5) | Yes | Yes | Yes |
| Sentiment -- entire contact (up to 5) | Yes | Yes | No |
| Interruptions (up to 5) | Yes | Yes | No |
| Response time (up to 4 hours) | No | Yes | No |
| Non-talk time (up to 5 hours) | Yes | No | No |

### Rule Actions

Rules can trigger:
- Task creation (see Tasks channel)
- Email notifications
- EventBridge events
- Contact categorization labels

---

## AI-Powered Manager Assistance (Preview)

### How It Works

Managers can ask natural language questions about their contact center performance and receive AI-generated answers with data, diagnosis, and recommendations.

### Capabilities

- **150+ metrics accessible** -- the AI can query and reason across the full range of Connect metrics including agent scheduling, self-service experience, performance evaluations, and historical data
- **Natural language queries** -- managers ask questions in plain English instead of building reports
- **Instant answers** -- results in seconds, eliminating hours of manual data gathering
- **Diagnosis** -- the AI identifies root causes of performance issues (e.g., "Service level dropped because handle time increased on the Billing queue due to a system outage")
- **Recommendations** -- suggests specific recovery actions (e.g., "Consider adding 3 agents to the Billing queue for the next 2 hours" or "Enable callback on the Support queue to reduce abandonment")

### Example Queries

| Manager Question | AI Response Type |
|-----------------|------------------|
| "Why did our service level drop yesterday?" | Root cause analysis with contributing factors |
| "Which agents are struggling this week?" | Performance ranking with specific areas for improvement |
| "How is the Billing queue performing today?" | Real-time metrics snapshot with trend comparison |
| "What should I do about the high abandonment rate?" | Actionable recommendations with expected impact |
| "Compare this week's performance to last week" | Week-over-week delta analysis across key metrics |
| "Which queue needs the most attention right now?" | Priority ranking based on current performance gaps |
| "Which queues are at risk of missing service level targets?" | Predictive risk assessment with recovery actions |

### Current Status

This feature is in **preview** (announced March 2026). To request access, contact your AWS account team or an AWS Representative.

Limitations:
- Response accuracy depends on the breadth of metrics data available
- Complex multi-factor questions may require follow-up prompts
- Recommendations are suggestions and should be validated by the manager

---

## Coaching Workflows

### How It Works

Managers create structured coaching plans from evaluation scorecards, and agents receive, acknowledge, and track these plans within the Connect agent workspace. Announced March 2026 as an integrated workflow.

### Workflow

```
Evaluation Completed
      |
      v
Manager Reviews Scorecard
      |
      v
Manager Creates Coaching Plan
  - Selects areas for improvement
  - Links specific customer interaction examples
  - Adds specific guidance/instructions
  - Sets target date
  - Optionally links to training resources
      |
      v
Agent Receives Coaching Plan
  - Notification in agent workspace
  - Reviews the plan details
      |
      v
Agent Acknowledges Plan
  - Confirms they've read and understood
  - Can add notes/questions to confirm understanding of expectations and next steps
      |
      v
Progress Tracking
  - Subsequent evaluations show trend
  - Manager monitors improvement
  - Plan can be marked complete
```

### Manager Actions

- **Create coaching plan** -- initiated from a completed evaluation scorecard
- **Select improvement areas** -- choose specific evaluation criteria that need improvement
- **Link interaction examples** -- include specific customer interactions demonstrating the issue
- **Add guidance** -- write specific instructions, best practices, or reference materials
- **Set targets** -- define the expected score improvement and timeline
- **Track progress** -- view agent's subsequent evaluations to measure improvement
- **Close plan** -- mark the coaching plan as complete when targets are met

### Agent Actions

- **View coaching plans** -- see all active coaching plans in the agent workspace
- **Acknowledge plan** -- confirm receipt and understanding
- **Add notes** -- write responses, ask questions, or document self-reflection
- **Track own progress** -- view their evaluation trend over time relative to coaching targets

### Integration Points

- **Evaluation forms** -- coaching plans are linked to specific evaluations and criteria
- **Contact Lens** -- AI-identified patterns can trigger coaching recommendations
- **Performance dashboards** -- coaching plan status and progress are visible in supervisor dashboards
- **Notifications** -- agents receive notifications when new coaching plans are created or updated
- **Single coaching page** -- both managers and agents access all coaching history on a single page for systematic progress tracking

---

## AI-Powered Case Summaries

### How It Works

With a single click, agents or managers can generate a concise case summary even when the case spans multiple interactions, follow-up tasks, and teams. Announced November 2025.

### Key Characteristics

- **Multi-interaction support** -- summarizes across voice, chat, email, and task contacts within a case
- **Cross-team context** -- captures handoffs and actions taken by different teams
- **Structured output** -- captures key details:
  - Issue background
  - Actions taken
  - Next steps
- **Customizable** -- administrators can configure custom prompts and guardrails to align summaries with organizational style and preferences
- **One-click generation** -- agent or manager clicks to generate the summary on demand

### Use Cases

- Reduce manual wrap-up work on complex, multi-touch cases
- Provide context when cases are transferred between teams
- Help new agents quickly understand case history
- Accelerate case resolution by surfacing key details

---

## Automatic Note-Taking

### How It Works

Post-contact summaries serve as automatic structured notes from conversations, eliminating the need for agents to manually write call notes during ACW.

### Output Structure

- **Issue** -- what the customer contacted about
- **Outcome** -- resolution status
- **Action items** -- follow-up tasks or commitments

This structured output reduces ACW time and ensures consistent documentation across all contacts.

---

## Feature Quotas

| Item | Specification |
|------|---------------|
| Contact Lens rules (post-call) | 500 |
| Contact Lens rules (post-chat) | 500 |
| Contact Lens rules (real-time) | 500 |
| Contact Lens rules (email, natural language) | 15 |
| Custom vocabularies | 20 |
| Evaluation forms per instance | 400 |
| Versions per evaluation form | 50 |
| Sections per form | 100 |
| Questions per form | 100 |
| Evaluations per agent per month | 3,000 |
| Section nesting depth | 2 levels |
| Conditions per rule | 20 |

---

## Region Availability

Generative AI features are progressively rolling out across AWS regions:

- **Post-contact summaries** -- available in regions where Contact Lens is supported
- **Automated evaluations** -- multi-language support (English, Portuguese, French, Italian, German, Spanish)
- **Email conversational analytics** -- available where email channel is supported
- **AI-powered manager assistance** -- preview, available in select regions (contact AWS account team)
- **AI-powered case summaries** -- generally available (November 2025)
- **Coaching workflows** -- generally available (March 2026)
- **Email AI (overviews, suggested responses)** -- generally available (October 2025)
- **Predictive insights enhancements** -- preview in Frankfurt, N. Virginia, Seoul, Tokyo, Oregon, Singapore, Sydney, Canada Central

Check the [AWS Region Table](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/) for the latest availability.
