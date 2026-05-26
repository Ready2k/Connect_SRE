import boto3

def get_dynamodb_resource(region_name="us-west-2"):
    session = boto3.Session(profile_name="connect-sre-dev")
    return session.resource("dynamodb", region_name=region_name)

def seed_policies(env="dev", region="us-west-2"):
    print(f"--- Bootstrapping Connect SRE Agent Gating Policies (Env: {env}, Region: {region}) ---")
    
    db = get_dynamodb_resource(region)
    policy_table = db.Table(f"{env}-connect-sre-policy-config")
    
    # 7 Premium Operational Policies for SRE Agent management
    policies = [
        {
            "policyId": "POL-001",
            "name": "Require Human Approval for Remediations",
            "description": "Mandates that any state-changing remediation action must be explicitly approved by a human operator in the UI before dispatch.",
            "enabled": True
        },
        {
            "policyId": "POL-002",
            "name": "Allow Connect Routing Profile Modification",
            "description": "Grants the SRE agent permission to dynamically update routing profiles during a severe queue backup or agent shortage.",
            "enabled": False
        },
        {
            "policyId": "POL-003",
            "name": "Allow Connect Prompt Creation",
            "description": "Grants the SRE agent permission to create temporary audio prompts for emergency IVR announcements.",
            "enabled": True
        },
        {
            "policyId": "POL-004",
            "name": "Allow Lex Bot Alias Rollbacks",
            "description": "Authorizes the SRE agent to propose or execute a rollback of Amazon Lex bot aliases to a previous stable version during NLU failures.",
            "enabled": True
        },
        {
            "policyId": "POL-005",
            "name": "Enforce Max Outage Blast Radius Gate",
            "description": "Blocks any automatic or proposed agent remediation action if its calculated blast radius exceeds 20% of the instance call volume.",
            "enabled": True
        },
        {
            "policyId": "POL-006",
            "name": "Allow Emergency Call Callback Activation",
            "description": "Permits the SRE agent to automatically configure priority queue callbacks when queue wait times exceed 300 seconds.",
            "enabled": False
        },
        {
            "policyId": "POL-007",
            "name": "Restrict Out-Of-Hours Automatic Mutations",
            "description": "Blocks any autonomous write action outside standard business hours (08:00 - 22:00 local time) without multi-party SRE authorization.",
            "enabled": True
        }
    ]
    
    print("Writing policies to DynamoDB dev-connect-sre-policy-config table...")
    for p in policies:
        print(f"  Saving policy: {p['name']} ({p['policyId']})")
        policy_table.put_item(Item=p)
        
    print("--- Policies Bootstrapped Successfully! ---")

if __name__ == "__main__":
    seed_policies(env="dev", region="us-west-2")
