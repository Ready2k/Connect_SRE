import boto3

def get_dynamodb_resource(region_name="us-west-2"):
    session = boto3.Session(profile_name="connect-sre-dev")
    return session.resource("dynamodb", region_name=region_name)

def seed_policies(env="dev", region="us-west-2"):
    print(f"--- Bootstrapping Connect SRE Agent Gating Policies (Env: {env}, Region: {region}) ---")

    db = get_dynamodb_resource(region)
    policy_table = db.Table(f"{env}-connect-sre-policy-config")

    # Field name is "policyName" — must match what tools.py checks with p.get("policyName", "").
    # POL-005, POL-007, POL-008, POL-009 are the four policies that tools.py evaluates at
    # remediation time; their policyName values must match exactly.
    policies = [
        {
            "policyId": "POL-001",
            "policyName": "Require Human Approval for Remediations",
            "description": "Mandates that any state-changing remediation action must be explicitly approved by a human operator in the UI before dispatch.",
            "enabled": True,
        },
        {
            "policyId": "POL-002",
            "policyName": "Allow Connect Routing Profile Modification",
            "description": "Grants the SRE agent permission to dynamically update routing profiles during a severe queue backup or agent shortage.",
            "enabled": False,
        },
        {
            "policyId": "POL-003",
            "policyName": "Allow Connect Prompt Creation",
            "description": "Grants the SRE agent permission to create temporary audio prompts for emergency IVR announcements.",
            "enabled": True,
        },
        {
            "policyId": "POL-004",
            "policyName": "Allow Lex Bot Alias Rollbacks",
            "description": "Authorizes the SRE agent to propose or execute a rollback of Amazon Lex bot aliases to a previous stable version during NLU failures.",
            "enabled": True,
        },
        {
            "policyId": "POL-005",
            # Name must match tools.py propose_remediation blast_policy check exactly.
            "policyName": "Max Blast Radius: 20%",
            "description": "Blocks any automatic or proposed agent remediation action if its calculated blast radius exceeds 20% of the instance call volume.",
            "enabled": True,
        },
        {
            "policyId": "POL-006",
            "policyName": "Allow Emergency Call Callback Activation",
            "description": "Permits the SRE agent to automatically configure priority queue callbacks when queue wait times exceed 300 seconds.",
            "enabled": False,
        },
        {
            "policyId": "POL-007",
            # Name must match tools.py propose_remediation out_of_hours_policy check exactly.
            "policyName": "Block Out-of-hours Deployments",
            "description": "Blocks any autonomous write action outside standard business hours (22:00-06:00 UTC).",
            "enabled": True,
        },
        {
            "policyId": "POL-008",
            # Name must match tools.py propose_remediation lambda_policy check exactly.
            "policyName": "Require Approval for Lambda Updates",
            "description": "Forces human approval for any remediation that targets a Lambda function, even when other gates would auto-approve.",
            "enabled": True,
        },
        {
            "policyId": "POL-009",
            # Name must match tools.py propose_remediation sev4_policy check exactly.
            "policyName": "Auto-approve SEV4 Changes",
            "description": "Allows the agent to auto-approve low-impact SEV4 remediations without waiting for human review. Disabled by default.",
            "enabled": False,
        },
    ]

    print("Writing policies to DynamoDB...")
    for p in policies:
        print(f"  Saving policy: {p['policyName']} ({p['policyId']})")
        policy_table.put_item(Item=p)

    print("--- Policies Bootstrapped Successfully! ---")

if __name__ == "__main__":
    seed_policies(env="dev", region="us-west-2")
