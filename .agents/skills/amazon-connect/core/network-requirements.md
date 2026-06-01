# Amazon Connect — Network Requirements for CCP

## Browser Requirements
- Google Chrome (latest 3 versions)
- Mozilla Firefox (latest 3 versions)
- Microsoft Edge Chromium (latest 3 versions)
- Firefox limitation: In VDI split mode, Firefox CCP outside the VDI loses microphone access when the CCP tab is not in focus

## Network Configuration
- CCP requires WebRTC for softphone voice
- Minimum bandwidth: 100 Kbps per active voice call (both directions)
- Recommended: low-latency connection (<150ms RTT to Connect endpoint)
- TLS 1.2+ required for all connections
- No SSL/TLS inspection on WebRTC media traffic (breaks encryption)

## Domain Allowlist (Option 1 — Recommended)

This approach replaces broad IP range allowlisting with specific domain patterns. Test with 200+ calls before production; if error rate exceeds 2%, fall back to Option 2.

### Required Domains

| Domain Pattern | Port | Protocol | Direction | Purpose |
|---|---|---|---|---|
| `rtc*.connect-telecom.{{region}}.amazonaws.com` | 443 | TCP | OUTBOUND | WebRTC signaling (CCP v1) |
| `*.my.connect.aws` | 443 | TCP | OUTBOUND | Agent workspace, CCP login, API calls |
| `*.transport.connect.{{region}}.amazonaws.com` | 443 | TCP | OUTBOUND | WebRTC signaling and media (CCP v2) |
| `*.telemetry.connect.{{region}}.amazonaws.com` | 443 | TCP | OUTBOUND | Telemetry and monitoring |
| `participant.connect.{{region}}.amazonaws.com` | 443 | TCP | OUTBOUND | Participant service (chat, tasks) |
| `{{S3-bucket}}.s3.{{region}}.amazonaws.com` | 443 | TCP | OUTBOUND | Attachments storage |
| `TurnNlb-*.elb.{{region}}.amazonaws.com` | 3478 | UDP | OUTBOUND | TURN/STUN relay for NAT traversal |
| `{{instance-id.source-region}}.sign-in.connect.aws` | 443 | HTTPS | OUTBOUND | Global Resiliency SAML sign-in only |
| `*.{{source-region}}.region-discovery.connect.aws` | 443 | HTTPS | OUTBOUND | Global Resiliency region discovery only |

Replace `{{region}}` with your Connect instance region (e.g., `us-east-1`).
Replace `{{myInstanceName}}` with your Connect instance alias.

**Legacy domain**: `*.awsapps.com` is being deprecated — update to `*.my.connect.aws`.

### CloudFront Domains for Static Assets

Per-region CloudFront distributions for static content (JS, CSS, images):

| Region | CloudFront Domains |
|---|---|
| us-east-1 | `https://dd401jc05x2yk.cloudfront.net/`, `https://d1f0uslncy85vb.cloudfront.net/` |
| us-west-2 | `https://d38fzyjx9jg8fj.cloudfront.net/`, `https://d366s8lxuwna4d.cloudfront.net/` |
| ap-northeast-1 | `https://d3h58onr8hrozw.cloudfront.net/`, `https://d13ljas036gz6c.cloudfront.net/` |
| ap-northeast-2 | `https://d11ouwvqpq1ads.cloudfront.net/` |
| ap-southeast-1 | `https://d2g7up6vqvaq2o.cloudfront.net/`, `https://d12o1dl1h4w0xc.cloudfront.net/` |
| ap-southeast-2 | `https://d2190hliw27bb8.cloudfront.net/`, `https://d3mgrlqzmisce5.cloudfront.net/` |
| eu-central-1 | `https://d1n9s7btyr4f0n.cloudfront.net/`, `https://d3tqoc05lsydd3.cloudfront.net/` |
| eu-west-2 | `https://dl32tyuy2mmv6.cloudfront.net/`, `https://d2p8ibh10q5exz.cloudfront.net/` |
| ca-central-1 | Static content served behind `*.my.connect.aws` (no separate CloudFront domain) |

Non-SAML CloudFront domains (if no SAML and firewall restrictions apply):

