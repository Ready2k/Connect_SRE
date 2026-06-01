# Amazon Connect — Security

## Shared Responsibility Model
- **AWS**: Security OF the cloud (infrastructure, availability)
- **You**: Security IN the cloud (config, access, data classification)

## Identity & Access Management (IAM)

### IAM Resource-Level Permissions

Connect ARN format:
```
arn:aws:connect:{region}:{account}:instance/{instance-id}/{resource-type}/{resource-id}
```

Supported resource types in ARNs:
- `instance` — the Connect instance itself
- `contact-flow` — individual flows and modules
- `queue` — queues
- `routing-profile` — routing profiles
- `user` — Connect users
- `security-profile` — security profiles
- `hours-of-operation` — operating hours
- `agent-status` — agent status definitions
- `phone-number` — claimed phone numbers
- `integration-association` — integrations (Lex, Lambda, etc.)

#### Example: Read-Only IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:Describe*",
        "connect:List*",
        "connect:Get*",
        "connect:Search*"
      ],
      "Resource": "arn:aws:connect:us-east-1:123456789012:instance/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "connect:DescribeInstance",
        "connect:ListInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Example: Flow Management IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:CreateContactFlow",
        "connect:UpdateContactFlowContent",
        "connect:UpdateContactFlowName",
        "connect:UpdateContactFlowMetadata",
        "connect:DescribeContactFlow",
        "connect:ListContactFlows",
        "connect:DeleteContactFlow"
      ],
      "Resource": "arn:aws:connect:us-east-1:123456789012:instance/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/contact-flow/*"
    }
  ]
}
```

#### IAM Condition Keys

| Condition Key | Description |
|---|---|
| `connect:InstanceId` | Restrict actions to a specific instance |
| `aws:ResourceTag/{TagKey}` | Restrict based on resource tags |
| `connect:MonitorCapabilities` | Control monitor/barge capabilities |
| `aws:RequestTag/{TagKey}` | Require specific tags on creation |
| `aws:TagKeys` | Control which tag keys can be used |

### Service-Linked Role

- **Role name**: `AWSServiceRoleForAmazonConnect`
- **Managed policy**: `AmazonConnectServiceLinkedRolePolicy`
- Auto-created when you create a new Connect instance
- Cannot be modified or deleted while any Connect instance exists
- Grants Connect permissions to:
  - Manage CloudWatch metrics and logs
  - Access S3 buckets for recordings and exported reports
  - Invoke Lambda functions associated with the instance
  - Access Lex bots associated with the instance
  - Manage Kinesis streams and Firehose for data streaming
  - Access Customer Profiles domain resources
  - Publish to SNS topics for event notifications

### Tag-Based Access Control (TBAC)

Taggable resources: queues, flows, users, routing profiles, security profiles, hours of operation, agent statuses, phone numbers.

#### Example: Restrict Supervisors to Their Team's Queues

Tag queues with `Team=TeamA` or `Team=TeamB`, then apply this IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:DescribeQueue",
        "connect:UpdateQueueName",
        "connect:UpdateQueueStatus",
        "connect:GetCurrentMetricData",
        "connect:GetMetricDataV2"
      ],
      "Resource": "arn:aws:connect:us-east-1:123456789012:instance/*/queue/*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Team": "TeamA"
        }
      }
    }
  ]
}
```

Use case examples:
- Restrict supervisors to only manage queues tagged with their team
- Allow flow developers to edit only flows tagged with their department
- Limit metric access to users tagged with a specific business unit

## Security Profiles

### Predefined Roles

| Profile | Access |
|---|---|
| **Admin** | Full access to all permissions across every category. Can manage users, security profiles, instance settings, flows, queues, and all configuration. |
| **Agent** | Contact Control Panel (CCP) access only. Can handle inbound/outbound contacts, transfer calls, and view the contact directory. No access to metrics, flows, or admin settings. |
| **CallCenterManager** | Metrics and reporting (real-time and historical), user management, queue management, recording playback, agent scheduling, and quality management. Cannot modify flows or instance settings. |
| **QualityAnalyst** | Recording playback and review, Contact Lens analytics, evaluation forms, quality metrics, and contact search. No user management or flow editing. |

### Full Permission Taxonomy

Security profile permissions are organized into these categories:

- **Routing** — Queues (create/edit/enable-disable), routing profiles, quick connects, hours of operation, prompts, task templates
- **Numbers** — Claim/release phone numbers, manage number associations
- **Flows** — Create/edit/publish contact flows and modules
- **Contact Control Panel (CCP)** — Make/receive calls, transfer, hold, conference, create tasks, restrict contact attributes visibility
- **Users** — Create/edit/view users, manage hierarchy groups, agent statuses, proficiencies
- **Metrics** — Access real-time metrics, historical metrics, agent activity audit, login/logout reports, saved reports
- **Recording** — Access recorded conversations, monitor live calls, barge into calls, manager listen-in, screen recording playback
- **Quality** — Evaluation forms, calibrations, Contact Lens analytics, post-contact summaries
- **Rules** — Create/edit/delete automation rules, manage rule templates
- **Contact Search** — Search contacts by attributes, view contact details, view contact flow logs, access contact records
- **Cases** — Create/edit/view cases, manage case templates, case fields, case event configurations
- **Customer Profiles** — View/edit/create customer profiles, manage profile object types, calculated attributes
- **Campaigns** — Outbound campaigns management, campaign scheduling, contact list management
- **Dashboard** — View/customize supervisor dashboards, create saved views
- **Views** — Manage step-by-step guides and agent workspace views
- **Data Tables** — Create/read/update/delete data table records
- **Workspace** — Configure agent workspace layout, app integrations
- **AI/ML** — Forecast management, capacity planning, agent scheduling, Contact Lens configuration

