# Evaluations and Quality Management

Amazon Connect provides a comprehensive evaluation framework for assessing agent and self-service interaction performance, automating quality reviews, and driving coaching workflows.

---

## Evaluation Forms

Evaluation forms define the criteria used to assess interactions. They consist of sections, questions, and scoring rules. You can create different forms for each business unit, queue, or for evaluating agent vs. self-service (bot/AI agent) interactions.

### Form Structure

```
Evaluation Form
  |-- Section 1: Greeting & Opening
  |     |-- Question 1.1: Did the agent greet the customer? (Single select)
  |     |-- Question 1.2: Did the agent verify identity? (Single select)
  |
  |-- Section 2: Data Collection
  |     |-- Question 2.1: Were all required fields collected? (Numeric 1-5)
  |     |-- Question 2.2: Was the account number confirmed? (Single select)
  |
  |-- Section 3: Script Adherence
  |     |-- Question 3.1: Did the agent follow the disclosure script? (Single select, critical)
  |     |-- Question 3.2: Was the hold procedure followed? (Single select)
  |
  |-- Section 4: Closing
        |-- Question 4.1: Did the agent summarize next steps? (Single select)
        |-- Question 4.2: Did the agent ask if there was anything else? (Single select)
```

### Question Types

| Type | Description |
|---|---|
| **Single selection** | Choose one option from a predefined list (e.g., Yes/No, Good/Fair/Poor). Can include scoring. |
| **Multiple selection** | Choose multiple answers from a list (e.g., products discussed, non-compliant behaviors). |
| **Text field** | Free-form text response from the evaluator. |
| **Number** | Numeric rating on a defined scale with configurable ranges (e.g., 1-5, 1-10). |
| **Date** | Date picker answer. |

### Conditional Questions

Questions can be conditionally enabled or disabled based on answers to other questions:

- A parent question must be **Single selection** or **Multiple selection** and cannot be optional.
- Configure one or more answer values that trigger the conditional question.
- Conditionally enabled questions are disabled by default; conditionally disabled questions are enabled by default.
- If Gen AI automation is enabled on a conditional question, it counts towards the Gen AI usage limit regardless of whether it was triggered.

### Question Instructions

The **Instructions to evaluators** field provides guidance for both human evaluators and generative AI. Clear, specific instructions improve both human consistency and AI accuracy.

### Scoring

#### Enabling Scoring

1. On the **Scoring** tab, check **Enable scoring**.
2. This enables score assignment on Single select answers and range-based scoring on Number questions.

#### Score Assignment

- **Single select**: Assign a score to each answer option.
- **Number**: Define ranges with scores (e.g., 0 interruptions = 10 points, 1-4 = 5 points, 5-10 = 1 point).
- **Automatic fail**: Any answer can be configured as **0 (Automatic fail)**. This can apply to the section, subsection, or entire form. The evaluation receives a zero score for the affected scope.

#### Weight Distribution

Weights determine each section/question's contribution to the overall score.

- **Weight by section**: Evenly distribute question weights within each section. Set section-level weights.
- **Weight by question**: Set individual question weights directly.
- When you change one weight, others auto-adjust so the total remains 100%.
- **Exclude optional questions from scoring**: Assigns all optional questions a weight of zero and redistributes among remaining questions.
- The overall evaluation score is a weighted average expressed as a percentage (0-100%).

### Form Lifecycle

| State | Description |
|---|---|
| **Draft** | Form is being created or edited. Cannot be used for evaluations. Use **Save draft** to preserve work. |
| **Active** | Form is active and can be used for evaluations. Only one version of a form can be active. Previous versions are preserved for historical evaluations. |
| **Inactive** | Form has been deactivated. Existing evaluations are preserved but no new evaluations can be created. |

Activating a form makes it available to evaluators. The previous version is no longer selectable for new evaluations, but historical evaluations retain their form version.

---

## Manual Evaluations

Quality analysts manually evaluate contacts by:

