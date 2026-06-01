# Amazon Connect — Global Resiliency

## Architecture
- **Default**: Active-active within a single AWS Region (all customers get this)
- **Global Resiliency (ACGR)**: Active-active across multiple AWS Regions (opt-in, requires AWS Enterprise Support or Unified Operations)
- ACGR is the **only AWS-supported** solution for multi-region resiliency — third-party or custom alternatives are unsupported and may impact SLA coverage

## Supported Regions and Pairing Rules

Global Resiliency is available in six regions with strict pairing constraints:

| Source Region | Replica Region |
|---|---|
| US East (N. Virginia) `us-east-1` | US West (Oregon) `us-west-2` |
| US West (Oregon) `us-west-2` | US East (N. Virginia) `us-east-1` |
| Europe (London) `eu-west-2` | Europe (Frankfurt) `eu-central-1` |
| Europe (Frankfurt) `eu-central-1` | Europe (London) `eu-west-2` |
| Asia Pacific (Tokyo) `ap-northeast-1` | Asia Pacific (Osaka) `ap-northeast-3` |

- Replicas can **only** be created within the same geographic pair (US↔US, EU↔EU, Tokyo→Osaka)
- Asia Pacific (Osaka) can only be a **replica** of Tokyo (one-directional)
- For Tokyo instances, only phone numbers explicitly enabled for ACGR support full replication to Osaka; inbound calls routed through Osaka may experience delivery times up to 20 seconds

## Requirements

- Both instances must be in the **same AWS account**
- Source instance must have **SAML 2.0** identity management enabled
- Source instance must be in `ACTIVE` status with an alias
- Instance domain must use the newer `*.my.connect.aws` format (instances with `*.awsapps.com` must update first)
- **AWS Enterprise Support or Unified Operations** is required for onboarding
- Service quotas in the replica must match the source — submit a service quota increase case for the replica
- Lambda functions across regions must have the **same name**
- Flows must replace hardcoded regions with `$.AwsRegion` or `$['AwsRegion']` parameters (except in Lambda function block `flowArn` — use a Set Contact Attributes block to construct the ARN, then reference the attribute key)
- Amazon Lex bots: either use Lex Global Resiliency to replicate with same bot ID, or branch flows based on `$.AwsRegion`

## Traffic Distribution Groups (TDGs)

A traffic distribution group links Connect instances across regions and controls how telephony traffic, agent sign-in, and agent routing are distributed.

### TDG Types
- **Default TDG**: Created automatically by `ReplicateInstance`. Supports three distribution types: SignIn, Agent, and Telephony. The **only** TDG type that allows `SignInConfig` changes.
- **Custom TDGs**: Created via `CreateTrafficDistributionGroup`. Support Agent and Telephony distributions only (no SignInConfig).

### TDG Lifecycle

**Create:**
```
CreateTrafficDistributionGroup
  InstanceId: string (required) — source instance ID
  Name: string (required) — display name
  Description: string (optional)
  Tags: map (optional)
```
- Returns a TDG ARN and ID
- Use `DescribeTrafficDistributionGroup` to poll until `Status` is `ACTIVE` before claiming numbers or updating distribution

**Describe:**
```
DescribeTrafficDistributionGroup
  TrafficDistributionGroupId: string (required) — ID or ARN
```
- Returns: Name, Description, Status, InstanceArn, Arn, Id, IsDefault, Tags

**Status values:** `CREATION_IN_PROGRESS`, `ACTIVE`, `CREATION_FAILED`, `PENDING_DELETION`, `DELETION_FAILED`, `UPDATE_IN_PROGRESS`

**List:**
```
ListTrafficDistributionGroups
  InstanceId: string (optional) — filter by instance
  MaxResults: integer (optional)
  NextToken: string (optional)
```

**Delete:**
```
DeleteTrafficDistributionGroup
  TrafficDistributionGroupId: string (required)
```
- All phone numbers must be released or moved away from the TDG before deletion
- All agent associations must be removed first

### Updating Traffic Distribution

```
UpdateTrafficDistribution
  Id: string (required) — TDG ID or ARN
  TelephonyConfig: object (required)
  SignInConfig: object (optional, default TDG only)
  AgentConfig: object (optional)
```

**TelephonyConfig** — controls inbound voice call routing:
```json
{
  "Distributions": [
    { "Region": "us-east-1", "Percentage": 70 },
    { "Region": "us-west-2", "Percentage": 30 }
  ]
}
```

**SignInConfig** — controls which region's backend servers agents sign into (default TDG only):
```json
{
  "Distributions": [
    { "Region": "us-east-1", "Percentage": 100 },
    { "Region": "us-west-2", "Percentage": 0 }
  ]
}
```

