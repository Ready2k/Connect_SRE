import os
import json
import uuid
import datetime
import boto3

DYNAMODB = boto3.resource("dynamodb")
SQS = boto3.client("sqs")

INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
EVIDENCE_BUCKET_NAME = os.environ.get("EVIDENCE_BUCKET_NAME")
TOPOLOGY_REFRESH_QUEUE_URL = os.environ.get("TOPOLOGY_REFRESH_QUEUE_URL")


def handler(event, context):
    print(f"Normalizer received event: {json.dumps(event)}")

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
            and "connect" in event.get("detail", {}).get("eventSource", "")
        ):
            normalized_incident = parse_connect_cloudtrail(event)
        elif "lex" in source or (
            source == "aws.cloudtrail"
            and "lex" in event.get("detail", {}).get("eventSource", "")
        ):
            normalized_incident = parse_lex_cloudtrail(event)
        elif "lambda" in source or (
            source == "aws.cloudtrail"
            and "lambda" in event.get("detail", {}).get("eventSource", "")
        ):
            normalized_incident = parse_lambda_cloudtrail(event)
        elif source == "connect-sre.schedule":
            normalized_incident = handle_proactive_check(event)
        else:
            print(f"Received unclassified event from source '{source}', ignoring.")
            return {"ok": True, "message": "unclassified_source"}

        if normalized_incident:
            # 2. Write to DynamoDB and save a raw copy to S3
            save_incident(normalized_incident, event)

            # 3. If it's a configuration change, request a partial topology scan
            if normalized_incident.get("isMutation", False):
                trigger_topology_refresh(normalized_incident)

            return {"ok": True, "incidentId": normalized_incident["incidentId"]}

    except Exception as e:
        print(f"Error normalizing incident: {str(e)}")
        # Raise error to trigger EventBridge SQS DLQ
        raise e

    return {"ok": True, "message": "no_incident_created"}


def parse_cloudwatch_alarm(event):
    detail = event.get("detail", {})
    alarm_name = detail.get("alarmName", "")
    state = detail.get("state", {}).get("value", "UNKNOWN")

    if state != "ALARM":
        print(f"Alarm {alarm_name} transitioned to {state}, ignoring.")
        return None

    now = datetime.datetime.utcnow().isoformat() + "Z"
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

    # Infer resource targets from alarm description or dimensions
    dimensions = (
        detail.get("configuration", {})
        .get("metrics", [{}])[0]
        .get("metricStat", {})
        .get("metric", {})
        .get("dimensions", {})
    )
    connect_resource_id = dimensions.get(
        "ContactFlowId",
        dimensions.get("QueueId", dimensions.get("InstanceId", "unknown-resource")),
    )

    # Estimate severity based on Alarm Name
    severity = "SEV3"
    if "SEV1" in alarm_name or "Fatal" in alarm_name or "Latency" in alarm_name:
        severity = "SEV1"
    elif "SEV2" in alarm_name or "Errors" in alarm_name:
        severity = "SEV2"

    return {
        "incidentId": incident_id,
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

    return {
        "incidentId": incident_id,
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

    return {
        "incidentId": incident_id,
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

    return {
        "incidentId": incident_id,
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
        # Deduplicate: if an open incident of same type exists within last 30 minutes, ignore or merge
        # For MVP, we will write a new version but reference the parent incident.
        incident["parentId"] = latest["incidentId"]

    table.put_item(Item=incident)
    print(f"Incident {incident['incidentId']} saved to DynamoDB.")

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

    # Queue up a message for the TopologyScanner to run a partial update
    payload = {
        "eventType": "topology_partial_refresh_requested",
        "resourceType": "contact_flow",
        "resourceId": incident["connectResourceId"],
        "reason": incident["title"],
        "observedAt": incident["createdAt"],
    }

    SQS.send_message(
        QueueUrl=TOPOLOGY_REFRESH_QUEUE_URL, MessageBody=json.dumps(payload)
    )
    print(
        f"Requested partial topology refresh for resource {incident['connectResourceId']} via SQS."
    )
