import os
import boto3
import json

DYNAMODB = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
S3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))

TOPOLOGY_TABLE_NAME = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE_NAME = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")
RUNBOOK_BUCKET_NAME = os.environ.get("RUNBOOK_BUCKET_NAME", "")

def query_topology(node_id: str) -> dict:
    """
    Query the Connect SRE topology graph for a specific node ID.
    Returns the node's metadata and all connected edges (dependencies).
    
    Args:
        node_id (str): The unique identifier of the node (e.g. 'flow:1234', 'queue:5678', 'module:abcd').
    """
    try:
        table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
        # Query all edges for this node (where nodeId is the partition key)
        response = table.query(
            KeyConditionExpression="nodeId = :nid",
            ExpressionAttributeValues={":nid": node_id}
        )
        
        metadata = None
        edges = []
        for item in response.get("Items", []):
            if item.get("edgeTypeTarget") == "METADATA":
                metadata = item
            else:
                edges.append(item)
                
        return {
            "status": "success",
            "metadata": metadata,
            "edges": edges
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_recent_mutations(resource_id: str) -> dict:
    """
    Query the incident table for recent configuration changes or mutations 
    associated with a specific Connect resource ID.
    
    Args:
        resource_id (str): The Connect resource ID to look up (e.g., flow ID, Lex bot ID).
    """
    try:
        table = DYNAMODB.Table(INCIDENT_TABLE_NAME)
        # We query the GSI to find incidents by resource ID
        response = table.query(
            IndexName="by-connect-resource-createdAt",
            KeyConditionExpression="connectResourceId = :rid",
            ExpressionAttributeValues={":rid": resource_id},
            ScanIndexForward=False, # Newest first
            Limit=5
        )
        return {
            "status": "success",
            "recent_incidents": response.get("Items", [])
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def fetch_runbook(topic: str) -> dict:
    """
    Fetch a standard operating procedure or runbook from the S3 runbook library.
    
    Args:
        topic (str): The name or topic of the runbook to retrieve.
    """
    if not RUNBOOK_BUCKET_NAME:
        return {"status": "error", "message": "RUNBOOK_BUCKET_NAME is not configured."}
        
    try:
        response = S3.get_object(Bucket=RUNBOOK_BUCKET_NAME, Key=f"{topic}.md")
        content = response["Body"].read().decode("utf-8")
        return {
            "status": "success",
            "content": content
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def propose_remediation(action_type: str, params: dict, incident_id: str, justification: str) -> dict:
    """
    Propose a remediation action for a human supervisor to approve. 
    This creates an approval ticket in DynamoDB which will later be executed by the action_dispatcher.
    
    Args:
        action_type (str): The strict name of the action (e.g., 'connect_toggle_emergency_routing').
        params (dict): Key-value parameters required by the action.
        incident_id (str): The ID of the incident this remediates.
        justification (str): The agent's reasoning for why this action is required.
    """
    try:
        import uuid
        import datetime
        
        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        table = DYNAMODB.Table(APPROVAL_TABLE_NAME)
        table.put_item(Item={
            "approvalId": approval_id,
            "status": "PENDING",
            "actionType": action_type,
            "parameters": params,
            "incidentId": incident_id,
            "justification": justification,
            "createdAt": now
        })
        
        return {
            "status": "success", 
            "message": f"Remediation ticket {approval_id} created successfully and is awaiting human approval."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
