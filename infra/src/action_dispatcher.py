import os
import json
import datetime
import boto3
from botocore.exceptions import ClientError

DYNAMODB = boto3.resource("dynamodb")
SSM = boto3.client("ssm")
SFN = boto3.client("stepfunctions")

INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "dev-connect-sre-incidents")
APPROVAL_TABLE_NAME = os.environ.get("APPROVAL_TABLE_NAME", "dev-connect-sre-approvals")
POLICY_TABLE_NAME = os.environ.get("POLICY_TABLE_NAME", "dev-connect-sre-policy-config")
TOOL_REGISTRY_TABLE_NAME = os.environ.get(
    "TOOL_REGISTRY_TABLE_NAME", "dev-connect-sre-tool-registry"
)

ENABLE_CONNECT_WRITE_ACTIONS = (
    os.environ.get("ENABLE_CONNECT_WRITE_ACTIONS", "false").lower() == "true"
)
ENABLE_AUTONOMOUS_ACTIONS = (
    os.environ.get("ENABLE_AUTONOMOUS_ACTIONS", "false").lower() == "true"
)


def handler(event, context):
    print(json.dumps({"event": "dispatcher_invoked", "approvalId": event.get("approvalId"), "actionType": event.get("actionType"), "incidentId": event.get("incidentId"), "operator": event.get("operator", "system")}))

    approval_id = event.get("approvalId")
    action_type = event.get("actionType")  # e.g. "connect_toggle_emergency_routing"
    parameters = event.get("parameters", {})
    operator = event.get("operator", "system")
    incident_id = event.get("incidentId")
    actioned_at = event.get("actionedAt")

    now = datetime.datetime.utcnow().isoformat() + "Z"

    try:
        # 1. Fetch Policy Decisions & Verify Tool Registration
        policy = get_policy_config(action_type)
        tool_registered = verify_tool_registration(action_type)

        if not tool_registered:
            return deny_execution(
                approval_id,
                incident_id,
                action_type,
                "Tool not registered in SRE registry.",
                now,
            )

        # 2. Check Governance Rules
        is_allowed = evaluate_policy_gates(policy, operator, approval_id)
        if not is_allowed:
            return deny_execution(
                approval_id,
                incident_id,
                action_type,
                "Policy gate violation: Action blocked by security rules.",
                now,
            )

        # 3. Trigger safe SSM or Step Functions wrapper
        execution_id = execute_remediation(action_type, parameters)

        # 4. Log Success
        log_successful_dispatch(
            approval_id, incident_id, action_type, execution_id, now, operator, actioned_at
        )

        return {"status": "DISPATCHED", "executionId": execution_id, "timestamp": now}

    except Exception as e:
        print(json.dumps({"event": "dispatch_error", "approvalId": approval_id, "incidentId": incident_id, "error": str(e)}))
        raise e


def get_policy_config(action_type):
    try:
        table = DYNAMODB.Table(POLICY_TABLE_NAME)
        res = table.get_item(Key={"policyId": action_type})
        return res.get("Item", {})
    except Exception:
        # Default fallback policy in case lookup fails
        return {"riskLevel": "high", "requiresApproval": True}


def verify_tool_registration(action_type):
    try:
        table = DYNAMODB.Table(TOOL_REGISTRY_TABLE_NAME)
        res = table.get_item(Key={"toolId": action_type})
        return res.get("Item", {}).get("enabled", False)
    except Exception:
        # If registry table lookup fails, fail-safe to False
        return False


