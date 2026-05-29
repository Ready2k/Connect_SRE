import os
import json
import uuid
import base64
import gzip
import datetime
import boto3
import urllib.request
import urllib.error
from dateutil.parser import parse as parse_date

DYNAMODB = boto3.resource("dynamodb")
SQS = boto3.client("sqs")

INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
EVIDENCE_BUCKET_NAME = os.environ.get("EVIDENCE_BUCKET_NAME")
TOPOLOGY_REFRESH_QUEUE_URL = os.environ.get("TOPOLOGY_REFRESH_QUEUE_URL")
AGENT_API_URL = os.environ.get("AGENT_API_URL") # e.g., http://localhost:8000
DEDUPE_WINDOW_MINUTES = int(os.environ.get("DEDUPE_WINDOW_MINUTES", "30"))


def handler(event, context):
    # CloudWatch Logs subscription filter delivers a different envelope entirely
    if "awslogs" in event:
        incidents = parse_contact_flow_log_errors(event)
        for normalized_incident in incidents:
            save_incident(normalized_incident, event)
            if normalized_incident.get("status") != "Linked":
                trigger_agent_investigation(normalized_incident)
        print(json.dumps({"event": "contact_flow_log_errors_processed", "count": len(incidents)}))
        return {"ok": True, "count": len(incidents)}

    print(json.dumps({"event": "normalizer_invoked", "source": event.get("source"), "detail_type": event.get("detail-type")}))

    # 1. Parse EventBridge signals
    source = event.get("source", "")
    detail_type = event.get("detail-type", "")

    normalized_incident = None

    try:
        if (
            source == "aws.cloudwatch"
            and detail_type == "CloudWatch Alarm State Change"
        ):
            normalized_incident = parse_cloudwatch_alarm(event)
        elif source == "aws.connect" or (
            source == "aws.cloudtrail"
            and event.get("detail", {}).get("eventSource") == "connect.amazonaws.com"
        ):
            normalized_incident = parse_connect_cloudtrail(event)
        elif source == "aws.lex" or (
            source == "aws.cloudtrail"
            and event.get("detail", {}).get("eventSource") in ("lexv2.amazonaws.com", "lex.amazonaws.com")
        ):
            normalized_incident = parse_lex_cloudtrail(event)
        elif source == "aws.lambda" or (
            source == "aws.cloudtrail"
            and event.get("detail", {}).get("eventSource") == "lambda.amazonaws.com"
        ):
            normalized_incident = parse_lambda_cloudtrail(event)
        elif source == "connect-sre.schedule":
            normalized_incident = handle_proactive_check(event)
        else:
            print(json.dumps({"event": "unclassified_source", "source": source, "detail_type": detail_type}))
            return {"ok": True, "message": "unclassified_source"}

        if normalized_incident:
            # 2. Write to DynamoDB and save a raw copy to S3
            save_incident(normalized_incident, event)

            # 3. If it's a configuration change, request a partial topology scan
            if normalized_incident.get("isMutation", False):
                trigger_topology_refresh(normalized_incident)

            # 4. Trigger ADK Agent Investigation — skip for incidents linked to a master
            if normalized_incident.get("status") != "Linked":
                trigger_agent_investigation(normalized_incident)

            return {"ok": True, "incidentId": normalized_incident["incidentId"]}

    except Exception as e:
        print(f"Error normalizing incident: {str(e)}")
        # Raise error to trigger EventBridge SQS DLQ
        raise e

    return {"ok": True, "message": "no_incident_created"}


