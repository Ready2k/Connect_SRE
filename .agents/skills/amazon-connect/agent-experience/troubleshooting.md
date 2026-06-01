# CCP Troubleshooting Guide

Common issues, diagnostics, and resolution steps for the Amazon Connect Contact Control Panel.

Troubleshooting CCP issues requires support from network operations, system administrator, and virtual desktop (VDI) solution teams. Categorize issues by symptoms to determine appropriate resources to engage.

---

## No Audio Issues

### One-Way Audio (Agent Hears Customer, Customer Does Not Hear Agent)

**Symptoms:** Agent hears the customer but the customer reports silence.

**Causes and fixes:**

1. **Microphone not selected or muted.**
   - Open CCP settings (gear icon) > Audio devices.
   - Verify the correct microphone is selected.
   - Check that the microphone is not muted in the operating system's sound settings.
   - Check for a physical mute switch on the headset.

2. **Microphone permissions denied in browser.**
   - The browser must have permission to access the microphone.
   - Chrome: click the lock icon in the address bar > Site settings > Microphone > Allow.
   - Firefox: click the lock icon > Permissions > Use the Microphone > Allow.
   - Edge: click the lock icon > Site permissions > Microphone > Allow.
   - After changing permissions, refresh the page.

3. **Application has exclusive control of microphone/speaker (Windows).**
   - Another application may have taken exclusive control of the audio device.
   - On Windows: open Sound settings > Playback device > Properties > Advanced tab > uncheck "Allow applications to take exclusive control of this device."
   - On Mac: check Sound settings > Input and verify no other application is using the microphone.

4. **WebRTC media path blocked by firewall.**
   - Softphone uses WebRTC for media. If the outbound UDP path on ports 3478 and 49152-65535 is blocked, media cannot flow.
   - See "Network Diagnostics" section below.

5. **VPN or proxy intercepting media traffic.**
   - Split tunneling must be configured to route media traffic directly, not through the VPN tunnel.
   - See "Corporate Proxy/VPN Issues" section below.

### One-Way Audio (Customer Hears Agent, Agent Does Not Hear Customer)

**Symptoms:** Customer can hear the agent but the agent hears silence.

**Causes and fixes:**

1. **Speaker/headset not selected.**
   - Open CCP settings > Audio devices.
   - Verify the correct output device is selected.
   - Test with the built-in audio check.

2. **Volume muted or too low.**
   - Check the system volume for the selected output device.
   - Check the browser tab volume (some operating systems allow per-tab volume control).

3. **Inbound media blocked by firewall.**
   - The firewall may allow outbound UDP but block inbound media return traffic.
   - Ensure stateful firewall rules allow return UDP traffic.

### No Audio (Both Directions)

**Symptoms:** Neither party hears the other.

**Causes and fixes:**

1. **Softphone not initialized.**
   - The CCP may not have successfully initialized the softphone.
   - Refresh the CCP page.
   - Check the browser console for errors related to `connect-rtc`.

2. **WebRTC entirely blocked.**
   - Some corporate networks block WebRTC entirely.
   - Run the Amazon Connect Endpoint Test Utility (see "Endpoint Test Utility").
   - Switch to desk phone mode as a workaround while network issues are resolved.

3. **Browser does not support WebRTC.**
   - Use a supported browser (see "Browser Issues").

---

## CCP Browser Microphone Access

The CCP conforms to microphone usage guidance specific to each browser:
- Microphone access permission is stored in the browser's memory for the current session.
- **Firefox specifically** requires the CCP tab to be in focus for microphone and audio to pass through.

**Symptoms:** Missed calls when CCP tab has no microphone access or is not in focus.

**Error message:** "Microphone is not accessible" / "Enable access to the microphone and refresh the page"

**Fixes:**
- If using Firefox, ensure agents focus on the CCP tab when accepting voice contacts.
- Use the Endpoint Test Utility to verify browser media device access.
- Check browser permissions for the Connect domain.

---

## CCP Initialization Issues

