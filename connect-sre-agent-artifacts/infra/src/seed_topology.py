import sys
import datetime
import boto3


def get_dynamodb_client(region_name="eu-west-2"):
    return boto3.resource("dynamodb", region_name=region_name)


def seed_topology(env="dev", region="eu-west-2"):
    print(
        f"--- Bootstrapping Connect SRE Topology Seeder (Env: {env}, Region: {region}) ---"
    )

    db = get_dynamodb_client(region)
    topo_table = db.Table(f"{env}-connect-sre-topology")
    journey_table = db.Table(f"{env}-connect-sre-journey-map")

    now = datetime.datetime.utcnow().isoformat() + "Z"

    # 1. Seed Business Journeys
    journeys = [
        {
            "journeyId": "journey-authentication",
            "name": "Customer Authentication",
            "description": "Critical security verification journey for high-value banking calls.",
            "criticality": "TIER1",
            "owner": "SRE-Security-Team",
            "createdAt": now,
        },
        {
            "journeyId": "journey-billing",
            "name": "Billing & Payments",
            "description": "Standard business customer billing and self-service account queries.",
            "criticality": "TIER2",
            "owner": "Billing-Operations",
            "createdAt": now,
        },
    ]

    print("Seeding Business Journeys...")
    for j in journeys:
        journey_table.put_item(Item=j)

    # 2. Seed Topology Nodes and Edges
    # DynamoDB Adjacency List Pattern:
    # Partition Key (nodeId): unique identifier of the node
    # Sort Key (edgeTypeTarget): 'METADATA' for the node's properties, or '<RELATIONSHIP>#<targetNodeId>' for directed edges.

    items = []

    # Nodes (METADATA records)
    nodes = [
        # Regional Node
        {
            "nodeId": "region:us-west-2",
            "nodeType": "region",
            "label": "us-west-2 (Oregon)",
            "status": "Active",
        },
        # Connect Instances
        {
            "nodeId": "instance:connect-prod-1",
            "nodeType": "instance",
            "label": "Connect-Prod-Instance-1",
            "status": "Active",
            "arn": "arn:aws:connect:us-west-2:123456789012:instance/prod-1",
        },
        # Phone Entry Points
        {
            "nodeId": "phone:+18005550199",
            "nodeType": "phone",
            "label": "+1-800-555-0199 (Auth Line)",
            "status": "Active",
        },
        {
            "nodeId": "phone:+18005550122",
            "nodeType": "phone",
            "label": "+1-800-555-0122 (Billing Line)",
            "status": "Active",
        },
        # Contact Flows
        {
            "nodeId": "flow:auth-inbound",
            "nodeType": "flow",
            "label": "Auth Inbound Flow",
            "status": "Active",
            "arn": "arn:aws:connect:us-west-2:123456789012:instance/prod-1/contact-flow/auth",
        },
        {
            "nodeId": "flow:billing-main",
            "nodeType": "flow",
            "label": "Billing Main Flow",
            "status": "Active",
            "arn": "arn:aws:connect:us-west-2:123456789012:instance/prod-1/contact-flow/billing",
        },
        # Flow Modules
        {
            "nodeId": "module:customer-verify",
            "nodeType": "module",
            "label": "Customer Verification Module",
            "status": "Degraded",
            "version": "v4",
            "arn": "arn:aws:connect:us-west-2:123456789012:instance/prod-1/contact-flow-module/verify",
        },
        # Lex Bots
        {
            "nodeId": "lex:identity-verification-bot",
            "nodeType": "lex",
            "label": "IdentityVerificationBot",
            "status": "Active",
            "version": "v2",
        },
        # Lambdas
        {
            "nodeId": "lambda:check-balance",
            "nodeType": "lambda",
            "label": "CheckCustomerBalance",
            "status": "Active",
            "arn": "arn:aws:lambda:us-west-2:123456789012:function:CheckCustomerBalance",
        },
        # Queues
        {
            "nodeId": "queue:auth-escalations",
            "nodeType": "queue",
            "label": "Auth Escalations Queue",
            "status": "Active",
            "arn": "arn:aws:connect:us-west-2:123456789012:instance/prod-1/queue/auth-esc",
        },
        {
            "nodeId": "queue:billing-agents",
            "nodeType": "queue",
            "label": "Billing Agents Queue",
            "status": "Active",
            "arn": "arn:aws:connect:us-west-2:123456789012:instance/prod-1/queue/billing-main",
        },
        # Routing Profiles
        {
            "nodeId": "routing:tier1-support",
            "nodeType": "routing",
            "label": "Tier 1 Customer Support",
            "status": "Active",
        },
        {
            "nodeId": "routing:specialist-tier2",
            "nodeType": "routing",
            "label": "Specialist Tier 2 Support",
            "status": "Active",
        },
        # Agents (Users)
        {
            "nodeId": "user:bob-agent",
            "nodeType": "agent",
            "label": "Bob Agent (Tier 1)",
            "status": "Available",
        },
        {
            "nodeId": "user:alice-agent",
            "nodeType": "agent",
            "label": "Alice Agent (Tier 2)",
            "status": "On-Call",
        },
    ]

    # Add METADATA items
    for n in nodes:
        items.append(
            {
                "nodeId": n["nodeId"],
                "edgeTypeTarget": "METADATA",
                "nodeType": n["nodeType"],
                "label": n["label"],
                "status": n.get("status", "Active"),
                "arn": n.get("arn", "N/A"),
                "version": n.get("version", "N/A"),
                "lastSeenAt": now,
                "lastUpdated": now,
                "scanConfidence": "1.0",
            }
        )

    # Directed Edges (Adjacency relationships)
    edges = [
        # Region to Instance
        ("region:us-west-2", "REGION_HAS_INSTANCE", "instance:connect-prod-1"),
        # Journey entry points
        ("journey:journey-authentication", "JOURNEY_ENTERS_VIA", "phone:+18005550199"),
        ("journey:journey-billing", "JOURNEY_ENTERS_VIA", "phone:+18005550122"),
        # Phone lines trigger Flows
        ("phone:+18005550199", "PHONE_STARTS_FLOW", "flow:auth-inbound"),
        ("phone:+18005550122", "PHONE_STARTS_FLOW", "flow:billing-main"),
        # Inbound flows use common Verification Module
        ("flow:auth-inbound", "FLOW_USES_MODULE", "module:customer-verify"),
        ("flow:billing-main", "FLOW_USES_MODULE", "module:customer-verify"),
        # Verification module calls Lex bot and Lambda database checks
        ("module:customer-verify", "MODULE_USES_LEX", "lex:identity-verification-bot"),
        ("module:customer-verify", "MODULE_CALLS_LAMBDA", "lambda:check-balance"),
        # Flows route to corresponding agent queues
        ("flow:auth-inbound", "FLOW_ROUTES_TO_QUEUE", "queue:auth-escalations"),
        ("flow:billing-main", "FLOW_ROUTES_TO_QUEUE", "queue:billing-agents"),
        # Queues are linked to routing profiles
        ("queue:auth-escalations", "QUEUE_USES_ROUTING", "routing:specialist-tier2"),
        ("queue:billing-agents", "QUEUE_USES_ROUTING", "routing:tier1-support"),
        # Routing profiles contain agent users
        ("routing:tier1-support", "ROUTING_HAS_AGENT", "user:bob-agent"),
        ("routing:specialist-tier2", "ROUTING_HAS_AGENT", "user:alice-agent"),
    ]

    for src, edge_type, tgt in edges:
        items.append(
            {
                "nodeId": src,
                "edgeTypeTarget": f"{edge_type}#{tgt}",
                "targetNodeId": tgt,
                "relationshipType": edge_type,
                "lastSeenAt": now,
                "lastUpdated": now,
                "scanConfidence": "1.0",
            }
        )

    print(f"Seeding {len(items)} Adjacency Records to {env}-connect-sre-topology...")

    with topo_table.batch_writer() as batch:
        for idx, item in enumerate(items):
            batch.put_item(Item=item)
            if (idx + 1) % 5 == 0 or (idx + 1) == len(items):
                print(f"  Inserted {idx + 1}/{len(items)} records...")

    print("--- Seeding Completed Successfully! ---")


if __name__ == "__main__":
    env_name = "dev"
    if len(sys.argv) > 1:
        env_name = sys.argv[1]

    # Run seeder
    seed_topology(env=env_name)
