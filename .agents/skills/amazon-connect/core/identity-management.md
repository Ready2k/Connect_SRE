# Identity Management

## Identity Options

The identity model is chosen at instance creation and **cannot be changed after**. Three options:

### 1. Connect-Managed Identity

Amazon Connect stores usernames and passwords internally.

- Users created with username + password via console or `CreateUser` API
- Password policies: minimum length, complexity, expiration (configurable)
- No external directory dependency
- Best for: small deployments, proof-of-concept, teams without existing directory infrastructure

**Limitation**: No SSO. Each user has a separate Connect-specific credential.

### 2. AWS Directory Service (Active Directory)

Link the Connect instance to an existing AWS Managed Microsoft AD or AD Connector.

- Users authenticate with their AD credentials
- User provisioning: AD users must still be explicitly added to Connect (not auto-synced)
- Groups in AD do not map to Connect security profiles — assignment is done in Connect
- Best for: enterprises with existing Active Directory infrastructure

```
Setup:
1. Create or identify an AWS Managed Microsoft AD or AD Connector in the same region
2. During Connect instance creation, select "AWS Directory Service" and choose the directory
3. After creation, add AD users to Connect via console or API (specify DirectoryUserId)
```

**Limitation**: Directory must be in the same AWS region as the Connect instance. Cannot change directories after instance creation.

### 3. SAML 2.0 Federation

Federate authentication to an external Identity Provider (IdP) — Okta, Azure AD, Ping Identity, OneLogin, etc.

- Users authenticate through the IdP, not Connect
- Connect trusts the IdP via SAML assertions
- Best for: organizations requiring SSO, centralized MFA, or compliance-driven identity management

---

## SAML Setup

### Step 1: Create IAM Identity Provider

```
# In IAM, create a SAML provider with the IdP's metadata XML
aws iam create-saml-provider \
  --saml-metadata-document file://idp-metadata.xml \
  --name ConnectIdP
```

### Step 2: Create IAM Role for Federation

The role's trust policy allows the IdP to assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::123456789012:saml-provider/ConnectIdP"
    },
    "Action": "sts:AssumeRoleWithSAML",
    "Condition": {
      "StringEquals": {
        "SAML:aud": "https://signin.aws.amazon.com/saml"
      }
    }
  }]
}
```

Attach a policy granting `connect:GetFederationToken` to this role.

### Step 3: Configure Attribute Mapping in IdP

| SAML Attribute | Maps To | Required |
|---|---|---|
| `https://aws.amazon.com/SAML/Attributes/RoleSessionName` | Connect username | Yes |
| `https://aws.amazon.com/SAML/Attributes/Role` | IAM Role ARN + Provider ARN | Yes |

The `RoleSessionName` must match the username configured in Connect for that user.

### Step 4: Set Relay State

The relay state URL tells AWS where to redirect after SAML authentication:

```
https://<region>.console.aws.amazon.com/connect/federate/<instance-id>
```

Configure this as the relay state (or default relay state) in your IdP's application settings.

### MFA

MFA is handled entirely by the IdP. Connect does not have its own MFA mechanism for SAML-federated users. Configure MFA policies (TOTP, push, hardware keys) in Okta, Azure AD, or whichever IdP you use.

---

## Emergency Login

Every Connect instance has a direct login URL that bypasses SAML federation:

```
https://<instance-alias>.my.connect.aws/login
```

- Only works for users who have a Connect-managed password set (even in SAML instances, the admin account typically has one)
- Use case: IdP outage, SAML misconfiguration, emergency access
- Best practice: create one emergency admin account with a Connect-managed password, even in SAML instances. Store credentials securely (e.g., AWS Secrets Manager or a password vault). Test annually.

---

## Approved Origins (CORS)

When embedding the Contact Control Panel (CCP), chat widget, or other Connect components in a custom web application, the hosting domain must be whitelisted.

### Why It Is Required

Connect's streaming and signaling APIs enforce CORS. Without an approved origin, the browser blocks:
- CCP iframe communication
- WebSocket connections for softphone
- Chat widget API calls
- Any custom application using Amazon Connect Streams JS

### Managing Approved Origins

```
# Add an approved origin
AssociateApprovedOrigin:
  InstanceId: "instance-id"
  Origin: "https://app.example.com"       # Must include protocol, no trailing slash

# List approved origins
ListApprovedOrigins:
  InstanceId: "instance-id"

# Remove an approved origin
DisassociateApprovedOrigin:
  InstanceId: "instance-id"
  Origin: "https://old-app.example.com"
```

### Rules

- Origin format: `https://domain.com` — protocol required, no path, no trailing slash
- `http://` origins are allowed for `localhost` only (development)
- Wildcard subdomains are not supported — each subdomain must be listed individually
- Maximum: 50 approved origins per instance (soft limit, can request increase)

### Common Approved Origins

```
https://app.example.com            # Production app
https://staging.example.com        # Staging environment
http://localhost:3000               # Local development
https://dashboard.example.com      # Internal dashboard
```

---

## Session Management

### Session Timeout

Controls how long an agent's browser session remains valid without re-authentication.

```
# Default: 12 hours (720 minutes)
# Range: 20 minutes to 12 hours

# Configure via Authentication Profile:
UpdateAuthenticationProfile:
  InstanceId: "instance-id"
  AuthenticationProfileId: "auth-profile-id"
  IdleSessionTimeout: 60          # Minutes — session expires after this idle time
```

### IP-Based Access Control

Authentication profiles support IP address restrictions:

```
UpdateAuthenticationProfile:
  InstanceId: "instance-id"
  AuthenticationProfileId: "auth-profile-id"
  AllowedIps: ["203.0.113.0/24", "198.51.100.0/24"]
```

- When configured, agents can only access Connect from the specified IP ranges
- Applies to both CCP and admin console access
- Use case: restrict access to corporate network or VPN IP ranges
- If an agent's IP is not in the allowed list, they receive an access denied error on login

### Session Behavior

- Active contacts keep the session alive regardless of idle timeout
- Closing the browser tab does not immediately end the session — the agent remains logged in until timeout
- Agents can be forcibly logged out via `PutUserStatus` API (set to Offline) but the session token remains valid until expiry
- For SAML instances, the Connect session is independent of the IdP session — logging out of the IdP does not log the agent out of Connect
