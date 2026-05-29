import os
import json
import datetime
import boto3
import re

DYNAMODB = boto3.resource("dynamodb")
CONNECT = boto3.client("connect")
LEX = boto3.client("lexv2-models")
LAMBDA = boto3.client("lambda")

TOPOLOGY_TABLE_NAME = os.environ.get("TOPOLOGY_TABLE_NAME", "dev-connect-sre-topology")
CONNECT_INSTANCE_IDS = [i for i in os.environ.get("CONNECT_INSTANCE_IDS", "").split(",") if i.strip()]


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
    
    # Auto-discover instances if not provided in env var
    instances_to_scan = CONNECT_INSTANCE_IDS
    if not instances_to_scan:
        try:
            print("No instances configured. Auto-discovering Connect instances...")
            instance_summaries = CONNECT.list_instances().get("InstanceSummaryList", [])
            instances_to_scan = [i.get("Id") for i in instance_summaries if i.get("Id")]
        except Exception as e:
            print(f"Failed to auto-discover instances: {e}")
            return

    for instance_id in instances_to_scan:
        if not instance_id:
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
            flows = []
            paginator_kwargs = {"InstanceId": instance_id}
            while True:
                resp = CONNECT.list_contact_flows(**paginator_kwargs)
                flows.extend(resp.get("ContactFlowSummaryList", []))
                next_token = resp.get("NextToken")
                if not next_token:
                    break
                paginator_kwargs["NextToken"] = next_token
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
                
                # Extract deep edges from flow content
                content = flow_details.get("Content", "")
                if content:
                    extract_flow_edges(instance_id, flow_id, content, now)

            # 3. Scan Contact Flow Modules
            modules = []
            paginator_kwargs = {"InstanceId": instance_id}
            while True:
                resp = CONNECT.list_contact_flow_modules(**paginator_kwargs)
                modules.extend(resp.get("ContactFlowModuleSummaryList", []))
                next_token = resp.get("NextToken")
                if not next_token:
                    break
                paginator_kwargs["NextToken"] = next_token
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
            queues = []
            paginator_kwargs = {"InstanceId": instance_id, "QueueTypes": ["STANDARD"]}
            while True:
                resp = CONNECT.list_queues(**paginator_kwargs)
                queues.extend(resp.get("QueueSummaryList", []))
                next_token = resp.get("NextToken")
                if not next_token:
                    break
                paginator_kwargs["NextToken"] = next_token
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
            routing_profiles = []
            paginator_kwargs = {"InstanceId": instance_id}
            while True:
                resp = CONNECT.list_routing_profiles(**paginator_kwargs)
                routing_profiles.extend(resp.get("RoutingProfileSummaryList", []))
                next_token = resp.get("NextToken")
                if not next_token:
                    break
                paginator_kwargs["NextToken"] = next_token
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

            # 6. Scan Lex V2 bots associated with the instance (instance-level association,
            #    independent of whether any flow references them by ARN in its content).
            try:
                bots_resp = CONNECT.list_bots(InstanceId=instance_id, LexVersion="V2", MaxResults=25)
                bot_list = bots_resp.get("LexBots") or bots_resp.get("LexBotConfigSummaryList", [])
                for b in bot_list:
                    inner = b.get("LexBotConfig", b)
                    alias_arn = inner.get("LexV2Bot", {}).get("AliasArn", "")
                    if not alias_arn:
                        continue
                    node_id = f"lex:{alias_arn}"
                    write_edge(f"instance:{instance_id}", "INSTANCE_HAS_LEX", node_id, now)
                    try:
                        parts = alias_arn.split("bot-alias/")
                        if len(parts) == 2:
                            ids = parts[1].split("/")
                            if len(ids) == 2:
                                bot_id, alias_id = ids[0], ids[1]
                                alias_detail = LEX.describe_bot_alias(botId=bot_id, botAliasId=alias_id)
                                write_metadata(
                                    node_id=node_id,
                                    node_type="lex",
                                    label=alias_detail.get("botAliasName", alias_id),
                                    arn=alias_arn,
                                    status=alias_detail.get("botAliasStatus", "Unknown"),
                                    now=now,
                                    extra={"botId": bot_id, "botAliasId": alias_id,
                                           "botVersion": alias_detail.get("botVersion", "Unknown")},
                                )
                    except Exception as e:
                        print(f"Warning: Could not describe Lex alias for {alias_arn}: {e}")
                        write_metadata(
                            node_id=node_id,
                            node_type="lex",
                            label=alias_arn.split("/")[-1],
                            arn=alias_arn,
                            status="Unknown",
                            now=now,
                        )
            except Exception as e:
                print(f"Warning: Could not list Lex bots for {instance_id}: {e}")

            # 7. Scan Phone Numbers
            try:
                phone_numbers = CONNECT.list_phone_numbers_v2(
                    TargetArn=instance_details.get("Arn")
                ).get("ListPhoneNumbersSummaryList", [])
                for pn in phone_numbers:
                    pn_id = pn.get("PhoneNumberId")
                    if not pn_id:
                        continue
                    write_metadata(
                        node_id=f"phone:{pn_id}",
                        node_type="phone_number",
                        label=pn.get("PhoneNumber", "Unknown Number"),
                        arn=pn.get("PhoneNumberArn", "N/A"),
                        status="ACTIVE",
                        now=now,
                    )
                    write_edge(
                        f"instance:{instance_id}",
                        "INSTANCE_HAS_PHONE",
                        f"phone:{pn_id}",
                        now,
                    )
                    target_arn = pn.get("TargetArn", "")
                    if "contact-flow/" in target_arn:
                        target_flow_id = target_arn.split("contact-flow/")[-1]
                        write_edge(
                            f"phone:{pn_id}",
                            "PHONE_ROUTES_TO_FLOW",
                            f"flow:{target_flow_id}",
                            now,
                        )
            except Exception as e:
                print(f"Warning: Could not fetch phone numbers for {instance_id}: {e}")

        except Exception as e:
            print(f"Error scanning Connect instance {instance_id}: {str(e)}")

    print("Full scan complete.")


