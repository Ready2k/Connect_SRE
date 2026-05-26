# Amazon Connect CCP Streams, WebRTC, and State Failures

## Overview
This runbook guides front-line SREs and helpdesk support engineers in diagnosing and resolving browser-based agent connection drops, WebRTC ICE signaling failures, and client-to-backend agent state mismatch errors.

---

## Symptoms & Alarms
* **Symptom**: Agents stuck in "Pending" status in CCP, experiencing "Missed Call" notifications without CCP ringing, or reporting complete voice path silence.
* **Symptom**: Web console errors indicating `WebRTC session creation failed` or `ICE connection state failed`.

---

## Step-by-Step Diagnostics

### 1. Run Connect Endpoint Test Tool
Direct agents to navigate to the official Amazon Connect Endpoint Test utility (`https://<instance-name>.my.connect.aws/endpoint-test/`) to verify local browser WebRTC capacity, microphone access, and socket latency.

### 2. Verify Port Configuration and Firewalls
WebRTC voice data is carried over UDP. Firewall blockages of outbound UDP ports will drop voice packets.
* Verify that agent workstations have outbound UDP traffic open for ports **3478** (STUN/TURN) and **5000-65535** (WebRTC RTP voice stream).

---

## Remediation Actions

### Action A: Force Agent Session Flush
If an agent's state in CCP is misaligned with the Amazon Connect backend (e.g., agent shows `Available` in CCP but is `Offline` in Connect Admin):
1. In the Connect Directory or Admin console, locate the affected agent.
2. Select the agent and click **Logout** from the Admin interface to terminate all active agent browser tokens.
3. Advise the agent to close all browser tabs, open a single fresh tab, sign back in, and test status synchronization.

### Action B: Switch CCP Signaling Protocol
If the agent is behind an aggressive corporate network proxy:
1. Configure Connect CCP Streams initialization parameters (`connect.agent`) to enable **turnForce** or fall back to HTTP-based signaling.
2. Enforce browser configurations to prioritize TCP signaling when UDP WebRTC endpoints are blocked by local firewalls.
