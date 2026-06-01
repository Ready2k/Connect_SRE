# Data Tables

Data tables provide structured data storage directly accessible from Amazon Connect contact flows, eliminating the need for Lambda functions for simple data lookups and writes. They store configuration data, business rules, customer preferences, and other reference data that flows need at runtime.

## Overview

Data tables store and manage data that impacts configurations within Connect. They can be referenced by other resources such as flows and views. Changes made to data tables are available immediately via public APIs and on-screen -- no redeployment necessary.

Unlike predefined attributes (simple key-value pairs), data tables support multiple columns, various data types, and complex relationships.

A data table consists of:
- **Table metadata** -- structure and validation rules (attributes/columns, primary keys, default values, validation rules)
- **Table values** -- the actual data stored in records (rows)

**When to use data tables vs Lambda:**
- **Data tables** -- simple lookups, configuration data, business rules, small reference datasets, dynamic routing decisions, status checks, feature flags
- **Lambda** -- complex logic, external API calls, large datasets, joins across multiple sources, multi-row transactional consistency

**When to use data tables vs predefined attributes:**
- **Predefined attributes** -- simple key-value pairs
- **Data tables** -- multiple columns, various data types, complex relationships, multiple records

---

## Table Structure

### Primary Keys

Primary keys identify and reference specific records. They also enable granular access control to table data.

- One or more attributes can be designated as primary (composite keys supported)
- Primary attributes become the first column(s) of the table
- If no primary attribute is defined, the table can contain only one record
- Primary attributes cannot be added or removed if the table contains data (all rows must be deleted first)
- Values in primary attributes can be edited after creation
- Non-primary attributes can be added at any time, even after the table is populated

### Attribute Types

| Type | Variants | Description |
|---|---|---|
| **Single** | Text, Number, Boolean (yes/no) | A single scalar value |
| **List** | Text list, Number list | An ordered collection of values |

### Validation

- **Basic validation** -- max length for text, range for numeric values
- **Collection validation** -- predefined choice values for text or numeric attributes; optionally restrict to only those values
- Data inputs are automatically validated on write (type, length, etc.)
- Rows are auto-sorted by primary value(s) (e.g., A-Z for text)

### Example Structures

Simple single-key table:

| Language (primary) | Greeting |
|---|---|
| English | Hello |
| Spanish | Hola |

Multi-key composite table:

| Language (primary) | Department (primary) | Greeting |
|---|---|---|
| English | Sales | Hello. This is sales. |
| Spanish | Sales | Hola. Soy del departamento de ventas. |
| English | Marketing | Hi. You've reached marketing. |

Three-dimensional lookup:

| Language (primary) | Department (primary) | Message type (primary) | Message |
|---|---|---|---|
| English | Sales | Greeting | Hello. This is sales. |
| Spanish | Sales | Greeting | Hola. Soy del departamento de ventas. |
| English | Marketing | Farewell | Thanks for contacting marketing. |

---

## Creating Data Tables (Admin Console)

1. Go to **Routing > Data tables**
2. Select **Add new data table**
   - Provide a **Name**
   - Optionally provide a **Description**
   - Indicate a **Time zone** (for time-based use cases)
   - Define a **Lock level** -- locking prevents multiple editors from overwriting changes at the data table, record (row), attribute (column), or value (cell) level
3. Select **Add attribute** to define columns (inserted leftmost)
   - Provide a **Name**
   - Select a **Type** (Single text/number/boolean, or List of text/numbers)
   - Optionally select **Use as primary attribute**
   - Optionally add **Basic validation** (max length for text, range for numeric)
   - Optionally add **Collection validation** (predefined choice values, restrict to those values)
4. Select **Add value** to insert rows
   - Acknowledge that primary attributes cannot be changed if values exist
   - Data inputs are automatically validated

---

## Flow Block Operations

The **Data Table** flow block supports three operations. Supported on all channels (voice, chat, task, email) and all flow types.

### Evaluate (Single-Row Lookup)

Query data tables and retrieve specific attribute values based on defined criteria.

**Configuration:**
1. Select **Read from data table** as the action
2. Select **Evaluate Data Table values**
3. Configure queries:
   - Up to **5 queries** per Data Table block (minimum 1 required)
   - **Query Name** (required) -- must be unique across the entire flow (not just the block)
   - **Primary Attributes** -- auto-populated from table schema; all primary attributes are required; uses **exact matching**
   - **Query Attributes** -- select which non-primary attributes to return

**Accessing retrieved data:**

Use namespace format: `$.DataTables.{{QueryName}}.{{AttributeName}}`

For attribute names with special characters: `$.DataTables.CustomQuery['my attribute name with spaces']`

When using the Data tables namespace dropdown, the root `$.DataTables.` can be omitted.

