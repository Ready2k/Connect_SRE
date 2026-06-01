# Amazon Connect — Recent Changes (2026)

## May 2026
- **Default Step-by-Step Guides for ACW**: Auto-launch guides when agents enter ACW state
- **Multi-contact time zone detection**: Outbound campaigns detect customer time zones using all phone numbers and addresses
- **Cases identity resolution**: Auto-reassociate cases when duplicate profiles merge
- **Increased attachment size**: 20MB → 100MB for chat, cases, tasks; custom file extensions configurable
- **CloudTrail for supervisor status changes**: Agent activity status changes captured in CloudTrail
- **8 new AI Agent performance metrics**: Goal success rate, faithfulness score, tool selection accuracy, customer feedback ratings
- **Contact priority ordering**: Configure dial order based on up to 10 profile attributes for voice campaigns
- **Hourly segment refresh**: Reduced from 24h minimum to hourly for outbound campaigns
- **Auto customer context for AI self-service**: Pass customer context into calls without re-identification
- **Flow modules across all flow types**: Modules now work in all flows (not just inbound), support nesting

## April 2026
- **Updated service-linked role policy**: Added wisdom:* permissions for Connect AI agents

## March 2026
- **Case data in analytics data lake**: Case data alongside other Connect analytics
- **AI-powered manager assistance (preview)**: Natural language queries across 150+ metrics
- **Conversational analytics for email**: Categorization, PII redaction, summaries for email
- **Integrated manager coaching**: Create plans from scorecards, agents acknowledge feedback
- **Multiple "from" email addresses**: Agents select sender per queue
- **Email forwarding**: Forward to external addresses and distribution lists
- **Tag-based access control for quick responses**: TBAC for routing profile assignments
- **Chat testing and simulation**: Configure test parameters, business conditions, results analysis

## February 2026
- **Service Quotas for Cases**: Centralized view of limits, request increases directly
- **Larger multi-line text fields**: Cases support up to 4,100 characters
- **Per-channel auto-accept and ACW timeouts**: Configure separately for chat, tasks, email, callbacks
- **Audio enhancement for agents**: Noise suppression, voice isolation
- **CSV upload for dependent field options**: Bulk configure cascading dropdowns in Cases
- **In-app notifications**: Header notifications with URLs for urgent updates

## January 2026
- **Recurring events for operating hours**: Visual calendar for managing hours, holidays

## Agent Workspace Dev Guide Changes
- **Dec 2025**: AWS-managed app integration via Streams
- **Jul 2025**: 3P Services (headless) + AppController API
- **Apr 2025**: SDK API v1.0.5

---

For the latest changes, check:
- Admin Guide: https://docs.aws.amazon.com/connect/latest/adminguide/doc-history.html
- Dev Guide: https://docs.aws.amazon.com/agentworkspace/latest/devguide/doc-history.html