1. Searching for a contact via Contact Search (or receiving a shared URL/task).
2. On the **Contact details** page, choosing **Evaluations**.
3. Selecting an evaluation form from the dropdown and clicking **Start evaluation**.
4. Reviewing the recording/transcript alongside the form.
5. Answering each question. Use section arrows to collapse/expand long forms.
6. Adding notes (per-question or overall).
7. Choosing **Save** to keep as Draft, or **Submit** to complete.

### Evaluation States

| State | Description |
|---|---|
| **Draft** | Evaluation started but not submitted. Can be edited, returned to later, or deleted. |
| **Submitted** | Evaluation completed and submitted. Can be edited only with Edit permission. Can be resubmitted. |

Optional questions can be skipped or marked as **Not applicable**. A confirmation warning appears before submitting with skipped optional questions.

---

## Automated Evaluations

Automated evaluations use generative AI and Contact Lens analytics to assess conversations at scale without manual reviewer effort.

### How It Works

1. Define an evaluation form with questions suitable for automation.
2. Configure automation on each question (see automation methods below).
3. Enable **Enable fully automated submission of evaluations** toggle.
4. Activate the form.
5. Create a Contact Lens rule that triggers automated evaluation for matching contacts.
6. Contact Lens analyzes each contact, the AI evaluates against the form questions, and completed evaluations are stored with scores and AI-generated justifications.

### Three Automation Methods

#### 1. Contact Lens Categories (Single select and Multiple select)

- Map category presence/absence to answer values.
- Example: If category `ProperGreeting` is present, answer is "Yes".
- For optional questions: first check applicability via a category, then evaluate.
- Multiple selection: all conditions execute sequentially; multiple categories can each select an answer.
- Requires pre-configured Contact Lens rules that categorize contacts.

#### 2. Generative AI (Single select and Text field)

- AI analyzes the transcript using the question title and instructions.
- Provides an answer with justification.
- Clear, complete sentences in question titles and specific evaluation criteria in instructions improve accuracy.
- Cannot currently automate evaluations of self-service (bot/AI agent) interactions.

#### 3. Metrics (Number questions)

- Automatically fill numeric answers using Contact Lens metrics (sentiment score, non-talk time percentage, interruption count) or contact metrics (longest hold duration, number of holds, agent interaction duration).

### Capabilities

- **Scale** -- Evaluate 100% of contacts automatically (vs. typical 1-3% manual sample).
- **Consistency** -- Every contact assessed against the same criteria, eliminating evaluator bias.
- **Speed** -- Evaluations available shortly after contact completion.
- **Coverage** -- Identify issues across the entire contact volume.

### Limitations

- Not all question types are automatable. Free-form judgment questions may require manual review.
- Accuracy depends on Contact Lens transcription quality and the clarity of evaluation criteria.
- Automated evaluations should be periodically validated against manual evaluations for calibration.
- Gen AI automation on conditional questions counts toward usage limits even if not triggered.

---

## Generative AI Recommendations (Ask AI)

When performing manual evaluations, generative AI can pre-populate answers:

1. Open a contact for evaluation.
2. Select an evaluation form.
3. Click **Ask AI** / **Get AI recommendations**.
4. Review each recommendation with its confidence level and justification.
5. Accept, modify, or override as needed.
6. Submit the evaluation.

This accelerates manual evaluation while maintaining human oversight. Requires the **Evaluation forms - ask AI assistant** permission.

---

## Screen Recording

Screen recording captures the agent's desktop during interactions, enabling reviewers to see exactly what the agent did during the contact.

### What It Captures

- Agent's CCP (Contact Control Panel) actions.
- Applications the agent accessed.
- Data entry and navigation.
- Screen content visible to the agent.

### Configuration

- Enabled per contact flow using the `Set recording and analytics behavior` block.
- Requires the Amazon Connect agent workspace or a supported CCP.
- Recordings are stored in the configured S3 bucket.

### Viewing

- Screen recordings are available on the Contact details page.
- Playback is synchronized with the audio recording and transcript.
- Reviewers can see agent actions alongside what was being said.

### Use Cases

- Verify data entry accuracy.
- Identify workflow inefficiencies.
- Detect unauthorized application usage.
- Training material creation.