def handle_partial_scan(payload):
    # Triggers on direct configuration changes to quickly refresh a single node and its dependencies
    resource_id = payload.get("resourceId", "")
    resource_type = payload.get("resourceType", "contact_flow")
    now = datetime.datetime.utcnow().isoformat() + "Z"

    print(f"Performing targeted scan for mutated {resource_type}: {resource_id}")
    
    # We need the instance_id to make boto3 calls. For MVP, we auto-discover it
    # or assume it's the first available if not provided in payload.
    instance_id = CONNECT_INSTANCE_IDS[0] if CONNECT_INSTANCE_IDS else None
    if not instance_id:
        try:
            instance_summaries = CONNECT.list_instances().get("InstanceSummaryList", [])
            instance_id = instance_summaries[0].get("Id") if instance_summaries else None
        except Exception:  # nosec B110
            pass

    if not instance_id:
        print("Cannot perform partial scan: No instance ID available.")
        return

    try:
        if resource_type == "contact_flow":
            flow_details = CONNECT.describe_contact_flow(
                InstanceId=instance_id, ContactFlowId=resource_id
            ).get("ContactFlow", {})
            
            write_metadata(
                node_id=f"flow:{resource_id}",
                node_type="flow",
                label=flow_details.get("Name", "Unnamed Flow"),
                arn=flow_details.get("Arn", "N/A"),
                status=flow_details.get("State", "ACTIVE"),
                now=now,
            )
            content = flow_details.get("Content", "")
            if content:
                extract_flow_edges(instance_id, resource_id, content, now)
                
            print(f"Partial scan complete for flow {resource_id}")
            
        elif resource_type == "contact_flow_module":
            mod_details = CONNECT.describe_contact_flow_module(
                InstanceId=instance_id, ContactFlowModuleId=resource_id
            ).get("ContactFlowModule", {})
            write_metadata(
                node_id=f"module:{resource_id}",
                node_type="module",
                label=mod_details.get("Name", "Unnamed Module"),
                arn=mod_details.get("Arn", "N/A"),
                status=mod_details.get("State", "ACTIVE"),
                now=now,
            )
            print(f"Partial scan complete for module {resource_id}")
            
    except Exception as e:
        print(f"Failed targeted scan update for {resource_type} {resource_id}: {str(e)}")


