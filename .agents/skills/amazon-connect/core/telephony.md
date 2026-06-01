# Amazon Connect — Telephony & Phone Numbers

## Telephony Architecture

AWS manages carrier connections, redundancy, and routing for Amazon Connect telephony. The service is spread across multiple Availability Zones with multiple telephony providers per region, each with multiple links into data centers. This ensures alternate routes remain available even if multiple carrier links fail.

- **Telephony-as-a-Service**: AWS manages the carrier network globally
- **Proactive monitoring** by telephony experts
- **Auto-scales** with demand — no multi-year contracts or peak commitments
- **Carrier redundancy**: Multiple carriers per region with diverse connections
- **Link redundancy**: Multiple links across Availability Zones

## Phone Number Types

### DID (Direct Inward Dial)
- Also called DDI (Direct Dial-In) in Europe
- Locally formatted numbers matching local dialing patterns (e.g., +1(206)-NXX-XXXX for Seattle)
- Available in 110+ countries
- Managed by a single carrier — **no carrier redundancy** (only link redundancy across AZs)
- Less expensive than toll-free but less redundant
- Capacity limitation on concurrent calls per number (varies by region, typically ~100 concurrent)
- Useful for: local caller ID on outbound, local presence for inbound, queued callbacks
- Regulated by State Public Utilities commissions (US)

### Toll-Free
- Distinct prefix codes, no charge to caller
- Available in select countries (US: regulated by FCC)
- **Carrier redundancy**: AWS registers with SOMOS (US), selects multiple carriers for route AND carrier redundancy
- Higher price than DID but highest availability — remains available even during complete carrier outage
- Best option for primary inbound when reliability is critical

### UIFN (Universal International Freephone Numbers)
- Inbound only
- Available in participating countries with preset porting windows

## E.164 Format

All phone numbers in Amazon Connect use E.164 format:
- Format: `+[country code][number]`
- Examples: `+12065551234` (US), `+442071234567` (UK), `+61291234567` (AU)
- Required for all API operations, outbound caller ID, and transfers

## Claiming Phone Numbers

### Process
1. Open Amazon Connect admin website or use API
2. Select country and number type (DID or toll-free)
3. Choose from available numbers (with optional prefix selection)
4. Associate number to a flow

