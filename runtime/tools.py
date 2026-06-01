import os
import json
import logging
import time
import uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))


def _compress_tool_output(payload: str) -> str:
    """Compress a tool output string before handing it to the agent.

    Falls back to the original payload on any error so a headroom issue never
    breaks a tool call.  Logs the compression ratio when compression fires.
    """
    try:
        from headroom import compress as _hr_compress
        model_id = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        compressed = _hr_compress(payload, model=model_id)
        if len(compressed) >= len(payload):
            return payload
        try:
            json.loads(payload)
            try:
                json.loads(compressed)
            except Exception:
                return payload
        except Exception:
            pass
        ratio = 1.0 - len(compressed) / max(len(payload), 1)
        logger.info("[headroom] compressed %d → %d chars (%.0f%% reduction)", len(payload), len(compressed), ratio * 100)
        return compressed
    except Exception as exc:
        logger.debug("[headroom] compression skipped: %s", exc)
        return payload
DYNAMODB = boto3.resource("dynamodb", region_name=_REGION)
S3 = boto3.client("s3", region_name=_REGION)

TOPOLOGY_TABLE_NAME = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE_NAME = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")
POLICY_TABLE_NAME = os.environ.get("POLICY_TABLE_NAME", "dev-connect-sre-policy-config")
MEMORY_TABLE_NAME = os.environ.get("MEMORY_TABLE_NAME", "dev-connect-sre-memory")
RUNBOOK_BUCKET_NAME = os.environ.get("RUNBOOK_BUCKET_NAME", os.environ.get("RUNBOOKS_BUCKET_NAME", ""))

_MEMORY_TTL_DAYS = 180


def query_topology(node_id: str) -> str:
    """
    Query the Connect SRE topology graph for a specific node ID.
    Returns the node's metadata and all connected edges (dependencies).

    Args:
        node_id (str): The unique identifier of the node (e.g. 'flow:1234', 'queue:5678', 'module:abcd').
    """
    t0 = time.time()
    logger.info("[TOOL] query_topology node_id=%s", node_id)
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
        logger.info("[TOOL] query_topology node_id=%s latency_ms=%d edges=%d", node_id, int((time.time()-t0)*1000), len(edges))
        return json.dumps({"status": "success", "metadata": metadata, "edges": edges}, default=str)
    except Exception as e:
        logger.error("[TOOL] query_topology node_id=%s error=%s", node_id, e)
        return json.dumps({"status": "error", "message": str(e)})


def _blast_radius_raw(start_node_id: str, max_depth: int = 3, direction: str = "upstream") -> str:
    """Run the BFS traversal and return the raw JSON string (no compression).

    Used internally by propose_remediation so it can json.loads() the result
    without needing to undo compression.
    """
    t0 = time.time()
    logger.info("[TOOL] calculate_blast_radius node=%s depth=%d dir=%s", start_node_id, max_depth, direction)
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

        count_resp = table.scan(Select="COUNT")
        total_count = count_resp.get("Count", 0)

        result = json.dumps({
            "status": "success",
            "start_node": start_node_id,
            "direction": direction,
            "impacted_count": len(impacted_nodes),
            "total_node_count": total_count,
            "impact_tree": impacted_nodes
        })
        logger.info("[TOOL] calculate_blast_radius node=%s impacted=%d latency_ms=%d", start_node_id, len(impacted_nodes), int((time.time()-t0)*1000))
        return result
    except Exception as e:
        logger.error("[TOOL] calculate_blast_radius node=%s error=%s", start_node_id, e)
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
    return _compress_tool_output(_blast_radius_raw(start_node_id, max_depth, direction))


def query_recent_mutations(resource_id: str) -> str:
    """
    Query the incident table for recent configuration changes or mutations
    associated with a specific Connect resource ID.

    Args:
        resource_id (str): The Connect resource ID to look up (e.g., flow ID, Lex bot ID).
    """
    t0 = time.time()
    logger.info("[TOOL] query_recent_mutations resource_id=%s", resource_id)
    try:
        table = DYNAMODB.Table(INCIDENT_TABLE_NAME)
        response = table.query(
            IndexName="by-connect-resource-createdAt",
            KeyConditionExpression="connectResourceId = :rid",
            ExpressionAttributeValues={":rid": resource_id},
            ScanIndexForward=False,
            Limit=5
        )
        items = response.get("Items", [])
        logger.info("[TOOL] query_recent_mutations resource_id=%s found=%d latency_ms=%d", resource_id, len(items), int((time.time()-t0)*1000))
        return json.dumps({"status": "success", "recent_incidents": items}, default=str)
    except Exception as e:
        logger.error("[TOOL] query_recent_mutations resource_id=%s error=%s", resource_id, e)
        return json.dumps({"status": "error", "message": str(e)})


