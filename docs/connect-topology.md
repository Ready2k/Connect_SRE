# Connect Topology Graph

The topology graph is the SRE agent's primary source of truth during incident triage. It is an adjacency-list stored in DynamoDB (`dev-connect-sre-topology`) and built by the Topology Scanner Lambda from live Connect APIs. The FLOW, MODULE, IMPACT, and RISK specialists all query it directly — without it they cannot calculate blast radius or map dependencies.

---

## DynamoDB schema

Every row has two key fields:

| Field | Type | Purpose |
|---|---|---|
| `nodeId` (PK) | String | Identifies the node: `{type}:{id}` — e.g. `flow:abc-123` |
| `edgeTypeTarget` (SK) | String | `"METADATA"` for attribute rows; `"{EDGE_TYPE}#{targetNodeId}"` for edge rows |

### Metadata row (`edgeTypeTarget = "METADATA"`)

Holds the node's attributes. Always present for every node:

```json
{
  "nodeId": "flow:abc-123",
  "edgeTypeTarget": "METADATA",
  "nodeType": "flow",
  "label": "InboundBankingFlow",
  "arn": "arn:aws:connect:us-west-2:...:contact-flow/abc-123",
  "status": "ACTIVE",
  "lastSeenAt": "2026-05-29T18:00:00Z",
  "scanConfidence": "1.0"
}
```

Optional extra fields on `lex` nodes: `botId`, `botAliasId`, `botVersion`.

### Edge row (`edgeTypeTarget = "{EDGE_TYPE}#{targetNodeId}"`)

Records a directed relationship from `nodeId` → `targetNodeId`:

```json
{
  "nodeId": "flow:abc-123",
  "edgeTypeTarget": "FLOW_USES_MODULE#module:xyz-789",
  "targetNodeId": "module:xyz-789",
  "relationshipType": "FLOW_USES_MODULE",
  "lastSeenAt": "2026-05-29T18:00:00Z",
  "scanConfidence": "1.0"
}
```

---

## Node types

| `nodeType` | `nodeId` prefix | Source API |
|---|---|---|
| `instance` | `instance:{instanceId}` | `connect:DescribeInstance` |
| `flow` | `flow:{contactFlowId}` | `connect:ListContactFlows` + `DescribeContactFlow` |
| `module` | `module:{moduleId}` | `connect:ListContactFlowModules` + `DescribeContactFlowModule` |
| `queue` | `queue:{queueId}` | `connect:ListQueues` (STANDARD type only) + `DescribeQueue` |
| `routing` | `routing:{routingProfileId}` | `connect:ListRoutingProfiles` |
| `lex` | `lex:{aliasArn}` | `connect:ListBots` (V2) + `lexv2-models:DescribeBotAlias` |
| `phone_number` | `phone:{phoneNumberId}` | `connect:ListPhoneNumbersV2` |
| `lambda` | `lambda:{functionArn}` | Extracted from flow JSON content (regex) |

---

## Edge types

### Instance-level edges (written during full scan)

| Edge type | Source | Target | Meaning |
|---|---|---|---|
| `INSTANCE_HAS_FLOW` | `instance:*` | `flow:*` | Instance owns this flow |
| `INSTANCE_HAS_MODULE` | `instance:*` | `module:*` | Instance owns this module |
| `INSTANCE_HAS_QUEUE` | `instance:*` | `queue:*` | Instance owns this queue |
| `INSTANCE_HAS_ROUTING` | `instance:*` | `routing:*` | Instance owns this routing profile |
| `INSTANCE_HAS_LEX` | `instance:*` | `lex:*` | Lex bot associated at instance level |
| `INSTANCE_HAS_PHONE` | `instance:*` | `phone:*` | Phone number claimed by instance |

### Flow-level edges (extracted from flow JSON content)

| Edge type | Source | Target | Meaning |
|---|---|---|---|
| `FLOW_USES_LAMBDA` | `flow:*` | `lambda:*` | Flow invokes this Lambda ARN |
| `FLOW_USES_LEX` | `flow:*` | `lex:*` | Flow references this Lex alias ARN |
| `FLOW_ROUTES_TO_QUEUE` | `flow:*` | `queue:*` | Flow transfers to this queue |
| `FLOW_USES_MODULE` | `flow:*` | `module:*` | Flow references this shared module |

### Entry-point edges

| Edge type | Source | Target | Meaning |
|---|---|---|---|
| `PHONE_ROUTES_TO_FLOW` | `phone:*` | `flow:*` | Phone number's primary flow |

---

## Blast radius traversal

`calculate_blast_radius(start_node_id, max_depth, direction)` in `tools.py` does a BFS over the topology graph:

