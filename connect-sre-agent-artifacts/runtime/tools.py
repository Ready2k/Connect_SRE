import os
import boto3
import json

DYNAMODB = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))
S3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))

TOPOLOGY_TABLE_NAME = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE_NAME = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")
POLICY_TABLE_NAME = os.environ.get("POLICY_TABLE_NAME", "dev-connect-sre-policy-config")
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

def calculate_blast_radius(start_node_id: str, max_depth: int = 3, direction: str = 'upstream') -> dict:
    """
    Traverses the DynamoDB topology graph to calculate the blast radius of a component failure.
    Returns a consolidated impact tree avoiding multiple LLM round-trips.
    
    Args:
        start_node_id (str): The node ID that failed or is changing (e.g. 'lex:bot:1234')
        max_depth (int): Maximum depth of traversal (default 3)
        direction (str): 'upstream' finds what depends on this node (impact). 'downstream' finds what this node depends on (dependencies).
    """
    try:
        table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
        visited = set()
        impacted_nodes = []
        
        # We will do a Breadth-First Search
        queue = [(start_node_id, 0)]
        edge_prefix = "REQUIRED_BY#" if direction == "upstream" else "DEPENDS_ON#"
        
        while queue:
            current_node, depth = queue.pop(0)
            if current_node in visited or depth > max_depth:
                continue
                
            visited.add(current_node)
            
            # Query edges
            # For upstream, we look for REQUIRED_BY# edges. For downstream, DEPENDS_ON#.
            response = table.query(
                KeyConditionExpression="nodeId = :nid AND begins_with(edgeTypeTarget, :prefix)",
                ExpressionAttributeValues={
                    ":nid": current_node,
                    ":prefix": edge_prefix
                }
            )
            
            for item in response.get("Items", []):
                edge_target = item.get("edgeTypeTarget").split("#", 1)[1]
                impacted_nodes.append({
                    "source": current_node,
                    "target": edge_target,
                    "depth": depth + 1,
                    "relation": direction
                })
                
                if edge_target not in visited:
                    queue.append((edge_target, depth + 1))
                    
        return {
            "status": "success",
            "start_node": start_node_id,
            "direction": direction,
            "impacted_count": len(impacted_nodes),
            "impact_tree": impacted_nodes
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
        
        # 1. Fetch policies
        policy_table = DYNAMODB.Table(POLICY_TABLE_NAME)
        policies = policy_table.scan().get("Items", [])
        
        status = "PENDING"
        blocked_reason = None
        
        # 2. Evaluate Block Out-of-hours Deployments
        out_of_hours_policy = next((p for p in policies if p["policyName"] == "Block Out-of-hours Deployments" and p.get("enabled", False)), None)
        if out_of_hours_policy:
            current_hour = datetime.datetime.utcnow().hour
            if current_hour >= 22 or current_hour < 6:
                blocked_reason = "Blocked by Policy: Out-of-hours Deployments (22:00-06:00 UTC)"

        # 3. Evaluate Max Blast Radius: 20%
        blast_policy = next((p for p in policies if p["policyName"] == "Max Blast Radius: 20%" and p.get("enabled", False)), None)
        if blast_policy and not blocked_reason:
            target_node = params.get("targetNodeId")
            if target_node:
                impact = calculate_blast_radius(target_node, max_depth=3, direction='upstream')
                impacted = impact.get("impacted_count", 0)
                # Using 100 as the mock denominator for MVP total nodes
                if impacted / 100.0 > 0.20:
                    blocked_reason = f"Blocked by Policy: Max Blast Radius exceeded. Impacted: {impacted} nodes (>20%)"

        # 4. Evaluate Require Approval for Lambda Updates
        lambda_policy = next((p for p in policies if p["policyName"] == "Require Approval for Lambda Updates" and p.get("enabled", False)), None)
        lambda_requires_approval = False
        if lambda_policy and not blocked_reason:
            if "lambda" in action_type.lower() or "lambda" in str(params).lower():
                lambda_requires_approval = True
                status = "PENDING"

        # 5. Evaluate Auto-approve SEV4 Changes
        sev4_policy = next((p for p in policies if p["policyName"] == "Auto-approve SEV4 Changes" and p.get("enabled", False)), None)
        if sev4_policy and not blocked_reason and not lambda_requires_approval:
            # If incident is SEV4 (heuristically checking justification or params)
            if "sev4" in justification.lower() or params.get("severity") == "SEV4":
                status = "AUTO_APPROVED"
                
        # If blocked, return immediately so the agent knows it failed
        if blocked_reason:
            return {
                "status": "BLOCKED",
                "message": blocked_reason
            }
        
        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        table = DYNAMODB.Table(APPROVAL_TABLE_NAME)
        table.put_item(Item={
            "approvalId": approval_id,
            "status": status,
            "actionType": action_type,
            "parameters": params,
            "incidentId": incident_id,
            "justification": justification,
            "createdAt": now
        })
        
        if status == "AUTO_APPROVED":
            return {
                "status": "success", 
                "message": f"Remediation ticket {approval_id} was automatically approved by SEV4 policy and dispatched."
            }
        else:
            return {
                "status": "success", 
                "message": f"Remediation ticket {approval_id} created successfully and is awaiting human approval."
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