**AgentConfig** — controls agent routing:
```json
{
  "Distributions": [
    { "Region": "us-east-1", "Percentage": 80 },
    { "Region": "us-west-2", "Percentage": 20 }
  ]
}
```

**Rules:**
- Distribution percentages must add up to **100%**
- Must be specified in **10% increments** (e.g., 0, 10, 20, ..., 100)
- Must provide distribution for **both** linked instances
- Instance ARNs in the config must match the linked instances
- When calling from the replica region, must use the TDG **ARN** (not just the ID)
- When shifting telephony, also shift agents/sign-ins to ensure agents are available in the target region
- Fails with `InvalidRequestException` if rules are violated

**Get current distribution:**
```
GetTrafficDistribution
  Id: string (required) — TDG ID or ARN
```
- Returns current TelephonyConfig, SignInConfig, and AgentConfig

### Agent Association with TDGs

```
AssociateTrafficDistributionGroupUser
  TrafficDistributionGroupId: string (required)
  UserId: string (required)
```
- Agents must exist in both source and replica instances before association
- Cannot associate newly added agents until they are replicated to the other region

```
DisassociateTrafficDistributionGroupUser
  TrafficDistributionGroupId: string (required)
  UserId: string (required)
```

## ReplicateInstance API

```
ReplicateInstance
  InstanceId: string (required) — source instance ID
  ReplicaRegion: string (required) — target region
  ReplicaAlias: string (required) — alias for replica
  ClientToken: string (optional) — idempotency token
```

### What Gets Replicated (Mirrored Bidirectionally)
- Flows and flow modules (including versions and aliases)
- Users
- Routing profiles
- Queues
- Security profiles
- Hours of operation
- Quick connects
- Predefined attributes
- Prompts (not including S3-stored prompts)
- User hierarchies (groups and levels)
- Agent status
- Agent proficiencies
- Saved reports (but **not** schedules associated with them)
- Views (published state only — drafts are **not** replicated)
- Data tables (ARNs auto-adjust region code; expression-based ARNs may not)
- Workspaces
- Custom metrics
- Test cases
- Notifications

**Replicated associations:**
- Phone number → flow
- Queue → routing profile
- User → security profile, routing profile, user hierarchy
- Queue → quick connects
- Queue → hours of operation
- Queue → flow

### What Is NOT Replicated
- Lambda functions (must deploy separately with same name in both regions)
- Amazon Lex bots (use Lex Global Resiliency or branch on `$.AwsRegion`)
- Third-party integrations
- Saved report schedules
- Draft-state views
- Service quotas beyond auto-matched resources

### Replication Behavior
- Initial replication copies all configuration; subsequent changes sync **bidirectionally** in near real-time
- If sync fails, ACGR retries within 30 minutes
- The replica instance gets the **same instance ID** as the source
- A default TDG is created automatically if one does not exist
- All phone numbers on the source not already in a number group are auto-added to the default TDG
- Resource name conflicts (same name, different resource ID) throw `ResourceConflictException` — resolve and re-run

### ReplicateInstance Failure Conditions (InvalidRequestException)
1. Replica region is the same as the source region
2. Instance was already replicated in a different call
3. Instance has no alias
4. Instance is not in `ACTIVE` status
5. Instance does not have SAML enabled
6. Resource name conflict exists

### Finding the Source Region
- Call `ListTrafficDistributionGroups` with your `InstanceId`
- The returned `InstanceARN` contains the source region: `arn:aws:connect:{{source-region}}:{{account-id}}:traffic-distribution-group/{{tdg-id}}`

## Phone Numbers Across Regions

### Claiming to a TDG
- Use `ClaimPhoneNumber` with `TargetArn` set to the **traffic distribution group ARN** (not an instance ARN)
- Numbers claimed to a TDG can serve calls in any linked region
- Default distribution is **100%–0%** (100% to source instance)
- After claiming to an instance, use `UpdatePhoneNumber` to reassign to a TDG for multi-region capability

### Failover
- Update telephony distribution via `UpdateTrafficDistribution` to shift 100% of calls to the healthy region
- Number porting and release work the same as single-region, but the number is associated with the TDG
- Each phone number can belong to only **one TDG** at a time

### Port Requirements
- All phone numbers intended for multi-region failover must be **ported** to Connect (not just claimed)

## Chat Across Regions

- There is **no automatic chat failover** — chat does not participate in TDG telephony distribution
- Chat widgets must be configured with **region-specific** endpoints
- Two approaches:
  1. **Custom chat interfaces**: Configure the replica interface to use the replica region's API endpoint
  2. **Out-of-box communication widgets**: Create a widget in each region's instance, embed the appropriate script

