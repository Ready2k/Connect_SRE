import datetime
import boto3
import os

def get_dynamodb_resource(region_name="us-west-2"):
    session = boto3.Session(profile_name="connect-sre-dev")
    return session.resource("dynamodb", region_name=region_name)

def seed_journeys(env="dev", region="us-west-2"):
    print(f"--- Bootstrapping Connect SRE Business Journeys Seeder (Env: {env}, Region: {region}) ---")
    
    db = get_dynamodb_resource(region)
    journey_table = db.Table(f"{env}-connect-sre-journey-map")
    
    now = datetime.datetime.utcnow().isoformat() + "Z"
    
    # 7 Rich Business Journeys covering Connect, Lex, Q in Connect, Lambda, DynamoDB, EventBridge, and CCP Streams
    journeys = [
        {
            "journeyId": "journey-authentication",
            "name": "Customer Authentication & Biometrics",
            "description": "Critical security verification journey using Amazon Lex PIN validation and voice biometrics.",
            "criticality": "TIER1",
            "status": "Healthy",
            "entryPoint": "+1-800-555-0199 (Auth Line)",
            "flows": ["Auth Inbound Flow", "Identity Verification Bot (Lex)"],
            "activeContacts": 14,
            "sla": "99.9%",
            "owner": "Security-Ops",
            "createdAt": now
        },
        {
            "journeyId": "journey-billing",
            "name": "Billing & Payments Self-Service",
            "description": "Automated customer self-service billing check, transaction dips, and balance queries.",
            "criticality": "TIER1",
            "status": "Healthy",
            "entryPoint": "+1-800-555-0122 (Billing Line)",
            "flows": ["Billing Main Flow", "CheckCustomerBalance (Lambda)"],
            "activeContacts": 28,
            "sla": "99.5%",
            "owner": "Billing-Operations",
            "createdAt": now
        },
        {
            "journeyId": "journey-agent-assist",
            "name": "Agent Copilot & Knowledge Assist (Q)",
            "description": "Amazon Q in Connect assistant providing real-time article recommendations and prompt delivery inside CCP.",
            "criticality": "TIER2",
            "status": "Healthy",
            "entryPoint": "Agent CCP Integration",
            "flows": ["Q-Assistant-Trigger-Flow", "Wisdom-Ingest-Stream"],
            "activeContacts": 57,
            "sla": "99.2%",
            "owner": "Agent-Experience",
            "createdAt": now
        },
        {
            "journeyId": "journey-telephony",
            "name": "SIP Trunk Ingestion & Core Routing",
            "description": "Underlying Amazon Connect carrier SIP ingestion, routing, and telephony capacity management.",
            "criticality": "TIER1",
            "status": "Healthy",
            "entryPoint": "Amazon Connect Direct-Dial SIP",
            "flows": ["Telephony Ingestion Router"],
            "activeContacts": 108,
            "sla": "99.99%",
            "owner": "Core-Telephony-Platform",
            "createdAt": now
        },
        {
            "journeyId": "journey-agent-sync",
            "name": "CCP Streams & State Sync (WebRTC)",
            "description": "Real-time remote agent WebRTC signaling, client state synchronization, and CCP Streams connectivity.",
            "criticality": "TIER1",
            "status": "Healthy",
            "entryPoint": "WebRTC Client Socket Pool",
            "flows": ["Agent WebRTC Signaling Flow", "Agent State Sync Event Rule"],
            "activeContacts": 42,
            "sla": "99.8%",
            "owner": "Workforce-Management",
            "createdAt": now
        },
        {
            "journeyId": "journey-outbound",
            "name": "High-Volume Fraud & Verify Alerts",
            "description": "Automated outbound campaign dials, security verification push notifications, and Lambda-driven alerts.",
            "criticality": "TIER2",
            "status": "Healthy",
            "entryPoint": "Lambda Outbound Trigger Api",
            "flows": ["Fraud Notification Outbound Flow"],
            "activeContacts": 8,
            "sla": "98.9%",
            "owner": "Risk-Management",
            "createdAt": now
        },
        {
            "journeyId": "journey-callback",
            "name": "VIP Priority Escalation & Callback",
            "description": "Priority VIP routing logic, callback registration, and seamless transfer escalation groups.",
            "criticality": "TIER1",
            "status": "Healthy",
            "entryPoint": "Queue Callback Handler",
            "flows": ["Priority Callback Trigger Flow", "Warm Transfer Flow"],
            "activeContacts": 3,
            "sla": "99.6%",
            "owner": "Contact-Center-Core",
            "createdAt": now
        }
    ]
    
    print("Writing journeys to DynamoDB dev-connect-sre-journey-map table...")
    for j in journeys:
        print(f"  Saving journey: {j['name']} ({j['journeyId']})")
        journey_table.put_item(Item=j)
        
    print("--- Journeys Bootstrapped Successfully! ---")

if __name__ == "__main__":
    seed_journeys(env="dev", region="us-west-2")