def parse_contact_flow_log_errors(event):
    raw = base64.b64decode(event["awslogs"]["data"])
    payload = json.loads(gzip.decompress(raw))

    # Always use the configured instance UUID — the log group suffix may be an
    # alias (e.g. /aws/connect/archdemos) rather than the raw instance ID.
    instance_id = os.environ.get("CONNECT_INSTANCE_ID", "")

    incidents = []
    for log_event in payload.get("logEvents", []):
        try:
            entry = json.loads(log_event["message"])
        except (json.JSONDecodeError, KeyError):
            continue

        if entry.get("Results") != "Error":
            continue

        error_details = entry.get("ErrorDetails", {})
        error_code = error_details.get("ErrorCode", "UnknownError")
        error_message = error_details.get("Message", "")
        flow_arn = entry.get("ContactFlowId", "")
        flow_id = flow_arn.split("/")[-1] if "/" in flow_arn else flow_arn
        flow_name = entry.get("ContactFlowName", "unknown-flow")
        contact_id = entry.get("ContactId", "unknown-contact")
        module_type = entry.get("ContactFlowModuleType", "")

        severity = "SEV1" if error_code in ("InternalServerException", "ThrottlingException") else "SEV2"
        incident_id = f"INC-FLOW-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow().isoformat() + "Z"

        incidents.append({
            "incidentId": incident_id,
            "instanceId": instance_id,
            "dedupeKey": f"flow-error:{flow_id}:{error_code}",
            "title": f"Contact Flow Error: {flow_name} — {error_code}",
            "severity": severity,
            "status": "Investigating",
            "connectResourceId": flow_id or instance_id,
            "isMutation": False,
            "details": f"Module '{module_type}' failed for contact {contact_id}. Error: {error_message}",
            "rca": "Pending agent investigation.",
            "impact": "Calls may have been disconnected or failed to reach an agent.",
            "suggestedAction": "Check Lex bot configuration and integration bindings.",
            "createdAt": now,
            "updatedAt": now,
        })

    return incidents


def parse_cloudwatch_alarm(event):
    detail = event.get("detail", {})
    alarm_name = detail.get("alarmName", "")
    state = detail.get("state", {}).get("value", "UNKNOWN")

    if state != "ALARM":
        print(json.dumps({"event": "alarm_ignored", "alarmName": alarm_name, "state": state}))
        return None

    now = datetime.datetime.utcnow().isoformat() + "Z"
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

    # Infer resource targets from alarm description or dimensions
    metric_stat = detail.get("configuration", {}).get("metrics", [{}])[0].get("metricStat", {})
    metric_name = metric_stat.get("metric", {}).get("metricName", "")
    dimensions = metric_stat.get("metric", {}).get("dimensions", {})
    
    # Extract InstanceId explicitly
    instance_id = dimensions.get("InstanceId")
    if not instance_id:
        instance_id = os.environ.get("CONNECT_INSTANCE_ID", "")
        
    connect_resource_id = dimensions.get(
        "ContactFlowId",
        dimensions.get("QueueId", instance_id or "unknown-resource"),
    )

    # Estimate severity based on Alarm Name or Metric Name
    severity = "SEV3"
    if any(s in alarm_name for s in ["SEV1", "Fatal", "Latency"]) or "Fatal" in metric_name:
        severity = "SEV1"
    elif any(s in alarm_name for s in ["SEV2", "Errors"]) or "Error" in metric_name:
        severity = "SEV2"

    return {
        "incidentId": incident_id,
        "instanceId": instance_id,
        "dedupeKey": f"alarm:{alarm_name}:{connect_resource_id}",
        "title": f"CloudWatch Alarm: {alarm_name} in {state}",
        "severity": severity,
        "status": "Investigating",
        "connectResourceId": connect_resource_id,
        "isMutation": False,
        "details": detail.get("state", {}).get("reason", "Alarm threshold breached."),
        "rca": "Pending ADK specialist agent correlation analysis...",
        "impact": "Pending CustomerImpactAgent estimation...",
        "suggestedAction": "Pending RunbookAgent recommendation...",
        "createdAt": now,
        "updatedAt": now,
    }


def parse_connect_cloudtrail(event):
    detail = event.get("detail", {})
    event_name = detail.get("eventName", "")
    request_params = detail.get("requestParameters", {})

    # Identify mutation events
    mutations = [
        "UpdateContactFlowContent",
        "PublishContactFlow",
        "UpdateContactFlowModuleContent",
        "UpdateQueueHoursOfOperation",
        "UpdateRoutingProfileQueues",
    ]
    if event_name not in mutations:
        return None

    now = datetime.datetime.utcnow().isoformat() + "Z"
    incident_id = f"INC-MUT-{uuid.uuid4().hex[:8].upper()}"

    # Parse target resource
    connect_resource_id = request_params.get(
        "contactFlowId",
        request_params.get(
            "contactFlowModuleId",
            request_params.get("queueId", "unknown-connect-resource"),
        ),
    )
    user_identity = detail.get("userIdentity", {}).get("arn", "Unknown SRE Operator")
    
    # Extract instanceId from ARN if available
    instance_id = request_params.get("instanceId", os.environ.get("CONNECT_INSTANCE_ID", ""))

    return {
        "incidentId": incident_id,
        "instanceId": instance_id,
        "dedupeKey": f"mutation:{event_name}:{connect_resource_id}",
        "title": f"Config Mutation: {event_name}",
        "severity": "SEV4",  # Configuration changes are initially tracked as SEV4 informational events
        "status": "Config-Change",
        "connectResourceId": connect_resource_id,
        "isMutation": True,
        "details": f"Operator '{user_identity}' triggered {event_name} inside Connect.",
        "rca": "N/A - Direct Configuration Change",
        "impact": "Potential blast radius under SRE evaluation.",
        "suggestedAction": "Auto-requesting partial topology rescan.",
        "createdAt": now,
        "updatedAt": now,
    }