### Configuration Parameters (differ per region)
- **Same across regions**: Instance ID, Flow ID
- **Different per region**: Target AWS Region, API endpoint (API Gateway URL)

### Failover for Chat
- **Manual switch**: Replace the source widget/endpoint with the replica's in your website
- **Automated approach**: Use a centrally controlled database (e.g., DynamoDB Global Table) to store the active region parameter; website checks this and routes accordingly; update this parameter at the same time as `UpdateTrafficDistribution`

### Limitations
- **Persistent chat** is region-bound — cannot resume a session in a different region
- If a region goes down, active chat sessions in that region are **lost**
- Widget configuration changes in the source must be manually replicated to the replica widget

## Metrics and Reporting Across Regions

### Consolidated Metrics (requires AWS Support enablement)
- **Real-time metrics**: Shows consolidated agent activity and contact metrics across paired ACGR instances (e.g., 5 agents in us-east-1 + 10 in us-west-2 = 15 agents shown)
- **Historical metrics**: Consolidated performance data across ACGR instances
- **Metrics APIs**: Return consolidated data across paired instances
- **Analytics** (Contact Lens, etc.) remain **region-specific** and are not consolidated

### Contact Search (requires AWS Support enablement)
- Contact Search page shows contacts from **both** paired ACGR instances by default
- **Active Region filter**: New filter in the dropdown to narrow results to a specific region
- Region-specific resource filters (custom attributes, categories, evaluation filters, email) show only resources from the logged-in region
- Manually typed filter values matching identical names across regions return results from both
- Saved searches display contacts from both instances
- **SearchContacts API** response includes `GlobalResiliencyMetadata`:
  - `ActiveRegion` — the region where the contact is/was processed
  - `OriginRegion` — the region where the contact originated
  - `TrafficDistributionGroupId` — the TDG that routed the contact

### Contact Details
- Full details viewable regardless of originating region: overview, attributes, tags, Contact Lens data, recordings, transcripts
- Contact Lens data (analytics, transcripts, recordings) accessible cross-region for both in-progress and completed contacts
- Contact actions (Transfer, Reschedule, End) route to the contact's active region
- **Contact evaluations** are only available for contacts active in the logged-in region
- If the contact's active region is **impaired**, some data may be unavailable: recordings, transcripts, Contact Lens data, email attachments

### Onboarding Impact
- Alias changes to `{{region}}.{{sourcealias}}.my.connect.aws` format
- Supervisors/admins must authenticate via the global sign-in endpoint (not regional)

### For Unified Custom Reporting
- Export CTRs and agent events from both regions to a data lake (S3, Kinesis)
- Aggregate with Athena, QuickSight, or a custom pipeline
- Contact records include `GlobalResiliencyMetadata` fields to correlate cross-region activity

## Failover Procedures

### Manual Failover (Primary Method)
1. Call `UpdateTrafficDistribution` to shift telephony to 0% source / 100% replica
2. Simultaneously shift `AgentConfig` to route agents to the replica
3. Shift `SignInConfig` (default TDG only) so new agent sign-ins go to the replica
4. For chat: switch website/app to use the replica region's widget/endpoint
5. Update any centralized region parameter (DynamoDB Global Table) if using automated chat routing

### Gradual Migration
- Use 10% increments to slowly shift traffic (e.g., 90/10 → 80/20 → ... → 0/100)
- Monitor metrics in both regions during the shift

### Failback
- Reverse the process: shift distribution back to the original source region
- Verify all agents can sign in and calls land correctly before completing

### There Is No Automatic Failover
- All failover is **manual** via API calls
- No built-in health check or automatic region switching
- You must build your own monitoring and automation around `UpdateTrafficDistribution`

## Limitations and Unsupported Features

- **Voice and chat only** — cross-region distribution supports voice and chat channels
- **Tasks** are region-bound and cannot failover
- **Email** is region-bound
- **Outbound campaigns** are region-bound
- Contact flows, queues, routing profiles, and other configuration are mirrored automatically, but **Lambda functions, Lex bots, and third-party integrations** must be maintained independently
- Agent hierarchy and historical changes are replicated, but **saved report schedules** are not
- No automatic chat failover — requires application-level routing
- No cross-region contact evaluations — evaluations are region-specific
- `SignInConfig` can only be modified on the **default** TDG (not custom TDGs)
- Distribution percentages must be in **10% increments** only
- `$.AwsRegion` is supported only for Lambda ARN and Lex ARN parameters in flows
- CloudTrail 409 (conflict) errors may appear during rapid configuration mirroring — these are benign and do not impact actual sync