def write_metadata(node_id, node_type, label, arn, status, now, extra=None):
    table = DYNAMODB.Table(TOPOLOGY_TABLE_NAME)
    item = {
        "nodeId": node_id,
        "edgeTypeTarget": "METADATA",
        "nodeType": node_type,
        "label": label,
        "arn": arn,
        "status": status,
        "lastSeenAt": now,
        "scanConfidence": "1.0",
    }
    if extra:
        item.update(extra)
    table.put_item(Item=item)


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


def extract_flow_edges(instance_id, flow_id, content, now):
    """
    Parses the JSON Content of a contact flow to extract dependencies.
    """
    # 1. Extract Lambda functions
    lambda_arns = set(re.findall(r'arn:aws:lambda:[^"]+?:function:[a-zA-Z0-9-_]+', content))
    for l_arn in lambda_arns:
        write_edge(f"flow:{flow_id}", "FLOW_USES_LAMBDA", f"lambda:{l_arn}", now)

    # 2. Extract Lex V2 bots
    # ARN format: arn:aws:lex:region:account:bot-alias/BOT_ID/ALIAS_ID
    lex_arns = set(re.findall(r'arn:aws:lex:[^"]+?:bot-alias/[A-Za-z0-9]+/[A-Za-z0-9]+', content))
    for lx_arn in lex_arns:
        node_id = f"lex:{lx_arn}"
        write_edge(f"flow:{flow_id}", "FLOW_USES_LEX", node_id, now)
        # Write metadata using the Lex V2 API (lexv2-models).
        # ARN format: arn:aws:lex:region:account:bot-alias/BOT_ID/ALIAS_ID
        try:
            parts = lx_arn.split("bot-alias/")
            if len(parts) == 2:
                ids = parts[1].split("/")
                if len(ids) == 2:
                    bot_id, alias_id = ids[0], ids[1]
                    alias_detail = LEX.describe_bot_alias(botId=bot_id, botAliasId=alias_id)
                    alias_name = alias_detail.get("botAliasName", alias_id)
                    alias_status = alias_detail.get("botAliasStatus", "Unknown")
                    bot_version = alias_detail.get("botVersion", "Unknown")
                    write_metadata(
                        node_id=node_id,
                        node_type="lex",
                        label=alias_name,
                        arn=lx_arn,
                        status=alias_status,
                        now=now,
                        extra={"botId": bot_id, "botAliasId": alias_id, "botVersion": bot_version},
                    )
        except Exception as e:
            print(f"Warning: Could not describe Lex alias for {lx_arn}: {e}")
            write_metadata(
                node_id=node_id,
                node_type="lex",
                label=lx_arn.split("/")[-1],
                arn=lx_arn,
                status="Unknown",
                now=now,
            )

    # 3. Extract Queues
    # Format: arn:aws:connect:region:account:instance/id/queue/queue-id
    queue_ids = set(re.findall(r'instance/[^/]+/queue/([a-zA-Z0-9-]+)', content))
    for q_id in queue_ids:
        write_edge(f"flow:{flow_id}", "FLOW_ROUTES_TO_QUEUE", f"queue:{q_id}", now)

    # 4. Extract Modules
    # Format: arn:aws:connect:region:account:instance/id/contact-flow-module/module-id
    module_ids = set(re.findall(r'instance/[^/]+/contact-flow-module/([a-zA-Z0-9-]+)', content))
    for m_id in module_ids:
        write_edge(f"flow:{flow_id}", "FLOW_USES_MODULE", f"module:{m_id}", now)