def parse_lex_cloudtrail(event):
    detail = event.get("detail", {})
    event_name = detail.get("eventName", "")
    if "BotAlias" not in event_name and "BotVersion" not in event_name:
        return None

    now = datetime.datetime.utcnow().isoformat() + "Z"
    incident_id = f"INC-LEX-{uuid.uuid4().hex[:8].upper()}"
    bot_id = detail.get("requestParameters", {}).get("botId", "unknown-lex-bot")
    instance_id = os.environ.get("CONNECT_INSTANCE_ID", "")

    return {
        "incidentId": incident_id,
        "instanceId": instance_id,
        "dedupeKey": f"mutation:lex:{event_name}:{bot_id}",
        "title": f"Lex Configuration: {event_name}",
        "severity": "SEV4",
        "status": "Config-Change",
        "connectResourceId": bot_id,
        "isMutation": True,
        "details": f"Lex API triggered {event_name} for bot {bot_id}.",
        "rca": "N/A",
        "impact": "Associated Connect contact flows may experience recognition spikes.",
        "suggestedAction": "Auto-requesting topology rescan.",
        "createdAt": now,
        "updatedAt": now,
    }


def parse_lambda_cloudtrail(event):
    # Triggers on Lambda function updates which are integrated in Connect flows
    detail = event.get("detail", {})
    event_name = detail.get("eventName", "")
    if (
        "UpdateFunctionCode" not in event_name
        and "UpdateFunctionConfiguration" not in event_name
    ):
        return None

    now = datetime.datetime.utcnow().isoformat() + "Z"
    incident_id = f"INC-LMD-{uuid.uuid4().hex[:8].upper()}"
    function_name = detail.get("requestParameters", {}).get(
        "functionName", "unknown-lambda"
    )
    instance_id = os.environ.get("CONNECT_INSTANCE_ID", "")

    return {
        "incidentId": incident_id,
        "instanceId": instance_id,
        "dedupeKey": f"mutation:lambda:{event_name}:{function_name}",
        "title": f"Lambda Integration Update: {event_name}",
        "severity": "SEV4",
        "status": "Config-Change",
        "connectResourceId": function_name,
        "isMutation": True,
        "details": f"Lambda function {function_name} was updated. This lambda is registered in Connect flows.",
        "rca": "N/A",
        "impact": "Downstream flow API requests could fail if dependencies are missing.",
        "suggestedAction": "Auto-requesting topology rescan.",
        "createdAt": now,
        "updatedAt": now,
    }


def handle_proactive_check(event):
    # Proactive scheduler trigger
    now = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "incidentId": f"INC-SCH-{uuid.uuid4().hex[:8].upper()}",
        "instanceId": os.environ.get("CONNECT_INSTANCE_ID", ""),
        "dedupeKey": "scheduled:proactive-heartbeat",
        "title": "Scheduled SRE Heartbeat Verification",
        "severity": "SEV4",
        "status": "Healthy",
        "connectResourceId": "connect-instance-heartbeat",
        "isMutation": False,
        "details": "Routine proactively triggered agent swarm check.",
        "rca": "N/A",
        "impact": "No operational impact detected.",
        "suggestedAction": "None.",
        "createdAt": now,
        "updatedAt": now,
    }