**Symptoms:** CCP shows "Initialization Failed" error, resulting in missed calls.

**Cause:** Missing domain or port/IP allowlist entries in the agent environment. The CCP initialization depends on API and signaling endpoints accessed via allowlisted domains such as `*{{myInstanceName}}.awsapps.com/connect/api` and `*.transport.connect.{{region}}.amazonaws.com`.

**Error message:** "Initialization Failed" / "Try fixing your connection by logging out, and then logging on again."

**Fixes:**
- Verify all required domains and IP addresses are allowlisted (see "Verify Firewall Rules" below).
- Use the Endpoint Test Utility to check endpoint connectivity.
- Check agent network connections for latency or outages.

---

## CCP WebRTC Issues

**Symptoms:** Missed calls due to WebRTC `ice_collection_timeout`.

**Cause:** Request to Connect Softphone Media (`TurnNlb-xxxxxxxxxxxxx.elb.{{region}}.amazonaws.com:3478?transport=udp`) times out and the CCP cannot collect ICE candidates to establish a connection.

**Error message:** "ice_collection_timeout" / "Call failed due to a browser-side WebRTC issue."

**Fixes:**
- Check firewall/NAT settings to allow UDP 3478 outbound traffic to Amazon Connect Softphone Media.
- Use the Endpoint Test Utility to verify endpoint connectivity.
- Check network conditions for latency or congestion.

---

## Windows 11 Audio Failure on First Call After Reboot

**Symptoms:** Complete audio failure ("dead air") on the first call after a Windows 11 system reboot. Neither agent nor customer can hear each other.

**Root cause:** Two Windows 11 behaviors:
1. The network interface card (NIC) unexpectedly restarts when Chrome/Edge browsers request audio packet prioritization.
2. Volume control adjustments trigger network-related services, causing NIC restarts.

**Affected systems:** Windows 11 workstations with Chrome or Edge browsers.

**Resolution:** Modify the startup type of the following Windows services from **Manual** to **Automatic** (requires admin privileges):
- **qWAVE** (Quality Windows Audio/Video Experience)
- **ndisuio.sys**
- **dmwAppushSvc** (Device Management Wireless Application Protocol Push message Routing Service)
- **SstpSvc** (Secure Socket Tunneling Protocol Service)
- **RasMan** (Remote Access Connection Manager)

This ensures critical services that could restart the NIC are launched before the agent's first call.

---

## Dropped Calls

**Symptoms:** Calls disconnect unexpectedly during handling.

**Causes and fixes:**

1. **Network instability.**
   - WebRTC media requires a stable connection. Packet loss above 5% or latency above 300ms degrades call quality and may cause drops.
   - Test bandwidth and latency using a speed test to the AWS region hosting the Connect instance.
   - If on Wi-Fi, switch to a wired Ethernet connection.

2. **Session timeout.**
   - If the agent's browser session expires, the CCP loses connection.
   - Ensure the agent's browser tab remains active (not sleeping/hibernated).
   - Check for session expiry warnings from the Activity client.

3. **Contact flow timeout.**
   - Some contact flows have timeout branches that disconnect after a set period.
   - Review the contact flow for timeout configurations.

4. **Customer-side disconnect.**
   - The customer may have hung up. Check the CTR for the disconnect reason (`CUSTOMER_DISCONNECT` vs. `AGENT_DISCONNECT` vs. `SYSTEM_ERROR`).

---

## Agent Cannot Sign In

**Symptoms:** Agent sees an error when trying to access the CCP or workspace.

**Causes and fixes:**

1. **User not created in Connect instance.**
   - Verify the agent exists in the Connect console under "User management."

2. **Incorrect credentials.**
   - If using Connect-managed authentication, verify username and password.
   - If using SAML/SSO, verify the SAML identity provider configuration and attribute mappings.

3. **Security profile not assigned.**
   - Every agent must have a security profile assigned. Without one, login fails.