**Limitations:**
- List-type attribute values are not supported in Evaluate
- Subsequent Data Table blocks clear previous queries from the namespace
- Query results are only available in the flow containing the block
- If no results or attribute not found, the reference is empty/null

**Use case:** Look up a customer's tier level by account number to route to the appropriate queue.

### List (Multi-Row Query)

Retrieve whole rows from a data table that match specified criteria.

**Configuration:**
1. Select **Read from data table** as the action
2. Select **List Data Table values**
3. Configure primary value groups:
   - Up to **5 primary value groups** per block
   - **Group Name** (required) -- must be unique across the entire flow
   - **Primary Attributes** -- all required; uses **exact matching**
   - Returns entire records (all attributes), not just selected ones

**Return behavior:**
- Returns complete records with all attributes
- If no primary value group is configured, the entire table is loaded (32KB limit)
- If no matching records found, the primaryKeyGroups array is empty

**Accessing retrieved data:**

- Table ID: `$.DataTableList.ResultData.dataTableId`
- Lock version: `$.DataTableList.ResultData.lockVersion.dataTable`
- Specific row by index: `$.DataTableList.ResultData.primaryKeyGroups.{{GroupName}}[{{index}}]`
- Primary key value: `$.DataTableList.ResultData.primaryKeyGroups.{{GroupName}}[{{index}}].primaryKeys[{{index}}].attributeValue`
- Attribute value: `$.DataTableList.ResultData.primaryKeyGroups.{{GroupName}}[{{index}}].attributes[{{index}}].attributeValue`
- Default group (no filter): `$.DataTableList.ResultData.primaryKeyGroups.default[index]`

Use backticks when accessing array elements in flow blocks.

**Use case:** List all active promotions for a product category to play in the IVR.

### Write (Create/Update)

Create new records or update existing records (upsert behavior).

**Configuration:**
1. Select **Write to data table** as the action
2. Configure primary value groups:
   - No fixed limit on number of primary value groups (minimum 1 required)
   - **Group Name** (required) -- must be unique across the entire flow
   - **Primary Attributes** -- all required; determines which record to create/update
   - Two input methods: **Input tab** (structured form) or **Raw JSON tab** (advanced)
3. Configure attributes to write:
   - Select attribute from dropdown
   - Choose **Set attribute value** (static text, contact attributes, system variables) or **Use default value** (from table schema)

**Write attribute limit:** Total of **25 attributes** across all primary value groups in a single block.
- If a group has no "Attributes to write" configured: count of primary attribute values counts toward the limit
- If a group has "Attributes to write" configured: only the attributes-to-write count (primary attributes excluded)

**Lock version (concurrency control):**
- **Use Latest** -- always writes to the most recent version (default, suitable for most cases)
- **Set dynamically** -- specify version number at runtime via Lambda or module (for optimistic locking)

**Use case:** Record a customer's language preference during an IVR interaction for future calls.

### Error Handling

All operations have **Success** and **Error** branches. Common error cases:
- Key not found (Evaluate)
- Table does not exist
- Insufficient permissions
- Throttling (rate limit exceeded)
- Validation failure (Write)

---

## Query Patterns

| Pattern | Operation | Description |
|---|---|---|
| **Exact match** | Evaluate, List, Write | All primary attributes must match exactly |
| **Composite key** | All | Multiple primary attributes combine for row identification |
| **Full table scan** | List (no filter) | When no primary value group is configured, returns entire table (32KB limit) |

---

## Concurrency Handling

### Optimistic Locking

The system supports optimistic locking to prevent concurrent update conflicts:

- **Lock level** is configured at table creation (data table, record, attribute, or cell level)
- The Write block supports a **Lock Version** setting:
  - **Use Latest** -- always writes to the most recent version (last-write-wins)
  - **Set dynamically** -- specify a version number; the write fails if the record has been modified since that version was read
- The system automatically alerts users when changes occur outside their current session, prompting a refresh

### Propagation

- Changes take effect **almost immediately** in subsequent flow executions and API calls
- Data is **not cached in flows** -- no lag required for refresh after a change
- In rare cases, a brief delay (typically milliseconds) may occur before all system components reflect the change
- Best practice: plan updates during operational windows to minimize impact

---

## Access Control

### Security Profile Permissions

Data table access is managed through Connect security profiles under the Routing section:

| Permission | Allows |
|---|---|
| **View** | Read data tables and their records |
| **Edit** | Modify existing records |
| **Create** | Create new data tables and add records |
| **Delete** | Delete data tables and records |

### Tag-Based Access Control (TBAC)

- Provides record-level restrictions using primary key values
- Use when multiple teams need to access different subsets of data within large, multi-purpose tables
- Controls which primary values a business user can view or modify based on their responsibilities

---

## Custom User Interfaces with Views

Data tables can power custom UIs built with the Views no-code UI builder:

