# User Management

## User Lifecycle

### Creating Users

```
CreateUser:
  Username: "jdoe"                          # Unique within instance
  Password: "initial-password"              # Only for Connect-managed identity
  IdentityInfo:
    FirstName: "Jane"
    LastName: "Doe"
    Email: "jdoe@example.com"
    SecondaryEmail: "jane.doe@example.com"   # Optional
    Mobile: "+15551234567"                   # Optional
  PhoneConfig:
    PhoneType: SOFT_PHONE                    # SOFT_PHONE or DESK_PHONE
    AutoAccept: false                        # Auto-answer incoming contacts
    AfterContactWorkTimeLimit: 30            # ACW timeout in seconds (0 = manual)
    DeskPhoneNumber: "+15559876543"          # Required if DESK_PHONE
  SecurityProfileIds: ["sp-id"]             # At least one required
  RoutingProfileId: "rp-id"                 # Exactly one required
  HierarchyGroupId: "hg-id"                # Optional
  DirectoryUserId: "ad-user-id"             # Required for AD/SAML identity
  Tags:
    Department: "Support"
```

### Updating Users

Separate API calls for different aspects:

| API | What It Updates |
|---|---|
| `UpdateUserIdentityInfo` | First name, last name, email, mobile |
| `UpdateUserPhoneConfig` | Phone type, auto-accept, ACW timeout, desk phone number |
| `UpdateUserSecurityProfiles` | Security profile assignments |
| `UpdateUserRoutingProfile` | Routing profile assignment |
| `UpdateUserHierarchyGroup` | Hierarchy group placement |

Each call is atomic — you cannot update identity info and phone config in one call.

### Deleting Users

```
DeleteUser:
  UserId: "user-id"
```

Deleting a user removes their agent queue, CCP access, and all assignments. Historical data (CDRs, recordings, metrics) is retained — it references the user ID, not the live user record.

---

## Bulk User Operations

The Connect console supports CSV-based bulk user management.

### CSV Upload (Create/Update)

Download the template from the Connect console → User Management → Bulk Upload. Fields:

| Field | Required | Notes |
|---|---|---|
| first name | Yes | |
| last name | Yes | |
| email address | Yes | |
| user login | Yes | Must be unique |
| password | Conditional | Required for Connect-managed identity |
| routing profile name | Yes | Must match existing profile name exactly |
| security_profile name | Yes | Can list multiple separated by semicolons |
| phone type | Yes | `soft` or `desk` |
| phone number | Conditional | Required if phone type is `desk` |
| soft phone auto accept | Yes | `yes` or `no` |
| ACW timeout | Yes | Seconds (0 = manual) |
| hierarchy group | No | Full path: `Division/Department/Team/Group` |

### Limitations

- Maximum 100 users per CSV upload
- Cannot delete users via CSV — only create and update
- Validation errors fail the entire batch (no partial success)
- Duplicate usernames in the CSV cause the entire upload to fail

---

## Security Profiles

Security profiles control what a user can see and do in the Connect console, CCP, and APIs.

### Permission Categories

| Category | Controls |
|---|---|
| Routing | Queues, routing profiles, hours of operation, quick connects |
| Numbers & Flows | Phone numbers, contact flows, flow modules, prompts |
| Contact Control Panel | CCP access, call controls, transfer, hold, create task |
| Users & Permissions | User management, security profiles, hierarchy groups, agent status |
| Metrics & Reporting | Real-time metrics, historical metrics, login/logout reports, saved reports |
| Recording & Analytics | Recording access, Contact Lens, screen recording, playback |
| Quality & Evaluation | Evaluation forms, agent evaluations, calibration |
| Rules & Automation | Rules engine, event triggers, automated actions |
| Contact Search | Contact search, contact details, contact attributes |
| Cases | Case management, case templates, case fields |
| Customer Profiles | Profile access, profile editing, calculated attributes |
| Campaigns | Outbound campaigns |
| Dashboard & Views | Dashboard configuration, custom views, saved views |
| Data Tables | Table access, row-level CRUD |
| Workspace | Custom workspace views, third-party app integration |
| AI/ML | Amazon Q in Connect, Contact Lens rules, AI features |

### Predefined Roles

| Role | Access Level |
|---|---|
| **Admin** | Full access to all features and settings. Use for: instance administrators. |
| **Agent** | CCP access, own metrics, basic contact handling. Use for: frontline agents. |
| **CallCenterManager** | Metrics, recordings, user management, quality. No flow editing. Use for: supervisors and managers. |
| **QualityAnalyst** | Evaluations, recordings, Contact Lens analytics. No user management. Use for: QA teams. |

### Custom Security Profiles