### Country Availability
- DID and toll-free numbers available across 200+ countries/regions
- Full list in the [Amazon Connect Telecoms Country Coverage Guide](https://d1v2gagwb6hfe1.cloudfront.net/Amazon_Connect_Telecoms_Coverage.pdf)
- All AWS Regions supported **except** Africa (Cape Town) and AWS GovCloud (US-West) unless noted
- Some countries require local address and identification documents
- PO Box addresses are **not valid** in any country

### Regulations by Country (Examples)
- **United States**: No ID required for DID or toll-free; porting supported with LOA
- **Australia**: Local address required for DID; toll-free accepts global address; porting supported with LOA + recent invoice
- **United Kingdom**: Local address required for DID; toll-free accepts global address
- **Germany**: Local address required; proof of address (utility bill, etc.)
- **Argentina**: No ID required for DID or toll-free; porting has specific windows (Mon-Fri, Buenos Aires time)
- **Japan (Tokyo)**: Special claiming process — separate documentation for AP-Tokyo region

### Claiming via API
```
SearchAvailablePhoneNumbers  — find numbers by country, type, prefix
ClaimPhoneNumber             — claim from available pool
```

### After Claiming
- Numbers appear on the **Manage Phone numbers** page
- You see only claimed numbers, not all available numbers in that country
- Each number must be associated to exactly one flow

## Phone Number Limits

| Resource | Default | Adjustable |
|---|---|---|
| Phone numbers per instance | 5 | Yes (via Service Quotas) |

**Note**: You may receive "You've reached the limit of Phone Numbers" even on first claim — this requires AWS Support to resolve.

## Phone Number Porting

### Process
1. Submit porting request via AWS Support case (same form as quota increases)
2. Provide Letter of Authorization (LOA) signed by the authorized person
3. Provide recent invoice from current carrier (within 30 days typically)
4. AWS coordinates with current carrier for number transfer
5. After porting completes, numbers appear in the **Manage Phone numbers** page

### Key Details
- Porting availability varies by country — some countries do not support porting
- Country-specific porting windows apply (e.g., Argentina: Mon-Fri specific hours)
- South Korea and Thailand have additional specific porting regulations
- UIFN numbers have preset porting times only
- **Recommendation**: Forward existing numbers to new claimed numbers during migration, port after fully converted (provides fallback)

## Association

- Associate phone number to flow: `AssociatePhoneNumberContactFlow`
- **One number maps to exactly one flow**
- Multiple numbers can point to the same flow
- Disassociate: `DisassociatePhoneNumberContactFlow`

## Outbound Calling

### Configuration
- 200+ outbound calling destinations supported
- Configure outbound caller ID per queue via `UpdateQueueOutboundCallerConfig`
- E.164 format required for all outbound numbers
- Caller ID must be a number claimed or ported to your instance

### Early Media
- Agents hear pre-connection audio: busy signals, failure-to-connect errors, informational messages from telephony providers
- Enabled by default for instances created after April 17, 2020
- **Not supported** for transfers dialed through the "Transfer to phone number" flow block
- Toggle via instance telephony settings or `UpdateInstanceAttribute`

### Emergency Calling
- Amazon Connect does **not** support emergency calling (e.g., 911/112)
- Not designed as a replacement for traditional phone service for emergency purposes

### Multi-Party Calls
- Default: 3 participants on a voice call (2 agents + customer, or agent + customer + external)
- Enhanced: up to 6 participants when "Multi-Party Calls and Enhanced Monitoring" is enabled
- Enables supervisor barge-in capability (CCPv2 only)

## STIR/SHAKEN
- Amazon Connect supports STIR/SHAKEN attestation for caller identity verification
- Helps reduce spoofed/robocalls
- Applied automatically to US numbers

## Phone Numbers with Traffic Distribution Groups (Global Resiliency)

- Phone numbers can be associated with traffic distribution groups for multi-region failover
- Enables global resiliency by distributing traffic across AWS Regions
- Use `ReplicateInstance` to set up cross-region instance replication
- Numbers in traffic distribution groups can shift traffic between regions

## Pricing Model

- **DID numbers**: Per-day charge for the phone number + per-minute inbound usage
- **Toll-free numbers**: Higher per-day charge + per-minute inbound usage (includes carrier redundancy)
- **Outbound calling**: Per-minute charge varying by destination country
- No multi-year contracts, no peak commitments, no upfront fees
- See [Amazon Connect pricing](https://aws.amazon.com/connect/pricing/) for current rates

## Migration Use Cases

### Starting Fresh
- Claim new numbers via console or API

### Migrating from Another Provider
1. Forward existing numbers to newly claimed Amazon Connect numbers
2. Run proof of concept
3. After full conversion, port existing numbers into Amazon Connect
4. Provides fallback if migration issues arise

### Maintaining Two Platforms
- Choose primary call-handling platform, forward to secondary
- If Connect is primary: port/claim numbers, design flows to transfer to external platform
- If external is primary: configure forwarding to a claimed Connect number (toll-free recommended for redundancy)
- Engage AWS Solutions Architecture support for well-architected design

## Key APIs

| API | Purpose |
|---|---|
| `ClaimPhoneNumber` | Claim a phone number from available pool |
| `ReleasePhoneNumber` | Return a phone number to the pool |
| `ImportPhoneNumber` | Import a number from an external carrier |
| `SearchAvailablePhoneNumbers` | Find numbers by country, type, prefix |
| `ListPhoneNumbers` | List numbers (legacy) |
| `ListPhoneNumbersV2` | List numbers with enhanced filtering |
| `DescribePhoneNumber` | Get details of a specific number |
| `UpdatePhoneNumber` | Update phone number target (flow/TDG) |
| `UpdatePhoneNumberMetadata` | Update number metadata (description, etc.) |
| `AssociatePhoneNumberContactFlow` | Associate number with a flow |
| `DisassociatePhoneNumberContactFlow` | Remove number-flow association |