4. **Instance URL incorrect.**
   - Verify the URL format: `https://{instance-alias}.my.connect.aws/agent-app-v2/` for the workspace, or `https://{instance-alias}.my.connect.aws/ccp-v2/` for standalone CCP.

5. **Browser cookies/cache stale.**
   - Clear cookies and cache for the Connect domain.
   - Try an incognito/private browsing window.

6. **Pop-up blocker preventing login window.**
   - The CCP login flow may use a pop-up window.
   - Allow pop-ups for the Connect domain.

---

## CCP Not Loading

**Symptoms:** The CCP iframe shows a blank screen, spinner, or error message.

**Causes and fixes:**

1. **JavaScript errors.**
   - Open the browser developer console (F12 > Console) and check for errors.
   - Common errors: CORS violations, missing resources, Content Security Policy (CSP) blocks.

2. **CSP blocking the iframe.**
   - If the CCP is embedded in a custom page, the page's Content Security Policy must allow the Connect domain.
   - Add `https://{instance}.my.connect.aws` to `frame-src` and `connect-src` CSP directives.

3. **Third-party cookie blocking.**
   - The CCP requires third-party cookies for authentication.
   - Chrome: Settings > Privacy > Cookies > Allow third-party cookies (or add exception for `*.my.connect.aws`).
   - Firefox: Add exception for the Connect domain in Enhanced Tracking Protection settings.
   - Safari: Safari blocks third-party cookies by default. Use a pop-up login flow instead.

4. **Incompatible browser version.**
   - See "Browser Issues" for supported versions.

5. **Network blocking WebSocket connections.**
   - The CCP uses WebSocket connections to `wss://*.transport.connect.aws`.
   - Verify WebSocket traffic is allowed through the firewall/proxy.

---

## Outbound Call Issues

### Invalid Outbound Configuration

**Symptoms:** Agent sees "Invalid outbound configuration" / "Before you can place an outbound call, you must associate a phone number with this queue."

**Fixes:**
1. Enable outbound calling on the instance: Connect console > Instance > Telephony > "I want to make outbound calls with Connect."
2. Set outbound caller ID name and number on the default outbound queue.
3. Ensure agents have the **"Contact Control Panel (CCP) - Make outbound calls"** permission in their security profile.

### Invalid Number

**Symptoms:** Agent sees "Invalid number" / "We are unable to complete the call as dialed."

**Fixes:**
1. Verify the phone number is in **E.164 format** (e.g., +12025551234).
2. Verify the destination country is in the instance's allowed calling list.
3. If issues persist, contact AWS Support.

### Caller ID Not Showing

- Check queue outbound caller ID configuration.
- Verify the claimed number supports outbound calling.
- Ensure the outbound caller ID number is set in the queue settings.

---

## Error States

**Symptoms:** Agent is stuck in "Error" or "Missed" state.

**Causes and fixes:**

1. **Missed contact.**
   - The agent did not accept a contact within the configured timeout.
   - The agent is placed in Error (or "Missed Contact") state.
   - Resolution: the agent must manually change their status back to "Available" or another status.

2. **System error.**
   - A system error occurred during contact handling (e.g., network failure, service interruption).
   - Resolution: refresh the CCP. If the error persists, clear cookies and re-login.

3. **Stuck in ACW.**
   - The agent cannot clear a contact from ACW.
   - Check for pending step-by-step guide completion.
   - If the guide is stuck, refresh the CCP. The contact should re-appear and can be cleared.

---

## Endpoint Test Utility