---

## Coaching Workflows

Coaching connects evaluation results to agent development.

### Creating a Coaching Plan

1. From a completed evaluation, select **Create coaching plan**.
2. Include specific interaction examples (the evaluated contact).
3. Define coaching objectives and focus areas based on the evaluation scores.
4. Add notes and guidance for the agent.
5. Assign a coach and participant(s).

### Agent Experience

1. Agent receives a notification about the coaching plan.
2. Agent reviews the evaluation, feedback, and interaction examples.
3. Agent can listen to the recording and read the transcript of the example interaction.
4. Agent acknowledges the coaching plan.
5. Agent can add their own notes and comments.

### Manager Tracking

- Track coaching plan status (pending, acknowledged, completed).
- View coaching history per agent.
- Correlate coaching with subsequent evaluation score improvements.

---

## Calibration Sessions

Calibration ensures consistency across evaluators:

- Admins create calibration sessions assigning the same contact to multiple evaluators.
- Each evaluator independently evaluates the contact.
- Compare scores across evaluators to identify discrepancies.
- Calibration evaluations are distinguished from standard evaluations via `evaluation_type` field.
- Requires **Evaluation forms - manage calibration sessions** permission.

---

## Contact Sampling

Managers can randomly sample agents' contacts for evaluation:

- Select agents (e.g., all agents in a hierarchy).
- Specify sample size (e.g., 5 random contacts per agent).
- Define time range (e.g., last week).
- Requires **Sample contacts** permission.

---

## Rules Integration

Contact Lens rules can trigger automated evaluations:

1. Create a rule with conditions (e.g., specific categories, sentiment thresholds).
2. Set the rule action to submit an automated evaluation using a specific form.
3. Matching contacts are automatically evaluated and results stored.

---

## Permissions

### Evaluation Form Permissions

| Permission | Description |
|---|---|
| **Evaluation forms - manage form definitions - Create** | Create new evaluation forms. |
| **Evaluation forms - manage form definitions - View** | View evaluation forms. |
| **Evaluation forms - manage form definitions - Edit** | Edit evaluation forms. |
| **Evaluation forms - manage form definitions - Delete** | Delete draft evaluation forms. |

### Evaluation Execution Permissions

| Permission | Description |
|---|---|
| **Evaluation forms - perform contact evaluations - View** | View submitted evaluations on accessible contacts (subject to tag-based access control). |
| **Evaluation forms - perform contact evaluations - Create** | Create new evaluations, view and edit draft evaluations. Also enables search evaluations by form, score, date, evaluator, status. |
| **Evaluation forms - perform contact evaluations - Edit** | Edit submitted evaluations. |
| **Evaluation forms - perform contact evaluations - Delete** | Delete draft and submitted evaluations. |
| **Evaluation forms - view my received evaluations** | Agents can search for and view completed evaluations they received (not drafts/under review/calibrations). |
| **Evaluation forms - ask AI assistant** | Access the Ask AI button for Gen AI recommendations during evaluations. |
| **Evaluation forms - manage calibration sessions** | Create and manage calibration sessions. |
| **Sample contacts** | Randomly sample agents' contacts for evaluation. |

### Coaching Permissions

| Permission | Description |
|---|---|
| **Coaching - my coaching sessions - View** | View sessions where you are coach or participant. |
| **Coaching - my coaching sessions - Create** | Create sessions with yourself as coach. |
| **Coaching - my coaching sessions - Edit** | Edit sessions where you are coach. |
| **Coaching - my coaching sessions - Delete** | Delete sessions where you are coach. |
| **Coaching - manage coaching sessions - View** | View any coaching session (admin/QA manager). |
| **Coaching - manage coaching sessions - Create** | Create sessions and assign any user as coach. |
| **Coaching - manage coaching sessions - Edit** | Edit any coaching session. |
| **Coaching - manage coaching sessions - Delete** | Delete any coaching session. |

### Additional Required Permissions

