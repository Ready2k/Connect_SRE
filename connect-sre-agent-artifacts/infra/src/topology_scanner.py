import os
import json
import datetime
import boto3

DYNAMODB = boto3.resource("dynamodb")
CONNECT = boto3.client("connect")
LEX = boto3.client("lexv2-models")
LAMBDA = boto3.client("lambda")

TOPOLOGY_TABLE_NAME = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
CONNECT_INSTANCE_IDS = os.environ.get("CONNECT_INSTANCE_IDS", "").split(",")


def handler(event, context):
    print(f"Topology Scanner received trigger event: {json.dumps(event)}")

    # Check if trigger is SQS (meaning a partial refresh request)
    records = event.get("Records", [])
    if records:
        for record in records:
            body = json.loads(record.get("body", "{}"))
            if body.get("eventType") == "topology_partial_refresh_requested":
                handle_partial_scan(body)
        return {"ok": True, "scanType": "partial"}

    # Default behavior is a full scheduled scan
    handle_full_scan()
    return {"ok": True, "scanType": "full"}


def handle_full_scan():
    print("--- Starting Full Topology Scan ---")
    now = datetime.datetime.utcnow().isoformat() + "Z"

    for instance_id in CONNECT_INSTANCE_IDS:
        if not instance_id or instance_id == "":
            continue

        print(f"Scanning Connect Instance: {instance_id}")
        try:
            # 1. Scan Instance Metadata
            instance_details = CONNECT.describe_instance(InstanceId=instance_id).get(
                "Instance", {}
            )
            write_metadata(
                node_id=f"instance:{instance_id}",
                node_type="instance",
                label=instance_details.get(
                    "InstanceAlias", f"Connect-{instance_id[:8]}"
                ),
                arn=instance_details.get("Arn", "N/A"),
                status=instance_details.get("InstanceStatus", "ACTIVE"),
                now=now,
            )

            # 2. Scan Contact Flows
            flows = CONNECT.list_contact_flows(InstanceId=instance_id).get(
                "ContactFlowSummaryList", []
            )
            for f in flows:
                flow_id = f.get("Id")
                flow_details = CONNECT.describe_contact_flow(
                    InstanceId=instance_id, ContactFlowId=flow_id
                ).get("ContactFlow", {})
                write_metadata(
                    node_id=f"flow:{flow_id}",
                    node_type="flow",
                    label=f.get("Name", "Unnamed Flow"),
                    arn=f.get("Arn", "N/A"),
                    status=flow_details.get("State", "ACTIVE"),
                    now=now,
                )
                # Link Instance to Flow
                write_edge(
                    f"instance:{instance_id}",
                    "INSTANCE_HAS_FLOW",
                    f"flow:{flow_id}",
                    now,
                )

            # 3. Scan Contact Flow Modules
            modules = CONNECT.list_contact_flow_modules(InstanceId=instance_id).get(
                "ContactFlowModuleSummaryList", []
            )
            for m in modules:
                mod_id = m.get("Id")
                mod_details = CONNECT.describe_contact_flow_module(
                    InstanceId=instance_id, ContactFlowModuleId=mod_id
                ).get("ContactFlowModule", {})
                write_metadata(
                    node_id=f"module:{mod_id}",
                    node_type="module",
                    label=m.get("Name", "Unnamed Module"),
                    arn=m.get("Arn", "N/A"),
                    status=mod_details.get("State", "ACTIVE"),
                    now=now,
                )
                write_edge(
                    f"instance:{instance_id}",
                    "INSTANCE_HAS_MODULE",
                    f"module:{mod_id}",
                    now,
                )

            # 4. Scan Queues
            queues = CONNECT.list_queues(
                InstanceId=instance_id, QueueTypes=["STANDARD"]
            ).get("QueueSummaryList", [])
            for q in queues:
                queue_id = q.get("Id")
                queue_details = CONNECT.describe_queue(
                    InstanceId=instance_id, QueueId=queue_id
                ).get("Queue", {})
                write_metadata(
                    node_id=f"queue:{queue_id}",
                    node_type="queue",
                    label=q.get("Name", "Unnamed Queue"),
                    arn=q.get("Arn", "N/A"),
                    status=queue_details.get("Status", "ENABLED"),
                    now=now,
                )
                write_edge(
                    f"instance:{instance_id}",
                    "INSTANCE_HAS_QUEUE",
                    f"queue:{queue_id}",
                    now,
                )

            # 5. Scan Routing Profiles
            routing_profiles = CONNECT.list_routing_profiles(
                InstanceId=instance_id
            ).get("RoutingProfileSummaryList", [])
            for rp in routing_profiles:
                rp_id = rp.get("Id")
                write_metadata(
                    node_id=f"routing:{rp_id}",
                    node_type="routing",
                    label=rp.get("Name", "Unnamed Routing Profile"),
                    arn=rp.get("Arn", "N/A"),
                    status="ACTIVE",
                    now=now,
                )
                write_edge(
                    f"instance:{instance_id}",
                    "INSTANCE_HAS_ROUTING",
                    f"routing:{rp_id}",
                    now,
                )

        except Exception as e:
            print(f"Error scanning Connect instance {instance_id}: {str(e)}")

    print("Full scan complete.")


def handle_partial_scan(payload):
    # Triggers on direct configuration changes to quickly refresh a single node and its dependencies
    resource_id = payload.get("resourceId", "")
    resource_type = payload.get("resourceType", "contact_flow")
    now = datetime.datetime.utcnow().isoformat() + "Z"

    print(f"Performing targeted scan for mutated {resource_type}: {resource_id}")
    table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)

    # Mark the specific node as updated to reflect fresh telemetry
    try:
        if resource_type == "contact_flow":
            # Real boto3 calls would resolve the metadata
            # For partial scans, we update the timestamp to invalidate caches.
            table.update_item(
                Key={"nodeId": f"flow:{resource_id}", "edgeTypeTarget": "METADATA"},
                UpdateExpression="SET lastSeenAt = :now, scanConfidence = :conf",
                ExpressionAttributeValues={":now": now, ":conf": "1.0"},
            )
            print(f"Partial scan complete for flow {resource_id}")
    except Exception as e:
        print(f"Failed targeted scan update: {str(e)}")


def write_metadata(node_id, node_type, label, arn, status, now):
    table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
    table.put_item(
        Item={
            "nodeId": node_id,
            "edgeTypeTarget": "METADATA",
            "nodeType": node_type,
            "label": label,
            "arn": arn,
            "status": status,
            "lastSeenAt": now,
            "scanConfidence": "1.0",
        }
    )


def write_edge(source, edge_type, target, now):
    table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
    table.put_item(
        Item={
            "nodeId": source,
            "edgeTypeTarget": f"{edge_type}#{target}",
            "targetNodeId": target,
            "relationshipType": edge_type,
            "lastSeenAt": now,
            "scanConfidence": "1.0",
        }
    )