AWS provides the [Amazon Connect Endpoint Test Utility](https://tools.connect.aws/endpoint-test/) for validating connectivity.

### What It Tests

- Validates that the browser supports WebRTC
- Determines if the browser has appropriate access to media devices (microphone, speakers, etc.)
- Performs latency tests for all active Connect regions
- Performs latency tests to a specific Connect instance (if provided)
- Validates network connectivity across required ports for media streams

### How to Use

1. Navigate to `https://tools.connect.aws/endpoint-test/`
2. Optionally provide your Connect instance URL for instance-specific tests
3. Run the tests
4. Download results as a JSON file for support tickets
5. Use "Load previous results" to re-analyze saved results
6. Download a bookmark for your instance to simplify future tests

### URL Parameters for Customization

| Parameter | Description | Values |
|---|---|---|
| `lng` | Language | `en` (default), `es`, `fr` |
| `autoRun` | Run tests automatically | `true`, `false` (default) |
| `connectInstanceUrl` | Instance URL (must start with https) | Instance URL |
| `regions` | Comma-separated region codes | e.g., `us-east-1,us-west-2` |

Example: `https://tools.connect.aws/endpoint-test/?lng=es&autoRun=true&connectInstanceUrl=https://myinstance.awsapps.com&regions=us-east-1,us-west-2`

### Run Before Deployment

Run the Endpoint Test Utility on agent workstations before deployment to validate:
- TURN server reachability
- DNS resolution
- WebRTC capability
- Media path connectivity

---

## Network Diagnostics

### Check WebRTC Connectivity

WebRTC requires:

| Protocol | Port(s) | Direction | Purpose |
|---|---|---|---|
| HTTPS | 443 | Outbound | Signaling, API calls |
| WSS | 443 | Outbound | WebSocket signaling |
| UDP | 3478 | Outbound | STUN (NAT traversal) |
| UDP | 49152-65535 | Outbound | Media (RTP/SRTP) |
| TCP | 443 | Outbound | TURN fallback (when UDP is blocked) |

If UDP is blocked, WebRTC falls back to TCP via TURN servers on port 443. This works but adds latency and may reduce call quality.

### Verify Firewall Rules

Required domains to allowlist:

| Domain Pattern | Purpose |
|---|---|
| `*.my.connect.aws` | Workspace and CCP |
| `*.transport.connect.aws` | WebSocket signaling |
| `*.static.connect.aws` | Static assets |
| `*.execute-api.{region}.amazonaws.com` | API calls |
| `{region}.turn.connect.aws` | TURN servers |
| `*.cloudfront.net` | CDN for static assets |
| `*{myInstanceName}.awsapps.com` | Legacy instance domains |

Replace `{region}` with the AWS region of the Connect instance (e.g., `us-east-1`).

### Test Bandwidth

Minimum bandwidth requirements:

| Channel | Minimum | Recommended |
|---|---|---|
| Voice (softphone) | 100 Kbps up + 100 Kbps down | 200 Kbps up + 200 Kbps down |
| Chat | Negligible | Negligible |
| Video (if used) | 1 Mbps up + 1 Mbps down | 2 Mbps up + 2 Mbps down |

Measure bandwidth to the AWS region hosting the instance, not just to generic speed test servers.

---

## QualityMetrics in Contact Records

### Where to Find

QualityMetrics is part of the contact object returned by the `DescribeContact` API and also available via Kinesis CTR events. It is **not** available through the Connect admin website contact record view, and **not** part of EventBridge events.

```json
"QualityMetrics": {
  "Agent": {
    "Audio": {
      "PotentialQualityIssues": ["string"],
      "QualityScore": number
    }
  },
  "Customer": {
    "Audio": {
      "PotentialQualityIssues": ["string"],
      "QualityScore": number
    }
  }
}
```

### Fields

| Field | Description | Range |
|---|---|---|
| **QualityScore** | Overall audio quality estimate | 1.00 (poor) to 5.00 (high) |
| **PotentialQualityIssues** | List of detected issues | Empty list = no issues detected |

### PotentialQualityIssues Values

| Issue | Description | Common Causes |
|---|---|---|
| `HighPacketLoss` | Packet loss on outbound audio (egress) stream | Poor network, congestion, constrained bandwidth, competing applications |
| `HighJitterBuffer` | Excessive delay introduced by browser buffer to reorder audio packets | Network/hardware congestion, low bandwidth router; >30ms or frequently changing = problem |
| `HighRoundTripTime` | High RTT between participant device and Connect endpoint | Low-bandwidth network, VPN overhead, geographic distance to AWS region, virtualized desktop routing |

### Audio Quality Symptoms

| Symptom | Observation | Likely Cause |
|---|---|---|
| Choppy/broken audio | Audio stream interrupted, sounds choppy | Packet loss from poor network connectivity |
| Delayed audio | Delayed audio from other side, consistent overlapping | Constrained bandwidth/hardware/workstation congestion |
| Echo | Agent hears own voice repeated with delay | Audio feedback between microphone and speaker |
| Background noise | Extraneous noise (fans, typing, call center) | Environmental, microphone sensitivity |
| Distorted audio | Garbled or robotic-sounding audio | Bandwidth issues or faulty hardware |

### Analyzing Impact

Use QualityMetrics with other CTR fields (`AgentHierarchyGroup`, `DeviceInfo`) to identify patterns:
- **Scenario 1:** Single agent affected -- likely workstation/browser/network config issue
- **Scenario 2:** Multiple agents in same hierarchy/location -- likely local network issue (modem/ISP/router/LAN) or recent software upgrades
- **Scenario 3:** Multiple remote agents -- check browser/system updates and organizational network changes

---

## Softphone Errors

### Microphone Permissions

When the CCP first loads, the browser requests microphone access. If denied:

- **Chrome:** shows a crossed-out microphone icon in the address bar. Click it to re-enable.
- **Firefox:** shows a notification bar. Click "Allow."
- **Edge:** similar to Chrome, click the lock icon to change permissions.

If microphone access was permanently denied:

1. Navigate to browser settings > Site settings > Microphone.
2. Find the Connect domain in the blocked list.
3. Change to "Allow."
4. Refresh the CCP.

### Headset Detection

**Headset not recognized:**

1. Verify the headset is physically connected and powered on (for Bluetooth headsets, check pairing).
2. Open operating system sound settings and verify the headset appears as an input/output device.
3. In CCP settings > Audio devices, click the refresh button to re-detect devices.
4. If the headset was connected after the CCP loaded, refresh the page.

**Headset switching mid-call:**

- If a headset is connected or disconnected during an active call, the CCP may not automatically switch.
- The agent should manually select the new device in CCP settings.
- Some browsers (Chrome) support automatic device switching; others require manual selection.

---

## Browser Issues

### Supported Browsers

| Browser | Minimum Version | Notes |
|---|---|---|
| Google Chrome | Latest 3 major versions | Recommended. Best WebRTC support. |
| Mozilla Firefox | Latest 3 major versions | Supported. Requires CCP tab in focus for audio. May require additional permissions. |
| Microsoft Edge (Chromium) | Latest 3 major versions | Supported. Same engine as Chrome. |
| Safari | Not recommended | Limited WebRTC support. Third-party cookie issues. |

### Clear Cache

When experiencing loading or display issues:

1. Clear the browser cache for the Connect domain specifically (not all sites):
   - Chrome: Settings > Privacy > Clear browsing data > Advanced > select "Cached images and files" and set time range.
   - Or use Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac).