| Permission | Description |
|---|---|
| **Rules** | Create, view, edit, delete rules for contact categorization and automated evaluation triggers. |
| **Screen recordings - View** | View screen recordings on contact details page. |
| **Recorded conversations - Listen** | Listen to call recordings during evaluations. |

---

## APIs

### Form Management

| API | Description |
|---|---|
| `CreateEvaluationForm` | Create a new evaluation form in Draft state. |
| `UpdateEvaluationForm` | Update a draft evaluation form. |
| `ActivateEvaluationForm` | Activate a draft form, making it available for evaluations. |
| `DeactivateEvaluationForm` | Deactivate an active form. |
| `DescribeEvaluationForm` | Get details of an evaluation form. |
| `ListEvaluationForms` | List all evaluation forms in the instance. |
| `ListEvaluationFormVersions` | List versions of a specific evaluation form. |
| `DeleteEvaluationForm` | Delete a draft evaluation form. |

### Evaluation Operations

| API | Description |
|---|---|
| `StartContactEvaluation` | Start an evaluation for a specific contact using a specific form. Creates a Draft evaluation. |
| `UpdateContactEvaluation` | Update answers in a draft evaluation. |
| `SubmitContactEvaluation` | Submit a completed evaluation. |
| `DescribeContactEvaluation` | Get details of a specific evaluation. |
| `ListContactEvaluations` | List evaluations for a specific contact. |
| `SearchContactEvaluations` | Search evaluations across contacts with filters. |
| `DeleteContactEvaluation` | Delete a draft evaluation. |

### Search Filters

`SearchContactEvaluations` supports filtering by:

| Filter | Description |
|---|---|
| **EvaluationFormId** | Specific evaluation form. |
| **AgentId** | Specific agent. |
| **ScoreRange** | Minimum and/or maximum evaluation score. |
| **DateRange** | Evaluation submission date range. |
| **Status** | Draft or Submitted. |
| **AutomaticFail** | Whether the evaluation resulted in an automatic fail. |

---

## Data Model

### Evaluation Record

| Field | Type | Description |
|---|---|---|
| `EvaluationId` | String | Unique evaluation identifier. |
| `ContactId` | String | The evaluated contact. |
| `InstanceId` | String | Connect instance. |
| `EvaluationFormId` | String | The form used. |
| `EvaluationFormVersion` | Integer | Version of the form used. |
| `EvaluatorArn` | String | ARN of the evaluator (user or SYSTEM for automated). |
| `Score` | Object | Overall score percentage and per-section scores. |
| `Answers` | Map | Map of question ID to answer value, score, and notes. |
| `Notes` | Object | Overall evaluation notes. |
| `Status` | String | DRAFT or SUBMITTED. |
| `AutomaticFail` | Boolean | Whether any critical section triggered an automatic fail. |
| `CreatedTime` | ISO 8601 | When the evaluation was created. |
| `SubmittedTime` | ISO 8601 | When the evaluation was submitted. |
| `EvaluationSource` | String | Manual, assisted automation, or fully automatic. |
| `EvaluationType` | String | Standard or calibration. |
| `Resubmitted` | Boolean | Whether the evaluation was resubmitted. |
| `AcknowledgementStatus` | String | ACKNOWLEDGED or UNACKNOWLEDGED. |
| `EvaluatedParticipantRole` | String | Role of evaluated participant (agent, bot, AI agent). |

---

## Best Practices

1. **Start with 3-5 sections** -- Keep forms focused. Too many questions lead to evaluator fatigue and inconsistency.
2. **Use critical sections sparingly** -- Reserve automatic fail for true compliance requirements, not quality preferences.
3. **Write clear instructions** -- Specific, complete-sentence instructions improve both human and AI evaluation accuracy.
4. **Calibrate regularly** -- Have multiple evaluators assess the same contacts and compare scores to ensure consistency.
5. **Combine automated + manual** -- Use automated evaluations for coverage and manual evaluations for nuanced assessment.
6. **Close the loop** -- Always create coaching plans for low scores. Evaluations without follow-up do not improve performance.
7. **Version forms carefully** -- When updating criteria, create a new version rather than modifying the active form to preserve historical comparability.