- **`direction="upstream"`** (default, used for impact assessment): follows `REQUIRED_BY` relationships — finds everything that *depends on* the failed node. Starting at a broken `module:*`, this finds all `flow:*` nodes that use it, then all `phone:*` entry points that reach those flows.
- **`direction="downstream"`**: follows `DEPENDS_ON` relationships — finds what the node *itself* depends on.

The adjacency-list uses `DEPENDS_ON#` and `REQUIRED_BY#` sort-key prefixes for reverse-index lookups. The scanner writes `DEPENDS_ON` edges (e.g. `FLOW_USES_MODULE`); `REQUIRED_BY` edges are the same relationship stored in reverse so upstream traversal is O(1) per hop rather than a full table scan.

---

## How the scanner runs

### Full scan (EventBridge schedule)

The Topology Scanner Lambda is triggered on a schedule (configurable in CloudFormation) and re-scans all instances listed in `CONNECT_INSTANCE_IDS`. Order of operations:

1. Scan instance metadata
2. Scan all contact flows → extract Lambda, Lex, queue, module edges from flow JSON content
3. Scan all contact flow modules
4. Scan all queues (STANDARD type only)
5. Scan all routing profiles
6. Scan instance-level Lex V2 bot associations
7. Scan phone numbers → write `PHONE_ROUTES_TO_FLOW` edges

### Partial scan (SQS — triggered by Normalizer)

When the Normalizer processes a CloudTrail mutation event (e.g. `UpdateContactFlow`), it enqueues a partial scan message. The scanner picks this up and re-scans only the mutated resource (`handle_partial_scan()`), updating its METADATA row and re-extracting its edges.

Supported resource types for partial scan: `contact_flow`, `contact_flow_module`.

### Manual trigger (UI)

The `/topology` page has a "Scan" button → `POST /api/topology/scan` → SQS message → full scan.

---

## Querying the graph

### From agent tools

```python
# Get all edges for a node (metadata + all relationships)
query_topology("flow:abc-123")

# BFS upstream from a failed module (what flows and phones are impacted?)
calculate_blast_radius("module:xyz-789", max_depth=3, direction="upstream")
```

### From AWS CLI (debugging)

```bash
# Get METADATA for a specific node
aws dynamodb get-item \
  --table-name dev-connect-sre-topology \
  --key '{"nodeId": {"S": "flow:abc-123"}, "edgeTypeTarget": {"S": "METADATA"}}' \
  --profile connect-sre-dev

# Get all edges from a flow node
aws dynamodb query \
  --table-name dev-connect-sre-topology \
  --key-condition-expression "nodeId = :nid" \
  --expression-attribute-values '{":nid": {"S": "flow:abc-123"}}' \
  --profile connect-sre-dev

# Count all nodes in the table (post-scan sanity check)
aws dynamodb scan \
  --table-name dev-connect-sre-topology \
  --filter-expression "edgeTypeTarget = :m" \
  --expression-attribute-values '{":m": {"S": "METADATA"}}' \
  --select COUNT \
  --profile connect-sre-dev
```

---

## Graph limitations (current)

- **No routing profile → queue edges**: the scanner does not call `ListRoutingProfileQueues` to link `routing:*` nodes to the `queue:*` nodes they serve. IMPACT specialist cannot currently trace routing profile degradation to specific queues.
- **No Q Connect AI Agent nodes**: AI agents are not added to the topology graph. The AIA specialist uses `query_ai_agent_health()` (live `qconnect` API) rather than topology traversal.
- **Lambda function metadata not enriched**: `lambda:*` nodes are written as edges only — no `METADATA` row is created because the scanner does not call `lambda:GetFunction`. The `nodeType` field will be absent for Lambda nodes.
- **Scan staleness**: partial scans only cover `contact_flow` and `contact_flow_module`. Queue, routing profile, and phone number changes require a full scan cycle to be reflected.

---

## Populating a fresh environment

The topology table is empty after first deployment. Run the scanner before using the agent:

```bash
# Via test script (uses connect-sre-dev profile automatically)
./infra/scripts/test_topology_scanner.sh

# Or manually with a specific instance ID
cd infra/src
TOPOLOGY_TABLE_NAME=dev-connect-sre-topology \
CONNECT_INSTANCE_IDS=<your-instance-uuid> \
python topology_scanner.py
```

After the scan, verify with:
```bash
aws dynamodb scan \
  --table-name dev-connect-sre-topology \
  --select COUNT \
  --profile connect-sre-dev
```

An empty Connect instance with a few flows and queues will typically produce 50–200 rows. A large estate with hundreds of flows can produce thousands.