2. Alternatively, hard-refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac).
3. If issues persist, clear cookies for the Connect domain as well.

### Disable Extensions

Browser extensions can interfere with the CCP:

- **Ad blockers** may block WebSocket connections or API calls.
- **Privacy extensions** may block third-party cookies required for authentication.
- **VPN extensions** may route traffic through unexpected paths.

To diagnose: try the CCP in an incognito/private window with extensions disabled. If it works there, re-enable extensions one by one to find the culprit.

### Check for Multiple CCP Instances

Running multiple CCP instances (tabs, windows, or embedded instances) causes conflicts:

- Only one CCP instance should be active per browser profile.
- Multiple instances compete for the same WebRTC media session, causing audio issues.
- Close all CCP tabs/windows except one.
- If embedding, ensure only one `initCCP()` call executes.

---

## Log Collection for Support Cases

When filing an AWS support case for CCP issues, collect:

### Browser Console Logs

1. Open the browser developer tools (F12).
2. Navigate to the Console tab.
3. Reproduce the issue.
4. Right-click in the console > "Save as" to export logs.
5. Include the full console output in the support case.

### Network Logs (HAR File)

1. Open the browser developer tools (F12).
2. Navigate to the Network tab.
3. Check "Preserve log" to prevent logs from clearing on navigation.
4. Reproduce the issue.
5. Right-click in the network tab > "Save all as HAR with content."
6. Attach the HAR file to the support case.

