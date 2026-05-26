import boto3

def get_dynamodb_resource(region_name="us-west-2"):
    session = boto3.Session(profile_name="connect-sre-dev")
    return session.resource("dynamodb", region_name=region_name)

def seed_tools(env="dev", region="us-west-2"):
    print(f"--- Bootstrapping Connect SRE Agent Tool Registry (Env: {env}, Region: {region}) ---")

    db = get_dynamodb_resource(region)
    tools_table = db.Table(f"{env}-connect-sre-tool-registry")

    # -----------------------------------------------------------------------
    # Runtime tools — callable functions exposed to the supervisor agent.
    # These are displayed on the Tool Registry UI page.
    # -----------------------------------------------------------------------
    runtime_tools = [
        {
            "toolId": "query_topology",
            "description": "Fetches resources and adjacency paths (Connect flows, Lambdas, Lex bots, queues) from the SRE topology graph.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "calculate_blast_radius",
            "description": "Calculates downstream blast radius and aggregate customer call-volume impact for any component degradation.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "query_recent_mutations",
            "description": "Queries CloudTrail API and event histories to identify recent infrastructure or configuration changes.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "fetch_runbook",
            "description": "Retrieves approved Standard Operating Procedures (SOPs) for the active incident category from S3.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "propose_remediation",
            "description": "Generates state-changing rollback proposals and routes them to SRE human operators for approval.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "query_connect_metrics",
            "description": "Queries live real-time queue volumes and historical telephony performance metrics from Amazon Connect API.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "query_connect_ctrs",
            "description": "Fetches raw Contact Trace Records (CTRs) from Connect to inspect call metadata, queue details, and drop codes.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "query_cloudwatch_flow_logs",
            "description": "Retrieves and parses CloudWatch Flow Logs to trace step-by-step contact flow execution and errors.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "recall_prior_incidents",
            "description": "Queries long-term agentic memory for prior incidents on the same resource so the agent can skip re-investigation of known patterns.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "record_investigation_memory",
            "description": "Persists root cause, pattern, and resolution to the agentic memory table so future investigations can learn from this one.",
            "permission": "Read-Only",
            "status": "Active",
            "enabled": True,
        },
    ]

    # -----------------------------------------------------------------------
    # Action types — validated by action_dispatcher.py before execution.
    # toolId must match the actionType string the agent passes to
    # propose_remediation(), which in turn maps to SSM document
    # SRE-Connect-{toolId}.
    # -----------------------------------------------------------------------
    action_types = [
        {
            "toolId": "connect_toggle_emergency_routing",
            "description": "Toggles emergency routing mode for Amazon Connect flows, redirecting all traffic to a fallback queue.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "connect_rollback_contact_flow",
            "description": "Rolls back a contact flow to its last known-good published version.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "connect_rollback_contact_flow_module",
            "description": "Rolls back a shared contact flow module to its last known-good published version.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "connect_rollback_lex_alias",
            "description": "Reassigns a Lex bot alias to the previous stable bot version to recover from NLU failures.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "connect_update_routing_profile",
            "description": "Updates a routing profile to redistribute agent capacity across queues during a surge or outage.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "connect_update_queue_hours",
            "description": "Updates the hours-of-operation linked to a queue to extend or reduce availability during an incident.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
        {
            "toolId": "connect_disable_lambda",
            "description": "Removes a Lambda function association from a contact flow to bypass a failing integration.",
            "permission": "Requires Approval",
            "status": "Active",
            "enabled": True,
        },
    ]

    all_entries = runtime_tools + action_types
    print(f"Writing {len(runtime_tools)} runtime tools and {len(action_types)} action types to DynamoDB...")
    for entry in all_entries:
        print(f"  Registering: {entry['toolId']}")
        tools_table.put_item(Item=entry)

    print("--- Tool Registry Bootstrapped Successfully! ---")

if __name__ == "__main__":
    seed_tools(env="dev", region="us-west-2")