```
CreateSecurityProfile:
  SecurityProfileName: "Senior Agent"
  Description: "Agent with recording access and contact search"
  Permissions:
    - "BasicAgentAccess"
    - "ContactSearch"
    - "ContactRecording.Access"
    - "MetricsReports.RealTimeMetrics.Access"
  AllowedAccessControlTags:
    "Department": ["Support", "Sales"]      # Tag-based resource access
  TagRestrictedResources:
    - "Queue"
    - "User"
```

A user can have multiple security profiles — permissions are additive (union of all assigned profiles).

---

## Hierarchy Groups

Hierarchy groups organize agents into a reporting tree. Used for metric filtering, access control, and organizational rollups.

### Five-Level Structure

```
Level 1: Division       (e.g., North America, EMEA)
Level 2: Department      (e.g., Sales, Support)
Level 3: Team            (e.g., Enterprise Sales, SMB Sales)
Level 4: Group           (e.g., East Coast, West Coast)
Level 5: Agent Group     (e.g., Senior Agents, New Hires)
```

Not all levels are required. You can use 1, 2, or any number up to 5.

### Defining the Structure

```
UpdateUserHierarchyStructure:
  HierarchyStructure:
    LevelOne:
      Name: "Division"
    LevelTwo:
      Name: "Department"
    LevelThree:
      Name: "Team"
```

### Creating Groups

```
CreateUserHierarchyGroup:
  Name: "North America"
  ParentGroupId: null              # Top-level group (Level 1)

CreateUserHierarchyGroup:
  Name: "Technical Support"
  ParentGroupId: "north-america-id"  # Child of North America (Level 2)
```

### Use Cases

- **Metric Filtering**: Dashboard shows metrics for "North America → Support" only
- **Access Control**: Manager security profile scoped to their hierarchy subtree
- **Reporting Rollups**: Aggregate agent performance by team, department, or division
- **Workforce Management**: Schedule and forecast by organizational unit

### Assigning Users

```
UpdateUserHierarchyGroup:
  UserId: "user-id"
  HierarchyGroupId: "team-id"      # Assign to the most specific level
```

A user belongs to one hierarchy group. The group's ancestors (parent, grandparent, etc.) are inherited automatically.

---

## Agent Status

Agent status controls routing eligibility and appears in real-time metrics.

### Built-in Statuses

| Status | Routable | Description |
|---|---|---|
| **Available** | Yes | Agent can receive contacts |
| **Offline** | No | Agent is logged out or set to offline |
| **Error** | No | System error — missed contact, connection failure |

Built-in statuses cannot be modified or deleted.

### Custom Statuses

```
CreateAgentStatus:
  Name: "Break"
  State: DISABLED                 # ENABLED (routable) or DISABLED (non-routable)
  DisplayOrder: 1                 # Order in the agent's status dropdown
  Description: "15-minute break"

CreateAgentStatus:
  Name: "Training"
  State: DISABLED
  DisplayOrder: 2

# Routable custom status (rare — agent receives contacts while in this status):
CreateAgentStatus:
  Name: "Available - Outbound"
  State: ENABLED                  # Still receives inbound contacts
  DisplayOrder: 3
```

### Status Behavior

- **Routable** (`ENABLED`): Agent receives contacts. Functionally equivalent to Available but tracked separately in metrics.
- **Non-routable** (`DISABLED`): Agent does not receive contacts. Used for breaks, meetings, training.
- **Next Status**: If an agent selects a new status while handling a contact, the status changes after the current contact ends (including ACW). The pending status shows in metrics as "Next status."

### After Contact Work (ACW)

ACW is the state after a contact ends where the agent completes notes, disposition, or wrap-up tasks.

| ACW Mode | Behavior |
|---|---|
| **Auto** (`AfterContactWorkTimeLimit > 0`) | Agent enters ACW, automatically returns to Available after N seconds |
| **Manual** (`AfterContactWorkTimeLimit = 0`) | Agent enters ACW, must manually set Available when ready |

ACW time is tracked in metrics. During ACW, the agent is non-routable — no new contacts are delivered.

### Related APIs

| Operation | Purpose |
|---|---|
| `CreateAgentStatus` | Create a custom status |
| `UpdateAgentStatus` | Modify name, state, or display order |
| `ListAgentStatuses` | List all statuses for the instance |

---

## Hours of Operation and Users

Hours of operation are linked to **queues**, not users. The chain is:

```
Agent → Routing Profile → Queue → Hours of Operation
```

An agent's effective operating hours are determined by the queues in their routing profile. If all queues in an agent's routing profile are outside hours, contacts are not routed to those queues — but the agent can still be logged in and Available (they simply receive no contacts from closed queues).

This means:
- Different queues can have different hours in the same routing profile
- An agent can serve a mix of 24/7 queues and business-hours-only queues
- Changing hours requires updating the HoO on the queue, not on the agent or routing profile