### CCP Logs

Download CCP logs directly from the agent's CCP:

1. In the CCP, choose **Settings > Download logs**.
2. The `agent-log.txt` file saves to the browser's default download directory.
3. The file can be renamed after download.

**Note:** CCP logs do not persist through browser refreshes. Download before refreshing.

### CCP Log Parser

AWS provides a dedicated log parser tool:

1. Open `https://tools.connect.aws/ccp-log-parser/`
2. Drag and drop the `agent-log.txt` file into the parser
3. **Snapshots & Logs tab** -- view log entries with expandable JSON details
4. **Snapshots panel** -- view agent status captured during periodic AgentSnapshot retrieval
5. **Metrics tab** provides:
   - **Skew Metrics** -- difference between client-side and server-side timestamps (milliseconds)
   - **API Call Metrics** -- latency of API calls from CCP
   - **WebRTC Metrics** -- media stream conditions during calls (available if softphone was used)

### Programmatic Log Download

```javascript
// Download CCP logs via Streams API
connect.getLog().download();
```

### Information to Include in Support Cases

- Connect instance alias and region
- Agent username
- Contact ID(s) affected
- Timestamp of the issue (with timezone)
- Browser name and version
- Operating system and version
- Network environment (corporate network, VPN, home network)
- Steps to reproduce
- Screenshots or screen recordings if applicable
- CCP logs (`agent-log.txt`)
- HAR file
- Browser console logs

---

## Corporate Proxy/VPN Issues

### Problem

Corporate networks often route all traffic through a proxy server or VPN tunnel. This can cause:

- WebRTC media failure (proxy cannot handle UDP)
- High latency (traffic routed through distant proxy servers)
- WebSocket connection drops (proxy timeout on long-lived connections)
- Certificate inspection breaking TLS (proxy MITM)

### Split Tunneling

Configure the VPN to route Connect traffic directly (not through the VPN tunnel):

**Domains to exclude from VPN/proxy:**

- `*.my.connect.aws`
- `*.transport.connect.aws`
- `*.static.connect.aws`
- `*.turn.connect.aws`
- `*.amazonaws.com` (or specifically the Connect API endpoints)

**IP ranges to exclude:**

- AWS publishes IP ranges at `https://ip-ranges.amazonaws.com/ip-ranges.json`.
- Filter for the Connect service in the relevant region.

### Proxy Configuration

If split tunneling is not possible:

1. **HTTPS proxy** -- Configure the proxy to pass through (not inspect) traffic to `*.connect.aws` domains. TLS inspection will break WebSocket and may cause authentication failures.
2. **WebSocket proxy support** -- Ensure the proxy supports WebSocket upgrades (HTTP 101 Switching Protocols). Some older proxies do not.
3. **UDP proxy** -- Most corporate proxies cannot proxy UDP traffic. In this case, WebRTC will fall back to TCP via TURN on port 443. This adds latency but works.
4. **Proxy timeout** -- Increase the proxy idle timeout for WebSocket connections to at least 600 seconds (default proxy timeouts of 30-60 seconds will drop the connection).

### Recommended Network Architecture for Corporate Environments

```
Agent Browser
  |
  +-- HTTPS/WSS (port 443) --> Direct or via proxy --> Connect APIs + Signaling
  |
  +-- UDP (ports 3478, 49152-65535) --> Direct (bypass proxy) --> TURN/STUN servers --> Media
  |
  +-- TCP 443 (fallback) --> via proxy if needed --> TURN relay --> Media
```

The key principle: **media traffic (UDP) should bypass the proxy**. Signaling traffic (HTTPS/WSS) can go through the proxy if it supports WebSocket and does not break TLS.