### Custom Security Profile Guidance

- Start from the principle of least privilege — grant only the permissions an agent or role truly needs
- Use `CreateSecurityProfile` API or the admin console under Users > Security Profiles
- `UpdateSecurityProfile` to modify, `ListSecurityProfilePermissions` to audit
- Assign multiple security profiles to a single user when a role spans categories
- Audit profiles periodically — remove permissions that are no longer needed
- Name profiles descriptively (e.g., `Tier2Support-WithRecording`, `BillingTeamLead`)

## Data Protection

### Encryption at Rest

- **S3 recordings and exports**: SSE-S3 (default) or SSE-KMS (customer-managed key)
- **Kinesis streams**: Server-side encryption with KMS
- **Contact Lens output**: Encrypted in S3 alongside recordings

### Configuring KMS for Recordings

1. Create or select a KMS key in the same region as your Connect instance
2. Grant the Connect service-linked role `kms:GenerateDataKey` and `kms:Decrypt` on the key
3. In Connect admin console: Data Storage > Call Recordings > select "KMS key" and provide the key ARN
4. Same configuration available for chat transcripts, exported reports, and Contact Lens output
5. **Key rotation**: Enable automatic annual rotation on the KMS key. AWS retains old key material so existing recordings remain decryptable.

### Encryption in Transit
- TLS 1.2+ for all API calls and CCP connections
- SRTP for voice media between agents and Connect

### Customer Input Encryption
- Public signing key configured in contact flows
- Encrypts sensitive DTMF input (credit card numbers, SSNs)

### PII Redaction
- Contact Lens redacts PII from transcripts and audio
- Configurable categories: name, address, credit card, SSN, etc.

## Authentication Profiles

### IP Address Restrictions

- Specify allowed CIDR ranges in the authentication profile
- Applies to both admin console login and CCP (Contact Control Panel) login
- API: `UpdateAuthenticationProfile` with `AllowedIps` parameter
- CIDR format examples: `10.0.0.0/8`, `192.168.1.0/24`, `203.0.113.50/32`
- Best practice: restrict CCP access to corporate network CIDR blocks to prevent logins from untrusted networks

### Session Timeouts

- Default session duration: 12 hours
- Configurable range: 20 minutes to 12 hours
- API: `UpdateAuthenticationProfile` with `PeriodIntervalInMinutes`
- Shorter timeouts recommended for high-security environments
- Agents are logged out automatically when the session expires

### SAML 2.0 Federation
- Integrates with any SAML 2.0 IdP (Okta, Azure AD, OneLogin, PingFederate, etc.)
- Enables SSO and MFA through the IdP
- Relay state URL format: `https://{region}.console.aws.amazon.com/connect/federate/{instance-id}`
- Map IdP attributes to Connect user attributes

## Compliance
- GDPR, HIPAA eligible, PCI DSS, SOC 1/2/3, ISO 27001
- FedRAMP (GovCloud)
- HITRUST CSF

## Infrastructure Security
- Runs in AWS VPC
- No public endpoints exposed by default
- CloudTrail logs all API calls
- CloudWatch monitors instance health

## Cross-Service Confused Deputy Prevention
- Use `aws:SourceArn` and `aws:SourceAccount` condition keys
- Prevents services from being used as proxies

## Security Best Practices Checklist

1. **Use restrictive security profiles** — Never assign Admin to agents. Create custom profiles scoped to the exact permissions each role requires.

2. **Enable MFA** — Configure MFA through your SAML IdP. If using Connect-managed auth, enable RADIUS MFA integration.

3. **Emergency access URL** — The emergency login URL bypasses federation. Use it only when your IdP is down. Restrict knowledge of this URL to a small number of administrators.

4. **Prevent instance deletion with SCPs** — Apply a Service Control Policy at the AWS Organizations level:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyConnectInstanceDeletion",
      "Effect": "Deny",
      "Action": ["connect:DeleteInstance"],
      "Resource": ["arn:aws:connect:*:*:instance/*"]
    },
    {
      "Sid": "DenyConnectRoleDeletion",
      "Effect": "Deny",
      "Action": ["iam:DeleteRole"],
      "Resource": ["arn:aws:iam::*:role/ConnectUserRole"]
    }
  ]
}
```

5. **Enable CloudWatch logging for flows** — In instance settings, enable contact flow logs. Set CloudWatch alarms for flow errors and Lambda invocation failures.

6. **Archive logs with lifecycle policies** — Export CloudWatch logs to S3 with lifecycle rules (e.g., transition to Glacier after 90 days, expire after 7 years for compliance).

7. **Restrict IP ranges** — Use authentication profiles to limit CCP and console access to corporate CIDR ranges.

8. **Protect chat from XSS** — If building custom chat UIs:
   - Always encode output before rendering chat messages
   - Set a Content Security Policy (CSP) header
   - Never use `innerHTML` to render agent or customer messages
   - Sanitize any user-provided content before display

9. **Protect WebRTC participant tokens** — For custom CCP or video implementations:
   - Authenticate the user before issuing a participant token
   - Always use HTTPS for token delivery
   - Minimize token exposure time — generate tokens on demand, not ahead of time

10. **Monitor with CloudTrail** — Enable CloudTrail for the Connect instance. Key events to alert on:
    - `DeleteInstance`, `DeleteUser`, `DeleteContactFlow`
    - `CreateUser` with Admin security profile
    - `UpdateSecurityProfile` changes
    - `AssociateBot`, `AssociateLambdaFunction` (new integrations)

11. **Rotate credentials regularly** — Rotate KMS keys, review IAM policies quarterly, and audit security profile assignments monthly.

12. **Use resource tagging** — Tag all Connect resources for cost allocation, access control, and audit trail purposes.