def save_incident(incident, raw_event):
    # Save standard item to DynamoDB Table
    table = DYNAMODB.Table(INCIDENT_TABLE_NAME)

    # Check deduplication
    dedupe_key = incident["dedupeKey"]
    existing_incidents = table.query(
        IndexName="by-dedupe-createdAt",
        KeyConditionExpression="dedupeKey = :dkey",
        ExpressionAttributeValues={":dkey": dedupe_key},
        Limit=1,
        ScanIndexForward=False,  # Get the newest first
    ).get("Items", [])

    if existing_incidents:
        latest = existing_incidents[0]
        latest_created_at = parse_date(latest["createdAt"])
        now_dt = parse_date(incident["createdAt"])
        age_seconds = (now_dt - latest_created_at).total_seconds()
        if age_seconds < (DEDUPE_WINDOW_MINUTES * 60):
            master_id = latest["incidentId"]
            incident["parentId"] = master_id
            incident["status"] = "Linked"
            incident["dedupeDecision"] = "linked"
            incident["dedupeParentAgeSeconds"] = int(age_seconds)
            print(json.dumps({
                "event": "dedupe_linked",
                "newIncidentId": incident["incidentId"],
                "masterIncidentId": master_id,
                "dedupeKey": dedupe_key,
                "parentAgeSeconds": int(age_seconds),
                "windowSeconds": DEDUPE_WINDOW_MINUTES * 60,
            }))
            # Atomically bump the master's linkedCount and refresh its updatedAt
            try:
                table.update_item(
                    Key={"incidentId": master_id},
                    UpdateExpression="ADD linkedCount :one SET updatedAt = :now",
                    ExpressionAttributeValues={
                        ":one": 1,
                        ":now": incident["createdAt"],
                    },
                )
            except Exception as upd_err:
                print(json.dumps({"event": "dedupe_counter_update_failed", "masterIncidentId": master_id, "error": str(upd_err)}))
        else:
            print(json.dumps({
                "event": "dedupe_new_incident",
                "incidentId": incident["incidentId"],
                "dedupeKey": dedupe_key,
                "priorIncidentAge": int(age_seconds),
                "reason": f"Prior incident too old ({int(age_seconds)}s > {DEDUPE_WINDOW_MINUTES * 60}s window)",
            }))

    table.put_item(Item=incident)
    print(json.dumps({
        "event": "incident_saved",
        "incidentId": incident["incidentId"],
        "severity": incident.get("severity"),
        "isMutation": incident.get("isMutation", False),
        "parentId": incident.get("parentId"),
        "dedupeKey": dedupe_key,
    }))

    # Save raw EventBridge payload to S3 Evidence Bucket
    if EVIDENCE_BUCKET_NAME:
        s3 = boto3.client("s3")
        key = f"incidents/{incident['incidentId']}/event_raw.json"
        s3.put_object(
            Bucket=EVIDENCE_BUCKET_NAME,
            Key=key,
            Body=json.dumps(raw_event),
            ContentType="application/json",
        )
        print(f"Raw event payload saved to s3://{EVIDENCE_BUCKET_NAME}/{key}")


def trigger_topology_refresh(incident):
    if not TOPOLOGY_REFRESH_QUEUE_URL:
        return

    # Infer resource type from title
    resource_type = "contact_flow"
    if "Module" in incident.get("title", ""):
        resource_type = "contact_flow_module"
    elif "Queue" in incident.get("title", ""):
        resource_type = "queue"

    # Queue up a message for the TopologyScanner to run a partial update
    payload = {
        "eventType": "topology_partial_refresh_requested",
        "resourceType": resource_type,
        "resourceId": incident["connectResourceId"],
        "reason": incident["title"],
        "observedAt": incident["createdAt"],
    }

    SQS.send_message(
        QueueUrl=TOPOLOGY_REFRESH_QUEUE_URL, MessageBody=json.dumps(payload)
    )
    print(json.dumps({"event": "topology_refresh_queued", "incidentId": incident["incidentId"], "resourceId": incident["connectResourceId"], "resourceType": resource_type}))


def trigger_agent_investigation(incident):
    if not AGENT_API_URL:
        print(json.dumps({"event": "agent_trigger_skipped", "incidentId": incident["incidentId"], "reason": "AGENT_API_URL not configured"}))
        return

    # Call the ADK Agent API
    try:
        url = f"{AGENT_API_URL.rstrip('/')}/api/incidents"
        
        # We just need to POST the incidentId, the agent backend will fetch the rest from DynamoDB
        # Or we can post the full incident payload. The ADK main.py /api/incidents expects an Incident payload
        payload = json.dumps(incident).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Incident-Id": incident["incidentId"],
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:  # nosec B310
            if response.status in (200, 201, 202):
                print(json.dumps({"event": "agent_triggered", "incidentId": incident["incidentId"], "agentUrl": url}))
            else:
                print(json.dumps({"event": "agent_trigger_failed", "incidentId": incident["incidentId"], "httpStatus": response.status}))

    except Exception as e:
        print(json.dumps({"event": "agent_trigger_error", "incidentId": incident.get("incidentId"), "error": str(e)}))