---

## Attachment Issues (Chat, Email, Task, Case)

**Symptoms:** Attachments not displaying for agents in chat, email, tasks, or Cases.

**Causes and fixes:**

1. **CORS policy not configured on attachments S3 bucket.**
   - Configure CORS policy on the attachments bucket per the Connect documentation.

2. **Internal firewall blocking S3 access.**
   - Add the S3 bucket domain to the firewall allowlist.

3. **Attachments exceed size/count/type limits.**
   - Maximum attachment size: configurable up to 100 MB (default 20 MB).
   - Verify the configured size limit for your instance.
   - Check that file types are in the allowed file extensions list.

4. **File type rejected despite expected allowance.**
   - Verify the file extension has been explicitly added to the allowed file extensions list for the instance.

---

## Screen Recording Issues

### Chrome/Edge 147+ LNA Restriction (Critical)

Starting with Chrome 147 and Edge 147, Chromium-based browsers enforce Local Network Access (LNA) restrictions on WebSocket connections. This blocks the local WebSocket connection between the CCP and the Connect Client Application, causing screen recordings to fail. **Affected recordings cannot be recovered.**

**Symptoms:**
- Screen recording does not start for agents using Chrome 147+ or Edge 147+
- Works correctly on older browser versions
- Shared worker logs show: `IPC connection terminated with status code 1006`
- Shared worker or CCP logs show: `ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`

**Confirm the issue:**
- Chrome: navigate to `chrome://flags/#local-network-access-check`, set to "Disabled", restart Chrome
- Edge: navigate to `edge://flags/#local-network-access-check`, set to "Disabled", restart Edge
- If screen recording resumes, the issue is confirmed

**Resolution:** Deploy the `LoopbackNetworkAllowedForUrls` enterprise policy to pre-grant loopback network access for your CCP domain. Configure with: `[*.]my.connect.aws`

### General Screen Recording Issues

- **Not starting:** Check that the Set Recording block is in the contact flow and screen recording is enabled on the instance.
- **Quality issues:** Depends on agent screen resolution and network bandwidth.
- **Storage:** Recordings stored in S3; check bucket permissions and encryption configuration.
- **Client Application not installed:** The Connect Client Application must be installed and running on the agent machine.

---

## Audio Humming/Buzzing

**Cause:** Sample rate mismatch between the headset and browser audio context. Most commonly seen with Firefox when a headset has a preferred sample rate of 16000 Hz but the browser asserts 48000 Hz.

**Required sample rate:** 48000 Hz (48 kHz) for both input and output devices.

### Verify Firefox Sample Rate

1. Open CCP in Firefox, set status to Available, accept a call.
2. Open a second Firefox tab, type `about:support` in the address bar.
3. Scroll to **Media** section.
4. Verify input and output device sample rates are **48000**.

### Verify Chrome Sample Rate

1. Open CCP in Chrome, set status to Available, accept a call.
2. Open a second Chrome tab, type `chrome://media-internals` in the address bar.
3. On the **Audio** tab, check **Input Controllers** and **Output Controllers**.
4. Verify sample rates are **48000**.

### Fix

1. Go to the operating system sound settings and change the sample rate to 48000 if different.
2. If the headset does not support 48000 Hz, switch to a headset that does.
3. **USB headsets are preferred** over Bluetooth (lower latency, fewer codec issues).

---

## Mobile/Tablet Support

The Connect admin website, Contact Control Panel (CCP), and agent workspace do **NOT** support:
- Mobile phones (iPhone, Android)
- iPads/tablets
- Mobile browsers

**Desktop browser is required** for full CCP functionality.

**Workaround for audio on mobile:** Configure CCP to forward the audio portion of calls to a mobile device using desk phone mode:
1. In CCP, open Settings.
2. Under Phone type, choose **Desk phone**.
3. Enter the mobile phone number and save.
4. Audio goes to the mobile device; the agent manages the call via CCP on a desktop browser.