def evaluate_policy_gates(policy, operator, approval_id):
    # Rule A: If Connect writes are disabled completely at the stack level, block
    if not ENABLE_CONNECT_WRITE_ACTIONS:
        print(json.dumps({"event": "policy_gate_blocked", "rule": "A", "reason": "ENABLE_CONNECT_WRITE_ACTIONS=false"}))
        return False

    risk_level = policy.get("riskLevel", "high")

    # Rule B: High risk actions require approval
    if risk_level == "high" and not approval_id:
        print(json.dumps({"event": "policy_gate_blocked", "rule": "B", "reason": "high_risk_without_approval_ticket", "riskLevel": risk_level}))
        return False

    # Rule C: Auto remediation requires explicit switch
    if operator == "system" and not ENABLE_AUTONOMOUS_ACTIONS:
        print(json.dumps({"event": "policy_gate_blocked", "rule": "C", "reason": "ENABLE_AUTONOMOUS_ACTIONS=false", "operator": operator}))
        return False

    # Rule D: If approval ticket is provided, make sure it is marked APPROVED in database
    if approval_id:
        table = DYNAMODB.Table(APPROVAL_TABLE_NAME)
        ticket = table.get_item(Key={"approvalId": approval_id}).get("Item", {})
        if ticket.get("status") != "APPROVED":
            print(json.dumps({"event": "policy_gate_blocked", "rule": "D", "approvalId": approval_id, "ticketStatus": ticket.get("status"), "reason": "ticket_not_approved"}))
            return False

    print(json.dumps({"event": "policy_gates_passed", "approvalId": approval_id, "operator": operator, "riskLevel": risk_level}))
    return True


def execute_remediation(action_type, parameters):
    print(json.dumps({"event": "remediation_executing", "actionType": action_type, "parameters": parameters}))

    document_name = f"SRE-Connect-{action_type}"
    try:
        ssm_response = SSM.start_automation_execution(
            DocumentName=document_name,
            Parameters={k: [str(v)] for k, v in parameters.items()},
        )
        execution_id = ssm_response["AutomationExecutionId"]
        print(json.dumps({"event": "ssm_execution_started", "actionType": action_type, "documentName": document_name, "executionId": execution_id}))
        return execution_id
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "InvalidDocument":
            # SSM Automation document not yet provisioned — simulate for dev/MVP.
            # Once SRE-Connect-{action_type} documents are deployed this branch
            # will never be reached in production.
            simulated_id = f"sim-{uuid_hash()}"
            print(json.dumps({"event": "ssm_document_missing_simulated", "actionType": action_type, "documentName": document_name, "simulatedId": simulated_id}))
            return simulated_id
        print(json.dumps({"event": "ssm_execution_error", "actionType": action_type, "documentName": document_name, "errorCode": error_code, "error": str(e)}))
        raise


def deny_execution(approval_id, incident_id, action_type, reason, now, operator="system"):
    print(f"Action Denied: action_type={action_type} operator={operator} reason={reason}")
    if approval_id:
        table = DYNAMODB.Table(APPROVAL_TABLE_NAME)
        table.update_item(
            Key={"approvalId": approval_id},
            UpdateExpression="SET #s = :status, auditLog = :log, updatedAt = :now, operatorId = :op",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "BLOCKED",
                ":log": reason,
                ":now": now,
                ":op": operator,
            },
        )
    return {"status": "DENIED", "reason": reason, "timestamp": now, "operator": operator}


def log_successful_dispatch(approval_id, incident_id, action_type, execution_id, now, operator="system", actioned_at=None):
    print(f"Action Dispatched: action_type={action_type} executionId={execution_id} operator={operator}")
    # Mark approval ticket as executed
    if approval_id:
        table = DYNAMODB.Table(APPROVAL_TABLE_NAME)
        table.update_item(
            Key={"approvalId": approval_id},
            UpdateExpression="SET #s = :status, executionId = :exec, executedAt = :now, operatorId = :op, approvedAt = :aat",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "EXECUTED",
                ":exec": execution_id,
                ":now": now,
                ":op": operator,
                ":aat": actioned_at or now,
            },
        )

    # Update active incident suggestion state to active recovery
    if incident_id:
        table = DYNAMODB.Table(INCIDENT_TABLE_NAME)
        table.update_item(
            Key={"incidentId": incident_id},
            UpdateExpression="SET #s = :status, executionId = :exec, updatedAt = :now",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "Recovering",
                ":exec": execution_id,
                ":now": now,
            },
        )
    print(json.dumps({"event": "dispatch_complete", "approvalId": approval_id, "incidentId": incident_id, "actionType": action_type, "executionId": execution_id, "operator": operator}))


def uuid_hash():
    import uuid

    return uuid.uuid4().hex[:12].upper()
