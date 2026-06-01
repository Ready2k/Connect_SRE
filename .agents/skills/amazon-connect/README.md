# Amazon Connect Skill

[![skills.sh](https://skills.sh/b/JiteshGaikwad/claude-skills)](https://skills.sh/JiteshGaikwad/claude-skills)

A comprehensive Claude Code skill covering the entire Amazon Connect contact center ecosystem — 72 reference files, 33,000+ lines of structured documentation.

## What's Covered

| Section | Files | Coverage |
|---------|-------|----------|
| **Core** | 8 | Instances, telephony, security (IAM/TBAC/best practices), global resiliency, network (VDI/Direct Connect), routing & queues, user management, identity (SAML/AD/CORS) |
| **Flows** | 14 | Flow designer (mini-map, version control, copy/paste, notes), 53 blocks (full definitions), 9 default flows, 13 sample flows, best practices, flow logs, 13 initiation methods, flow language (56 action types), Lambda integration, contact attributes, media streaming, Nova Sonic, proficiency-based routing, encryption |
| **Channels** | 5 | Voice, chat/SMS, email, tasks, web/video calling |
| **AI** | 6 | Connect AI agents (12 prompt types, 10 agent types, MCP tools), Q Connect, Lex bots, outbound campaigns (journeys, metrics, best practices), generative AI, prompt engineering |
| **Analytics** | 9 | Contact Lens, real-time metrics, 80+ historical metrics, dashboards, data lake, CTR data model, evaluations, monitoring (25 CloudWatch metrics), contact search |
| **Streaming** | 4 | Kinesis data streaming, agent event streams, Contact Lens streams, EventBridge events (11 contact event types) |
| **Agent Experience** | 6 | Workspace, step-by-step guides, CCP, WFM, developer guide (10 SDK clients, 117 methods), troubleshooting |
| **Data** | 3 | Customer Profiles, Cases, data tables |
| **Testing** | 1 | Flow simulation and test cases |
| **API** | 12 | 9 service APIs (500+ actions, 1,070+ data types), rules language, testing language, SDK v3 patterns |
| **Admin** | 1 | Admin workspace themes, home dashboard, notifications |
| **Recent Changes** | 1 | 2026 release notes |

## Key Details

- **SDK**: All code examples use AWS SDK v3 for JavaScript/TypeScript only
- **Voice ID**: Excluded (EOL May 2026)
- **Self-updating**: SKILL.md points to AWS doc history pages so Claude can check for new features and update reference files

## Usage

```
/amazon-connect
```

Or it auto-triggers when working on Amazon Connect-related code.

## Installation

```bash
# As part of the full skills repo
git clone https://github.com/JiteshGaikwad/claude-skills.git ~/.claude/skills/claude-skills

# Or standalone
cp -r skills/amazon-connect/ ~/.claude/skills/amazon-connect
```

## Sources

Built from publicly available AWS documentation:
- [Amazon Connect Admin Guide](https://docs.aws.amazon.com/connect/latest/adminguide/)
- [Amazon Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [Agent Workspace Developer Guide](https://docs.aws.amazon.com/agentworkspace/latest/devguide/)