def fetch_runbook(topic: str) -> str:
    """
    Fetch a standard operating procedure or runbook from the S3 runbook library.

    Args:
        topic (str): The name or topic of the runbook to retrieve.
    """
    logger.info("[TOOL] fetch_runbook topic=%s", topic)
    if not RUNBOOK_BUCKET_NAME:
        return json.dumps({"status": "error", "message": "RUNBOOK_BUCKET_NAME is not configured."})
    try:
        response = S3.get_object(Bucket=RUNBOOK_BUCKET_NAME, Key=f"{topic}.md")
        content = response["Body"].read().decode("utf-8")
        logger.info("[TOOL] fetch_runbook topic=%s bytes=%d", topic, len(content))
        return json.dumps({"status": "success", "content": content})
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("NoSuchKey", "404"):
            logger.error("[TOOL] fetch_runbook topic=%s error=%s", topic, e)
            return json.dumps({"status": "error", "message": str(e)})
        # Key not found — fall back to word-overlap search across all runbooks in the bucket
        try:
            listing = S3.list_objects_v2(Bucket=RUNBOOK_BUCKET_NAME)
            keys = [obj["Key"] for obj in listing.get("Contents", []) if obj["Key"].endswith(".md")]
            topic_words = set(topic.lower().replace("-", "_").replace(" ", "_").split("_"))
            best_key, best_score = None, 0
            for key in keys:
                key_words = set(key.lower().replace("-", "_").replace(".md", "").split("_"))
                score = len(topic_words & key_words)
                if score > best_score:
                    best_key, best_score = key, score
            if best_key and best_score > 0:
                response = S3.get_object(Bucket=RUNBOOK_BUCKET_NAME, Key=best_key)
                content = response["Body"].read().decode("utf-8")
                logger.info("[TOOL] fetch_runbook topic=%s fallback_key=%s score=%d bytes=%d", topic, best_key, best_score, len(content))
                return json.dumps({"status": "success", "content": content, "matched_key": best_key})
            logger.warning("[TOOL] fetch_runbook topic=%s no_match available_keys=%s", topic, keys[:10])
            return json.dumps({"status": "not_found", "message": f"No runbook found for '{topic}'.", "available": keys[:20]})
        except Exception as list_err:
            logger.error("[TOOL] fetch_runbook topic=%s list_error=%s", topic, list_err)
            return json.dumps({"status": "error", "message": str(list_err)})
    except Exception as e:
        logger.error("[TOOL] fetch_runbook topic=%s error=%s", topic, e)
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

        out_of_hours_policy = next((p for p in policies if p.get("policyName", "") == "Block Out-of-hours Deployments" and p.get("enabled", False)), None)
        if out_of_hours_policy:
            current_hour = datetime.datetime.utcnow().hour
            if current_hour >= 22 or current_hour < 6:
                blocked_reason = "Blocked by Policy: Out-of-hours Deployments (22:00-06:00 UTC)"

        # Always compute blast radius when a target node is named so the data
        # is available for the approval record regardless of policy state.
        blast_radius_data = None
        target_node = params_dict.get("targetNodeId")
        if target_node:
            try:
                impact = json.loads(_blast_radius_raw(target_node, max_depth=3, direction="upstream"))
                if impact.get("status") == "error":
                    logger.warning("[propose_remediation] blast radius lookup failed: %s", impact.get("message"))
                else:
                    blast_radius_data = {
                        "impactedCount": impact.get("impacted_count", 0),
                        "totalNodeCount": impact.get("total_node_count", 0),
                        "impactedNodes": impact.get("impact_tree", [])[:50],
                    }
            except Exception:
                pass

        blast_policy = next((p for p in policies if p.get("policyName", "") == "Max Blast Radius: 20%" and p.get("enabled", False)), None)
        if blast_policy and not blocked_reason and blast_radius_data:
            impacted = blast_radius_data["impactedCount"]
            total = blast_radius_data.get("totalNodeCount", 0)
            if total > 0 and impacted / total > 0.20:
                blocked_reason = f"Blocked by Policy: Max Blast Radius exceeded. Impacted: {impacted}/{total} nodes ({impacted/total:.0%})"

        lambda_requires_approval = False
        lambda_policy = next((p for p in policies if p.get("policyName", "") == "Require Approval for Lambda Updates" and p.get("enabled", False)), None)
        if lambda_policy and not blocked_reason:
            if "lambda" in action_type.lower() or "lambda" in str(params_dict).lower():
                lambda_requires_approval = True

        sev4_policy = next((p for p in policies if p.get("policyName", "") == "Auto-approve SEV4 Changes" and p.get("enabled", False)), None)
        if sev4_policy and not blocked_reason and not lambda_requires_approval:
            if "sev4" in justification.lower() or params_dict.get("severity") == "SEV4":
                status = "AUTO_APPROVED"

        if blocked_reason:
            return json.dumps({"status": "BLOCKED", "message": blocked_reason})

        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow().isoformat() + "Z"

        item = {
            "approvalId": approval_id,
            "status": status,
            "actionType": action_type,
            "parameters": params_dict,
            "incidentId": incident_id,
            "justification": justification,
            "createdAt": now,
        }
        if blast_radius_data:
            item["blastRadius"] = blast_radius_data

        DYNAMODB.Table(APPROVAL_TABLE_NAME).put_item(Item=item)

        if status == "AUTO_APPROVED":
            return json.dumps({"status": "success", "approvalId": approval_id, "message": f"Remediation ticket {approval_id} auto-approved by SEV4 policy."})
        return json.dumps({"status": "success", "approvalId": approval_id, "message": f"Remediation ticket {approval_id} created and awaiting human approval."})
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