| Region | CloudFront Domain |
|---|---|
| us-east-1 | `https://d32i4gd7pg4909.cloudfront.net/` |
| us-west-2 | `https://d18af777lco7lp.cloudfront.net/` |
| eu-west-2 | `https://d16q6638mh01s7.cloudfront.net/` |
| ap-northeast-1 | `https://d2c2t8mxjhq5z1.cloudfront.net/` |
| ap-northeast-2 | `https://d9j3u8qaxidxi.cloudfront.net/` |
| ap-southeast-1 | `https://d3qzmd7y07pz0i.cloudfront.net/` |
| ap-southeast-2 | `https://dwcpoxuuza83q.cloudfront.net/` |
| eu-central-1 | `https://d1whcm49570jjw.cloudfront.net/` |
| ca-central-1 | `https://d2wfbsypmqjmog.cloudfront.net/` |
| us-gov-east-1 | `https://s3-us-gov-east-1.amazonaws.com/warp-drive-console-static-content-prod-osu/` |
| us-gov-west-1 | `https://s3-us-gov-west-1.amazonaws.com/warp-drive-console-static-content-prod-pdt/` |

### NLB Endpoints for TURN/STUN (Region-Specific)

If you prefer not to use the `TurnNlb-*.elb.{{region}}.amazonaws.com` wildcard:

| Region | TURN NLB Endpoints |
|---|---|
| us-east-1 | `TurnNlb-d76454ac48d20c1e.elb.us-east-1.amazonaws.com`, `TurnNlb-31a7fe8a79c27929.elb.us-east-1.amazonaws.com`, `TurnNlb-7a9b8e750cec315a.elb.us-east-1.amazonaws.com`, `TurnNlb-d40f7ff9cdd63758.elb.us-east-1.amazonaws.com`, `TurnNlb-7675623c965365c2.elb.us-east-1.amazonaws.com` |
| us-west-2 | `TurnNlb-8d79b4466d82ad0e.elb.us-west-2.amazonaws.com`, `TurnNlb-dbc4ebb71307fda2.elb.us-west-2.amazonaws.com`, `TurnNlb-13c884fe3673ed9f.elb.us-west-2.amazonaws.com`, `TurnNlb-6bb66ee54ee32710.elb.us-west-2.amazonaws.com`, `TurnNlb-ecc67f8fbd7a29f6.elb.us-west-2.amazonaws.com` |
| af-south-1 | `TurnNlb-29b8f2824c2958b8.elb.af-south-1.amazonaws.com` |
| ap-northeast-1 | `TurnNlb-3c6ddabcbeb821d8.elb.ap-northeast-1.amazonaws.com` |
| ap-northeast-2 | `TurnNlb-a2d59ac3f246f09a.elb.ap-northeast-2.amazonaws.com` |
| ap-southeast-1 | `TurnNlb-261982506d86d300.elb.ap-southeast-1.amazonaws.com` |
| ap-southeast-2 | `TurnNlb-93f2de0c97c4316b.elb.ap-southeast-2.amazonaws.com` |
| ca-central-1 | `TurnNlb-b019de6142240b9f.elb.ca-central-1.amazonaws.com` |
| eu-central-1 | `TurnNlb-ea5316ebe2759cbc.elb.eu-central-1.amazonaws.com`, `TurnNlb-cce94fede9926d70.elb.eu-central-1.amazonaws.com` |
| eu-west-2 | `TurnNlb-1dc64a459ead57ea.elb.eu-west-2.amazonaws.com`, `TurnNlb-0c39b6a52bcdd446.elb.eu-west-2.amazonaws.com` |
| us-gov-west-1 | `TurnNlb-d7c623c23f628042.elb.us-gov-west-1.amazonaws.com` |

## Option 2 (Not Recommended): Allow IP Address Ranges

Use the `ip-ranges.json` file at `https://ip-ranges.amazonaws.com/ip-ranges.json`:

| ip-ranges.json Service | Region Scope | Port | Protocol | Direction |
|---|---|---|---|---|
| `AMAZON_CONNECT` | GLOBAL + your instance region | 3478 | UDP | OUTBOUND |
| `EC2` | GLOBAL + your instance region | 443 | TCP | OUTBOUND |
| `CLOUDFRONT` | GLOBAL (all CloudFront ranges) | 443 | TCP | OUTBOUND |