- Create purpose-built interfaces assigned to agent workspaces
- Allow business users to make operational adjustments without IT intervention
- Combine multiple resources so users don't need permission to each underlying resource (flows, prompts, queues)

Example use cases:
- Managing queue assignments, operating hours, skill mappings, and escalation rules
- Modifying routing by language, location, or VIP status
- Activating emergency protocols

---

## Audit History

- On-screen audit history shows recent changes with before/after values
- Covers table structure changes (attributes, primary keys, default values) and record changes
- AWS CloudTrail tracks the complete history of all resource changes

---

## Service Quotas

| Resource | Default Limit |
|---|---|
| Tables per instance | 100 |
| Attributes (columns) per table | 100 |
| Values (rows/records) per table | 1,000 |
| List items per text/number list attribute | 100 |
| Characters for non-primary text values | 5,000 |
| Characters for TEXT_LIST items | 1,000 |
| Characters for primary text values | 1,000 |
| Queries per Evaluate block | 5 |
| Primary value groups per List block | 5 |
| Total write attributes per Write block | 25 |
| List result size (no filter) | 32 KB |

---

## Management APIs

### Table Operations

| API | Purpose |
|---|---|
| `CreateDataTable` | Create a new data table with its schema |
| `DescribeDataTable` | Get table metadata and schema |
| `ListDataTables` | List all tables in the instance |
| `UpdateDataTable` | Modify table metadata |
| `DeleteDataTable` | Delete a table and all its data |

### Attribute Operations

| API | Purpose |
|---|---|
| `CreateDataTableAttribute` | Add a new attribute (column) to a table |
| `UpdateDataTableAttribute` | Modify an attribute definition |

### Data Operations

| API | Purpose |
|---|---|
| `EvaluateDataTableValues` | Look up a row by key (same as flow block Evaluate) |
| `BatchCreateDataTableValue` | Insert multiple rows in a single call |
| `BatchUpdateDataTableValue` | Update multiple rows in a single call |
| `BatchDeleteDataTableValue` | Delete multiple rows in a single call |

### Example -- Create and Populate a Table

```javascript
import {
  ConnectClient,
  CreateDataTableCommand,
  BatchCreateDataTableValueCommand,
  EvaluateDataTableValuesCommand,
} from "@aws-sdk/client-connect";

const client = new ConnectClient({ region: "us-east-1" });

// Create table
await client.send(new CreateDataTableCommand({
  InstanceId: instanceId,
  DataTableName: "CustomerTiers",
  PrimaryKeyAttribute: {
    Name: "accountNumber",
    Type: "String",
  },
  Attributes: [
    { Name: "tierLevel", Type: "String" },
    { Name: "discountPercent", Type: "Number" },
    { Name: "priorityRouting", Type: "Boolean" },
  ],
}));

// Populate with data
await client.send(new BatchCreateDataTableValueCommand({
  InstanceId: instanceId,
  DataTableName: "CustomerTiers",
  Values: [
    {
      PrimaryKeyValue: "ACC-001",
      Attributes: {
        tierLevel: "Gold",
        discountPercent: "15",
        priorityRouting: "true",
      },
    },
    {
      PrimaryKeyValue: "ACC-002",
      Attributes: {
        tierLevel: "Silver",
        discountPercent: "10",
        priorityRouting: "false",
      },
    },
  ],
}));

// Look up a customer's tier
const result = await client.send(new EvaluateDataTableValuesCommand({
  InstanceId: instanceId,
  DataTableName: "CustomerTiers",
  PrimaryKeyValue: "ACC-001",
}));
// result.Attributes = { tierLevel: "Gold", discountPercent: "15", priorityRouting: "true" }
```

---

## Latency Characteristics

- Lookups are low-latency (single-digit milliseconds) since data is stored within the Connect infrastructure
- Data is not cached in flows -- every execution reads the latest value
- Changes propagate in milliseconds (rare brief delays possible)
- No external compute overhead (unlike Lambda invocations)

---

## Schema Changes and Migrations

- New non-primary attributes can be added at any time, even after the table is populated
- Existing rows will have null for new attributes until explicitly updated
- Primary attributes **cannot be added or removed** if the table contains data -- all rows must be deleted first
- Values within primary attributes can be edited
- Attribute type and validation rules can be modified via `UpdateDataTableAttribute`

---

## Key Considerations

- **No joins** -- tables are independent; use multiple Data Table blocks or Lambda for cross-table logic
- **Regional** -- data tables are regional resources tied to the Connect instance
- **Not for large datasets** -- 1,000 row limit per table; use DynamoDB or RDS for high-volume data
- **Batch operations** -- atomic per row but not across rows; for multi-row consistency, use Lambda
- **Flow namespace scoping** -- query results are only available in the flow containing the Data Table block; subsequent Data Table blocks clear previous query results