def query_lex_bot_health(node_id: str, start_minutes_ago: int = 60) -> str:
    """
    Check the health of an Amazon Lex V2 bot alias referenced by Connect flows.
    Calls the lexv2-models API to get alias status, then queries CloudWatch for NLU
    error metrics (MissedUtteranceCount, RuntimePollingFrequency).

    Args:
        node_id (str): The topology node ID for the Lex bot, in the form
                       'lex:arn:aws:lex:REGION:ACCOUNT:bot-alias/BOT_ID/ALIAS_ID'.
        start_minutes_ago (int): Minutes ago to start CloudWatch metric window (default 60).
    """
    import datetime

    t0 = time.time()
    logger.info("[TOOL] query_lex_bot_health node_id=%s", node_id)

    # Strip leading 'lex:' prefix and parse the V2 ARN.
    # V2 format: arn:aws:lex:REGION:ACCOUNT:bot-alias/BOT_ID/ALIAS_ID
    arn = node_id[4:] if node_id.startswith("lex:") else node_id
    try:
        parts = arn.split("bot-alias/")
        if len(parts) != 2:
            return json.dumps({"status": "error", "message": f"Cannot parse Lex V2 ARN from node_id: {node_id}"})
        ids = parts[1].split("/")
        if len(ids) != 2:
            return json.dumps({"status": "error", "message": f"Unexpected bot-alias path in ARN: {arn}"})
        bot_id, alias_id = ids[0], ids[1]
    except Exception as e:
        return json.dumps({"status": "error", "message": f"ARN parse error: {e}"})

    region = _REGION
    lex_client = boto3.client("lexv2-models", region_name=region)
    cw_client = boto3.client("cloudwatch", region_name=region)

    result = {"status": "success", "botId": bot_id, "botAliasId": alias_id, "arn": arn}

    # 1. Alias status via lexv2-models
    try:
        alias_detail = lex_client.describe_bot_alias(botId=bot_id, botAliasId=alias_id)
        result["aliasName"] = alias_detail.get("botAliasName", alias_id)
        result["aliasStatus"] = alias_detail.get("botAliasStatus", "Unknown")
        # aliasStatus values: Creating | Available | Deleting | Failed
        result["botVersion"] = alias_detail.get("botVersion", "Unknown")
        result["localeSettings"] = list(alias_detail.get("botAliasLocaleSettings", {}).keys())
    except Exception as e:
        result["aliasStatus"] = "Unknown"
        result["aliasError"] = str(e)

    # 2. Bot-level status
    try:
        bot_detail = lex_client.describe_bot(botId=bot_id)
        result["botName"] = bot_detail.get("botName", bot_id)
        result["botStatus"] = bot_detail.get("botStatus", "Unknown")
        # botStatus values: Creating | Available | Inactive | Deleting | Failed | Versioning | Importing
    except Exception as e:
        result["botStatus"] = "Unknown"
        result["botError"] = str(e)

    # 3. CloudWatch NLU metrics (AWS/Lex namespace, V2 dimensions)
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(minutes=start_minutes_ago)
    dimensions = [
        {"Name": "BotName", "Value": result.get("botName", bot_id)},
        {"Name": "BotAliasName", "Value": result.get("aliasName", alias_id)},
    ]
    cw_metrics = {}
    for metric_name in ("MissedUtteranceCount", "RuntimePollingRequests"):
        try:
            resp = cw_client.get_metric_statistics(
                Namespace="AWS/Lex",
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start,
                EndTime=now,
                Period=int(start_minutes_ago * 60),
                Statistics=["Sum"],
            )
            datapoints = resp.get("Datapoints", [])
            cw_metrics[metric_name] = datapoints[0]["Sum"] if datapoints else 0
        except Exception as e:
            cw_metrics[metric_name] = f"error: {e}"
    result["cloudwatchMetrics"] = cw_metrics

    logger.info("[TOOL] query_lex_bot_health node_id=%s alias_status=%s latency_ms=%d",
                node_id, result.get("aliasStatus"), int((time.time() - t0) * 1000))
    return json.dumps(result, default=str)


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
        instance_arn = f"arn:aws:connect:{region}:{account_id}:instance/{instance_id}"
        resource_arn = f"{instance_arn}/{resource_type.lower()}/{clean_resource_id}"
        metrics = (
            [{"Name": "AVG_FLOW_TIME"}, {"Name": "CONTACTS_FLOW_OUT"}]
            if resource_type == "CONTACT_FLOW"
            else [{"Name": "CONTACTS_QUEUED"}, {"Name": "CONTACTS_ABANDONED"}, {"Name": "MAX_QUEUED_TIME"}]
        )
        response = connect_client.get_metric_data_v2(
            ResourceArn=instance_arn,
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
    Query Amazon Connect Contact Trace Records (CTR) for a specific contact using
    the connect:DescribeContact API. Returns queue times, agent routing details,
    initiation method, channel, and disconnect reason.

    Args:
        instance_id (str): The Amazon Connect instance ID.
        contact_id (str): The specific contact ID to look up.
    """
    logger.info("[TOOL] query_connect_ctrs instance=%s contact=%s", instance_id, contact_id)
    try:
        client = boto3.client("connect", region_name=_REGION)
        resp = client.describe_contact(InstanceId=instance_id, ContactId=contact_id)
        contact = resp.get("Contact", {})
        queue_info = contact.get("QueueInfo", {})
        agent_info = contact.get("AgentInfo", {})
        disconnect = contact.get("DisconnectDetails", {})
        data = {
            "ContactId": contact.get("Id"),
            "InitialContactId": contact.get("InitialContactId"),
            "Channel": contact.get("Channel"),
            "InitiationMethod": contact.get("InitiationMethod"),
            "InitiationTimestamp": str(contact.get("InitiationTimestamp", "")),
            "DisconnectTimestamp": str(contact.get("DisconnectTimestamp", "")),
            "Queue": {
                "Id": queue_info.get("Id"),
                "EnqueueTimestamp": str(queue_info.get("EnqueueTimestamp", "")),
                "DequeueTimestamp": str(queue_info.get("DequeueTimestamp", "")),
            },
            "Agent": {
                "Id": agent_info.get("Id"),
                "ConnectedToAgentTimestamp": str(agent_info.get("ConnectedToAgentTimestamp", "")),
                "AgentPauseDurationInSeconds": agent_info.get("AgentPauseDurationInSeconds"),
            },
            "DisconnectReason": disconnect.get("PotentialDisconnectIssue", "CUSTOMER_DISCONNECT"),
            "Tags": contact.get("Tags", {}),
        }
        return json.dumps({"status": "success", "data": data}, default=str)
    except Exception as e:
        logger.error("[TOOL] query_connect_ctrs instance=%s contact=%s error=%s", instance_id, contact_id, e)
        return json.dumps({"status": "error", "message": str(e)})


def query_contact_lens(instance_id: str, contact_id: str) -> str:
    """
    Retrieve Contact Lens post-contact analysis for a completed contact: conversation
    transcript segments, overall sentiment (customer + agent), detected issues, and
    matched categories. Requires Contact Lens to be enabled on the Connect instance.

    Args:
        instance_id (str): The Amazon Connect instance ID.
        contact_id (str): The specific contact ID to analyse.
    """
    logger.info("[TOOL] query_contact_lens instance=%s contact=%s", instance_id, contact_id)
    try:
        client = boto3.client("connect", region_name=_REGION)
        segments = []
        kwargs: dict = {
            "InstanceId": instance_id,
            "ContactId": contact_id,
            "MaxResults": 100,
        }
        while True:
            resp = client.list_contact_analysis_segments(**kwargs)
            segments.extend(resp.get("Segments", []))
            next_token = resp.get("NextToken")
            if not next_token:
                break
            kwargs["NextToken"] = next_token

        # Separate by segment type for easier agent consumption.
        transcript: list[dict] = []
        categories: list[str] = []
        sentiment_summary: dict = {}

        for seg in segments:
            if "Transcript" in seg:
                t = seg["Transcript"]
                transcript.append({
                    "Id": t.get("Id"),
                    "ParticipantRole": t.get("ParticipantRole"),
                    "Content": t.get("Content"),
                    "BeginOffsetMillis": t.get("BeginOffsetMillis"),
                    "Sentiment": t.get("Sentiment"),
                    "IssuesDetected": t.get("IssuesDetected", []),
                })
            if "Categories" in seg:
                for match in seg["Categories"].get("MatchedCategories", []):
                    if match not in categories:
                        categories.append(match)
            if "PostContactSummary" in seg:
                sentiment_summary = seg["PostContactSummary"]

        result = {
            "status": "success",
            "contactId": contact_id,
            "transcriptSegments": len(transcript),
            "transcript": transcript[:50],  # cap at 50 turns to avoid oversized payloads
            "detectedCategories": categories,
            "postContactSummary": sentiment_summary,
        }
        return json.dumps(result, default=str)
    except client.exceptions.ResourceNotFoundException:
        return json.dumps({
            "status": "not_found",
            "message": f"No Contact Lens analysis found for contact {contact_id}. "
                       "Contact Lens may not be enabled for this flow, or the contact is too recent.",
        })
    except Exception as e:
        logger.error("[TOOL] query_contact_lens instance=%s contact=%s error=%s", instance_id, contact_id, e)
        return json.dumps({"status": "error", "message": str(e)})


def query_agent_events(instance_id: str, queue_id: str = "", start_minutes_ago: int = 30) -> str:
    """
    Query current agent availability and recent contact activity to assess staffing
    impact during an incident. Uses connect:GetCurrentUserData for live agent states
    and connect:SearchContacts to surface contacts handled in the time window.

    Args:
        instance_id (str): The Amazon Connect instance ID.
        queue_id (str): Optional queue ID to scope results (clean UUID, no ARN prefix).
        start_minutes_ago (int): How far back to search for contacts (default 30).
    """
    logger.info("[TOOL] query_agent_events instance=%s queue=%s window=%dm",
                instance_id, queue_id, start_minutes_ago)
    client = boto3.client("connect", region_name=_REGION)
    region = _REGION
    try:
        account_id = boto3.client("sts", region_name=region).get_caller_identity()["Account"]
    except Exception:
        account_id = "unknown"
    instance_arn = f"arn:aws:connect:{region}:{account_id}:instance/{instance_id}"

    result: dict = {"status": "success", "instanceId": instance_id}
    clean_queue_id = (queue_id.split(":")[-1] if ":" in queue_id else queue_id) if queue_id else ""

    # 1. Live agent states via GetCurrentUserData
    try:
        filters: dict = {}
        if clean_queue_id:
            filters["Queues"] = [f"{instance_arn}/queue/{clean_queue_id}"]
        user_resp = client.get_current_user_data(
            InstanceId=instance_id,
            Filters=filters,
            MaxResults=100,
        )
        agents = user_resp.get("UserDataList", [])
        state_counts: dict[str, int] = {}
        for agent in agents:
            status = agent.get("Status", {}).get("StatusName", "Unknown")
            state_counts[status] = state_counts.get(status, 0) + 1
        result["agentStateSummary"] = state_counts
        result["totalAgentsReturned"] = len(agents)
    except Exception as e:
        result["agentStateSummary"] = {"error": str(e)}

    # 2. Recent contacts via SearchContacts
    try:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(minutes=start_minutes_ago)
        search_criteria: dict = {}
        if clean_queue_id:
            search_criteria["QueueIds"] = [clean_queue_id]
        search_resp = client.search_contacts(
            InstanceId=instance_id,
            TimeRange={
                "Type": "INITIATION_TIMESTAMP",
                "StartTime": start_time,
                "EndTime": now,
            },
            SearchCriteria=search_criteria,
            MaxResults=25,
        )
        contacts = search_resp.get("Contacts", [])
        result["recentContacts"] = [
            {
                "ContactId": c.get("Id"),
                "InitiationTimestamp": str(c.get("InitiationTimestamp", "")),
                "DisconnectTimestamp": str(c.get("DisconnectTimestamp", "")),
                "InitiationMethod": c.get("InitiationMethod"),
                "AgentId": c.get("AgentInfo", {}).get("Id"),
                "QueueId": c.get("QueueInfo", {}).get("Id"),
                "Channel": c.get("Channel"),
            }
            for c in contacts
        ]
        result["recentContactCount"] = search_resp.get("TotalCount", len(contacts))
    except Exception as e:
        result["recentContacts"] = []
        result["searchError"] = str(e)

    return json.dumps(result, default=str)


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

    logger.info("[TOOL] query_cloudwatch_flow_logs instance=%s flow=%s window=%dm", instance_id, flow_id, window)
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
        query = f"fields @timestamp, Action, Parameters, @message | filter ContactFlowId like '{clean_flow_id}' | filter @message like /[Ee]rror/ | sort @timestamp desc | limit 20"
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
                return _compress_tool_output(json.dumps({"status": "success", "logs": res.get("results", [])}, default=str))
            if res["status"] in ("Failed", "Cancelled"):
                return json.dumps({
                    "status": "error",
                    "message": f"CloudWatch Logs Insights query {res['status'].lower()}.",
                    "queryId": query_id
                })
            time.sleep(1)
        return json.dumps({"status": "timeout", "message": "CloudWatch Logs Insights query timed out."})
    except Exception as e:
        logger.error("[TOOL] query_cloudwatch_flow_logs instance=%s flow=%s error=%s", instance_id, flow_id, e)
        return json.dumps({"status": "error", "message": str(e)})


# ---------------------------------------------------------------------------
# Agentic memory — recall and record investigation learnings
# ---------------------------------------------------------------------------

def recall_prior_incidents(resource_id: str, incident_type: str = "") -> str:
    """
    Recall past incidents for a specific Connect resource to surface known patterns,
    prior root causes, and what remediation actions previously succeeded or failed.
    Also surfaces operator rejection feedback (incidentType='OPERATOR_REJECTION') — when
    an operator rejects a proposed remediation they provide a reason, which is stored here
    as rootCause. Always check for OPERATOR_REJECTION records before proposing a remediation
    to avoid repeating actions that were previously rejected and to understand why.
    Call this BEFORE beginning a new investigation so you don't repeat prior work.

    Args:
        resource_id (str): The Connect resource ID to look up (e.g. flow ID, queue ID, Lex bot ID).
        incident_type (str): Optional filter — e.g. 'flow_fatal_error', 'queue_overflow', 'lex_failure'.
                             Use 'OPERATOR_REJECTION' to retrieve only past operator rejections.
    """
    logger.info("[TOOL] recall_prior_incidents resource_id=%s type=%s", resource_id, incident_type)
    try:
        table = DYNAMODB.Table(MEMORY_TABLE_NAME)
        kwargs = {
            "IndexName": "by-resource-createdAt",
            "KeyConditionExpression": "resourceId = :rid",
            "ExpressionAttributeValues": {":rid": resource_id},
            "ScanIndexForward": False,
            "Limit": 8,
        }
        if incident_type:
            kwargs["FilterExpression"] = "incidentType = :itype"
            kwargs["ExpressionAttributeValues"][":itype"] = incident_type

        response = table.query(**kwargs)
        items = response.get("Items", [])
        logger.info("[TOOL] recall_prior_incidents resource_id=%s found=%d", resource_id, len(items))
        if not items:
            return json.dumps({"status": "no_prior_incidents", "message": "No prior incidents found for this resource. Proceed with standard investigation."})

        summaries = []
        for m in items:
            summaries.append({
                "incidentId": m.get("incidentId", ""),
                "incidentType": m.get("incidentType", ""),
                "createdAt": m.get("createdAt", ""),
                "pattern": m.get("pattern", ""),
                "rootCause": m.get("rootCause", ""),
                "resolution": m.get("resolution", ""),
                "outcome": m.get("outcome", "unknown"),
            })
        return json.dumps({"status": "success", "prior_incidents": summaries}, default=str)
    except Exception as e:
        logger.error("[TOOL] recall_prior_incidents resource_id=%s error=%s", resource_id, e)
        return json.dumps({"status": "error", "message": str(e)})


def query_ai_agent_health(agent_id: str, assistant_id: str = "", start_minutes_ago: int = 60) -> str:
    """
    Inspect a Connect AI Agent (Q Connect orchestration agent) and report its health.
    Pulls config from the qconnect API, Bedrock invocation metrics for the agent's
    model, and Lex runtime metrics for the associated Connect bot.

    Args:
        agent_id (str): The qconnect AI agent ID (UUID).
        assistant_id (str): The Q Connect assistant ID. Defaults to the env var
                            QCONNECT_ASSISTANT_ID or the well-known archdemos value.
        start_minutes_ago (int): CloudWatch lookback window in minutes (default 60).
    """
    import datetime

    t0 = time.time()
    logger.info("[TOOL] query_ai_agent_health agent_id=%s", agent_id)

    _assistant_id = assistant_id or os.environ.get(
        "QCONNECT_ASSISTANT_ID", "de018ffb-f5ea-4ff4-8547-714cb0eeb736"
    )
    region = _REGION
    qc = boto3.client("qconnect", region_name=region)
    cw = boto3.client("cloudwatch", region_name=region)

    result: dict = {"agentId": agent_id, "assistantId": _assistant_id}

    # 1. Agent config from qconnect
    try:
        r = qc.get_ai_agent(assistantId=_assistant_id, aiAgentId=agent_id)
        ag = r.get("aiAgent", {})
        result["name"] = ag.get("name", agent_id)
        result["status"] = ag.get("status", "UNKNOWN")
        result["visibilityStatus"] = ag.get("visibilityStatus", "UNKNOWN")
        result["type"] = ag.get("type", "UNKNOWN")
        result["modifiedTime"] = str(ag.get("modifiedTime", ""))
        cfg = ag.get("configuration", {}).get("orchestrationAIAgentConfiguration", {})
        result["promptId"] = cfg.get("orchestrationAIPromptId", "")
        result["locale"] = cfg.get("locale", "")
        result["tools"] = [t.get("toolName") for t in cfg.get("toolConfigurations", [])]
        result["connectInstanceArn"] = cfg.get("connectInstanceArn", "")
    except Exception as e:
        result["configError"] = str(e)
        result["status"] = "UNKNOWN"

    # 2. Prompt / model details
    model_id = None
    if result.get("promptId"):
        try:
            prompt_id_bare = result["promptId"].split(":")[0]
            pr = qc.get_ai_prompt(assistantId=_assistant_id, aiPromptId=prompt_id_bare)
            prompt = pr.get("aiPrompt", {})
            model_id = prompt.get("modelId")
            result["modelId"] = model_id
            result["promptStatus"] = prompt.get("status", "UNKNOWN")
        except Exception as e:
            result["promptError"] = str(e)

    # 3. Bedrock invocation metrics for the agent's model
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(minutes=start_minutes_ago)
    period = int(start_minutes_ago * 60)

    bedrock_metrics: dict = {}
    if model_id:
        dims = [{"Name": "ModelId", "Value": model_id}]
        for metric in ("Invocations", "InvocationClientErrors", "InvocationLatency"):
            stat = "Average" if metric == "InvocationLatency" else "Sum"
            try:
                resp = cw.get_metric_statistics(
                    Namespace="AWS/Bedrock",
                    MetricName=metric,
                    Dimensions=dims,
                    StartTime=start,
                    EndTime=now,
                    Period=period,
                    Statistics=[stat],
                )
                dps = resp.get("Datapoints", [])
                bedrock_metrics[metric] = round(dps[0][stat], 2) if dps else 0
            except Exception as e:
                bedrock_metrics[metric] = f"error: {e}"

        # Derived error rate
        invocations = bedrock_metrics.get("Invocations", 0)
        errors = bedrock_metrics.get("InvocationClientErrors", 0)
        if isinstance(invocations, (int, float)) and isinstance(errors, (int, float)) and invocations > 0:
            bedrock_metrics["errorRatePct"] = round(100 * errors / invocations, 1)
        else:
            bedrock_metrics["errorRatePct"] = 0

    result["bedrockMetrics"] = bedrock_metrics

    # 4. Lex runtime metrics (the Connect bot that hosts Q Connect AI agents)
    lex_metrics: dict = {}
    try:
        lex_resp = cw.list_metrics(Namespace="AWS/Lex", MetricName="RuntimeRequestCount")
        lex_dims_set: list = []
        for m in lex_resp.get("Metrics", []):
            dim_map = {d["Name"]: d["Value"] for d in m.get("Dimensions", [])}
            if "BotId" in dim_map and "BotAliasId" in dim_map:
                lex_dims_set.append(m.get("Dimensions", []))
        # Use first available bot alias dims if any
        if lex_dims_set:
            for metric in ("RuntimeRequestCount", "RuntimeUserErrors"):
                try:
                    resp = cw.get_metric_statistics(
                        Namespace="AWS/Lex",
                        MetricName=metric,
                        Dimensions=lex_dims_set[0],
                        StartTime=start,
                        EndTime=now,
                        Period=period,
                        Statistics=["Sum"],
                    )
                    dps = resp.get("Datapoints", [])
                    lex_metrics[metric] = int(dps[0]["Sum"]) if dps else 0
                except Exception as e:
                    lex_metrics[metric] = f"error: {e}"
    except Exception as e:
        lex_metrics["lexError"] = str(e)

    result["lexMetrics"] = lex_metrics

    logger.info(
        "[TOOL] query_ai_agent_health agent_id=%s status=%s model=%s latency_ms=%d",
        agent_id, result.get("status"), model_id, int((time.time() - t0) * 1000),
    )
    return json.dumps(result, default=str)


def record_investigation_memory(
    resource_id: str,
    incident_type: str,
    pattern: str,
    root_cause: str,
    resolution: str,
    outcome: str,
    incident_id: str = "",
) -> str:
    """
    Persist what was learned from this investigation to long-term memory so future
    investigations on the same resource benefit from prior findings.
    Call this AFTER completing your investigation and proposing a remediation.

    Args:
        resource_id (str): The primary Connect resource ID that was investigated.
        incident_type (str): Short label for the failure type (e.g. 'flow_fatal_error', 'queue_overflow', 'lex_failure').
        pattern (str): Concise description of the symptoms and conditions that led to this incident.
        root_cause (str): The determined root cause (e.g. 'Lambda ARN mismatch after deploy').
        resolution (str): The remediation action taken or recommended (e.g. 'Rolled back Lambda alias to stable version').
        outcome (str): Result — 'resolved', 'partial', 'unresolved', or 'escalated'.
        incident_id (str): Optional incident ID for traceability.
    """
    logger.info("[TOOL] record_investigation_memory resource_id=%s type=%s outcome=%s", resource_id, incident_type, outcome)
    try:
        memory_id = f"mem-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        ttl = int((datetime.now(timezone.utc) + timedelta(days=_MEMORY_TTL_DAYS)).timestamp())

        DYNAMODB.Table(MEMORY_TABLE_NAME).put_item(Item={
            "memoryId": memory_id,
            "resourceId": resource_id,
            "incidentType": incident_type,
            "pattern": pattern[:2000],
            "rootCause": root_cause[:1000],
            "resolution": resolution[:1000],
            "outcome": outcome,
            "incidentId": incident_id,
            "createdAt": now,
            "ttl": ttl,
        })
        logger.info("[TOOL] record_investigation_memory saved memoryId=%s", memory_id)
        return json.dumps({"status": "success", "memoryId": memory_id, "message": "Investigation memory saved for future reference."})
    except Exception as e:
        logger.error("[TOOL] record_investigation_memory resource_id=%s error=%s", resource_id, e)
        return json.dumps({"status": "error", "message": str(e)})