### About Connect IP Ranges
- The `/19` range (e.g., `15.193.0.0/19`) is **exclusively** owned by Connect — not shared with other services
- Each range appears twice in ip-ranges.json: once for `AMAZON_CONNECT` service, once for `AMAZON` service
- New IP ranges are published to ip-ranges.json and kept for **30 days** before the service starts using them; traffic ramps over the following 2 weeks
- Add new ranges to your allowlist **within 30 days** of publication to avoid intermittent connectivity issues
- If your region does not appear in ip-ranges.json, use the `GLOBAL` entries only

## Port and Protocol Requirements

| Port | Protocol | Direction | Purpose |
|---|---|---|---|
| 443 | TCP (HTTPS) | OUTBOUND | Agent workspace, API calls, signaling, static assets |
| 443 | TCP (WSS) | OUTBOUND | WebSocket signaling for WebRTC (CCP v2 via `*.transport.connect`) |
| 3478 | UDP | OUTBOUND | TURN/STUN relay servers for NAT traversal |

### Proxy / Firewall Notes
- If using a proxy between CCP and Connect, increase the **SSL certificate cache timeout** to cover the agent's full shift (e.g., 8 hours + breaks) to avoid mid-shift certificate renewal disconnects
- WebSocket handling in proxy applications may impact functionality for `rtc*.connect-telecom`, `*.transport.connect`, and `*.awsapps.com` — test thoroughly before production
- For a **media-less CCP** (using Connect Streams API), only EC2 and CloudFront ports are needed — no TURN/STUN ports required
- Once ip-ranges.json is updated, begin using new ranges after 30 days — add them to your allowlist promptly

## Stateful vs Stateless Firewalls

### Stateful Firewalls
- Security groups, most enterprise firewalls
- Handle return traffic automatically — only outbound rules needed
- No additional configuration for WebRTC media return traffic

### Stateless Firewalls
- AWS NACLs, some hardware firewalls
- Do **not** track connection state — must create **explicit inbound rules** for return UDP traffic
- Required inbound ephemeral port ranges:
  - **Windows**: 49152–65535 (UDP)
  - **Linux**: 32768–61000 (UDP)
- IP range entry: `AMAZON_CONNECT`
- Without inbound rules for return traffic, WebRTC media will fail even if outbound is allowed

## Bandwidth Requirements

| Channel | Minimum | Recommended |
|---|---|---|
| Voice (softphone) | 100 Kbps per active call (both directions) | 200+ Kbps |
| Voice + screen sharing concurrent | 200 Kbps | Higher based on resolution |
| Audio quality | 16 kHz | — |

## DNS Resolution Requirements
- Resolve `*.my.connect.aws` domains without aggressive caching — IPs may change
- If DNS resolution is restricted, verify with `nslookup TurnNlb-*.elb.{{region}}.amazonaws.com`
- If DNS cannot resolve TURN endpoints, add `TurnNlb-*.elb.{{region}}.amazonaws.com` or the specific NLB endpoints to your allowlist
- Failure to resolve produces: "Failed to establish softphone connection. Browser unable to establish media channel with turn:TurnNlb-xxxxx.elb.{{region}}.amazonaws.com:3478?transport=udp"

## Scheduling Upload Endpoints
To allow time-off balance and allowance uploads in Connect scheduling, add to proxy exceptions:
- `https://bm-prod-{{region}}-cell-1-uploadservice-staging.s3.{{region}}.amazonaws.com`
- `https://bm-prod-{{region}}-cell-2-uploadservice-staging.s3.{{region}}.amazonaws.com`

## SAML 2.0 Remote Agents
- If using SAML 2.0 login, allowlist the AWS SSO endpoints listed in the AWS Sign-In endpoints documentation

## VPN and Split Tunneling

- **Split tunneling is strongly recommended** when agents use a VPN — route Connect media traffic directly to the internet, bypassing the VPN tunnel
- Forcing media through a VPN concentrator adds latency and jitter, degrading call quality
- If split tunneling is not possible, ensure the VPN path has **<150ms RTT** and sufficient bandwidth
- Test with the Connect endpoint connectivity tool before go-live
- Remote agents with unstable connections, packet loss, or high latency will experience compounded issues when using VPN

