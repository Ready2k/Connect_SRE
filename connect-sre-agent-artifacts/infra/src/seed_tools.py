import boto3

def get_dynamodb_resource(region_name="us-west-2"):
    session = boto3.Session(profile_name="connect-sre-dev")
    return session.resource("dynamodb", region_name=region_name)

def seed_tools(env="dev", region="us-west-2"):
    print(f"--- Bootstrapping Connect SRE Agent Tool Registry (Env: {env}, Region: {region}) ---")
    
    db = get_dynamodb_resource(region)
    tools_table = db.Table(f"{env}-connect-sre-tool-registry")
    
    # The 8 real agent tools from runtime/tools.py
    tools = [
        {
            "toolId": "query_topology",
            "description": "Fetches resources and adjacency paths (Connect flows, Lambdas, Lex bots, queues) from the SRE topology graph.",
            "permission": "Read-Only",
            "status": "Active"
        },
        {
            "toolId": "calculate_blast_radius",
            "description": "Calculates downstream blast radius and aggregate customer call-volume impact for any component degradation.",
            "permission": "Read-Only",
            "status": "Active"
        },
        {
            "toolId": "query_recent_mutations",
            "description": "Queries CloudTrail API and event histories to identify recent infrastructure or configuration changes.",
            "permission": "Read-Only",
            "status": "Active"
        },
        {
            "toolId": "fetch_runbook",
            "description": "Retrieves approved Standard Operating Procedures (SOPs) for the active incident category from S3.",
            "permission": "Read-Only",
            "status": "Active"
        },
        {
            "toolId": "propose_remediation",
            "description": "Generates state-changing rollback proposals and routes them to SRE human operators for approval.",
            "permission": "Requires Approval",
            "status": "Active"
        },
        {
            "toolId": "query_connect_metrics",
            "description": "Queries live real-time queue volumes and historical telephony performance metrics from Amazon Connect API.",
            "permission": "Read-Only",
            "status": "Active"
        },
        {
            "toolId": "query_connect_ctrs",
            "description": "Fetches raw Contact Trace Records (CTRs) from Connect to inspect call metadata, queue details, and drop codes.",
            "permission": "Read-Only",
            "status": "Active"
        },
        {
            "toolId": "query_cloudwatch_flow_logs",
            "description": "Retrieves and parses CloudWatch Flow Logs to trace step-by-step contact flow execution and errors.",
            "permission": "Read-Only",
            "status": "Active"
        }
    ]
    
    print("Writing tools to DynamoDB dev-connect-sre-tool-registry table...")
    for t in tools:
        print(f"  Registering tool: {t['toolId']}")
        tools_table.put_item(Item=t)
        
    print("--- Tool Registry Bootstrapped Successfully! ---")

if __name__ == "__main__":
    seed_tools(env="dev", region="us-west-2")
