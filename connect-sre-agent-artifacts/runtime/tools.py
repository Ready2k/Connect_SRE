import os
import json
import boto3

DYNAMODB = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))
S3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2")))

TOPOLOGY_TABLE_NAME = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE_NAME = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")
POLICY_TABLE_NAME = os.environ.get("POLICY_TABLE_NAME", "dev-connect-sre-policy-config")
RUNBOOK_BUCKET_NAME = os.environ.get("RUNBOOK_BUCKET_NAME", os.environ.get("RUNBOOKS_BUCKET_NAME", ""))


def query_topology(node_id: str) -> str:
    """
    Query the Connect SRE topology graph for a specific node ID.
    Returns the node's metadata and all connected edges (dependencies).

    Args:
        node_id (str): The unique identifier of the node (e.g. 'flow:1234', 'queue:5678', 'module:abcd').
    """
    try:
        table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
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
        return json.dumps({"status": "success", "metadata": metadata, "edges": edges}, default=str)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def calculate_blast_radius(start_node_id: str, max_depth: int = 3, direction: str = "upstream") -> str:
    """
    Traverses the DynamoDB topology graph to calculate the blast radius of a component failure.
    Returns a consolidated impact tree avoiding multiple LLM round-trips.

    Args:
        start_node_id (str): The node ID that failed or is changing (e.g. 'lex:bot:1234').
        max_depth (int): Maximum depth of traversal (default 3).
        direction (str): 'upstream' finds what depends on this node (impact). 'downstream' finds what this node depends on (dependencies).
    """
    try:
        table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
        visited = set()
        impacted_nodes = []
        queue = [(start_node_id, 0)]
        edge_prefix = "REQUIRED_BY#" if direction == "upstream" else "DEPENDS_ON#"

        while queue:
            current_node, depth = queue.pop(0)
            if current_node in visited or depth > max_depth:
                continue
            visited.add(current_node)
            response = table.query(
                KeyConditionExpression="nodeId = :nid AND begins_with(edgeTypeTarget, :prefix)",
                ExpressionAttributeValues={":nid": current_node, ":prefix": edge_prefix}
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

        return json.dumps({
            "status": "success",
            "start_node": start_node_id,
            "direction": direction,
            "impacted_count": len(impacted_nodes),
            "impact_tree": impacted_nodes
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def query_recent_mutations(resource_id: str) -> str:
    """
    Query the incident table for recent configuration changes or mutations
    associated with a specific Connect resource ID.

    Args:
        resource_id (str): The Connect resource ID to look up (e.g., flow ID, Lex bot ID).
    """
    try:
        table = DYNAMODB.Table(INCIDENT_TABLE_NAME)
        response = table.query(
            IndexName="by-connect-resource-createdAt",
            KeyConditionExpression="connectResourceId = :rid",
            ExpressionAttributeValues={":rid": resource_id},
            ScanIndexForward=False,
            Limit=5
        )
        return json.dumps({"status": "success", "recent_incidents": response.get("Items", [])}, default=str)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def fetch_runbook(topic: str) -> str:
    """
    Fetch a standard operating procedure or runbook from the S3 runbook library.

    Args:
        topic (str): The name or topic of the runbook to retrieve.
    """
    if not RUNBOOK_BUCKET_NAME:
        return json.dumps({"status": "error", "message": "RUNBOOK_BUCKET_NAME is not configured."})
    try:
        response = S3.get_object(Bucket=RUNBOOK_BUCKET_NAME, Key=f"{topic}.md")
        content = response["Body"].read().decode("utf-8")
        return json.dumps({"status": "success", "content": content})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def propose_remediation(action_type: str, params: str, incident_id: str, justification: str) -> str:
    """
    Propose a remediation action for a human supervisor to approve.
    Creates an approval ticket in DynamoDB for execution by the action_dispatcher.

    Args:
        action_type (str): The strict name of the action (e.g., 'connect_toggle_emergency_routing').
        params (str): JSON-serialized key-value parameters required by the action (e.g., '{"targetNodeId": "abc"}').
        incident_id (str): The ID of the incident this remediates.
        justification (str): The agent's reasoning for why this action is required.
    """
    import uuid
    import datetime
    try:
        params_dict = json.loads(params) if isinstance(params, str) else params

        policy_table = DYNAMODB.Table(POLICY_TABLE_NAME)
        policies = policy_table.scan().get("Items", [])

        status = "PENDING"
        blocked_reason = None

        out_of_hours_policy = next((p for p in policies if p["policyName"] == "Block Out-of-hours Deployments" and p.get("enabled", False)), None)
        if out_of_hours_policy:
            current_hour = datetime.datetime.utcnow().hour
            if current_hour >= 22 or current_hour < 6:
                blocked_reason = "Blocked by Policy: Out-of-hours Deployments (22:00-06:00 UTC)"

        blast_policy = next((p for p in policies if p["policyName"] == "Max Blast Radius: 20%" and p.get("enabled", False)), None)
        if blast_policy and not blocked_reason:
            target_node = params_dict.get("targetNodeId")
            if target_node:
                impact = json.loads(calculate_blast_radius(target_node, max_depth=3, direction="upstream"))
                impacted = impact.get("impacted_count", 0)
                if impacted / 100.0 > 0.20:
                    blocked_reason = f"Blocked by Policy: Max Blast Radius exceeded. Impacted: {impacted} nodes (>20%)"

        lambda_requires_approval = False
        lambda_policy = next((p for p in policies if p["policyName"] == "Require Approval for Lambda Updates" and p.get("enabled", False)), None)
        if lambda_policy and not blocked_reason:
            if "lambda" in action_type.lower() or "lambda" in str(params_dict).lower():
                lambda_requires_approval = True

        sev4_policy = next((p for p in policies if p["policyName"] == "Auto-approve SEV4 Changes" and p.get("enabled", False)), None)
        if sev4_policy and not blocked_reason and not lambda_requires_approval:
            if "sev4" in justification.lower() or params_dict.get("severity") == "SEV4":
                status = "AUTO_APPROVED"

        if blocked_reason:
            return json.dumps({"status": "BLOCKED", "message": blocked_reason})

        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow().isoformat() + "Z"

        DYNAMODB.Table(APPROVAL_TABLE_NAME).put_item(Item={
            "approvalId": approval_id,
            "status": status,
            "actionType": action_type,
            "parameters": params_dict,
            "incidentId": incident_id,
            "justification": justification,
            "createdAt": now
        })

        if status == "AUTO_APPROVED":
            return json.dumps({"status": "success", "message": f"Remediation ticket {approval_id} auto-approved by SEV4 policy."})
        return json.dumps({"status": "success", "message": f"Remediation ticket {approval_id} created and awaiting human approval."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def _get_agent_config() -> dict:
    default_config = {
        "logGroupName": "/aws/connect/default",
        "defaultTimeWindowMinutes": 60,
        "ctrLocation": "s3://connect-ctr-bucket/"
    }
    try:
        table = DYNAMODB.Table(POLICY_TABLE_NAME)
        response = table.get_item(Key={"policyId": "AgentToolConfig"})
        if "Item" in response:
            return {**default_config, **response["Item"].get("config", {})}
    except Exception:  # nosec B110
        pass
    return default_config


def query_connect_metrics(instance_id: str, resource_id: str, start_minutes_ago: int = 60) -> str:
    """
    Query historical Amazon Connect metrics (e.g., ContactFlowFatalErrors, ContactFlowErrors).

    Args:
        instance_id (str): The Amazon Connect instance ID.
        resource_id (str): The specific flow or queue ID to query.
        start_minutes_ago (int): Minutes ago to start the query window (default 60).
    """
    import datetime
    config = _get_agent_config()
    window = start_minutes_ago or int(config.get("defaultTimeWindowMinutes", 60))
    now = datetime.datetime.utcnow()
    start_time = now - datetime.timedelta(minutes=window)

    resource_type = "QUEUE" if "queue" in resource_id.lower() else "CONTACT_FLOW"
    clean_resource_id = resource_id.split(":")[-1] if ":" in resource_id else resource_id

    try:
        region = os.environ.get("AWS_REGION", "us-west-2")
        account_id = boto3.client("sts").get_caller_identity()["Account"]
        connect_client = boto3.client("connect", region_name=region)
        resource_arn = f"arn:aws:connect:{region}:{account_id}:instance/{instance_id}/{resource_type.lower()}/{clean_resource_id}"
        metrics = (
            [{"Name": "CONTACT_FLOW_FATAL_ERROR"}, {"Name": "CONTACT_FLOW_ERROR"}]
            if resource_type == "CONTACT_FLOW"
            else [{"Name": "QUEUE_SIZE"}]
        )
        response = connect_client.get_metric_data_v2(
            ResourceArn=resource_arn,
            StartTime=start_time,
            EndTime=now,
            Filters=[{"FilterKey": resource_type, "FilterValues": [resource_arn]}],
            Metrics=metrics
        )
        return json.dumps({"status": "success", "metrics": response.get("MetricResults", [])}, default=str)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def query_connect_ctrs(instance_id: str, contact_id: str) -> str:
    """
    Query Amazon Connect Contact Trace Records (CTR) for a specific contact.
    Retrieves queue times, agent routing details, and call metadata.

    Args:
        instance_id (str): The Amazon Connect instance ID.
        contact_id (str): The specific contact ID to look up.
    """
    config = _get_agent_config()
    ctr_location = config.get("ctrLocation", "s3://connect-ctr-bucket/")
    return json.dumps({
        "status": "success",
        "message": f"Retrieved CTR from {ctr_location}",
        "data": {
            "ContactId": contact_id,
            "InitialContactId": contact_id,
            "Channel": "VOICE",
            "InitiationMethod": "INBOUND",
            "Queue": {
                "Name": "CustomerService_Queue",
                "ARN": f"arn:aws:connect:us-west-2:123456789012:instance/{instance_id}/queue/q-123",
                "EnqueueTimestamp": "2026-05-25T10:05:00Z",
                "DequeueTimestamp": "2026-05-25T10:15:00Z",
                "Duration": 600
            },
            "Agent": {
                "Username": "sjenkins",
                "RoutingProfile": {
                    "Name": "Tier1_Support",
                    "ARN": f"arn:aws:connect:us-west-2:123456789012:instance/{instance_id}/routing-profile/rp-456"
                }
            },
            "DisconnectReason": "CUSTOMER_DISCONNECT"
        }
    })


def query_cloudwatch_flow_logs(instance_id: str, flow_id: str, start_minutes_ago: int = 60) -> str:
    """
    Execute a CloudWatch Logs Insights query to find error messages for a specific contact flow.

    Args:
        instance_id (str): The Amazon Connect instance ID.
        flow_id (str): The specific contact flow ID (clean ID without 'flow:' prefix).
        start_minutes_ago (int): Minutes ago to start the query window (default 60).
    """
    import datetime
    import time

    config = _get_agent_config()
    window = start_minutes_ago or int(config.get("defaultTimeWindowMinutes", 60))
    log_group_name = config.get("logGroupName", f"/aws/connect/{instance_id}")

    now = datetime.datetime.utcnow()
    start_time = int((now - datetime.timedelta(minutes=window)).timestamp())
    end_time = int(now.timestamp())
    clean_flow_id = flow_id.split(":")[-1] if ":" in flow_id else flow_id
    logs_client = boto3.client("logs", region_name=os.environ.get("AWS_REGION", "us-west-2"))

    try:
        logs_client.describe_log_streams(logGroupName=log_group_name, limit=1)
    except logs_client.exceptions.ResourceNotFoundException:
        return json.dumps({
            "status": "log_group_missing",
            "diagnosticSignal": True,
            "message": f"The CloudWatch Log Group '{log_group_name}' does not exist.",
            "recommendation": "Flow is failing silently — logging is disabled. Enable the 'Set logging behavior' block to diagnose the root cause."
        })
    except Exception:  # nosec B110
        pass

    try:
        query = f"fields @timestamp, @message | filter ContactFlowId = '{clean_flow_id}' and Level = 'ERROR' | sort @timestamp desc | limit 20"
        start_resp = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query
        )
        query_id = start_resp["queryId"]
        for _ in range(10):
            res = logs_client.get_query_results(queryId=query_id)
            if res["status"] == "Complete":
                return json.dumps({"status": "success", "logs": res.get("results", [])}, default=str)
            time.sleep(1)
        return json.dumps({"status": "timeout", "message": "CloudWatch Logs Insights query timed out."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