## VDI Environment (Citrix, VMware, RDP)

### Recommended: Split CCP Model
- Run a **media-less CCP** inside the VDI for signaling and call controls (using Connect Streams API)
- Run a **standard CCP** carrying media on the **local PC**
- Audio routes directly from the agent's local device to Connect, bypassing the VDI host
- This eliminates 100-300ms added VDI audio latency

### Cloud Desktop Support
- **Citrix**, **Amazon WorkSpaces**, and **Omnissa** cloud desktops support audio offloading to the agent's local device with automatic redirect to Connect
- Use the Connect open-source Streams library to build or update the agent UI for audio redirection

### Without Media Optimization
- Expect **100–300ms added latency** and reduced audio quality
- CCP operates like any WebRTC browser application inside the VDI session

### VDI Design Considerations
- **Agent location**: Minimize hops and RTT between agents and the VDI host
- **VDI host location**: Place on the same network segment as agents with lowest RTT to WebRTC and EC2 endpoints
- **Network**: Each hop increases failure possibility and latency; Direct Connect helps edge-to-AWS but does not fix internal LAN/WAN issues
- **Dedicated resources**: Isolate network and desktop resources for Connect users to prevent contention from backups, file transfers, etc.
- **Softphone with remote connections**: May degrade audio quality — consider rerouting audio to an external E.164 endpoint or using local media with remote signaling

### Firefox VDI Limitation
- In VDI split mode, Firefox CCP outside the VDI cannot maintain microphone access when the tab loses focus — CCP conforms to Firefox microphone usage guidance

## AWS Direct Connect

- Direct Connect is **not required** but improves call quality for on-premises agents
- Use a **Public VIF** (Virtual Interface) — Connect endpoints are public, not inside a VPC
- Provides a consistent network path vs. ISP-dependent internet routing
- Does **not** eliminate domain allowlist, DNS, or TLS requirements
- For hybrid setups: Direct Connect for office agents, internet for remote agents
- Does not address internal LAN/WAN routing issues — only solves edge-to-AWS path

## Region Selection

- Choose the region **closest to your agents** to minimize network latency
- Consider **data residency** requirements — recordings, CTRs, and data are stored in the selected region
- **Caller location**: Calls anchor to the Connect region endpoint and are subject to PSTN latency — place callers and transfer endpoints close to the instance region
- **Hub-and-spoke networks**: Multiple hops to reach an edge router add latency and degrade quality
- For globally distributed agents, use **Global Resiliency** (multi-region) to place agents in their nearest region
- **External transfers**: Remain anchored to the Connect region for the duration; per-minute usage accrues until the recipient disconnects; call is not recorded after agent drops; avoid circular transfers that compound PSTN latency

## Rerouting Audio
- When rerouting audio to an existing device, consider the device's location relative to the Connect region (additional latency)
- On incoming call, an outbound call is placed to the configured device; agent answers the device to connect with the caller
- If the agent does not answer, they are moved to missed contact state

## Agent Workstation Requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 2+ cores | 4 cores (if running CRM alongside CCP) |
| RAM | 4 GB | 8 GB |
| Network | 100 Kbps per active voice call | 200+ Kbps for concurrent voice + screen sharing |
| Browser | Chrome, Firefox, or Edge — latest 3 major versions | — |
| Audio | USB headset recommended; built-in mic/speakers supported but may cause echo | USB headset with echo cancellation |
| OS | Windows 10+, macOS 10.15+, or supported Linux | — |
| Display | 1280x720 minimum resolution | — |

## Softphone Features
- Built-in echo cancellation in CCP
- 16kHz audio quality
- USB headset connection recommended for best quality

## Common Issues
- Corporate proxies blocking WebRTC → one-way audio or no audio
- VPN without split tunneling → high latency, jitter, dropped calls
- Firewall blocking UDP → forces TCP fallback (higher latency, degraded quality)
- Aggressive DNS caching → stale IPs, connection failures
- SSL inspection on WebRTC → breaks encryption, media fails
- Stateless firewall without inbound ephemeral port rules → media failure
