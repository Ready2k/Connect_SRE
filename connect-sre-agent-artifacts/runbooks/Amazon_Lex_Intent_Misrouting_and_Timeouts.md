# Amazon Lex Intent Misrouting and Timeout Triage

## Overview
This runbook covers diagnostics and quick remediation actions for high fallback rates, intent misclassification loops, or response timeouts in Amazon Lex bots integrated with Amazon Connect.

---

## Symptoms & Alarms
* **Alarm**: `Lex-Bot-Fallback-Rate-High-Alert` (Spike in `FallbackIntent` triggers).
* **Symptom**: Customers stuck in conversational loops, Lex repeatedly eliciting the same slot, or silent timeouts during the speech-to-text input phases.

---

## Step-by-Step Diagnostics

### 1. Inspect Bot Fulfillment Lambda Logs
Most Lex bots delegate slot validation and fulfillment to an backend Lambda. If this Lambda crashes or takes longer than the Lex timeout threshold, Lex defaults to fallback.
* Check CloudWatch logs for `/aws/lambda/<Lex-Fulfillment-Lambda-Name>`.
* Look for `Task timed out after X seconds` or `NullPointerException` errors.

### 2. Identify Speech-to-Text (STT) Quality & Threshold Issues
* High noise floor on telephony streams can distort voice inputs.
* Check Lex runtime logs or Connect Contact Lens transcripts to see if the confidence score for recognized intents falls below the classification threshold (typically `0.4`).

---

## Remediation Actions

### Action A: Revert Bot Alias to Stable Version
If a new draft or bot version was recently published to the Connect-active alias:
1. Open the Amazon Lex V2 console.
2. Select the affected Bot and navigate to **Aliases**.
3. Select the alias (e.g., `Live` or `Prod`).
4. Change the bot version associated with the alias back to the previous stable numeric version (e.g., from `Version 5` to `Version 4`).
5. Wait 30 seconds for the change to propagate globally.

### Action B: Fallback to DTMF / Keypad Input
If speech recognition is consistently failing due to audio channel degradation, modify the Connect flow to utilize **DTMF (Keypad entry)** for routing rather than natural language understanding (NLU).
